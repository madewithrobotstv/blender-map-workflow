# Running the workflow

The external Python environment does GIS preparation. Blender's bundled Python builds and verifies the scene with `bpy` and NumPy. Do not install rasterio, pyproj, or shapely into Blender.

## Setup

Use Python 3.11 or newer and a stable Blender release >= 4.5. The reference run uses Python 3.14.7 and Blender 5.2.2 LTS on macOS/Metal. Other releases/platforms are supported by discovery and defensive settings but require their own validation.

From the directory containing `blender-map-workflow/`:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r blender-map-workflow/requirements.txt
.venv/bin/python blender-map-workflow/scripts/map.py doctor
```

On Windows, substitute `.venv\Scripts\python.exe` and `python` for the interpreter paths. Commands use argument lists internally, so executable paths containing spaces work. If Blender cannot be found, add `--blender "PATH_TO_BLENDER_EXECUTABLE"`; on macOS this is the executable inside the `.app`, not the `.app` directory.

## Reproduce the U.S. test

```sh
.venv/bin/python blender-map-workflow/scripts/map.py run \
  --config blender-map-workflow/presets/united-states.json \
  --output outputs/us-test \
  --cache cache \
  --render
```

The first run downloads official source files. Later requests with the same URLs use the cache only after checking SHA256 hashes. To forbid network access, add `--offline`. It fails explicitly if any checked source is missing. Network permissions and Blender GPU access must be granted by the agent's host environment; the skill does not bypass them.

Stages can be run separately:

```sh
python scripts/map.py prepare --config CONFIG --output OUTPUT --cache CACHE
python scripts/map.py build --config CONFIG --output OUTPUT
python scripts/map.py verify --output OUTPUT --render
```

These shorter commands assume the current directory is the skill directory and `python` is the configured GIS environment. Build and verify use the prepared `project.json` as the authoritative settings. Reprepare after configuration changes. To regenerate a saved output, add `--overwrite`; it copies the entire existing output to a sibling timestamped backup before doing work. Prefer a new output directory for iterative comparisons.

## Deliverable structure

```text
OUTPUT/
  config.json                  Effective requested settings
  project.json                 Source requests, hashes, dates, CRS, grids
  SLUG.blend                   Packed scene, editable terrain and overlays
  build-report.json            Counts, Blender/backend, measured render time
  verification-report.json     Saved-scene checks and optional reopened time
  environment.json             Python/library/Blender versions
  build.log / verify.log        Diagnostics
  assets/
    state-boundaries-source.zip
    PANEL-source.tif           Actual downloaded raw elevation
    PANEL-terrain.npz          Display elevations and land/NoData mask
    PANEL-normal.png           Fine relief shading
    PANEL-vectors.json         Projected editable geographic layers
    imported-vector-NN.geojson Original optional vector inputs; config paths are localized
  renders/
    overview.png              Initial render
    verified.png              Render from reopened file with --render
```

The scene embeds provenance and instructions as Blender text blocks. Source files remain outside the `.blend` for reprocessing; every normal texture is packed inside it. It uses Blender's built-in font, one perspective camera, ordinary driver expressions, and no persistent Python frame handlers.

## Another LLM using Blender MCP

Tell the LLM where `SKILL.md` is, and provide a filesystem/shell tool plus Blender or Blender MCP. A generic agent can read the Markdown directly; it does not need a Codex-specific installer.

1. Run the scripts through a shell tool. For long downloads/renders, retain the process/log handle and inspect completion before claiming success.
2. Inspect the generated PNG through an image tool. Use reports to choose changes, then rebuild.
3. If a live Blender connection is available, call its status and scene inspection tools before making changes. Preserve the current scene in the user's project before opening another file. Never clear live scene objects to run this builder.
4. Open the output `.blend` with Blender's normal file operator, then inspect through the camera. In Blender MCP this can be done with `execute_blender_code` and `look`, or equivalent tools in another connector.
5. Use custom properties instead of directly moving the driven camera:

```python
import bpy
rig = bpy.data.objects['CAMERA_RIG']
rig['Orbit (degrees)'] = 15.0
rig['Tilt (degrees)'] = 58.0
rig['Distance'] = 92.0
rig['Focal length (mm)'] = 48.0
rig.update_tag()
bpy.context.scene.frame_set(bpy.context.scene.frame_current)
bpy.context.view_layer.update()
```

Root properties change vertical exaggeration; root X/Y coordinates and scales define inset layout. Curves and labels share their panel's root so their positions respond to relief changes. Labels face the camera through constraints. Large graphic title/footer objects follow the camera; their placement is designed for the initial overview lens and should be reviewed when changing focal length.

## Example requests

“Use this skill to reproduce the United States preset in a new folder. Keep all states editable, render a preview, reopen the scene, and report the tested Blender version.”

“Use the North Carolina preset to create a statewide relief map. Add this attributed GeoJSON Cape Fear flowline as a separate river curve. Keep an editable rig; no animation yet.”

“Create a closer Wilmington shot. Choose an appropriately smaller DEM extent and denser mesh for that shot, rather than zooming into the national overview grid.”

Do not claim the minimal NC preset reproduces the complete reference scene: NLCD land cover, NWI wetlands, counties, and named river datasets require additional acquisition/preparation. Their reusable design lessons are documented separately.
