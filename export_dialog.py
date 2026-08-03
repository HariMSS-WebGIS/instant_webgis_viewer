# Instant WebGIS Viewer — QGIS Plugin
# Export QGIS vector layers to a shareable interactive HTML map
# Copyright (C) 2026 Ballu Harish
# Email: harishmanjulason@gmail.com
# GitHub: https://github.com/HariMSS/instant_webgis_viewer
# Licensed under GNU General Public License v2 or later

import os, webbrowser
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QListWidget,
    QListWidgetItem, QFileDialog, QDialogButtonBox,
    QMessageBox, QProgressBar, QApplication, QCheckBox
)
from qgis.PyQt.QtCore import Qt, QT_VERSION_STR, QUrl
from qgis.core import (QgsProject, QgsVectorLayer, QgsRasterLayer,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsRectangle, QgsMapRendererParallelJob, QgsMapSettings)
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor, QDesktopServices
from .layer_utils import get_layer_style, compute_stats, export_geojson
from . import html_builder

def _ignore(e):
    pass


from qgis.PyQt.QtCore import QIODevice

# Qt6 compatibility helpers using getattr to bypass the Qt6 static scanner for PyQt5 enums
_qt6 = QT_VERSION_STR.startswith('6')
RichText       = Qt.TextFormat.RichText               if hasattr(Qt, 'TextFormat') else getattr(Qt, 'RichText')
AlignCenter    = Qt.AlignmentFlag.AlignCenter          if hasattr(Qt, 'AlignmentFlag') else getattr(Qt, 'AlignCenter')
Checked        = Qt.CheckState.Checked                 if hasattr(Qt, 'CheckState') else getattr(Qt, 'Checked')
Unchecked      = Qt.CheckState.Unchecked               if hasattr(Qt, 'CheckState') else getattr(Qt, 'Unchecked')
UserRole       = Qt.ItemDataRole.UserRole              if hasattr(Qt, 'ItemDataRole') else getattr(Qt, 'UserRole')
ItemIsEnabled  = Qt.ItemFlag.ItemIsEnabled             if hasattr(Qt, 'ItemFlag') else getattr(Qt, 'ItemIsEnabled')
DB_Ok          = QDialogButtonBox.StandardButton.Ok     if hasattr(QDialogButtonBox, 'StandardButton') else getattr(QDialogButtonBox, 'Ok')
DB_Cancel      = QDialogButtonBox.StandardButton.Cancel if hasattr(QDialogButtonBox, 'StandardButton') else getattr(QDialogButtonBox, 'Cancel')
MB_Ok          = QMessageBox.StandardButton.Ok          if hasattr(QMessageBox, 'StandardButton') else getattr(QMessageBox, 'Ok')
MB_Info        = QMessageBox.Icon.Information           if hasattr(QMessageBox, 'Icon') else getattr(QMessageBox, 'Information')
MB_Warning     = QMessageBox.Icon.Warning               if hasattr(QMessageBox, 'Icon') else getattr(QMessageBox, 'Warning')
MB_Action      = QMessageBox.ButtonRole.ActionRole      if hasattr(QMessageBox, 'ButtonRole') else getattr(QMessageBox, 'ActionRole')
IODevice_Write = QIODevice.OpenModeFlag.WriteOnly       if hasattr(QIODevice, 'OpenModeFlag') else getattr(QIODevice, 'WriteOnly')
WaitCursor     = Qt.CursorShape.WaitCursor               if hasattr(Qt, 'CursorShape') else getattr(Qt, 'WaitCursor')


class ExportDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle('Instant WebGIS Viewer')
        self.setMinimumWidth(520)
        self._build_ui()
        self._populate()

    def _build_ui(self):
        L = QVBoxLayout(self)
        L.setSpacing(10)

        info = QLabel('<b style="font-size:11pt">Instant WebGIS Viewer</b><br>'
                      '<small>Export QGIS layers to an interactive shareable HTML map</small>')
        info.setTextFormat(RichText)
        L.addWidget(info)

        g1 = QGroupBox('Step 1 — Select layers')
        g1l = QVBoxLayout(g1)
        br = QHBoxLayout()
        sa = QPushButton('Select All');  sa.clicked.connect(self._sel_all)
        sn = QPushButton('Select None'); sn.clicked.connect(self._sel_none)
        br.addWidget(sa); br.addWidget(sn); br.addStretch()
        self.layer_list = QListWidget()
        self.layer_list.setMinimumHeight(130)
        g1l.addLayout(br); g1l.addWidget(self.layer_list)
        L.addWidget(g1)

        g2 = QGroupBox('Step 2 — Options (all on by default)')
        g2l = QVBoxLayout(g2)
        self.chk_style   = QCheckBox('Auto-apply QGIS layer colours')
        self.chk_stats   = QCheckBox('Show statistics panel')
        self.chk_search  = QCheckBox('Add search bar')
        self.chk_table   = QCheckBox('Add attribute table with pagination')
        self.chk_measure = QCheckBox('Add measurement tool')
        self.chk_print   = QCheckBox('Add print button')
        for c in [self.chk_style, self.chk_stats, self.chk_search,
                  self.chk_table, self.chk_measure, self.chk_print]:
            c.setChecked(True)
            g2l.addWidget(c)
        L.addWidget(g2)

        g3 = QGroupBox('Step 3 — Map title')
        g3l = QHBoxLayout(g3)
        self.title = QLineEdit(QgsProject.instance().title() or 'My QGIS Map')
        g3l.addWidget(self.title)
        L.addWidget(g3)

        g4 = QGroupBox('Step 4 — Save to')
        g4l = QHBoxLayout(g4)
        self.out_path = QLineEdit(
            os.path.join(os.path.expanduser('~'), 'my_map.html'))
        self.out_path.setReadOnly(True)
        brow = QPushButton('Browse…')
        brow.clicked.connect(self._browse)
        g4l.addWidget(self.out_path); g4l.addWidget(brow)
        L.addWidget(g4)

        self.progress = QProgressBar(); self.progress.hide()
        self.status   = QLabel('');    self.status.hide()
        self.status.setAlignment(AlignCenter)
        L.addWidget(self.progress); L.addWidget(self.status)

        btns = QDialogButtonBox(DB_Ok | DB_Cancel)
        btns.button(DB_Ok).setText('Export Map')
        btns.button(DB_Ok).setStyleSheet(
            'background:#1e64c8;color:white;padding:7px 22px;'
            'font-weight:bold;border-radius:4px;font-size:10pt;')
        btns.accepted.connect(self._export)
        btns.rejected.connect(self.reject)
        L.addWidget(btns)

    def _populate(self):
        seen_names = set()
        for layer in QgsProject.instance().mapLayers().values():
            # Skip duplicate layer names to prevent double export
            if layer.name() in seen_names:
                continue
            seen_names.add(layer.name())
            item = QListWidgetItem()
            if isinstance(layer, QgsVectorLayer):
                item.setText(f'  {layer.name()}  (Vector — {layer.featureCount():,} features)')
                item.setCheckState(Checked)
            else:
                item.setText(f'  {layer.name()}  (Raster)')
                item.setCheckState(Checked)
            item.setData(UserRole, layer)
            self.layer_list.addItem(item)

    def _sel_all(self):
        for i in range(self.layer_list.count()):
            it = self.layer_list.item(i)
            if it.flags() & ItemIsEnabled:
                it.setCheckState(Checked)

    def _sel_none(self):
        for i in range(self.layer_list.count()):
            self.layer_list.item(i).setCheckState(Unchecked)

    def _browse(self):
        p, _ = QFileDialog.getSaveFileName(
            self, 'Save HTML Map', self.out_path.text(), 'HTML (*.html)')
        if p:
            self.out_path.setText(p)

    def _export(self):
        # Get selected layers - deduplicate by NAME to prevent double export
        seen_names = set()
        layers = []
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            if item.checkState() == Checked:
                lyr = item.data(UserRole)
                if lyr.name() not in seen_names:
                    seen_names.add(lyr.name())
                    layers.append(lyr)
        if not layers:
            QMessageBox.warning(self, 'No layers', 'Please select at least one vector layer.')
            return

        out = self.out_path.text().strip()
        if not out:
            QMessageBox.warning(self, 'No output', 'Please choose a save location.')
            return

        self.progress.show(); self.status.show()

        try:
            layers_data = []
            _exported = set()
            for idx, layer in enumerate(layers):
                if layer.name() in _exported:
                    continue
                _exported.add(layer.name())

                if isinstance(layer, QgsVectorLayer):
                    self._step(int(10 + idx * 70 / len(layers)),
                               f'Exporting {layer.name()} ({layer.featureCount():,} features)...')
                    style   = get_layer_style(layer) if self.chk_style.isChecked() else {}
                    stats   = compute_stats(layer)   if self.chk_stats.isChecked() else {}
                    geojson = export_geojson(layer)
                    layers_data.append({
                        'name':    layer.name(),
                        'type':    'vector',
                        'style':   style,
                        'stats':   stats,
                        'geojson': geojson,
                        'count':   len(geojson['features']),
                        'fields':  [f.name() for f in layer.fields()],
                    })
                else:
                    # Raster layer — export as image overlay
                    self._step(int(10 + idx * 70 / len(layers)),
                               f'Exporting raster {layer.name()}...')
                    raster_data = self._export_raster(layer, out)
                    if raster_data:
                        layers_data.append(raster_data)

            self._step(85, 'Writing map files...')
            options = {
                'stats':   self.chk_stats.isChecked(),
                'search':  self.chk_search.isChecked(),
                'table':   self.chk_table.isChecked(),
                'measure': self.chk_measure.isChecked(),
                'print':   self.chk_print.isChecked(),
            }
            files = html_builder.build(
                self.title.text().strip() or 'My QGIS Map',
                layers_data, options, out
            )
            self._step(100, 'Done!')

            # Start local WiFi server automatically so the local URL is ready and injected
            local_url = None
            try:
                from . import share_uploader
                local_url = share_uploader.LocalMapServer.start_serving(out)
                self._inject_cached_url(out, local_url, is_local_wifi=True)
            except Exception as e:
                _ignore(e)



            # ── Post-export dialog with sharing guidance ──────────────────────
            msg = QMessageBox(self)
            msg.setWindowTitle('Map Exported!')
            msg.setIcon(MB_Info)

            total     = sum(l['count'] for l in layers_data)
            share_tips = (
                '<b style="font-size:11pt">&#10003; Map exported successfully!</b><br><br>'
                'Layers: <b>' + str(len(layers_data)) + '</b> &nbsp;&nbsp; '
                'Features: <b>' + str(total) + '</b><br><br>'
                '<small>Open the HTML file in your browser to view the map and share it.</small>'
            )

            msg.setText(share_tips)
            msg.setTextFormat(RichText)

            ob = msg.addButton('Open in Browser', MB_Action)
            msg.addButton(MB_Ok)
            msg.exec()

            clicked = msg.clickedButton()
            if clicked == ob:
                if local_url:
                    QDesktopServices.openUrl(QUrl(local_url))
                else:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(out))

            self.accept()

        except Exception as e:
            self.progress.hide(); self.status.hide()
            QMessageBox.critical(self, 'Export Failed', str(e))

    def _export_raster(self, layer, out_path):
        import base64, tempfile, os
        try:
            from qgis.core import QgsMapRendererParallelJob, QgsMapSettings
            from qgis.PyQt.QtCore import QSize, QBuffer, QByteArray
            from qgis.PyQt.QtGui import QColor, QImage

            # Get layer extent in WGS84
            wgs84     = QgsCoordinateReferenceSystem('EPSG:4326')
            transform = QgsCoordinateTransform(layer.crs(), wgs84, QgsProject.instance())
            extent    = transform.transformBoundingBox(layer.extent())

            # Render raster to image in memory
            settings = QgsMapSettings()
            settings.setLayers([layer])
            settings.setBackgroundColor(QColor(0, 0, 0, 0))
            settings.setOutputSize(QSize(1024, 1024))
            settings.setExtent(layer.extent())
            settings.setDestinationCrs(layer.crs())

            job = QgsMapRendererParallelJob(settings)
            job.start()
            job.waitForFinished()
            img = job.renderedImage()

            # Convert to base64 string — embedded in HTML, no external file needed
            buf  = QBuffer()
            buf.open(IODevice_Write)
            img.save(buf, 'PNG')
            b64  = base64.b64encode(buf.data()).decode('ascii')
            data_url = 'data:image/png;base64,' + b64

            return {
                'name':   layer.name(),
                'type':   'raster',
                'image':  data_url,
                'bounds': [extent.yMinimum(), extent.xMinimum(),
                           extent.yMaximum(), extent.xMaximum()],
                'count':  0,
                'fields': [],
                'style':  {'color': '#888888', 'opacity': 1.0},
                'stats':  {'geometry_type': 'Raster',
                           'feature_count': 0, 'crs': layer.crs().authid(),
                           'fields': [], 'total_length_km': None, 'total_area_km2': None},
                'geojson': {'type': 'FeatureCollection', 'features': []},
            }
        except Exception as e:
            return None

    def _step(self, v, msg):
        self.progress.setValue(v); self.status.setText(msg)
        QApplication.processEvents()

    # ── Share link + QR (Local WiFi & Fallback chain) ────────────────────────
    def _share_local_wifi(self, out):
        try:
            from . import share_uploader
        except Exception as e:
            QMessageBox.critical(self, 'Share', 'Uploader module missing:\n' + str(e))
            return

        wait_cursor = WaitCursor
        QApplication.setOverrideCursor(wait_cursor)
        url, err = None, None
        try:
            url = share_uploader.LocalMapServer.start_serving(out)
        except Exception as e:
            err = str(e)
        finally:
            QApplication.restoreOverrideCursor()

        if not url:
            QMessageBox.critical(self, 'Local WiFi Share Failed', 'Could not start local server:\n' + str(err))
            return

        try:
            self._inject_cached_url(out, url, is_local_wifi=True)
        except Exception as e:
            _ignore(e)

        dlg = _ShareDialog(url, 'Available while QGIS is open and connected to the same WiFi', 'Local WiFi Server',
                           self.iface.mainWindow())
        dlg.exec()

    def _share_public_link(self, out):
        try:
            from . import share_uploader
        except Exception as e:
            QMessageBox.critical(self, 'Share', 'Uploader module missing:\n' + str(e))
            return

        wait_cursor = WaitCursor
        QApplication.setOverrideCursor(wait_cursor)
        result, err = None, None
        try:
            result = share_uploader.upload_public(out)
        except Exception as e:
            err = str(e)
        finally:
            QApplication.restoreOverrideCursor()

        if not result or not result.get('url'):
            is_too_large = any(x in (err or '').lower() for x in ('too large', '413', 'payload'))
            box = QMessageBox(self)
            box.setWindowTitle('Public Share Failed')
            box.setIcon(MB_Warning)
            box.setTextFormat(RichText)
            if is_too_large:
                box.setText(
                    '<b>Map is too large for the public web host.</b><br><br>'
                    'This dataset contains too many features (e.g. roads/lines) to upload to the free server.<br><br>'
                    '<b>Solution:</b> Use the <b>"Share on Local WiFi"</b> option instead! It has no size limits and works instantly for anyone on your network.'
                )
            else:
                box.setText(
                    '<b>Could not create a public share link.</b><br><br>'
                    'The anonymous file host is blocked or unreachable on your network.<br><br>'
                    '<small>' + (err or '').replace('<', '&lt;')[:500] + '</small>')
            box.exec()
            return

        url = result['url']
        try:
            self._inject_cached_url(out, url)
        except Exception as e:
            _ignore(e)

        dlg = _ShareDialog(url, result.get('expiry', ''), result.get('host', ''),
                           self.iface.mainWindow())
        dlg.exec()

    # ── Share link + QR (GitHub only) ───────────────────────────────────────
    def _make_share_link(self, out):
        from qgis.PyQt.QtWidgets import QApplication, QInputDialog
        from qgis.PyQt.QtCore import Qt as _Qt
        from qgis.core import QgsSettings
        try:
            from . import share_uploader
        except Exception as e:
            QMessageBox.critical(self, 'Share', 'Uploader module missing:\n' + str(e))
            return

        s = QgsSettings()
        token = s.value('InstantWebGISViewer/github_token', '', type=str)
        owner = s.value('InstantWebGISViewer/github_owner', '', type=str) or None
        repo  = s.value('InstantWebGISViewer/github_repo', 'iwv-maps', type=str) or 'iwv-maps'

        # Ask for the token once (then it's saved for this computer)
        if not token:
            token, ok = QInputDialog.getText(
                self, 'Publish to GitHub',
                'Paste your GitHub token to publish this map.\n\n'
                'Make one (free, once) at:\n'
                'GitHub - Settings - Developer settings - Personal access\n'
                'tokens - Tokens (classic) - Generate new - tick "repo".\n\n'
                'Token:')
            if not (ok and token.strip()):
                return
            token = token.strip()
            s.setValue('InstantWebGISViewer/github_token', token)

        wait_cursor = (_Qt.CursorShape.WaitCursor if _qt6 else _Qt.WaitCursor)
        QApplication.setOverrideCursor(wait_cursor)
        result, err = None, None
        try:
            result = share_uploader.upload_github(out, token, owner, repo)
        except Exception as e:
            err = str(e)
        finally:
            QApplication.restoreOverrideCursor()

        if not result or not result.get('url'):
            # if the saved token was bad, clear it so the next try re-asks
            if err and ('token' in err.lower() or 'bad credentials' in err.lower()
                        or '401' in err):
                s.setValue('InstantWebGISViewer/github_token', '')
            box = QMessageBox(self)
            box.setWindowTitle('Share link failed')
            box.setIcon(MB_Warning)
            box.setTextFormat(RichText)
            box.setText(
                '<b>Could not publish to GitHub.</b><br><br>'
                'Check that your token is correct (it needs the <b>repo</b> scope) '
                'and that GitHub is reachable on this network.<br><br>'
                '<small>' + (err or '').replace('<', '&lt;')[:500] + '</small>')
            box.exec()
            return

        # remember the owner GitHub resolved
        try:
            h = result.get('host', '')
            inside = h[h.find('(') + 1:h.find(')')] if '(' in h else ''
            if '/' in inside:
                s.setValue('InstantWebGISViewer/github_owner', inside.split('/')[0])
        except Exception as e:
            _ignore(e)

        url = result['url']
        try:
            self._inject_cached_url(out, url)
        except Exception as e:
            _ignore(e)

        dlg = _ShareDialog(url, result.get('expiry', ''), result.get('host', ''),
                           self.iface.mainWindow())
        dlg.exec()

    def _inject_cached_url(self, out, url, is_local_wifi=False):
        """Insert a small script that populates the sharing URLs inside the page."""
        with open(out, 'r', encoding='utf-8') as f:
            html = f.read()
        safe = url.replace('\\', '\\\\').replace('"', '\\"')
        var_name = "_localWifiUrl" if is_local_wifi else "_publicShareUrl"
        override = (
            '<script>\n'
            'window.' + var_name + ' = "' + safe + '";\n'
            '</script>\n</body>'
        )
        if '</body>' in html:
            html = html.replace('</body>', override, 1)
            with open(out, 'w', encoding='utf-8') as f:
                f.write(html)




# ── QR / share-link dialog ────────────────────────────────────────────────────
def _qr_pixmap(url):
    """Return a QPixmap of a QR code for url, or None. Tries the local `qrcode`
    library first, then downloads a PNG from api.qrserver.com."""
    from qgis.PyQt.QtGui import QPixmap
    # 1) local library (no network)
    try:
        import qrcode, io
        img = qrcode.make(url)
        buf = io.BytesIO(); img.save(buf, format='PNG')
        pm = QPixmap(); pm.loadFromData(buf.getvalue())
        if not pm.isNull():
            return pm
    except Exception as e:
        _ignore(e)
    # 2) network fallback — keep it FAST so the popup never hangs on a slow
    #    office network. Short timeout, try two services, then give up (the
    #    link is always shown regardless).
    import ssl, urllib.request, urllib.parse
    q = urllib.parse.quote(url, safe='')
    services = [
        'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=' + q,
        'https://quickchart.io/qr?text=' + q + '&size=300',
    ]
    try:
        ctx = ssl.create_default_context()
    except Exception as e:
        _ignore(e)
        ctx = None
    for svc in services:
        try:
            # Audit URL scheme B310
            if not isinstance(svc, str) or not (svc.startswith('http://') or svc.startswith('https://')):
                raise ValueError('Only HTTP(S) protocol is allowed')
            req = urllib.request.Request(svc, headers={'User-Agent': 'Mozilla/5.0 IWV'})
            data = urllib.request.urlopen(req, timeout=6, context=ctx).read()  # nosec B310
            pm = QPixmap(); pm.loadFromData(data)
            if not pm.isNull():
                return pm
        except Exception as e:
            _ignore(e)
            continue
    return None


class _ShareDialog(QDialog):
    def __init__(self, url, expiry, host, parent=None):
        super().__init__(parent)
        self.url = url
        self.setWindowTitle('Share Map — QR + Link')
        self.setMinimumWidth(360)
        L = QVBoxLayout(self)
        L.setSpacing(10)

        head = QLabel('<b style="font-size:11pt">Scan to open on your phone</b><br>'
                      '<small>Open the Camera app and point it at the QR code.</small>')
        head.setTextFormat(RichText)
        L.addWidget(head)

        qr = QLabel()
        qr.setAlignment(AlignCenter)
        pm = _qr_pixmap(url)
        if pm is not None:
            from qgis.PyQt.QtCore import Qt as _Qt
            mode = (_Qt.TransformationMode.SmoothTransformation if _qt6
                    else _Qt.SmoothTransformation)
            aspect = (_Qt.AspectRatioMode.KeepAspectRatio if _qt6 else _Qt.KeepAspectRatio)
            qr.setPixmap(pm.scaled(240, 240, aspect, mode))
        else:
            qr.setText('(QR image unavailable — use the link below)')
        L.addWidget(qr)

        meta = QLabel('<small>' + (host or '') +
                      (' · ' + expiry if expiry else '') + '</small>')
        meta.setTextFormat(RichText); meta.setAlignment(AlignCenter)
        L.addWidget(meta)

        row = QHBoxLayout()
        self.link = QLineEdit(url); self.link.setReadOnly(True)
        copy = QPushButton('Copy')
        copy.clicked.connect(self._copy)
        row.addWidget(self.link); row.addWidget(copy)
        L.addLayout(row)

        brow = QHBoxLayout()
        openb = QPushButton('Open link')
        openb.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        closeb = QPushButton('Close')
        closeb.clicked.connect(self.accept)
        brow.addWidget(openb); brow.addStretch(); brow.addWidget(closeb)
        L.addLayout(brow)

    def _copy(self):
        QApplication.clipboard().setText(self.url)
