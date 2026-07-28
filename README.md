# Instant WebGIS Viewer — QGIS Plugin

**Export any QGIS vector or raster layer to a fully interactive shareable HTML map in one click.**

No server. No Apache. No configuration. Just click Export and share!

---

## Features

| Feature | Description |
|---|---|
| 🎨 **Auto QGIS Styling** | Reads your QGIS layer colours and applies them to the HTML map |
| 🎨 **Colour Picker** | Change vector layer colours interactively in the HTML map |
| 📊 **Statistics Panel** | Feature count, total length (km), total area (km²), CRS, field count |
| 📋 **Attribute Table** | Full table with pagination (100 rows/page), click row to zoom to feature |
| 🔍 **Feature Search** | Search any attribute value across all layers |
| 📍 **Feature Info Popup** | Click any feature to see all its attributes |
| 🗺 **9 Basemaps** | OSM, USGS Imagery, Topo, Carto Dark/Light, ESRI Street/Imagery, BrightGray, None |
| 📱 **QR + Link Sharing** | One click makes a QR code + link. People you share with just scan/tap — no account or setup needed to view |
| 🖨 **Print Button** | One-click print-ready map output |
| 📴 **Works Offline** | Exported HTML is fully self-contained, no internet needed to view |

---

## Supported Layer Types

| Layer Type | Supported |
|---|---|
| Vector Point | ✅ |
| Vector Line | ✅ |
| Vector Polygon | ✅ |
| Raster (GeoTIFF, Satellite etc.) | ✅ |
| Any CRS (auto-reprojected to WGS84) | ✅ |
| Shapefile, GeoPackage, GeoJSON, CSV | ✅ |

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

### Sharing your map (QR code + link)

After exporting, in the **"Map Exported!"** window click **Create Share Link + QR**.
The plugin publishes your map to the internet and shows you a **QR code + a link**.
Scan the QR with your phone camera, or send the link to anyone — the full
interactive map opens in their browser.

**Who needs what — please read:**

- **People you SHARE a map with** (you send them the QR or link): they need
  **nothing at all** — no account, no token, no setup. They just scan or click,
  and the map opens. This is anyone, anywhere in the world.

- **You (or any user) creating a Share/QR on a NORMAL network** (home, most
  internet connections): just click **Create Share Link + QR**. The plugin uses
  free public hosts automatically. **No token needed.**

- **You (or any user) creating a Share/QR on a BLOCKED network** (many office /
  college / government networks block file-sharing sites): the free hosts won't
  work there. In that case the plugin offers a one-time **GitHub** option. You
  paste a free GitHub token once and your maps are published from your own GitHub
  account. See **"Sharing on a blocked network"** below. (If you don't want to do
  this, just try again later from a normal network or a phone hotspot.)

> Not sure if your network is blocked? Just click the button. If it gives you a
> link, you're fine. Only if it fails will it ask about GitHub.

### Sharing on a blocked network (one-time GitHub setup)

Only needed if the free hosts are blocked on your network. It's free and you do
it once per computer. **Never share your token with anyone** — it is like your
GitHub password. Each person sets up their own; their maps go to their own account.

1. Create a free account at **github.com** and sign in.
2. Open **https://github.com/settings/tokens** (Settings → Developer settings →
   Personal access tokens → **Tokens (classic)**).
3. Click **Generate new token → Generate new token (classic)**.
4. **Note:** type anything, e.g. `QGIS map sharing`.
5. **Expiration:** choose **No expiration** (so you never have to redo it).
6. **Select scopes:** tick the **`repo`** box (the items under it tick
   automatically — that's correct). Tick nothing else.
7. Click **Generate token**, then **copy** the code that starts with `ghp_...`
   **immediately** — GitHub shows it only once.
8. In QGIS, click **Create Share Link + QR** and paste the token when asked.
   It's saved on this computer, so you won't be asked again.

Your maps are published to a **public** repository called `iwv-maps` in your
account (public so the links open for anyone). You can delete any map anytime
from that repo.

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
GitHub: https://github.com/HariMSS-WebGIS/instant_webgis_viewer