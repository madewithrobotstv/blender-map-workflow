# Failures and targeted recovery

| Symptom | Action |
|---|---|
| `doctor` reports missing libraries | Install `requirements.txt` in the external GIS environment, not Blender's Python |
| Blender not found / only alpha found | Set `BLENDER_BIN` or pass `--blender` to a stable >= 4.5 executable |
| Download/DNS failure | Check host network permissions. Retry up to the script's bounded limit; use `--offline` only with a complete cache |
| ArcGIS export error | Read the JSON response; check EPSG projection, bbox, extent aspect, and <=8000 pixels per dimension |
| Old export JSON points at expired TIFF | Remove only that failed DEM request JSON and its `.source.json` cache metadata, then rerun online for a fresh export URL |
| Missing-land threshold fails | Inspect coverage/source NoData, acquire an alternate real DEM, or explicitly reduce the region. Do not fabricate elevation |
| Offline cache hash fails | Restore the original checked file or reacquire it online; do not remove the hash check |
| GPU crash before scripts run | Run Blender with allowed graphics-system access. Check stable driver/backend support on that host |
| Render artifacts in alpha | Repeat from the same saved scene in a stable release before rewriting geography; the reference project showed version-specific artifacts |
| Geographic layer floats or sinks | Check projection, datum, pixel centers, panel root, unit conversion, and triangle interpolation before changing offsets |
| Terrain fails camera margins | Reframe via rig target/distance/tilt; inspect the actual preview and rerun saved-file checks |
| Text disappears into terrain | Raise/reposition billboard using local maximum terrain under its footprint; review the final camera angle |
| Render works but relocation fails | Pack images, use relative paths, remove hidden source-scene dependencies, and rerun from a fresh directory |
| Output already has a `.blend` | Choose a new output or use `--overwrite`, which makes a backup first |

An unsaved/live scene is never a target for the scene builder. It requires a fresh background Blender process. To inspect in the user's live Blender, save their work and open the generated scene through ordinary Blender operations.

The tested render is an overview, not an exhaustive camera/animation certification. If animation is requested, sample beginning/middle/end frames and any closest views, inspect labels/seams/overlays at those views, and validate a short sequence before a long render.
