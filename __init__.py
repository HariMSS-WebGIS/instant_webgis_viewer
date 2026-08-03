# Instant WebGIS Viewer — QGIS Plugin
# Export QGIS vector layers to a shareable interactive HTML map
# Copyright (C) 2026 Ballu Harish
# Email: harishmanjulason@gmail.com
# GitHub: https://github.com/HariMSS/instant_webgis_viewer
# Licensed under GNU General Public License v2 or later

def classFactory(iface):
    from .main_plugin import QuickShareMap
    return QuickShareMap(iface)
