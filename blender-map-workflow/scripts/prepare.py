"""Prepare aligned, projected DEM grids and editable vectors outside Blender."""
import argparse
import copy
import io
import json
import math
import urllib.parse
import zipfile
from pathlib import Path

import numpy as np
import rasterio
import shapefile
from PIL import Image
from pyproj import CRS, Transformer
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from shapely.geometry import box, mapping, shape
from shapely.ops import transform, unary_union, triangulate

from common import download, load_config, sha256, write_json


def read_states(path):
    with zipfile.ZipFile(path) as archive:
        files = archive.namelist()
        reader = shapefile.Reader(**{extension: io.BytesIO(archive.read(next(n for n in files if n.endswith('.' + extension))))
                                    for extension in ('shp', 'shx', 'dbf')})
        prj = next(n for n in files if n.endswith('.prj'))
        source_crs = CRS.from_wkt(archive.read(prj).decode())
        return [{'fips': s.record['STATEFP'], 'name': s.record['NAME'],
                 'abbr': s.record['STUSPS'], 'geometry': shape(s.shape.__geo_interface__)}
                for s in reader.iterShapeRecords()], source_crs


def geometry_parts(geom, kind):
    if geom.is_empty:
        return []
    if geom.geom_type == kind:
        return [geom]
    if hasattr(geom, 'geoms'):
        return [p for g in geom.geoms for p in geometry_parts(g, kind)]
    return []


def export_dem(config, panel, bounds, width, height, cache, offline):
    params = {'bbox': ','.join(f'{x:.3f}' for x in bounds), 'bboxSR': CRS(panel['crs']).to_epsg(),
              'imageSR': CRS(panel['crs']).to_epsg(), 'size': f'{width},{height}', 'format': 'tiff',
              'pixelType': 'F32', 'interpolation': 'RSP_BilinearInterpolation', 'adjustAspectRatio': 'false',
              'renderingRule': json.dumps({'rasterFunction': 'None'}), 'f': 'json'}
    if params['bboxSR'] is None:
        raise ValueError('This downloader requires an EPSG projected CRS')
    url = config['elevation_service'].rstrip('/') + '/exportImage?' + urllib.parse.urlencode(params)
    key = __import__('hashlib').sha256(url.encode()).hexdigest()[:20]
    response_path = cache / f'dem-{key}.json'
    raster_path = cache / f'dem-{key}.tif'
    response_source = download(url, response_path, offline)
    response = json.loads(response_path.read_text())
    if 'error' in response or 'href' not in response:
        raise RuntimeError(f'USGS elevation export failed: {response}')
    raster_source = download(response['href'], raster_path, offline)
    with rasterio.open(raster_path) as dataset:
        if dataset.count != 1 or dataset.crs != CRS(panel['crs']):
            raise RuntimeError('Elevation response has unexpected bands or CRS')
        if dataset.width != width or dataset.height != height:
            raise RuntimeError('Elevation response has unexpected dimensions')
        dem = dataset.read(1, masked=True).filled(np.nan).astype(np.float32)
        dem[(dem < -500) | (dem > 10000)] = np.nan
        return dem, dataset.transform, tuple(dataset.bounds), [response_source, raster_source], raster_path


def prepare(config_path, output, cache, offline=False):
    config_path, output, cache = Path(config_path).resolve(), Path(output).resolve(), Path(cache).resolve()
    config = load_config(config_path)
    assets = output / 'assets'
    assets.mkdir(parents=True, exist_ok=True)
    boundary_path = cache / ('boundaries-' + __import__('hashlib').sha256(config['boundary_url'].encode()).hexdigest()[:16] + '.zip')
    sources = [download(config['boundary_url'], boundary_path, offline)]
    states, boundary_crs = read_states(boundary_path)
    import shutil
    shutil.copy2(boundary_path, assets / 'state-boundaries-source.zip')
    effective_config = copy.deepcopy(config)
    for index, layer in enumerate(config.get('vector_layers', [])):
        source_path = (config_path.parent / layer['path']).resolve()
        local_path = assets / f'imported-vector-{index:02d}.geojson'
        if source_path != local_path:
            shutil.copy2(source_path, local_path)
        effective_config['vector_layers'][index]['path'] = local_path.relative_to(output).as_posix()
    write_json(output / 'config.json', effective_config)
    manifest = {'schema_version': 1, 'config_sha256': sha256(output / 'config.json'),
                'requested_config_sha256': sha256(config_path), 'config': effective_config, 'panels': [],
                'sources': sources, 'attribution': 'Elevation: USGS 3DEP. Boundaries: U.S. Census Bureau, 2024 cartographic boundary files.',
                'boundary_crs': boundary_crs.to_string(),
                'vertical_datum': 'Provider vertical datum; untransformed metres. This is a visualization, not a surveying product.',
                'palette_type': 'Stylized hypsometric elevation colors; not satellite imagery or land-cover classification.'}
    for panel in config['panels']:
        print('PREPARING', panel['id'], flush=True)
        crs = CRS(panel['crs'])
        if not crs.is_projected or any(a.unit_name != 'metre' for a in crs.axis_info[:2]):
            raise ValueError('Each panel requires a projected CRS measured in metres')
        project = Transformer.from_crs(boundary_crs, crs, always_xy=True)
        label_project = Transformer.from_crs('EPSG:4326', crs, always_xy=True)
        selected = []
        for state in states:
            if panel.get('states') and state['fips'] not in panel['states']:
                continue
            if state['fips'] in panel.get('exclude_states', []):
                continue
            geographic = state['geometry']
            if panel.get('clip_lonlat'):
                geographic = geographic.intersection(box(*panel['clip_lonlat']))
            geom = transform(project.transform, geographic)
            if not geom.is_empty:
                selected.append({**state, 'geometry': geom})
        if not selected:
            raise ValueError(f'No states matched panel {panel["id"]}')
        land = unary_union([s['geometry'] for s in selected])
        xmin, ymin, xmax, ymax = land.bounds
        padding = (xmax - xmin) * 0.025
        requested_bounds = (xmin - padding, ymin - padding, xmax + padding, ymax + padding)
        width = panel['texture_width']
        height = math.ceil(width * (requested_bounds[3] - requested_bounds[1]) / (requested_bounds[2] - requested_bounds[0]))
        if height > 8000:
            raise ValueError('DEM height exceeds service limit; reduce texture_width')
        dem, raster_transform, bounds, dem_sources, raster_path = export_dem(config, panel, requested_bounds, width, height, cache, offline)
        manifest['sources'].extend(dem_sources)
        land_mask = rasterize([(mapping(land), 1)], out_shape=dem.shape, transform=raster_transform, dtype='uint8').astype(bool)
        if not land_mask.any():
            raise RuntimeError(f'{panel["id"]}: no land pixels at this sampling resolution')
        missing = land_mask & ~np.isfinite(dem)
        missing_fraction = float(missing.sum() / max(1, land_mask.sum()))
        if missing_fraction > config.get('max_missing_land_fraction', 0.02):
            raise RuntimeError(f'{panel["id"]}: {missing_fraction:.1%} of land has no elevation. Acquire another DEM; do not fabricate relief.')
        # Pixel centers, not GeoTIFF outside edges, define the Blender grid.
        dx, dy = abs(raster_transform.a), abs(raster_transform.e)
        centers = [bounds[0] + dx / 2, bounds[1] + dy / 2, bounds[2] - dx / 2, bounds[3] - dy / 2]
        mesh_w = panel['mesh_width']
        mesh_h = max(16, round(mesh_w * height / width))
        ix = np.linspace(0, width - 1, mesh_w)
        iy = np.linspace(0, height - 1, mesh_h)
        # Bilinear reduction on the raw elevation grid; retain NoData as missing.
        xx, yy = np.meshgrid(ix, iy)
        i, j = np.minimum(xx.astype(int), width - 2), np.minimum(yy.astype(int), height - 2)
        tx, ty = xx - i, yy - j
        coarse = (dem[j, i] * (1 - tx) * (1 - ty) + dem[j, i + 1] * tx * (1 - ty) +
                  dem[j + 1, i] * (1 - tx) * ty + dem[j + 1, i + 1] * tx * ty)
        coarse_transform = from_bounds(centers[0] - (centers[2]-centers[0])/(mesh_w-1)/2,
                                       centers[1] - (centers[3]-centers[1])/(mesh_h-1)/2,
                                       centers[2] + (centers[2]-centers[0])/(mesh_w-1)/2,
                                       centers[3] + (centers[3]-centers[1])/(mesh_h-1)/2, mesh_w, mesh_h)
        coarse_land = rasterize([(mapping(land), 1)], out_shape=(mesh_h, mesh_w), transform=coarse_transform, dtype='uint8')
        valid = (coarse_land > 0) & np.isfinite(coarse)
        # Missing pixels stay excluded from geometry. A benign value only prevents NaN normal texels off the terrain.
        safe = np.where(np.isfinite(dem), np.maximum(dem, 0), 0)
        dzdy, dzdx = np.gradient(safe * panel['relief'], -dy, dx)
        normals = np.stack([-dzdx, -dzdy, np.ones_like(dem)], axis=-1)
        normals /= np.maximum(np.linalg.norm(normals, axis=-1, keepdims=True), 1e-8)
        normal_path = assets / f'{panel["id"]}-normal.png'
        Image.fromarray(np.clip((normals * .5 + .5) * 255, 0, 255).astype(np.uint8)).save(normal_path)
        np.savez_compressed(assets / f'{panel["id"]}-terrain.npz', elevation=coarse.astype(np.float32), valid=valid)
        center = [(centers[0] + centers[2]) / 2, (centers[1] + centers[3]) / 2]
        spacing = (centers[2] - centers[0]) / (mesh_w - 1)
        tolerance = spacing * .25
        vectors = []
        for state in selected:
            outline = state['geometry'].simplify(tolerance, preserve_topology=True).boundary.segmentize(spacing * .45)
            rings = [list(line.coords) for line in geometry_parts(outline, 'LineString')]
            representative = state['geometry'].representative_point()
            vectors.append({'name': state['name'], 'abbr': state['abbr'], 'fips': state['fips'], 'lines': rings,
                            'label_xy': [representative.x, representative.y], 'area_m2': state['geometry'].area})
        additional = []
        for layer in effective_config.get('vector_layers', []):
            if layer['panel'] != panel['id']:
                continue
            path = output / layer['path']
            data = json.loads(path.read_text())
            projector = Transformer.from_crs(layer.get('crs', 'EPSG:4326'), crs, always_xy=True)
            manifest['sources'].append({'file': layer['path'], 'sha256': sha256(path), 'attribution': layer['attribution']})
            for feature in data['features']:
                geom = transform(projector.transform, shape(feature['geometry'])).intersection(box(*centers))
                if geom.is_empty:
                    continue
                item = {'name': str(feature.get('properties', {}).get(layer.get('name_field', 'name'), layer['name'])),
                        'kind': layer.get('kind', 'river'), 'color': layer.get('color', '#53b4c4'), 'width': layer.get('width', .018)}
                if item['kind'] == 'waterbody':
                    polygons = geometry_parts(geom, 'Polygon')
                    if not polygons:
                        raise ValueError(f'Waterbody layer requires polygons: {item["name"]}')
                    item['triangles'] = [list(t.exterior.coords)[:3] for p in polygons for t in triangulate(p) if p.covers(t)]
                else:
                    if item['kind'] != 'river' or not geometry_parts(geom, 'LineString'):
                        raise ValueError(f'River layer requires lines and kind=river: {item["name"]}')
                    geom = geom.simplify(tolerance * .4).segmentize(spacing * .3)
                    item['lines'] = [list(line.coords) for line in geometry_parts(geom, 'LineString')]
                additional.append(item)
        labels = []
        for label in config.get('labels', []):
            if label['panel'] == panel['id']:
                x, y = label_project.transform(label['lon'], label['lat'])
                labels.append({**label, 'xy': [x, y]})
        write_json(assets / f'{panel["id"]}-vectors.json', {'states': vectors, 'additional': additional, 'labels': labels})
        # Copy the actual source raster into the portable output, never a link to a personal archive.
        shutil.copy2(raster_path, assets / f'{panel["id"]}-source.tif')
        info = {**panel, 'bounds': centers, 'center': center, 'texture_size': [width, height], 'mesh_size': [mesh_w, mesh_h],
                'source_spacing_m': [dx, dy], 'mesh_spacing_m': spacing, 'missing_land_fraction': missing_fraction,
                'land_elevation_range_m': [float(np.nanmin(dem[land_mask])), float(np.nanmax(dem[land_mask]))],
                'state_count': len(selected), 'state_fips': [s['fips'] for s in selected]}
        manifest['panels'].append(info)
        print('PREPARED', panel['id'], f'{mesh_w}x{mesh_h} mesh / {width}x{height} relief texture / missing land {missing_fraction:.2%}', flush=True)
    write_json(output / 'project.json', manifest)
    print('PREPARATION_COMPLETE', output, flush=True)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--cache', required=True, type=Path)
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    prepare(args.config, args.output, args.cache, args.offline)
