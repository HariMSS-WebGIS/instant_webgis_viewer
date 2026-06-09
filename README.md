# Instant WebGIS Viewer — QGIS Plugin

**Export any QGIS vector layer to a fully interactive shareable HTML map in one click.**

No server. No Apache. No configuration. Just click Export and share!

---

## Features

| Feature | Description |
|---|---|
| 🎨 **Auto QGIS Styling** | Reads your QGIS layer colours and applies them to the HTML map |
| 📊 **Statistics Panel** | Feature count, total length (km), total area (km²), CRS, field count |
| 📋 **Attribute Table** | Full table with pagination (100 rows/page), click row to zoom to feature |
| 🔍 **Feature Search** | Search any attribute value across all layers |
| 📍 **Feature Info Popup** | Click any feature to see all its attributes |
| 🗺 **9 Basemaps** | OSM, USGS Imagery, Topo, Carto Dark/Light, ESRI Street/Imagery, BrightGray, None |
| 📏 **Measurement Tool** | Measure distance and area on the map |
| 🖨 **Print Button** | One-click print-ready map output |
| 📴 **Works Offline** | Exported HTML is fully self-contained, no internet needed to view |

---

## Supported Layer Types

- ✅ Point, Line, and Polygon layers
- ✅ Any CRS (auto-reprojected to WGS84)
- ✅ Shapefile, GeoPackage, GeoJSON, CSV with geometry
- ❌ Raster layers (not supported)

---

## Installation

### From QGIS Plugin Repository
1. **Plugins → Manage and Install Plugins**
2. Search **Instant WebGIS Viewer** → Install

### From ZIP
1. **Plugins → Manage and Install Plugins → Install from ZIP**
2. Select `instant_webgis_viewer.zip` → Install

---

## Usage

1. Load your layers in QGIS
2. Click **Instant WebGIS Viewer** in the toolbar or Web menu
3. Select layers to export
4. Set map title and output location
5. Click **Export Map**
6. Open the HTML file in any browser

### To open on mobile
Send the HTML file to your phone via WhatsApp or Email — it opens directly in the mobile browser and works offline.

---

## Requirements

- QGIS 3.16 or later
- Windows, macOS, or Linux

---

## License

GNU General Public License v2 or later.
Copyright (C) 2026 Ballu Harish

## Author

**Ballu Harish**
Email: harishmanjulason@gmail.com
GitHub: https://github.com/HariMSS/instant_webgis_viewer
