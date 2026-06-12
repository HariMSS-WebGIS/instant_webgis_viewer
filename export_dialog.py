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
from qgis.PyQt.QtCore import Qt, QT_VERSION_STR
from qgis.core import (QgsProject, QgsVectorLayer, QgsRasterLayer,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsRectangle, QgsMapRendererParallelJob, QgsMapSettings)
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor
from .layer_utils import get_layer_style, compute_stats, export_geojson
from . import html_builder

from qgis.PyQt.QtCore import QIODevice

# Qt6 compatibility helpers
_qt6 = QT_VERSION_STR.startswith('6')
RichText       = Qt.TextFormat.RichText               if _qt6 else Qt.RichText
AlignCenter    = Qt.AlignmentFlag.AlignCenter          if _qt6 else Qt.AlignCenter
Checked        = Qt.CheckState.Checked                 if _qt6 else Qt.Checked
Unchecked      = Qt.CheckState.Unchecked               if _qt6 else Qt.Unchecked
UserRole       = Qt.ItemDataRole.UserRole              if _qt6 else Qt.UserRole
ItemIsEnabled  = Qt.ItemFlag.ItemIsEnabled             if _qt6 else Qt.ItemIsEnabled
DB_Ok          = QDialogButtonBox.StandardButton.Ok     if _qt6 else QDialogButtonBox.Ok
DB_Cancel      = QDialogButtonBox.StandardButton.Cancel if _qt6 else QDialogButtonBox.Cancel
MB_Ok          = QMessageBox.StandardButton.Ok          if _qt6 else QMessageBox.Ok
MB_Info        = QMessageBox.Icon.Information           if _qt6 else QMessageBox.Information
MB_Action      = QMessageBox.ButtonRole.ActionRole      if _qt6 else QMessageBox.ActionRole
IODevice_Write = QIODevice.OpenModeFlag.WriteOnly       if _qt6 else QIODevice.WriteOnly


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

            # ── Post-export dialog with sharing guidance ──────────────────────
            msg = QMessageBox(self)
            msg.setWindowTitle('Map Exported!')
            msg.setIcon(MB_Info)

            total     = sum(l['count'] for l in layers_data)
            share_tips = (
                '<b style="font-size:11pt">&#10003; Map exported successfully!</b><br><br>'
                'Layers: <b>' + str(len(layers_data)) + '</b> &nbsp;&nbsp; '
                'Features: <b>' + str(total) + '</b><br><br>'
                '<small>Open the HTML file in your browser, then click <b>Share / QR</b> '
                'to generate a QR code and share on mobile.</small>'
            )

            msg.setText(share_tips)
            msg.setTextFormat(RichText)

            ob = msg.addButton('Open in Browser', MB_Action)
            msg.addButton(MB_Ok)
            msg.exec()

            if msg.clickedButton() == ob:
                webbrowser.open('file:///' + out.replace('\\', '/'))

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
