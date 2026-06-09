# Instant WebGIS Viewer — QGIS Plugin
# Export QGIS vector layers to a shareable interactive HTML map
# Copyright (C) 2026 Ballu Harish
# Email: harishmanjulason@gmail.com
# GitHub: https://github.com/HariMSS/instant_webgis_viewer
# Licensed under GNU General Public License v2 or later

import json
from qgis.core import (
    QgsVectorLayer, QgsWkbTypes,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsProject, QgsDistanceArea, QgsUnitTypes,
    QgsSingleSymbolRenderer, QgsCategorizedSymbolRenderer,
    QgsGraduatedSymbolRenderer,
)

PALETTE = ['#1e64c8','#e05c2a','#27a845','#8b2fc9',
           '#c8a01e','#c8285a','#1ec8b4','#6e6e6e']
_idx = [0]


def get_layer_style(layer):
    color = PALETTE[_idx[0] % len(PALETTE)]
    _idx[0] += 1
    try:
        r = layer.renderer()
        if not r:
            return {'color': color, 'opacity': 0.7}

        def from_sym(sym):
            if not sym:
                return color, 0.7
            c = sym.color()
            return '#{:02x}{:02x}{:02x}'.format(c.red(), c.green(), c.blue()), round(c.alpha()/255, 2)

        if isinstance(r, QgsSingleSymbolRenderer):
            col, op = from_sym(r.symbol())
        elif isinstance(r, QgsCategorizedSymbolRenderer):
            cats = r.categories()
            col, op = from_sym(cats[0].symbol()) if cats else (color, 0.7)
        elif isinstance(r, QgsGraduatedSymbolRenderer):
            rngs = r.ranges()
            col, op = from_sym(rngs[0].symbol()) if rngs else (color, 0.7)
        else:
            col, op = color, 0.7
        return {'color': col, 'opacity': max(0.2, op)}
    except Exception:
        return {'color': color, 'opacity': 0.7}


def get_geometry_type(layer):
    flat = QgsWkbTypes.flatType(layer.wkbType())
    if flat in (QgsWkbTypes.Point, QgsWkbTypes.MultiPoint):
        return 'Point'
    if flat in (QgsWkbTypes.LineString, QgsWkbTypes.MultiLineString):
        return 'Line'
    if flat in (QgsWkbTypes.Polygon, QgsWkbTypes.MultiPolygon):
        return 'Polygon'
    return 'Vector'


def compute_stats(layer):
    stats = {
        'feature_count': layer.featureCount(),
        'geometry_type': get_geometry_type(layer),
        'crs': layer.crs().authid(),
        'fields': [f.name() for f in layer.fields()],
        'total_length_km': None,
        'total_area_km2': None,
    }
    try:
        da = QgsDistanceArea()
        da.setSourceCrs(layer.crs(), QgsProject.instance().transformContext())
        da.setEllipsoid('WGS84')
        gtype = stats['geometry_type']
        total = 0.0
        if gtype == 'Line':
            for feat in layer.getFeatures():
                if feat.geometry() and not feat.geometry().isEmpty():
                    total += da.measureLength(feat.geometry())
            stats['total_length_km'] = round(
                da.convertLengthMeasurement(total, QgsUnitTypes.DistanceKilometers), 2)
        elif gtype == 'Polygon':
            for feat in layer.getFeatures():
                if feat.geometry() and not feat.geometry().isEmpty():
                    total += da.measureArea(feat.geometry())
            stats['total_area_km2'] = round(
                da.convertAreaMeasurement(total, QgsUnitTypes.AreaSquareKilometers), 2)
    except Exception:
        pass
    return stats


def export_geojson(layer):
    wgs84 = QgsCoordinateReferenceSystem('EPSG:4326')
    transform = QgsCoordinateTransform(layer.crs(), wgs84, QgsProject.instance())
    features = []
    for feat in layer.getFeatures():
        geom = feat.geometry()
        if not geom or geom.isEmpty():
            continue
        geom.transform(transform)
        props = {}
        for field in layer.fields():
            val = feat[field.name()]
            if val is None:
                props[field.name()] = None
            elif isinstance(val, (int, float)):
                props[field.name()] = val
            else:
                try:
                    props[field.name()] = str(val).replace('\x00','').replace('\r',' ')
                except Exception:
                    props[field.name()] = None
        features.append({
            'type': 'Feature',
            'geometry': json.loads(geom.asJson()),
            'properties': props,
        })
    return {'type': 'FeatureCollection', 'features': features}
