# Configuration and geographic quality

The JSON presets are the practical schema. Paths for imported GeoJSON are relative to the configuration file; output and cache locations are supplied separately. Nothing in the skill relies on a user's personal folder.

| Setting | Meaning |
|---|---|
| `schema_version` | Must be `1` |
| `name`, `slug` | Graphic title and safe output filename |
| `boundary_url` | Census state-boundary ZIP with STATEFP, NAME, STUSPS fields; CRS is read from its `.prj` |
| `elevation_service` | USGS-compatible ArcGIS elevation ImageServer with raw F32 TIFF export |
| `metres_per_unit` | Horizontal metre to Blender-unit conversion; elevations use the same base conversion |
| `max_missing_land_fraction` | Fails preparation if too much land lacks real elevation; default 2% |
| `panels` | One or more independently projected and positioned map regions |
| `style.palette` | Ascending `[elevation_metres, "#RRGGBB"]` pairs; stylized hypsometric color |
| `style.contours` | Optional shader contours from physical elevation attribute; false in national overview to avoid visual noise |
| `style.boundary_width` | Visible boundary bevel radius in final scene units |
| `camera` | Rig orbit/tilt in degrees, dolly distance in scene units, lens in millimetres, target position |
| `render` | Pixel width, pixel height, EEVEE samples |
| `labels` | Attributed/checked label positions in WGS84 lon/lat, panel, text, size in scene units; `water: true` puts text on ocean level |
| `vector_layers` | Additional attributed local GeoJSON rivers/lines or lake polygons |

## Panels

- `id` is a unique lowercase slug; `title` is editable display text.
- `states` includes specified two-digit Census FIPS codes; `exclude_states` removes specified codes. With no include list, the panel includes all non-excluded records. Puerto Rico and island areas are excluded from the U.S. test; D.C. remains included.
- `crs` is a projected metre EPSG CRS. Use a local state/regional CRS for close shots. EPSG:5070 is the national CONUS Albers projection; EPSG:3338 is Alaska Albers; EPSG:32605 covers Hawaii's principal islands. Do not put Alaska/Hawaii into the CONUS projection or treat insets as geographically contiguous.
- `clip_lonlat` optionally limits visible geographic scope before projection. Hawaii's preset clips the main islands; it does not depict the entire Northwestern Hawaiian island chain.
- `texture_width` controls the exported DEM/normal-texture sample count across the panel; `mesh_width` controls display geometry. Heights preserve aspect. Both are sampling settings, not statements of the underlying data's native resolution.
- `relief` is nominal vertical exaggeration relative to horizontal scale. `scale` resizes an entire panel uniformly; `position` places its center in scene X/Y. Insets retain independent scales and are labeled accordingly.

The projected grid uses pixel-center endpoints. Raw GeoTIFF metadata is checked for CRS, dimensions, band count, and finite elevation range. Land masks preserve polygon holes so major lakes remain water. Mesh faces require four valid land/elevation samples, which avoids false terrain bridging across water but omits islands below display spacing. Boundaries may show those small islands without raised terrain. Increase sampling for a closer shot rather than hiding that limitation.

Vector outlines are simplified by one quarter of display grid spacing and densified before draping. Boundaries follow the actual triangle surface, not a differently sampled DEM. The physical `Elevation_m` point attribute drives colors/contours and remains independent of artistic exaggeration.

## River and lake example

Add to `vector_layers`:

```json
{
  "panel": "north-carolina",
  "name": "Cape Fear River",
  "path": "data/cape-fear.geojson",
  "crs": "EPSG:4326",
  "name_field": "GNIS_NAME",
  "kind": "river",
  "color": "#53b4c4",
  "width": 0.018,
  "attribution": "USGS NHD; include dataset edition and acquisition date here"
}
```

`river` expects LineString or MultiLineString geometry. Each feature stays an independent editable curve. `waterbody` expects Polygon/MultiPolygon geometry and triangulates only covered areas, preserving holes; these draped cartographic fills are not hydrologic water-level simulations. Rivers are illustrative widths unless widths are explicitly sourced. Never substitute manually invented river routes for authoritative geometry.

This importer reads local GeoJSON. It does not automatically download NHD/3DHP, NLCD, or NWI data. Supply source attribution and check each layer's CRS/edition. Unexpected geometry types should be corrected upstream rather than silently accepted.

## Extending detail without excessive geometry

For closeups, build a new regional panel or output at finer spacing. If adding nested grids, align child edges to parent vertices, blend heights across a transition, and test seams from the final shot. Do not stack overlapping terrain tiles or assume coincident XY coordinates imply matching elevation.

For land cover/wetlands, reproject/resample data to the same DEM grid and pack textures. Use nearest-neighbor resampling for categorical classes; keep class masks separate from styled colors. A shaded elevation palette alone does not show vegetation, urban development, or wetlands.

## Primary data references

- [USGS 3DEP elevation service](https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer)
- [Census cartographic boundary files](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html)
- [Census 2024 boundary download](https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_state_500k.zip)
- [USGS hydrography access](https://www.usgs.gov/3d-hydrography-program/access-3dhp-data-products)
- [Blender Python API](https://docs.blender.org/api/current/)

Source requests, download dates, and SHA256 hashes are recorded per run. Provider data may change between uncached runs. Retain checked caches or source assets to preserve the exact inputs; a URL alone does not pin a changing service.


## General camera and ocean controls

`camera.dof` accepts `{"enabled": true, "aperture": 5.6}`. It defaults to disabled to preserve readable wide-map typography; the shared aim/focus null always exists. Its Damped Track constraint aims the camera at the same object used for focus.

`style.ocean` accepts `ripple_strength`, `color_variation`, `water_roughness` and `drift_speed` (defaults 0.16, 0.65, 0.40 and 0.16). Ripples are procedural bump shading on one quad; drift follows the scene frame rate. Controls are editable/keyframable object properties.

The detailed NC presets use a separate configuration shape with `mode: detailed-template`. See [detailed-map.md](detailed-map.md); do not mix panel/DEM configuration into that fixed snapshot mode.
