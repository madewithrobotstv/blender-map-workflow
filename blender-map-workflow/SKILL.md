---
name: blender-map-workflow
description: Build geographically aligned, stylized relief maps in Blender from real elevation and boundary data. Use for editable terrain maps, regional or U.S. map scenes, map camera rigs, and reproducible GIS-to-Blender workflows; includes portable scripts, general U.S./state presets, and a checked detailed North Carolina/Cape Fear V2 template with land cover, wetlands, hydrography, counties, procedural ocean and an aim/DOF null.
---

# Blender Map Workflow

Produce an editable `.blend`, a reviewed preview, source data, and a provenance report. Use the scripts for repeatable geometry and alignment; use judgment for framing, labels, visual emphasis, and shot-specific detail. No GUI or custom add-on is needed.

## Start

For first-use questions, request examples, or deciding between an overview and a close-up, read [user-guide.md](references/user-guide.md). It describes the user-facing process and the state-map rebuild procedure.

1. Establish the region, intended shot, output directory, and any highlighted features from the user's request. Default to a warm stylized relief map and one animatable perspective camera. The U.S. preset includes 50 states plus D.C., Alaska in its own projection, and Hawaii's main islands in an explicitly labeled inset.
2. Resolve this skill's directory from the location of `SKILL.md`. Use that path to find `scripts/`, `presets/`, and `requirements.txt`; never assume a particular working directory, username, archive, or installation path.
3. Read [workflow.md](references/workflow.md) for setup, execution, and Blender MCP operation. Run `scripts/map.py doctor` with the external GIS Python environment. A stable Blender release >= 4.5 is required; only 5.2.2 LTS/macOS Metal has been end-to-end tested here.
4. Copy the relevant JSON preset into the user's project and adapt it. Read [configuration.md](references/configuration.md) when changing geography, projection, detail, styling, or importing rivers/lakes. For regions outside the U.S., replace the providers with local authoritative DEM and vector data; the bundled downloader specifically supports USGS/Census U.S. maps.

## Choose the correct mode

For the finished detailed NC/Cape Fear treatment, read [detailed-map.md](references/detailed-map.md) and use `presets/north-carolina-detailed.json` (stored V2 shot), `north-carolina-detailed-overview.json` (wide shot), or `north-carolina-detailed-cape-fear.json` (close-up). This mode reassembles a checked packed template from binary parts, needs stable Blender >= 5.2, and runs offline with ordinary Python. It preserves existing keyframes; it does not add new animation. Do not substitute the lighter state preset when the user requests the finished NC map. Render and verify through the same `map.py run` entry point. Return the scope honestly: this is a fixed NC data snapshot; another state requires new geographic layers, not just a renamed preset.

Keep V2 rivers/borders as printed terrain ink and their raised curve archives hidden. Preserve coast tapering and shared terrain-depth controls. The public copy uses an OFL font; disclose its difference from the artist reference. Data provenance pins NLCD 2025 even though the source year property reads 2009.

For U.S. overviews and newly prepared state geography, follow the general build below. The general builder includes a shared aim/focus null and procedural ocean; DOF is optional and defaults off for readable overview typography. Detailed land cover/wetlands/counties are not automatically acquired by the general downloader.

## Build and review

Run `scripts/map.py run --config CONFIG --output OUTPUT --cache CACHE`. Set `BLENDER_BIN` or pass `--blender` when discovery finds the wrong installation. This prepares source data, builds in a fresh background Blender process, and reopens the saved scene for verification. `--render` also renders after reopening. Do not treat a successful save as proof of a correct map.

- Keep elevation and vectors in the same projected metre CRS within each panel. Pixel centers define the mesh grid; raster edges define the source extent. Center projected coordinates before converting to Blender units.
- Use real elevations. Report source/export spacing separately from display mesh spacing. NoData remains excluded; do not replace missing land with invented mountains or silently flatten it. A failing coverage check requires another valid source or an explicitly disclosed scope change.
- Match mesh density to the closest intended shot, retaining finer DEM relief in packed normal textures. The U.S. overview is not suitable for close river/city shots without rebuilding regional data.
- Drape overlays against the display mesh's actual triangle interpolation. Borders, rivers, waterbodies, labels, ocean, and rig controls remain independent scene elements. Do not use unrelated scene files as hidden build inputs.
- Preserve existing work. The builder runs only in a fresh background process. A saved output is protected unless `--overwrite` is provided, which first backs up the entire output. Save any live artist scene before opening a generated map.
- Use shader node inputs for colors. Identify existing nodes by their type, and inspect API properties before applying version-dependent settings. Avoid loading project-specific add-ons or machine-specific GPU assumptions into the scene.

Inspect `renders/overview.png` with an image tool and read `build-report.json` and `verification-report.json`. Check recognizable geography, coasts and lakes, elevation seams, boundary alignment, glyph occlusion, inset labeling, and camera margins. Adjust the configuration or narrow script behavior based on observed issues, then rerun in a new output directory. Geographic checks alone do not certify visual quality.

For portability validation, copy the `.blend` and `project.json` to a different directory without `assets/`, then run `scripts/map.py verify --output COPIED_OUTPUT --render`. Packed images and packed or built-in fonts should allow the scene to render without original asset paths. Keep the full source assets with the normal deliverable for reproducibility.

## Refine in Blender

Use Blender MCP when available, or equivalent Blender Python/UI tools. First inspect the connected Blender version and scene. Open the generated project only after preserving current work. Tune `CAMERA_RIG` custom properties for orbit, tilt, distance, and focal length; move the rig to pan. Move `Camera Target | Aim and Focus` to change aim and focus together; enable camera DOF and set aperture for focus blur. Tune the ocean custom properties for ripples, color variation, roughness and drift. Tune each `MAP / ...` root's `Vertical exaggeration` property to move terrain and draped overlays together. Use ordinary Blender keyframes only when animation is requested.

Prefer configuration changes for reproducible edits. For artistic edits made directly in Blender, save a distinct scene version and describe the differences so they can later be transferred into the build configuration. The skill scripts need no Blender MCP connection; the rendered scene needs neither GIS packages nor an add-on.

## Deliver

Return links to the `.blend`, the actual preview, and the output folder. State region/inset scope, data attribution, exaggeration, measured performance, and any untested platform or version. Include failed checks honestly; do not describe the scene as verified when required checks remain false. Read [troubleshooting.md](references/troubleshooting.md) when downloads, rendering, or verification fail. The original workflow review is in the repository's `docs/workflow-review.md` for design context; it is not needed to run the skill.
