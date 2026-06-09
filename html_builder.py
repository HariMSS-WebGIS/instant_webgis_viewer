# Instant WebGIS Viewer — QGIS Plugin
# Export QGIS vector layers to a shareable interactive HTML map
# Copyright (C) 2026 Ballu Harish
# Email: harishmanjulason@gmail.com
# GitHub: https://github.com/HariMSS/instant_webgis_viewer
# Licensed under GNU General Public License v2 or later

"""
HTML Builder — writes a single self-contained .html file.

All layer data, options, and app logic are inlined as <script> blocks
so the file works when opened directly, sent via WhatsApp/email,
dropped on Netlify, or shared via any other means — no companion files needed.
"""

import os, json

def build(title, layers_data, options, out_path):
    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)

    count = len(layers_data)
    total = sum(l['count'] for l in layers_data)

    clean     = _sanitize(layers_data)
    data_json = json.dumps(clean,   ensure_ascii=True, separators=(',', ':'))
    opts_json = json.dumps(options, ensure_ascii=True)
    # Keep data_block for backward compat but it's unused now
    data_block = ''

    # Read map_app.js from the plugin folder (same directory as this file)
    plugin_js_path = os.path.join(os.path.dirname(__file__), 'map_app.js')
    with open(plugin_js_path, 'r', encoding='utf-8') as f:
        app_js_block = f.read()

    html = _html(title, count, total, data_json, opts_json, app_js_block)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # Return only the single output file (no companion files)
    return [out_path]


def _sanitize(obj):
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, str):
        return obj.replace('\x00', '').replace('\r', ' ')
    return obj


def _html(title, count, total, data_json, opts_json, app_js_block):
    safe_title = (title
                  .replace('&', '&amp;')
                  .replace('<', '&lt;')
                  .replace('>', '&gt;'))
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>""" + safe_title + """</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Arial,sans-serif;background:#0f172a;overflow:hidden}

.hdr{position:fixed;top:0;left:0;right:0;height:52px;z-index:3000;
  background:linear-gradient(135deg,#1e3a8a,#1e64c8);
  display:flex;align-items:center;justify-content:space-between;padding:0 10px;
  box-shadow:0 2px 8px rgba(0,0,0,.4)}
.hdr-left{display:flex;align-items:center;gap:8px;min-width:0;flex:1}
.hdr h1{font-size:.92rem;font-weight:700;color:white;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hdr p{font-size:.62rem;color:rgba(255,255,255,.7)}
.hdr-btns{display:flex;gap:6px;flex-shrink:0}
.hbtn{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);
  color:white;padding:6px 11px;border-radius:6px;cursor:pointer;font-size:.76rem;white-space:nowrap}
.hbtn:active{background:rgba(255,255,255,.3)}
.ham{display:none;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);
  color:white;width:44px;height:44px;border-radius:6px;cursor:pointer;font-size:1.2rem;
  align-items:center;justify-content:center;flex-shrink:0}

#map{position:fixed;top:52px;left:260px;right:0;bottom:22px}

.sidebar{position:fixed;top:52px;left:0;width:260px;bottom:22px;z-index:2000;
  background:#0f172a;border-right:1px solid #1e293b;display:flex;flex-direction:column;
  transition:transform .25s ease}
.tabs{display:flex;border-bottom:1px solid #1e293b;flex-shrink:0}
.tab{flex:1;padding:9px 2px;text-align:center;font-size:.7rem;color:#64748b;
  cursor:pointer;border-bottom:2px solid transparent;transition:all .15s;user-select:none}
.tab.on{color:#3b82f6;border-bottom-color:#3b82f6;font-weight:700;background:#0f1f3a}
.pane{display:none;flex:1;overflow-y:auto;overflow-x:hidden;padding:10px;-webkit-overflow-scrolling:touch}
.pane.on{display:block}

.lcard{background:#1e293b;border:1px solid #334155;border-radius:8px;padding:9px;margin-bottom:8px}
.lhead{display:flex;align-items:center;gap:7px;margin-bottom:7px}
.ldot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.lname{font-size:.82rem;font-weight:600;color:#e2e8f0;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ltag{font-size:.6rem;color:#64748b;background:#0f172a;border-radius:4px;padding:1px 5px}
.lrow{display:flex;align-items:center;justify-content:space-between;margin-bottom:5px}
.llbl{font-size:.68rem;color:#94a3b8}
.tog{position:relative;width:40px;height:22px}
.tog input{opacity:0;width:0;height:0}
.sl{position:absolute;inset:0;background:#475569;border-radius:20px;cursor:pointer;transition:.2s}
.sl:before{content:'';position:absolute;width:16px;height:16px;left:3px;top:3px;background:white;border-radius:50%;transition:.2s}
input:checked+.sl{background:#3b82f6}
input:checked+.sl:before{transform:translateX(18px)}
.oprow{display:flex;align-items:center;gap:6px}
.oplbl{font-size:.65rem;color:#64748b;flex-shrink:0}
input[type=range]{flex:1;height:4px;accent-color:#3b82f6;cursor:pointer}
.opval{font-size:.65rem;color:#94a3b8;width:28px;text-align:right;flex-shrink:0}
.lcnt{font-size:.65rem;color:#64748b;text-align:right;margin-top:3px}

.sbox{background:#1e293b;border:1px solid #334155;border-radius:8px;padding:9px;margin-bottom:8px}
.stitle{font-size:.78rem;font-weight:700;margin-bottom:6px}
.srow{display:flex;justify-content:space-between;font-size:.74rem;padding:3px 0;border-bottom:1px solid #334155}
.srow:last-child{border:none}
.sk{color:#94a3b8}.sv{color:#e2e8f0;font-weight:600}

.sinp{width:100%;background:#1e293b;border:1px solid #334155;border-radius:7px;
  padding:8px 10px;color:#e2e8f0;font-size:.84rem;outline:none;margin-bottom:6px}
.sinp:focus{border-color:#3b82f6}
.sres{background:#1e293b;border:1px solid #334155;border-radius:7px;
  max-height:240px;overflow-y:auto;display:none;-webkit-overflow-scrolling:touch}
.sitem{padding:9px 10px;font-size:.78rem;cursor:pointer;border-bottom:1px solid #334155;color:#e2e8f0}
.sitem:active{background:#3b82f6;color:white}
.sitem:last-child{border:none}
.slyr{font-size:.65rem;color:#94a3b8;margin-top:2px}

.tlsel{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px}
.tlbtn{border:none;border-radius:5px;padding:5px 10px;font-size:.72rem;cursor:pointer;color:white}
.twrap{overflow:auto;max-height:calc(100vh - 220px);-webkit-overflow-scrolling:touch}
table{width:100%;border-collapse:collapse;font-size:.72rem}
th{background:#1e3a8a;color:white;padding:5px 8px;text-align:left;white-space:nowrap;position:sticky;top:0}
td{padding:5px 8px;border-bottom:1px solid #1e293b;color:#e2e8f0;white-space:nowrap;max-width:120px;overflow:hidden;text-overflow:ellipsis}
tr:active td{background:#1e3a5a}
.pgbar{display:flex;align-items:center;gap:4px;margin:6px 0;flex-wrap:wrap}
.pgbtn{background:#1e293b;color:#e2e8f0;border:1px solid #334155;border-radius:4px;padding:4px 8px;cursor:pointer;font-size:.7rem}
.pgbtn:disabled{opacity:.4;cursor:not-allowed}
.pglbl{font-size:.7rem;color:#94a3b8;padding:0 4px}

.fi{position:fixed;bottom:30px;left:270px;z-index:2500;background:white;
  border-radius:10px;width:270px;max-height:300px;overflow:hidden;
  box-shadow:0 4px 20px rgba(0,0,0,.3);display:none;flex-direction:column}
@media(max-width:768px){
  /* Hide desktop sidebar toggle arrow on mobile */
  #desk-toggle{ display:none !important; }
  .fi{
    left:0!important;right:0!important;bottom:56px!important;
    width:100%!important;max-width:100%!important;
    height:50vh!important;max-height:85vh!important;
    border-radius:16px 16px 0 0!important;
    box-shadow:0 -4px 24px rgba(0,0,0,.25)!important;
    transition:height .2s ease;
  }
  .fibody{
    overflow-y:scroll!important;
    -webkit-overflow-scrolling:touch!important;
    flex:1!important;
    height:calc(100% - 90px)!important;
  }
}
.fi.on{display:flex}
.fihdr{background:#1e3a8a;color:white;padding:8px 12px;border-radius:10px 10px 0 0;
  display:flex;justify-content:space-between;align-items:center;flex-shrink:0}
.fihdr h3{font-size:.85rem;font-weight:700}
.ficls{background:none;border:none;color:white;font-size:1.2rem;cursor:pointer;padding:8px 12px;min-width:44px;min-height:44px;display:flex;align-items:center;justify-content:center}
.fibody{overflow-y:auto;flex:1;-webkit-overflow-scrolling:touch}
.filyr{border-bottom:1px solid #f0f4ff}
.filhdr{background:#eff6ff;padding:6px 12px;font-size:.72rem;font-weight:700;color:#1e40af;display:flex;align-items:center;gap:5px}
.fidot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.firow{display:flex;padding:4px 12px;border-bottom:1px solid #f8fafc;font-size:.75rem}
.fik{color:#64748b;min-width:75px;flex-shrink:0;font-size:.7rem}
.fiv{color:#1e293b;font-weight:500;word-break:break-all}
.fimt{padding:8px 12px;color:#94a3b8;font-size:.75rem;font-style:italic}

/* ── Mobile bottom sheet ── */
@media(max-width:768px){
  .fi{
    left:0!important;right:0!important;bottom:0!important;
    width:100%!important;max-height:70vh!important;
    border-radius:18px 18px 0 0!important;
    box-shadow:0 -4px 24px rgba(0,0,0,.35)!important;
    transform:translateY(100%);
    transition:transform .3s cubic-bezier(.4,0,.2,1);
    display:flex!important;
    flex-direction:column;
  }
  .fi.on{transform:translateY(0)!important;}
  .fi-handle{display:flex;justify-content:center;padding:10px 0 4px;cursor:pointer;flex-shrink:0}
  .fi-handle-bar{width:40px;height:4px;background:rgba(255,255,255,.5);border-radius:4px}
  .fihdr{border-radius:0!important;padding:6px 16px 10px;}
  .fihdr h3{font-size:1rem}
  .ficls{font-size:1.4rem;padding:10px 14px;min-width:48px;min-height:48px}
  .firow{padding:10px 16px;font-size:.88rem}
  .fik{min-width:100px;font-size:.8rem}
  .filhdr{padding:10px 16px;font-size:.8rem}
  .fimt{padding:12px 16px;font-size:.85rem}
}
/* hide handle on desktop */
.fi-handle{display:none}

.bmwrap{position:absolute;top:10px;right:10px;z-index:1000}
.bmbtn{background:white;border:2px solid rgba(0,0,0,.2);border-radius:6px;
  padding:6px 12px;cursor:pointer;font-size:.78rem;font-weight:600;color:#334155;
  box-shadow:0 2px 6px rgba(0,0,0,.2)}
.bmpanel{display:none;position:absolute;right:0;top:38px;background:white;
  border-radius:8px;padding:12px 14px;min-width:190px;
  box-shadow:0 4px 20px rgba(0,0,0,.2);z-index:1001}
.bmpanel.on{display:block}
.bmpanel h4{font-size:.7rem;text-transform:uppercase;letter-spacing:.8px;color:#64748b;
  font-weight:700;margin-bottom:8px;padding-bottom:5px;border-bottom:1px solid #e2e8f0}
.bmopt{display:flex;align-items:center;gap:8px;padding:6px 4px;cursor:pointer;border-radius:4px}
.bmopt:active{background:#eff6ff}
.bmopt input{accent-color:#1e64c8;width:16px;height:16px}
.bmopt label{font-size:.84rem;color:#334155;cursor:pointer;flex:1}
.bmopt.cur label{color:#1e64c8;font-weight:700}

.coord{position:fixed;bottom:0;left:260px;right:0;background:rgba(15,23,42,.95);
  color:#64748b;font-size:.68rem;padding:4px 12px;z-index:1000;
  border-top:1px solid #1e293b;pointer-events:none;height:22px;display:flex;align-items:center}

/* ── Mobile bottom toolbar ── */
.mob-toolbar{display:none}
@media(max-width:768px){
  .mob-toolbar{
    display:flex;
    position:fixed;bottom:0;left:0;right:0;
    height:56px;z-index:3000;
    background:#0f172a;
    border-top:1px solid #1e3a8a;
    align-items:center;
    justify-content:space-around;
    padding:0 8px;
  }
  .mtool{
    display:flex;flex-direction:column;align-items:center;justify-content:center;
    gap:3px;flex:1;height:100%;
    background:none;border:none;color:#94a3b8;
    font-size:.6rem;cursor:pointer;
    border-radius:8px;padding:6px 4px;
    transition:background .15s,color .15s;
    -webkit-tap-highlight-color:transparent;
  }
  .mtool:active,.mtool.active{background:#1e3a8a;color:#60a5fa}
  .mtool svg{width:22px;height:22px;flex-shrink:0}
  /* push map and coord up so toolbar doesn't overlap */
  #map{bottom:56px!important}
  .coord{display:none!important}
}

.sb-overlay{display:none;position:fixed;inset:0;z-index:1999;background:rgba(0,0,0,.45)}
.sb-overlay.on{display:block}

@media(max-width:768px){
  .ham{display:flex}
  #map{left:0!important;top:52px;bottom:48px;right:0}
  .coord{left:0;bottom:0;height:48px;font-size:.72rem;padding:0 14px}
  .sidebar{transform:translateX(-100%);width:88vw;max-width:320px;bottom:48px;
    box-shadow:4px 0 24px rgba(0,0,0,.6)}
  .sidebar.open{transform:translateX(0)}
  .tab{padding:16px 2px;font-size:.82rem;min-height:48px;display:flex;align-items:center;justify-content:center}
  /* fi handled by dedicated mobile bottom-sheet block above */
  .bmpanel{right:auto;left:0;min-width:210px}
  .hbtn{padding:8px 10px;font-size:.78rem}
  .tog{width:52px;height:32px}
  .sl:before{width:24px;height:24px;top:4px;left:4px}
  input:checked+.sl:before{transform:translateX(20px)}
  input[type=range]{height:6px}
  .pgbtn{padding:12px 16px;font-size:.82rem;min-height:44px}
  .sitem{padding:16px 14px;font-size:.88rem;min-height:48px}
  .bmopt{padding:14px 8px;min-height:48px}
  .bmopt label{font-size:.95rem}
}

@media print{
  .sidebar,.hdr-btns,.bmwrap,.fi,.coord,.ham,.sb-overlay{display:none!important}
  #map{left:0!important;top:0!important;bottom:0!important;right:0!important}
}
</style>
</head>
<body>

<div class="hdr">
  <div class="hdr-left">
    <button class="ham" id="ham-btn" onclick="toggleSidebar()">&#9776;</button>
    <div>
      <h1>&#128506; """ + safe_title + """</h1>
      <p>""" + str(count) + """ layer(s) &middot; """ + f'{total:,}' + """ features &middot; Instant WebGIS Viewer</p>
    </div>
  </div>
  <div class="hdr-btns">
    <button class="hbtn" onclick="window.print()">&#128424; Print</button>
    <button class="hbtn" id="share-btn" onclick="openShare()">&#128241; Share / QR</button>
  </div>
</div>

<div class="sb-overlay" id="sb-overlay" onclick="closeSidebar()"></div>

<div class="sidebar" id="sidebar">
  <div class="tabs">
    <div class="tab on" id="t-layers" onclick="showTab('layers')">Layers</div>
    <div class="tab"    id="t-stats"  onclick="showTab('stats')">Stats</div>
    <div class="tab"    id="t-search" onclick="showTab('search')">Search</div>
    <div class="tab"    id="t-table"  onclick="showTab('table')">Table</div>
  </div>
  <div class="pane on" id="p-layers"><div id="lctrl"></div></div>
  <div class="pane"    id="p-stats"><div id="sctrl"></div></div>
  <div class="pane"    id="p-search">
    <input class="sinp" id="sinp" placeholder="Search any attribute value..."
           oninput="doSearch(this.value)">
    <div class="sres" id="sres"></div>
    <div id="sinfo" style="font-size:.72rem;color:#64748b;margin-top:4px">Search across all layers</div>
  </div>
  <div class="pane" id="p-table">
    <div class="tlsel" id="tlsel"></div>
    <div class="twrap" id="twrap"></div>
  </div>
</div>

<div id="map">
  <div class="bmwrap" id="bmwrap">
    <button class="bmbtn" onclick="toggleBM()">&#128506; Base Layers &#9660;</button>
    <div class="bmpanel" id="bmpanel">
      <h4>Base Layers</h4>
      <div class="bmopt cur"><input type="radio" name="bm" id="b0" checked onchange="setBM(0)"><label for="b0">OSM Street Map</label></div>
      <div class="bmopt"><input type="radio" name="bm" id="b1" onchange="setBM(1)"><label for="b1">USGS Imagery</label></div>
      <div class="bmopt"><input type="radio" name="bm" id="b2" onchange="setBM(2)"><label for="b2">OSM Topographic</label></div>
      <div class="bmopt"><input type="radio" name="bm" id="b3" onchange="setBM(3)"><label for="b3">Carto Dark</label></div>
      <div class="bmopt"><input type="radio" name="bm" id="b4" onchange="setBM(4)"><label for="b4">Carto Light</label></div>
      <div class="bmopt"><input type="radio" name="bm" id="b5" onchange="setBM(5)"><label for="b5">ESRI World Street</label></div>
      <div class="bmopt"><input type="radio" name="bm" id="b6" onchange="setBM(6)"><label for="b6">ESRI World Imagery</label></div>
      <div class="bmopt"><input type="radio" name="bm" id="b7" onchange="setBM(7)"><label for="b7">OSM BrightGray</label></div>
      <div class="bmopt"><input type="radio" name="bm" id="b8" onchange="setBM(8)"><label for="b8">No Basemap</label></div>
    </div>
  </div>
</div>

<div class="fi" id="fi">
  <!-- Drag handle bar - touch and drag UP to expand -->
  <div id="fi-drag-handle" style="
    display:flex;justify-content:center;align-items:center;
    padding:10px 0 6px;cursor:grab;touch-action:none;
    background:transparent">
    <div style="width:48px;height:5px;background:#94a3b8;border-radius:3px"></div>
  </div>
  <div class="fihdr">
    <h3>&#128205; Feature Info</h3>
    <button class="ficls" onclick="closeFI()">&#10005;</button>
  </div>
  <div class="fibody" id="fibody"></div>
</div>

<div class="coord" id="coord">Tap a feature for info &middot; pinch to zoom</div>

<!-- Inline data — safe JSON script tag -->
<script id="qsm-data" type="application/json">
""" + data_json + """</script>
<script id="qsm-opts" type="application/json">
""" + opts_json + """</script>

<!-- On web URL: hide Share button and prevent any modal from opening -->
<script>
(function(){
  var isWeb = window.location.protocol !== 'file:';
  if(!isWeb) return;
  // Hide share button
  window.addEventListener('DOMContentLoaded', function(){
    var sb = document.getElementById('share-btn');
    if(sb) sb.style.display = 'none';
    // Force close modal if somehow opened
    var m = document.getElementById('qrmodal');
    if(m) m.style.display = 'none';
  });
  // Override generateQR and openShare to do nothing on web
  window.generateQR = function(){ 
    var m = document.getElementById('qrmodal');
    if(m) m.style.display = 'none';
  };
  window.openShare = function(){
    var m = document.getElementById('qrmodal');
    if(m) m.style.display = 'none';
  };
})();
</script>
<!-- Inline app logic — embedded at export time -->
<script>
""" + app_js_block + """</script>


<!-- Mobile bottom toolbar (hidden on desktop) -->
<div class="mob-toolbar" id="mob-toolbar">
  <button class="mtool active" id="mtool-info" onclick="setMobileTool('info')" title="Feature Info">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
    </svg>
    Info
  </button>
  <button class="mtool" id="mtool-search" onclick="setMobileTool('search')" title="Search">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>
    Search
  </button>
  <button class="mtool" id="mtool-layers" onclick="setMobileTool('layers')" title="Layers">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>
    </svg>
    Layers
  </button>
  <button class="mtool" id="mtool-table" onclick="setMobileTool('table')" title="Table">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/>
    </svg>
    Table
  </button>
</div>

<!-- QR Share Modal -->
<div id="qrmodal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);
  z-index:9999;align-items:center;justify-content:center">
  <div style="background:white;border-radius:12px;padding:22px;width:90%;max-width:360px;
    box-shadow:0 8px 40px rgba(0,0,0,.3);text-align:center">

    <!-- Step 1: Prompt -->
    <div id="qr-step1">
      <h3 style="color:#1e293b;margin-bottom:8px;font-size:1rem">Share Map on Mobile</h3>
      <p style="color:#64748b;font-size:.82rem;margin-bottom:14px">
        Upload your map to the web and get a QR code.<br>
        Scan with phone camera - full interactive map opens!
      </p>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
        padding:10px;margin-bottom:14px;text-align:left;font-size:.77rem;color:#475569">
        What happens:<br>
        1. Map uploads to a free server<br>
        2. You get a real web link + QR code<br>
        3. Scan QR - full map opens on phone!<br>
        <span style="color:#94a3b8;font-size:.7rem">Link expires in 24 hours.</span>
      </div>
      <button id="qr-gen-btn" onclick="generateQR()"
        style="width:100%;background:#1e64c8;color:white;border:none;border-radius:8px;
        padding:11px;cursor:pointer;font-size:.9rem;font-weight:700;margin-bottom:8px;
        transition:opacity .2s">
        Generate QR Code
      </button>
      <button onclick="document.getElementById('qrmodal').style.display='none'"
        style="width:100%;background:#f1f5f9;color:#64748b;border:none;border-radius:8px;
        padding:9px;cursor:pointer;font-size:.82rem">Cancel</button>
    </div>

    <!-- Step 2: Uploading / Result -->
    <div id="qr-step2" style="display:none">
      <h3 style="color:#1e293b;margin-bottom:14px;font-size:1rem">Share Map on Mobile</h3>
      <div id="qr-progress-box" style="background:#eff6ff;border:1px solid #bfdbfe;
        border-radius:8px;padding:14px;margin-bottom:12px;color:#1e40af;font-size:.85rem">
        <div style="font-size:1.4rem;margin-bottom:6px">&#9203;</div>
        <div id="qr-progress-text">Uploading...</div>
      </div>
      <div id="qr-success" style="display:none">
        <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;
          padding:8px;margin-bottom:10px;color:#16a34a;font-weight:700;font-size:.85rem">
          Uploaded! Open Camera app &amp; point at QR code (do not use Google Lens)
        </div>
        <div style="font-size:.7rem;color:#64748b;margin-bottom:4px" id="qr-host-info"></div>
        <div id="qr-canvas" style="margin:10px auto;text-align:center"></div>
        <div id="qr-url-box" style="display:none;margin-top:10px">
          <div style="font-size:.72rem;color:#64748b;margin-bottom:4px">Or share this link:</div>
          <div style="display:flex;gap:6px">
            <input id="qr-url" readonly onclick="this.select()"
              style="flex:1;font-size:.7rem;padding:5px 8px;border:1px solid #e2e8f0;
              border-radius:6px;background:#f8fafc;color:#334155">
            <button id="qr-copy-btn" onclick="copyQRUrl()"
              style="background:#1e64c8;color:white;border:none;border-radius:6px;
              padding:6px 10px;cursor:pointer;font-size:.72rem;white-space:nowrap">
              Copy</button>
          </div>
        </div>
      </div>
      <button onclick="document.getElementById('qrmodal').style.display='none'"
        style="width:100%;background:#f1f5f9;color:#64748b;border:none;border-radius:8px;
        padding:9px;cursor:pointer;font-size:.82rem;margin-top:12px">Close</button>
    </div>

    <!-- Error -->
    <div id="qr-error" style="display:none">
      <h3 style="color:#1e293b;margin-bottom:14px;font-size:1rem">&#128241; Share Map on Mobile</h3>
      <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;
        padding:14px;margin-bottom:14px;font-size:.85rem;color:#1e40af;text-align:center">
        Please click on Try Again for getting QR code
      </div>
      <button onclick="generateQR()"
        style="width:100%;background:#1e64c8;color:white;border:none;border-radius:8px;
        padding:11px;cursor:pointer;font-size:.9rem;font-weight:700;margin-bottom:8px">
        Try Again
      </button>
      <button onclick="document.getElementById('qrmodal').style.display='none'"
        style="width:100%;background:#f1f5f9;color:#64748b;border:none;border-radius:8px;
        padding:9px;cursor:pointer;font-size:.82rem">Close</button>
    </div>

  </div>
</div>
</body>
</html>"""
