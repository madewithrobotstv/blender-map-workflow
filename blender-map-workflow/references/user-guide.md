# First-use guide: request a map with an LLM

This folder gives an LLM a repeatable way to create editable Blender relief maps from real geographic data. Start by describing the map you need. The LLM uses the skill and scripts to prepare data, build the scene, inspect a preview, and verify the saved file.

## 1. Open the project and prepare the environment

Open the folder containing `README.md` and `blender-map-workflow/` as your LLM's working project. If you downloaded only the skill archive, open the folder containing `SKILL.md` and refer to that file directly.

The LLM needs access to the files and a shell or equivalent execution tool. Install Python 3.11 or newer and a stable Blender release >= 4.5. Internet access is needed for the first geographic-data download. The full workflow has been tested with Blender 5.2.2 LTS on macOS; other environments need their own checks.

Ask the LLM to read `SKILL.md`, set up the project's Python environment, and run the environment check before building. The [execution guide](workflow.md#setup) contains the exact setup commands. Blender's own Python builds the scene; the separate project Python environment prepares the geographic data.

A live Blender MCP connection is optional. It helps the LLM inspect and adjust the finished scene in Blender. The scripts can also build and render a map in a background Blender process. Save any work already open in Blender before opening the generated map.

## 2. Describe the intended map and closest view

Include the region, the closest planned camera view, the features you want to emphasize, and whether you want surrounding geography. Mention an existing visual reference if you have one. You do not need to choose a projection or write a configuration file yourself.

| Your request | How the workflow should approach it |
|---|---|
| General United States map | Start from the national preset, including Alaska and Hawaii main-island insets |
| Entire state | Adapt the state preset, download elevation for that state, and frame a statewide scene |
| City, watershed, or river corridor | Restrict the geographic extent and choose finer sampling for the closer shot |
| Close-up of an existing map | Inspect its current detail; rebuild the relevant region if the existing terrain cannot support the shot |
| State plus neighboring terrain | Include the requested surrounding geography in the configuration; the default state preset isolates the state |

The folder includes national and North Carolina presets. Requests for another U.S. state require the LLM to adapt a preset. The bundled data acquisition supports U.S. maps; other countries require an appropriate data provider.

## 3. Use a starting request

### National overview

> Read `blender-map-workflow/SKILL.md` and follow its workflow. Create a United States relief map in a new output folder, with all 50 states, D.C., and clearly labeled Alaska and Hawaii insets. Keep the terrain, boundaries, and labels editable. Render and inspect a preview, reopen the saved scene, and return the scene and verification results. No animation yet.

### State map

> Read `blender-map-workflow/SKILL.md` and follow its state-map process. Create a statewide relief map of Colorado in a new output folder. Emphasize the mountains, include Denver and Colorado Springs labels, and keep the state boundary and camera rig editable. Choose appropriate local geographic data and detail for a statewide overview. Inspect the preview and verify the saved scene. No animation yet.

### Detailed close-up

> Use this workflow to create a detailed map of the Cape Fear River around Wilmington, North Carolina. Plan the data extent and terrain sampling for a close view of the city and river, and use sourced river geometry. Keep the river, terrain, labels, and camera editable. Render the closest intended view as well as an overview, inspect both, and return the source attribution and verified scene. No animation yet.

If using a skill-only download, replace the entrypoint path in these examples with `SKILL.md`. A Codex installation can also invoke `$blender-map-workflow`. Another LLM can simply read the Markdown and run the supplied scripts.

## How a state map is created

1. **Define the region.** The LLM copies the state preset into the project, sets the state name and Census identifier, and includes neighboring areas if requested. For a close-up, it adds a geographic clipping extent. The original preset remains available for reuse.
2. **Choose coordinates and sampling.** It selects a projected coordinate system measured in metres for the region. It chooses terrain-mesh and elevation-texture sampling for the closest intended shot, then sets a suitable scene scale and relief exaggeration.
3. **Prepare real data.** The scripts obtain the state boundary and elevation, reuse matching checked downloads, align the datasets, and check missing elevation coverage. Source files, acquisition dates, and hashes are retained.
4. **Build the editable scene.** Blender creates the terrain, separate boundaries, relief material, ocean/background, and one camera rig. Requested city labels are configured by the LLM. Sourced river or lake GeoJSON can be imported as independent objects.
5. **Compose and inspect.** The LLM adjusts the camera for the state's shape and reviews the rendered image for framing, recognizable geography, border alignment, and readable labels. Another state's framing is not automatically inherited correctly from the North Carolina example.
6. **Reopen and verify.** The workflow checks the saved scene's geometry, packed textures, controls, and framing. The LLM can render from a relocated copy to check that the scene opens without the original asset folder.

The state request therefore produces a map prepared at state scale. It does not rely on the national overview already containing enough detail for every state or city shot.

### What changes for a close-up

Camera movement changes the view of the geometry already loaded. The current workflow does not stream finer terrain or automatically switch detail levels when you zoom.

If a closer view needs more detail, the LLM narrows the region and rebuilds its elevation grid, terrain, and overlays with appropriate sampling. A wider view and a detailed view can be saved as separate outputs. A smooth animated transition between multiple terrain resolutions requires additional work; the current workflow does not create it automatically.

Ask for the closest intended shot early. Increasing export pixel counts cannot create geographic detail absent from the source dataset. The LLM should report both the downloaded elevation sampling and the displayed mesh spacing, and inspect the map at the closest view before calling it finished.

### What is included and what must be supplied

State boundaries and real elevation are acquired by the bundled scripts. Cities, named rivers, lakes, counties, land cover, and wetlands are additional features to request explicitly. The LLM must locate or prepare their appropriate sources and configuration; the scripts do not automatically download every such layer. River and lake import is already supported for attributed local GeoJSON. Land-cover and wetland styling requires additional preparation.

## 4. Review the preview before refining

Check that the requested area is visible, familiar features appear in the right places, text is readable, and the relief looks appropriate. Check both an overview and the nearest planned camera view when the request includes a close-up.

Useful follow-up instructions include:

- “Keep the geographic data, but lower the vertical exaggeration and use warmer colors.”
- “Move the label so it stays readable above the mountains.”
- “Show neighboring states for context.”
- “The river close-up needs finer terrain; rebuild that region at a more suitable sampling.”
- “Keep this overview and save the close-up as a separate output.”

Ask the LLM to preserve the existing scene and make changes reproducible through the configuration where practical. Animation can be requested after the static views and geographic layers are satisfactory.

## 5. Find and reopen the results

The LLM should return the actual output folder and links to the scene, preview, and verification report. A standard output contains:

| File or folder | What you use it for |
|---|---|
| `NAME.blend` | Open the editable scene in Blender |
| `renders/overview.png` | Review the initial camera composition |
| `renders/verified.png` | Review a render made after reopening, when requested |
| `config.json` | Keep the effective settings for this map |
| `project.json` | Review data sources, dates, projection, and sampling |
| `assets/` | Retain source elevation, boundaries, and optional imported vectors for rebuilding |
| `build-report.json` | Check scene size, geometry counts, and measured render time |
| `verification-report.json` | Check which saved-scene validations passed |

An additional close-up image is a deliverable the LLM should produce for that request; the default script renders one overview. A successful save alone does not mean the image has been visually reviewed.

Inside Blender, select `CAMERA_RIG` to adjust orbit, tilt, distance, and focal length. Move the rig to pan. Select a `MAP / ...` root to adjust vertical exaggeration. For reproducible rebuilding, keep the entire output folder and checked source cache. The packed `.blend` can be shared for viewing without the external textures; the raw source assets are still needed for reprocessing.

## What performance to expect

The reference United States overview has 299,111 terrain vertices and rendered in about 2.2 seconds on the tested Mac. A reduced-detail North Carolina importer test had 44,416 vertices and rendered in about 1.8 seconds. These are examples, not guaranteed timings or a controlled comparison.

State and close-up builds put detail into a smaller geographic area. Their cost depends on requested sampling, terrain shape, geographic overlays, image dimensions, and hardware. The workflow records the actual measurements for your run. See the [test report](../../docs/test-report.md) in the full source distribution for the tested scope; it is not included in the standalone skill archive.

For technical details, continue to the [execution guide](workflow.md), [configuration guide](configuration.md), or [troubleshooting guide](troubleshooting.md).


## Reproduce the finished detailed NC map

Use [the detailed-map guide](detailed-map.md) and the `north-carolina-detailed.json` preset for the stored V2 shot, or `north-carolina-detailed-overview.json` for a wide state view. This preserves land cover, wetlands, rivers, counties, printed river/state-border ink, coast tapering, terrain-depth controls, ocean texture/waves and the shared camera aim/DOF null. The general `north-carolina.json` preset is the lighter elevation builder. The detailed NC template is packed and works offline; another state still needs its own data preparation. Existing camera and target keyframes are retained.
