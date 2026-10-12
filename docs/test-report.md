# Reference validation — October 12, 2026

This report records the original general-map baseline. See [the detailed NC update report](nc-update-test-report.md) for the latest template, camera/ocean, privacy and relocation checks.

The national map was built from the portable scripts, inspected visually, reopened, and rendered again. The same workflow was run offline from checked cached inputs. The original reference scene was not edited.

## Tested environment

Blender 5.2.2 LTS, EEVEE, Metal, macOS 15.7.7 arm64. External preparation used Python 3.14.7, NumPy 2.5.4, Pillow 12.3.0, pyproj 3.8.0, rasterio 1.5.2, shapely 2.2.0, and pyshp 3.1.6. Only this Blender/platform combination has been tested end to end.

## National overview

| Measurement | Result |
|---|---|
| Scope | 50 states plus D.C.; separate Alaska and Hawaii main-island insets |
| Terrain vertices | 299,111 total |
| Terrain triangles | 588,902 total |
| Boundary objects | 51 independently editable objects |
| Packed normal textures | 3 |
| Render dimensions | 2560 × 1600 |
| Latest overview render | 2.18 seconds on the tested Mac |
| Scene size | 26.12 MB / 24.91 MiB |
| Missing sampled land elevation | 0% for every panel |
| Exaggeration | CONUS 45×, Alaska 30×, Hawaii 6× |

CONUS exported elevation spacing is about 2.02 km, with display mesh spacing about 5.39 km. Alaska spacing is about 2.75 km / 8.02 km; Hawaii about 692 m / 1.48 km. These are sampling intervals for an overview, not the native resolution of all contributing source DEMs. Small islands below the mesh spacing may retain boundaries without raised terrain.

## Verification

The saved scene passed checks for effective config hashes, a single perspective camera, valid drivers, complete state boundaries, packed/relative texture paths, finite triangulated terrain, physical elevation attributes, embedded provenance, working camera and relief controls, actual terrain framing, imported vector counts, and overlays matching the displayed triangle surface. The maximum national boundary drape difference was below 0.000009 scene units.

Three focused automated tests passed: triangle-based overlay sampling (where bilinear interpolation would produce the wrong height), north-to-south sample orientation at large projected coordinates, and offline cache integrity/tamper rejection. The skill passed the standard frontmatter/scaffold validator. A build into an existing saved output was correctly refused without `--overwrite`.

## Portability

The `.blend` and `project.json` were copied into a new directory without `assets/`. The relocated scene passed saved-file checks and rendered using only its packed normal textures and built-in font. Pixel comparison against the reopened reference was identical. This proves scene asset portability on the tested host, not cross-platform renderer equivalence.

The skill is also packaged separately from output, source caches, virtual environments, and original project files. No personal paths are embedded in its instructions or presets; platform installation discovery remains optional and can be overridden with an explicit executable.

The distributed skill archive was unpacked into a different path containing spaces. Its environment check and relocated-scene verification/render succeeded from another working directory with factory Blender preferences, so no preinstalled Blender add-on was needed.

## Regional import test

A reduced-detail variant of the North Carolina preset was tested at 1200 DEM samples / 500 mesh samples across the region. It retained one state boundary, 20 real USGS NHD Cape Fear flowline segments and one real NC OneMap waterbody polygon from the original public data cache. All saved-file checks passed, including feature counts and surface draping. Its overview was inspected visually; these selected segments are an importer test, not a complete Cape Fear river depiction.

Original GeoJSON inputs were copied into the output assets and their effective configuration paths localized. Repreparing from that effective config succeeded offline without depending on the original fixture paths.

## Limits

Animation, other Blender versions, Windows/Linux graphics systems, nationwide river layers, nested terrain seams, and full reference land-cover/wetland reproduction were not tested. The workflow includes guidance for those extensions and keeps them distinct from the tested national relief result. The benchmark is a single overview on one machine; it is not a controlled speed comparison against the original Cape Fear scene.
