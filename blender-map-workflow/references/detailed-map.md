# Detailed North Carolina / Cape Fear V2

Use this mode for the finished NC treatment. It includes **printed rivers and state
borders**, coast tapering, terrain-depth controls, land cover, wetlands, counties,
ocean waves and the shared camera aim/DOF target. The ordinary state preset is a
lighter elevation overview and does not reproduce these documentary layers.

## First run

Install stable Blender >= 5.2 (tested with 5.2.2 LTS) and Python 3.11+. Detailed mode
needs no GIS environment or internet connection. From the repository root:

```sh
python3 blender-map-workflow/scripts/map.py run \
  --config blender-map-workflow/presets/north-carolina-detailed.json \
  --output outputs/nc-detailed --render
```

Pass `--blender` or set `BLENDER_BIN` if needed. The workflow joins the three checked
binary parts into a cached template, verifies the complete SHA256, creates a new
editable scene and preview, reopens it, checks the data/material connections/controls,
and renders again with `--render`. Keep **all three** `.blend.partNN` files and the
manifest together. No Git LFS service or runtime download is required. The assembled
scene is about 119 MiB; each repository part is at most 40 MiB.

| Preset | Shot |
|---|---|
| `north-carolina-detailed.json` | Stored V2 shot, frame 38, original rig, 60 mm, DOF enabled at f/0.75 |
| `north-carolina-detailed-overview.json` | Frame 1, wider Distance 65, DOF off for sharp overview type |
| `north-carolina-detailed-cape-fear.json` | Frame 238, Cape Fear close-up using the retained camera/target actions |

Presets retain existing camera and target keyframes; they do not create new animation.
Outputs include the `.blend`, `renders/overview.png`, `renders/verified.png` with
`--render`, `project.json`, build and verification reports. “overview.png” is a
standard output filename, not a guarantee of wide framing. Existing saved outputs
are protected; `--overwrite` first backs up the whole output folder.

Example request:

> Read SKILL.md and references/detailed-map.md. Reproduce the detailed North Carolina
> V2 map in a new output folder. Keep the printed river and border treatment, tapered
> coast, terrain-depth controls, land cover, wetlands, counties, ocean and camera
> aim/DOF target. Inspect the preview, reopen and verify the scene, and return links
> to the scene and reports. Do not enable the archived raised curves.

## Controls

| Select | Change | Result |
|---|---|---|
| `CAMERA_RIG` | Location; Orbit, Tilt, Distance, Focal length properties | Pan, orbit, tilt, dolly and optical zoom |
| `Camera Target \| Aim and Focus` | Location | Aim and DOF focus move together |
| Camera data | DOF enabled; f-stop | Toggle blur and adjust focus depth |
| `MAP_DETAIL_CONTROLS` | Land cover amount, Wetland amount, Lowland relief boost | Classification colors, wetland tint and normal shading |
| `TERRAIN_DEPTH_CONTROLS` | Modifiers → Terrain Depth Controls | Shared elevation refinement, local relief and stylized channel depth |
| `Atlantic_Ocean_Surface` | Ripple strength, Color variation, Water roughness, Drift speed | Procedural shading and wave phase |
| `RELIEF_CONTROL_scale_Z` | Z scale | Overall terrain and attached geographic overlays |

Copy a preset before changing it. An empty `rig` object preserves the stored rig.
`target_location` accepts three numbers in the target's **parent coordinates**, or
null to preserve its animation. Setting an explicit location clears that target's
existing action in the new output. For other animation or geometry-node edits, work
on a saved output and preserve a distinct version; do not edit the distributed
reference input for an individual shot.

## The line and coast fixes

The rivers and state boundaries are baked **map-ink masks in terrain materials**.
They follow the terrain surface without round bevels or hovering cylinders. The
original geographic curves remain editable in hidden `Archive | raised ...`
collections. Editing those curves does not automatically regenerate the ink masks;
re-rasterize the relevant masks to update the visible geography. Do not re-enable
those archives as a shortcut. County curves remain separate, as in V2.

Packed coast-distance masks taper the terrain into the ocean and remove the raised
ivory shoreline. Shared geometry-node controls retain V2's height/refinement,
local-relief and channel treatment, including its subdivision modifiers. Channel
depth is stylized, not observed bathymetry. Nested grids also retain their baked
smoothstep transitions. The ocean is one quad with procedural bump waves and
frame-rate-aware drift, without a simulation or geometry displacement.

## Data and typography

There are three base terrain meshes with 1,851,872 vertices before modifiers,
100 county curves, 315 water-body objects, editable labels and lighting. Eighteen
packed images include the original normals/classification masks, four ink masks,
three coast masks and six height/relief fields. Optional watershed and county labels
remain hidden. The terrain's effective evaluated density is higher where subdivision
is enabled; the base count is not a final render triangle count.

NLCD is the pinned **2025** product, natively 30 m, styled here at about **252
projected metres per display texel**. V2's year property reads 2009, but its two
classification/mask textures are byte-identical to the pinned 2025/NWI inputs.
That property does not load historical data. Keep the source credits accurate.
NWI tint covers selected vegetation-wetland categories; water-body fills are
cartographic surfaces, not surveyed levels. EPSG:3857 distances are projected,
not uniform ground distances. See `templates/sources.json` for extents, requests,
acquisition dates and processing notes.

V2's white, flat typography is preserved with **Golos Text Medium**, packed under
SIL OFL 1.1. The artist reference used DIN Alternate Bold, whose font file is marked
for preview/print embedding. The public editable template deliberately substitutes
the open font. Label text remains editable; font shapes/metrics differ from DIN.
The complete Golos license is supplied beside the parts and inside the scene.

## Relocation check

Copy only the generated `.blend` and `project.json` into another folder, then:

```sh
python3 blender-map-workflow/scripts/map.py verify \
  --output outputs/relocated-nc --render
```

Verification does not require template parts, source caches, original images or
installed fonts. Opening/rendering the packed output itself needs only Blender.
Inspect the actual image as well as the checks; a valid hash does not certify framing,
coastal coverage, focus, readability or every animation frame.

## Rebuilding similar detail for another state

This release is a **pinned NC V2 processed-data snapshot**, not a nationwide
one-command NLCD/NWI/county downloader. Renaming its preset does not change geography.
For another region, start with the general state builder, then prepare its own
additional authoritative layers. The following is the V2 recipe; not every step is
implemented by the general `prepare.py`:

1. Choose the region, closest shot, projection, origin and units. Prepare USGS DEMs
   and Census state geometry. Align nested grid edges, blend parent/child heights,
   and preserve finer source-derived normal textures separately from base geometry.
2. Acquire counties and hydrography, paginate completely, validate counts/CRS and
   preserve source attributes. Use polygon water bodies with holes retained and
   attributed centerlines for river classes. Widths are cartographic symbols.
3. Rasterize state boundaries and river classes into aligned ink masks. In the NC
   snapshot, one shared state mask and three terrain-specific river masks feed the
   terrain materials. Use projected XY mapping to keep the ink registered across
   nested tiles. Archive the source curves for edits, with rendering disabled.
4. Obtain the chosen Annual NLCD year as categorical data. If decoding the official
   indexed WMS, use its official palette and reject unknown colors; retain class
   masks before styling. Rasterize selected NWI vegetation wetlands onto the same
   extent. Do not infer classes from interpolated styled colors or a year label.
5. Create height and local-relief fields from valid DEM samples. The NC reference
   subtracts an approximately 2 km neighborhood mean for relief residuals and fades
   them at tile edges. Pack these fields and link shared geometry-node controls.
   Derive coastal distance/taper masks from geographic land masks, test thin islands
   and small coastal fragments, and avoid inventing mountains or bathymetry.
6. Blend land cover/wetlands through independent controls, keeping lowland shading
   and outside-state context consistent. Add one rigged perspective camera, a shared
   aim/focus target, restrained labels, independent ocean shading and source credits.
   Review wide and close shots for seams, ink alignment, shoreline artifacts and DOF.
7. Export a reviewed scene through `export_template.py` in a separate background
   process. Use repeated `--redact-term` arguments for private project names and
   `--font` when a public font substitution is needed. Supply matching licenses.
   Review visible fields, packed-file paths, stale string buffers and image metadata.
   Then split a large template with `template_assets.py split`, keep the complete
   manifest and source credits, and adapt verification expectations for that region.

Update code/presets, the scene parts, source manifest and previews together. Run from
a fresh public folder, reopen the output and test relocation without the production
archive. Keep runtime scenes, caches, environments and diagnostic logs out of Git.
