# Instant WebGIS Viewer — QGIS Plugin
# Export QGIS vector layers to a shareable interactive HTML map
# Copyright (C) 2026 Ballu Harish
# Email: harishmanjulason@gmail.com
# GitHub: https://github.com/HariMSS/instant_webgis_viewer
# Licensed under GNU General Public License v2 or later

import os
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject


class QuickShareMap:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

    def initGui(self):
        icon = os.path.join(self.plugin_dir, 'icon.png')
        self.action = QAction(QIcon(icon), 'Instant WebGIS Viewer', self.iface.mainWindow())
        self.action.setToolTip('Interactive WebGIS Map')
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToWebMenu('Instant WebGIS Viewer', self.action)

    def unload(self):
        self.iface.removePluginWebMenu('Instant WebGIS Viewer', self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        if not list(QgsProject.instance().mapLayers().values()):
            QMessageBox.warning(self.iface.mainWindow(), 'No Layers',
                'Please load at least one layer in QGIS first.')
            return
        from .export_dialog import ExportDialog
        ExportDialog(self.iface, self.iface.mainWindow()).exec_()
