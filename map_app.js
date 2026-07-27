/* Quick Share Map App - map_app.js */
/* Quick Share Map App */
/* Quick Share Map - map_app.js */

// Read data from safe JSON script tags (immune to special characters)
var LAYERS  = JSON.parse(document.getElementById('qsm-data').textContent || '[]');
var OPTIONS = JSON.parse(document.getElementById('qsm-opts').textContent || '{}');
// Debug: log layer count
console.log('QSM: LAYERS count =', LAYERS.length, LAYERS.map(function(l){return l.name;}));
var PALETTE = ['#1e64c8','#e05c2a','#27a845','#8b2fc9',
               '#c8a01e','#c8285a','#1ec8b4','#6e6e6e'];

var isMobile = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0) || (screen.width <= 768);

// -- Sidebar toggle (mobile + desktop) ----------------------------------------
var sidebarOpen = true;

// On page load: reset sidebar state cleanly (fixes catbox URL issues)
window.addEventListener('load', function() {
  var sb  = document.getElementById('sidebar');
  var map = document.getElementById('map');
  var crd = document.getElementById('coord');
  var dt  = document.getElementById('desk-toggle');
  var ov  = document.getElementById('sb-overlay');
  if (!sb) return;

  if (isMobile) {
    // Mobile: close sidebar, reset all inline styles
    sb.classList.remove('open');
    sb.style.transform = '';
    if (ov) { ov.classList.remove('on'); ov.style.display = ''; }
    if (map) map.style.left = '';
    if (crd) crd.style.left = '';
  } else {
    // Desktop: force open sidebar and sync all state
    sidebarOpen = true;
    sb.style.transform  = '';
    sb.style.left       = '0';
    if (map) map.style.left = '260px';
    if (crd) crd.style.left = '260px';
    // Wait for desk-toggle to be created, then set its position
    setTimeout(function() {
      var dtBtn = document.getElementById('desk-toggle');
      if (dtBtn) {
        dtBtn.style.left    = '260px';
        dtBtn.innerHTML     = '&#9664;';
      }
    }, 100);
  }
});

function toggleSidebar() {
  var sb = document.getElementById('sidebar');
  var ov = document.getElementById('sb-overlay');
  if (!sb) return;
  if (isMobile) {
    if (sb.classList.contains('open')) {
      sb.classList.remove('open');
      if (ov) ov.classList.remove('on');
    } else {
      sb.classList.add('open');
      if (ov) ov.classList.add('on');
    }
  } else {
    sidebarOpen = !sidebarOpen;
    _applyDesktopSidebar();
  }
}

function _applyDesktopSidebar() {
  var sb  = document.getElementById('sidebar');
  var map = document.getElementById('map');
  var crd = document.getElementById('coord');
  var btn = document.getElementById('desk-toggle');
  var dtb = document.getElementById('desk-toggle');
  if (sidebarOpen) {
    sb.style.transform  = '';
    map.style.left      = '260px';
    if (crd) crd.style.left = '260px';
    if (btn) btn.innerHTML  = '&#9664;';
    if (btn) btn.title      = 'Collapse sidebar';
    if (dtb) { dtb.style.left = '260px'; dtb.innerHTML = '&#9664;'; }
  } else {
    sb.style.transform  = 'translateX(-260px)';
    map.style.left      = '0';
    if (crd) crd.style.left = '0';
    if (btn) btn.innerHTML  = '&#9654;';
    if (btn) btn.title      = 'Expand sidebar';
    if (dtb) { dtb.style.left = '0'; dtb.innerHTML = '&#9654;'; }
  }
  setTimeout(function(){ if(window.MAP) window.MAP.invalidateSize(); }, 260);
}

function closeSidebar() {
  var sb = document.getElementById('sidebar');
  var ov = document.getElementById('sb-overlay');
  if (sb) sb.classList.remove('open');
  if (ov) ov.classList.remove('on');
}

// -- Tabs ----------------------------------------------------------------------
function showTab(n) {
  ['layers','stats','search','table'].forEach(function(x) {
    var t = document.getElementById('t-' + x);
    var p = document.getElementById('p-' + x);
    if (t) t.classList.toggle('on', x === n);
    if (p) p.classList.toggle('on', x === n);
  });
}

// -- Basemaps ------------------------------------------------------------------
var BMS = [
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    {attribution:'&copy; OpenStreetMap',maxZoom:19}),
  L.tileLayer('https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}',
    {attribution:'&copy; USGS',maxZoom:16}),
  L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    {attribution:'&copy; OpenTopoMap',maxZoom:17}),
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    {attribution:'&copy; Carto',maxZoom:20}),
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    {attribution:'&copy; Carto',maxZoom:20}),
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
    {attribution:'&copy; Esri',maxZoom:19}),
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    {attribution:'&copy; Esri',maxZoom:19}),
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    {attribution:'&copy; Carto',maxZoom:20}),
  null
];

// -- Init map ------------------------------------------------------------------
// Clear any existing Leaflet instance (happens when loading from catbox outerHTML)
(function() {
  var mapEl = document.getElementById('map');
  if (!mapEl) return;
  // Always remove any leftover Leaflet SVG from outerHTML baking
  // _leaflet_id is lost during serialization so we check for SVG children instead
  var kids = mapEl.querySelectorAll('.leaflet-pane, .leaflet-control-container, svg');
  if (kids.length > 0) {
    kids.forEach(function(k) { k.parentNode && k.parentNode.removeChild(k); });
    // Also clear the leaflet id attribute
    delete mapEl._leaflet_id;
    mapEl.removeAttribute('data-leaflet-id');
  }
})();

var map = L.map('map', {
  center:[20,78], zoom:5,
  tap: true,
  tapTolerance: 20,
  touchZoom: true,
  bounceAtZoomLimits: false,
  zoomControl: true
});
window.MAP = map;
var curBM = BMS[0]; curBM.addTo(map);
L.control.scale({imperial:false, position:'bottomright'}).addTo(map);

// -- Desktop sidebar toggle button ---------------------------------------------
(function() {
  // Don't create if already exists (prevents duplicate on catbox URL)
  if(document.getElementById('desk-toggle')) return;
  var btn = document.createElement('button');
  btn.id        = 'desk-toggle';
  btn.innerHTML = '&#9664;';
  btn.title     = 'Collapse sidebar';
  // CSS media query handles mobile hiding — no JS needed
  btn.style.cssText = 'position:fixed;top:50%;left:260px;transform:translate(-50%,-50%);z-index:2100;width:20px;height:48px;background:#1e3a8a;color:white;border:none;border-radius:0 6px 6px 0;cursor:pointer;font-size:10px;line-height:1;padding:0;box-shadow:2px 0 6px rgba(0,0,0,.3);transition:left .25s ease;display:flex;align-items:center;justify-content:center';
  btn.onclick = function(){ toggleSidebar(); };
  document.body.appendChild(btn);
})();

map.on('mousemove', function(e) {
  var el = document.getElementById('coord');
  if (el) el.textContent =
    'Lat: ' + e.latlng.lat.toFixed(6) +
    '   Lng: ' + e.latlng.lng.toFixed(6) +
    '   Zoom: ' + map.getZoom();
});

// -- Basemap toggle ------------------------------------------------------------
var curBMi = 0;
function setBM(i) {
  if (curBM) map.removeLayer(curBM);
  curBM = BMS[i]; curBMi = i;
  if (curBM) curBM.addTo(map);
  document.querySelectorAll('.bmopt').forEach(function(el, j) {
    el.classList.toggle('cur', j === i);
  });
  document.getElementById('bmpanel').classList.remove('on');
}
function toggleBM() {
  document.getElementById('bmpanel').classList.toggle('on');
}
document.addEventListener('click', function(e) {
  var w = document.getElementById('bmwrap');
  if (w && !w.contains(e.target))
    document.getElementById('bmpanel').classList.remove('on');
});

// -- Feature Info --------------------------------------------------------------
function escHtml(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function showFI(feats) {
  var h = '';
  feats.forEach(function(f) {
    var entries = [];
    Object.keys(f.props || {}).forEach(function(k) {
      var v = f.props[k];
      if (v !== null && v !== undefined && String(v).trim() !== '')
        entries.push([k, v]);
    });
    h += '<div class="filyr"><div class="filhdr">' +
         '<div class="fidot" style="background:' + f.color + '"></div>' +
         escHtml(f.name) + '</div>';
    if (!entries.length) {
      h += '<div class="fimt">No attributes</div>';
    } else {
      entries.forEach(function(kv) {
        h += '<div class="firow"><span class="fik">' + escHtml(String(kv[0])) +
             '</span><span class="fiv">' + escHtml(String(kv[1])) + '</span></div>';
      });
    }
    h += '</div>';
  });
  document.getElementById('fibody').innerHTML = h;
  var fiPanel = document.getElementById('fi');
  fiPanel.style.display = '';  // clear any inline display:none
  fiPanel.classList.add('on');
  // On mobile scroll the info panel into view
  if (isMobile) {
    var fi = document.getElementById('fi');
    if (fi) setTimeout(function(){ fi.scrollIntoView({behavior:'smooth', block:'nearest'}); }, 100);
  }
}
function closeFI() { document.getElementById('fi').classList.remove('on'); }
map.on('click', function() { closeFI(); });

// -- Mobile toolbar tool switching ---------------------------------------------
var mobileTool = 'info';
function setMobileTool(tool) {
  mobileTool = tool;
  ['info','search','layers','table'].forEach(function(t) {
    var btn = document.getElementById('mtool-' + t);
    if (btn) btn.classList.toggle('active', t === tool);
  });
  if (tool === 'search') {
    toggleSidebar(); showTab('search');
    setTimeout(function(){ var s=document.getElementById('sinp'); if(s) s.focus(); }, 300);
  } else if (tool === 'layers') {
    toggleSidebar(); showTab('layers');
  } else if (tool === 'table') {
    toggleSidebar(); showTab('table');
  } else {
    // info mode - close sidebar if open
    var sb = document.getElementById('sidebar');
    if (sb && sb.classList.contains('open')) closeSidebar();
  }
}

// -- Clear any pre-rendered content (from outerHTML upload)
(function(){
  var lctrl = document.getElementById('lctrl');
  var sctrl = document.getElementById('sctrl');
  var tlsel = document.getElementById('tlsel');
  var twrap = document.getElementById('twrap');
  if(lctrl) lctrl.innerHTML = '';
  if(sctrl) sctrl.innerHTML = '';
  if(tlsel) tlsel.innerHTML = '';
  if(twrap) twrap.innerHTML = '';
})();

// -- Deduplicate layers (prevent same layer appearing twice)
(function(){
  var seen = {}, clean = [];
  for(var i=0;i<LAYERS.length;i++){
    if(!seen[LAYERS[i].name]){ seen[LAYERS[i].name]=true; clean.push(LAYERS[i]); }
  }
  LAYERS = clean;
})();

// -- Build layers --------------------------------------------------------------
var gLayers  = [];
var allFeats = [];
var bounds   = null;

// Deduplicate layers by name - prevent same layer rendering twice
var _seen = {};
var _unique = [];
for (var _i = 0; _i < LAYERS.length; _i++) {
  var _key = LAYERS[_i].name + '_' + (LAYERS[_i].count || 0);
  if (!_seen[_key]) {
    _seen[_key] = true;
    _unique.push(LAYERS[_i]);
  }
}
LAYERS = _unique;

// Track rendered layer names to skip duplicates
var _renderedNames = {};

// Cache uploaded QR URL so re-clicking Share/QR reuses it
var _cachedQRUrl = null;

LAYERS.forEach(function(lyr, idx) {
  // Skip if already rendered this layer name
  if(_renderedNames[lyr.name]) { return; }
  _renderedNames[lyr.name] = true;

  var col = (lyr.style && lyr.style.color) ? lyr.style.color : PALETTE[idx % PALETTE.length];
  var op  = (lyr.style && lyr.style.opacity) ? parseFloat(lyr.style.opacity) : 0.7;
  if(isNaN(op) || op < 0.1) op = 0.7;

  // ── RASTER layer: render as image overlay ────────────────────────────────
  if(lyr.type === 'raster' && lyr.image && lyr.bounds) {
    var bnds = [[lyr.bounds[0], lyr.bounds[1]], [lyr.bounds[2], lyr.bounds[3]]];
    var overlay = L.imageOverlay(lyr.image, bnds, {opacity: op, interactive: true}).addTo(map);
    gLayers.push(overlay);
    // Click on raster - read pixel value from image using canvas
    (function(lyrRef, ovRef) {
      // Preload image into a canvas for pixel reading
      var _canvas = document.createElement('canvas');
      var _img    = new Image();
      _img.src    = lyrRef.image;
      _img.onload = function() {
        _canvas.width  = _img.naturalWidth;
        _canvas.height = _img.naturalHeight;
        _canvas.getContext('2d').drawImage(_img, 0, 0);
      };

      ovRef.on('click', function(e) {
        L.DomEvent.stopPropagation(e);
        var lat = e.latlng.lat;
        var lng = e.latlng.lng;

        // Calculate pixel position from lat/lng
        var minLat = lyrRef.bounds[0], minLng = lyrRef.bounds[1];
        var maxLat = lyrRef.bounds[2], maxLng = lyrRef.bounds[3];
        var px = Math.floor(((lng - minLng) / (maxLng - minLng)) * _canvas.width);
        var py = Math.floor(((maxLat - lat) / (maxLat - minLat)) * _canvas.height);

        var props = {
          'Latitude':  lat.toFixed(6),
          'Longitude': lng.toFixed(6),
        };

        // Read pixel RGBA from canvas
        try {
          var ctx = _canvas.getContext('2d');
          var px2 = Math.max(0, Math.min(px, _canvas.width  - 1));
          var py2 = Math.max(0, Math.min(py, _canvas.height - 1));
          var pxData = ctx.getImageData(px2, py2, 1, 1).data;
          var r = pxData[0], g = pxData[1], b = pxData[2], a = pxData[3];

          if (a === 0) {
            props['Pixel Value'] = 'No Data';
          } else if (r === g && g === b) {
            // Grayscale band - show as DN value
            props['DN Value'] = r;
            // Approximate reflectance (0-255 -> 0.0-1.0)
            props['Reflectance'] = (r / 255.0).toFixed(4);
          } else {
            // RGB composite
            props['Red Band']   = r;
            props['Green Band'] = g;
            props['Blue Band']  = b;
          }
        } catch(ex) {
          props['Pixel Value'] = 'Unable to read';
        }

        props['Type']    = 'Raster Layer';
        props['CRS']     = (lyrRef.stats && lyrRef.stats.crs) || 'Unknown';

        showFI([{name: lyrRef.name, color: '#888888', props: props}]);
      });
    })(lyr, overlay);
    try { var rb=L.latLngBounds(bnds); if(rb.isValid()) bounds=bounds?bounds.extend(rb):rb; } catch(e){}
    var rcard = document.createElement('div');
    rcard.className = 'lcard';
    rcard.innerHTML =
      '<div class="lhead"><div class="ldot" style="background:#888"></div>' +
      '<span class="lname" title="'+escHtml(lyr.name)+'">'+escHtml(lyr.name)+'</span>' +
      '<span class="ltag">Raster</span></div>' +
      '<div class="lrow"><span class="llbl">Visible</span>' +
      '<label class="tog"><input type="checkbox" id="v'+idx+'" checked><span class="sl"></span></label></div>' +
      '<div class="oprow"><span class="oplbl">Opacity</span>' +
      '<input type="range" min="0" max="1" step="0.05" value="1" id="o'+idx+'">' +
      '<span class="opval" id="ov'+idx+'">100%</span></div>';
    document.getElementById('lctrl').appendChild(rcard);
    (function(i, ov, c){
      document.getElementById('v'+i).onchange = function(){
        if(this.checked){map.addLayer(ov);c.style.opacity='1';}
        else{map.removeLayer(ov);c.style.opacity='0.4';}
      };
      document.getElementById('o'+i).oninput = function(){
        var v=parseFloat(this.value);
        ov.setOpacity(v);
        document.getElementById('ov'+i).textContent=Math.round(v*100)+'%';
      };
    })(idx, overlay, rcard);
    return;
  }

  // ── VECTOR layer ──────────────────────────────────────────────────────────
  // Declare gl first so onEachFeature can safely reference it
  var gl;
  gl = L.geoJSON(lyr.geojson, {
    style: function() {
      return {color:col, weight:2, fillColor:col, fillOpacity:0.5, opacity:1};
    },
    pointToLayer: function(f, ll) {
      return L.circleMarker(ll, {
        radius: isMobile ? 14 : 6,  // much bigger tap target on mobile
        fillColor:col, color:'#fff', weight:1.5, fillOpacity:0.8
      });
    },
    onEachFeature: function(feat, layer) {
      allFeats.push({lidx:idx, name:lyr.name, color:col, props:feat.properties, ll:layer});

      // click works on both desktop AND mobile (Leaflet tap:true handles touch_click)
      layer.on('click', function(e) {
        L.DomEvent.stopPropagation(e);
        showFI([{name:lyr.name, color:col, props:feat.properties}]);
      });

      // mouseover/mouseout only on desktop - they don't fire on mobile
      if (!isMobile) {
        layer.on('mouseover', function() {
          if (layer.setStyle) layer.setStyle({weight:3, fillOpacity:0.8});
          if (layer.bringToFront) layer.bringToFront();
        });
        layer.on('mouseout', function() {
          if (gl) gl.resetStyle(layer);
        });
      }
    }
  }).addTo(map);
  gLayers.push(gl);

  try {
    var b = gl.getBounds();
    if (b.isValid()) bounds = bounds ? bounds.extend(b) : b;
  } catch(e) {}

  // Layer card
  var lctrl = document.getElementById('lctrl');
  var card  = document.createElement('div');
  card.className = 'lcard';
  card.innerHTML =
    '<div class="lhead">' +
      '<div class="ldot" style="background:'+col+'"></div>' +
      '<span class="lname" title="'+escHtml(lyr.name)+'">'+escHtml(lyr.name)+'</span>' +
      '<span class="ltag">'+escHtml((lyr.stats&&lyr.stats.geometry_type)||'Vector')+'</span>' +
    '</div>' +
    '<div class="lrow">' +
      '<span class="llbl">Visible</span>' +
      '<label class="tog"><input type="checkbox" id="v'+idx+'" checked><span class="sl"></span></label>' +
    '</div>' +
    '<div class="oprow">' +
      '<span class="oplbl">Opacity</span>' +
      '<input type="range" min="0" max="1" step="0.05" value="1" id="o'+idx+'">' +
      '<span class="opval" id="ov'+idx+'">100%</span>' +
    '</div>' +
    '<div class="lrow">' +
      '<span class="llbl">Colour</span>' +
      '<input type="color" id="c'+idx+'" value="'+col+'" style="width:36px;height:24px;border:none;cursor:pointer;border-radius:4px;padding:0">' +
    '</div>' +
    '<div class="lcnt">'+Number(lyr.count||0).toLocaleString()+' features</div>';
  lctrl.appendChild(card);

  (function(i, g, c) {
    document.getElementById('v'+i).onchange = function() {
      if (this.checked) { map.addLayer(g); c.style.opacity='1'; }
      else { map.removeLayer(g); c.style.opacity='0.4'; }
    };
    document.getElementById('o'+i).oninput = function() {
      var v = parseFloat(this.value);
      g.setStyle({fillOpacity:v*0.5, opacity:v});
      document.getElementById('ov'+i).textContent = Math.round(v*100)+'%';
    };
    // Colour picker - change all features colour
    var cp = document.getElementById('c'+i);
    if(cp) cp.addEventListener('input', function(){
      var nc = this.value;
      g.eachLayer(function(l){ if(l.setStyle) l.setStyle({color:nc, fillColor:nc}); });
      var dot = card.querySelector('.ldot');
      if(dot) dot.style.background = nc;
    });
  })(idx, gl, card);

  // Stats pane
  var st = lyr.stats || {};
  var sh = '<div class="sbox">' +
    '<div class="stitle" style="color:'+col+'">'+escHtml(lyr.name)+'</div>' +
    '<div class="srow"><span class="sk">Type</span><span class="sv">'+escHtml(st.geometry_type||'Vector')+'</span></div>' +
    '<div class="srow"><span class="sk">Features</span><span class="sv">'+Number(st.feature_count||lyr.count||0).toLocaleString()+'</span></div>' +
    '<div class="srow"><span class="sk">Fields</span><span class="sv">'+((st.fields||[]).length)+'</span></div>' +
    '<div class="srow"><span class="sk">CRS</span><span class="sv">'+escHtml(st.crs||'WGS84')+'</span></div>';
  if (st.total_length_km != null)
    sh += '<div class="srow"><span class="sk">Length</span><span class="sv">'+Number(st.total_length_km).toLocaleString()+' km</span></div>';
  if (st.total_area_km2 != null)
    sh += '<div class="srow"><span class="sk">Area</span><span class="sv">'+Number(st.total_area_km2).toLocaleString()+' km&#178;</span></div>';
  sh += '</div>';
  document.getElementById('sctrl').innerHTML += sh;

  // Table pane button
  var tb = document.createElement('button');
  tb.className = 'tlbtn'; tb.textContent = lyr.name; tb.style.background = col;
  (function(i) { tb.onclick = function() { buildTable(i, 0); }; })(idx);
  document.getElementById('tlsel').appendChild(tb);
  if (idx === 0) buildTable(0, 0);
});

if (bounds && bounds.isValid()) map.fitBounds(bounds, {padding:[20,20]});
setTimeout(function() { map.invalidateSize(); }, 300);

// -- Attribute table -----------------------------------------------------------
function buildTable(idx, page) {
  var lyr   = LAYERS[idx];
  var feats = lyr.geojson.features;
  var twrap = document.getElementById('twrap');
  if (!feats || !feats.length) {
    twrap.innerHTML = '<div style="padding:10px;color:#94a3b8">No features</div>';
    return;
  }
  var flds  = lyr.fields || (feats[0] ? Object.keys(feats[0].properties||{}) : []);
  var ps    = 100;
  var total = feats.length;
  var pages = Math.ceil(total / ps);
  page = Math.max(0, Math.min(page, pages - 1));
  var start = page * ps;
  var end   = Math.min(start + ps, total);

  function pgBtn(lbl, pg, dis) {
    return '<button class="pgbtn" onclick="buildTable('+idx+','+pg+')"'+(dis?' disabled':'')+'>'+lbl+'</button>';
  }
  function pgBar() {
    return '<div class="pgbar">'+
      '<span class="pglbl">'+(start+1)+'-'+end+' / '+total.toLocaleString()+'</span>'+
      '<span style="margin-left:auto;display:flex;gap:3px">'+
      pgBtn('&laquo;',0,page===0)+pgBtn('&lsaquo; Prev',page-1,page===0)+
      '<span class="pglbl">Page '+(page+1)+'/'+pages+'</span>'+
      pgBtn('Next &rsaquo;',page+1,page>=pages-1)+pgBtn('&raquo;',pages-1,page>=pages-1)+
      '</span></div>';
  }

  var h = pgBar()+'<table><thead><tr>';
  flds.forEach(function(f) { h += '<th>'+escHtml(f)+'</th>'; });
  h += '</tr></thead><tbody>';
  feats.slice(start, end).forEach(function(feat, i) {
    var ri = start + i;
    h += '<tr onclick="zoomRow('+idx+','+ri+')">';
    flds.forEach(function(f) {
      var v = feat.properties ? feat.properties[f] : '';
      v = (v === null || v === undefined) ? '' : String(v);
      h += '<td title="'+escHtml(v)+'">'+escHtml(v)+'</td>';
    });
    h += '</tr>';
  });
  h += '</tbody></table>'+pgBar();
  twrap.innerHTML = h;
}

function zoomRow(li, fi) {
  var feat = LAYERS[li].geojson.features[fi];
  if (!feat) return;
  var col = (LAYERS[li].style && LAYERS[li].style.color) ? LAYERS[li].style.color : '#1e64c8';
  var l   = gLayers[li].getLayers()[fi];
  if (l) {
    try {
      if (l.getBounds) map.fitBounds(l.getBounds(), {maxZoom:14});
      else if (l.getLatLng) map.setView(l.getLatLng(), 14);
    } catch(e) {}
    showFI([{name:LAYERS[li].name, color:col, props:feat.properties}]);
    if (isMobile) closeSidebar();
  }
}

// -- Search --------------------------------------------------------------------
function doSearch(q) {
  var res  = document.getElementById('sres');
  var info = document.getElementById('sinfo');
  if (!q || q.length < 2) {
    res.style.display = 'none';
    info.textContent  = 'Search across all layers';
    return;
  }
  var ql = q.toLowerCase(), matches = [];
  for (var fi = 0; fi < allFeats.length && matches.length < 50; fi++) {
    var f = allFeats[fi], props = f.props || {}, keys = Object.keys(props);
    for (var ki = 0; ki < keys.length; ki++) {
      var v = props[keys[ki]];
      if (v !== null && v !== undefined && String(v).toLowerCase().indexOf(ql) !== -1) {
        matches.push({name:f.name,color:f.color,props:f.props,mk:keys[ki],mv:String(v),ll:f.ll});
        break;
      }
    }
  }
  res._m = matches;
  if (!matches.length) {
    res.innerHTML = '<div class="sitem">No results found</div>';
    res.style.display = 'block';
    info.textContent = 'No matches';
    return;
  }
  var h = '';
  matches.forEach(function(m, i) {
    h += '<div class="sitem" onclick="goSearch('+i+')">'+
         '<div>'+escHtml(m.mk)+': <b>'+escHtml(m.mv)+'</b></div>'+
         '<div class="slyr" style="color:'+m.color+'">&#9679; '+escHtml(m.name)+'</div></div>';
  });
  res.innerHTML = h;
  res.style.display = 'block';
  info.textContent = matches.length+' result(s)';
}

function goSearch(i) {
  var m = document.getElementById('sres')._m[i];
  if (!m) return;
  try {
    if (m.ll.getBounds) map.fitBounds(m.ll.getBounds(), {maxZoom:14});
    else if (m.ll.getLatLng) map.setView(m.ll.getLatLng(), 14);
    showFI([{name:m.name,color:m.color,props:m.props}]);
    if (isMobile) closeSidebar();
  } catch(e) {}
  document.getElementById('sres').style.display = 'none';
}

// -- Share / QR ------------------------------------------------------------------
function openShare() {
  // If already on a web URL (opened via QR on mobile) — do nothing
  if(window.location.protocol !== 'file:') {
    return;
  }
  // If QR was already generated, show it directly without re-uploading
  if(_cachedQRUrl) {
    var m = document.getElementById('qrmodal');
    if(m) m.style.display = 'flex';
    document.getElementById('qr-step1').style.display = 'none';
    document.getElementById('qr-step2').style.display = 'block';
    document.getElementById('qr-error').style.display  = 'none';
    if(document.getElementById('qr-progress-box'))
      document.getElementById('qr-progress-box').style.display = 'none';
    document.getElementById('qr-success').style.display = 'block';
    return;
  }
  var m = document.getElementById('qrmodal');
  if(!m) return;
  // If already on a web URL, show a simpler message
  if (window.location.protocol !== 'file:') {
    // Already on web URL - just close the modal, nothing to do
    m.style.display = 'none';
    return;
  }
  document.getElementById('qr-step1').style.display = 'block';
  document.getElementById('qr-step2').style.display = 'none';
  document.getElementById('qr-error').style.display  = 'none';
  document.getElementById('qr-canvas').innerHTML     = '';
  document.getElementById('qr-url-box').style.display = 'none';
  m.style.display = 'flex';
}

function generateQR() {
  var step1 = document.getElementById('qr-step1');
  var step2 = document.getElementById('qr-step2');
  var errBox = document.getElementById('qr-error');
  var prog   = document.getElementById('qr-progress-text');
  step1.style.display  = 'none';
  step2.style.display  = 'block';
  errBox.style.display = 'none';
  prog.textContent     = 'Uploading map... please wait';

  // Clone document and clear dynamic content before uploading
  // This prevents duplicate cards when mobile opens the uploaded HTML
  var docClone = document.documentElement.cloneNode(true);
  // Clear entire Leaflet map content — it gets rebuilt fresh by JS on load
  var mapDiv = docClone.querySelector('#map');
  if(mapDiv) {
    // Keep only the bmwrap (basemap selector), remove all Leaflet SVG
    var bmw = mapDiv.querySelector('#bmwrap');
    mapDiv.innerHTML = '';
    if(bmw) mapDiv.appendChild(bmw);
    // Clear leaflet_id so L.map() can reinitialize
    mapDiv._leaflet_id = null;
    delete mapDiv._leaflet_id;
  }
  // Hide feature info panel properly
  var fiEl = docClone.querySelector('#fi');
  if(fiEl) { fiEl.className = 'fi'; fiEl.style.display = ''; }
  var toEmpty = ['lctrl','sctrl','tlsel','twrap','fibody','sres'];
  toEmpty.forEach(function(id){
    var el = docClone.querySelector('#' + id);
    if(el) el.innerHTML = '';
  });
  // Remove desk-toggle from clone — JS recreates it fresh on load
  var dtClone = docClone.querySelector('#desk-toggle');
  if(dtClone) dtClone.parentNode.removeChild(dtClone);
  // Reset sidebar inline styles in clone
  var sbClone = docClone.querySelector('#sidebar');
  if(sbClone) { sbClone.style.transform=''; sbClone.classList.remove('open'); }
  var mapClone = docClone.querySelector('#map');
  if(mapClone) mapClone.style.left = '260px';
  var coordClone = docClone.querySelector('#coord');
  if(coordClone) coordClone.style.left = '260px';
  // Hide modal and feature info
  var modal = docClone.querySelector('#qrmodal');
  if(modal) modal.style.display = 'none';
  var fi = docClone.querySelector('#fi');
  if(fi) { fi.className = 'fi'; fi.style.display = ''; }

  var html = docClone.outerHTML;
  var blob = new Blob([html], {type:'text/html'});
  var sizeMB = (blob.size / 1024 / 1024).toFixed(1);
  prog.textContent = 'Uploading ' + sizeMB + ' MB...';

  // Upload to catbox (reliable, no CORS issues)
  var fd1 = new FormData();
  fd1.append('reqtype', 'fileupload');
  fd1.append('time', '72h');
  fd1.append('fileToUpload', blob, 'qgis_map.html');
  fetch('https://litterbox.catbox.moe/resources/internals/api.php',
        {method:'POST', body:fd1})
    .then(function(r){ return r.text(); })
    .then(function(url){
      url = url.trim();
      if(url.indexOf('http')===0){ showQRCode(url); return; }
      throw new Error('failed');
    })
    .catch(function(){
      prog.textContent = 'Generating QR code...';
      var fd2 = new FormData();
      fd2.append('file', blob, 'qgis_map.html');
      fetch('https://tmpfiles.org/api/v1/upload', {method:'POST', body:fd2})
        .then(function(r){ return r.json(); })
        .then(function(d){
          if(d.data && d.data.url){
            showQRCode(d.data.url.replace('tmpfiles.org/','tmpfiles.org/dl/'));
          } else { throw new Error(); }
        })
        .catch(function(){
          step2.style.display  = 'none';
          errBox.style.display = 'block';
        });
    });
}


function showQRCode(url) {
  _cachedQRUrl = url;  // cache for re-use
  document.getElementById('qr-progress-box').style.display = 'none';
  document.getElementById('qr-success').style.display = 'block';
  // Re-enable button
  var gb = document.getElementById('qr-gen-btn');
  if(gb){ gb.disabled=false; gb.textContent='Generate QR Code'; gb.style.opacity='1'; }
  document.getElementById('qr-host-info').textContent = 'Link valid for 24 hours';
  var canvas = document.getElementById('qr-canvas');
  canvas.innerHTML = '';

  // Show URL immediately so user can copy even if QR image fails
  document.getElementById('qr-url').value = url;
  document.getElementById('qr-url-box').style.display = 'block';

  // Try QR image from multiple sources
  var img = document.createElement('img');
  img.style.cssText = 'width:200px;height:200px;display:block;margin:0 auto 10px;border-radius:8px;border:1px solid #e2e8f0';
  img.alt = 'QR Code';

  var sources = [
    'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=' + encodeURIComponent(url),
    'https://chart.googleapis.com/chart?chs=200x200&cht=qr&chl=' + encodeURIComponent(url),
    'https://quickchart.io/qr?text=' + encodeURIComponent(url) + '&size=200'
  ];
  var srcIdx = 0;

  img.onerror = function() {
    srcIdx++;
    if(srcIdx < sources.length) {
      img.src = sources[srcIdx];
    } else {
      // All QR sources failed - show message with link
      canvas.innerHTML = '<div style="background:#eff6ff;border:1px solid #bfdbfe;' +
        'border-radius:8px;padding:14px;color:#1e40af;font-size:.82rem;text-align:center">' +
        'QR image blocked by network.<br><b>Copy the link below and open on phone.</b></div>';
    }
  };

  img.onload = function() {
    // QR loaded successfully - make sure it shows
    img.style.display = 'block';
  };

  img.src = sources[0];
  canvas.appendChild(img);
}

function copyQRUrl() {
  var url = document.getElementById('qr-url').value;
  if(navigator.clipboard){
    navigator.clipboard.writeText(url).then(function(){
      document.getElementById('qr-copy-btn').textContent = 'Copied!';
      setTimeout(function(){
        document.getElementById('qr-copy-btn').textContent = 'Copy Link';
      }, 2000);
    });
  } else { window.prompt('Copy link:', url); }
}

var _qrm = document.getElementById('qrmodal');
if(_qrm) _qrm.addEventListener('click', function(e){
  if(e.target===this) this.style.display='none';
});
