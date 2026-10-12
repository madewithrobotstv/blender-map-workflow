# Refining the map workflow

Reviewed the current Cape Fear project's README, camera rig construction, stable-version finalization, render reports, and archived terrain preparation/EEVEE optimization scripts. The original scene and assets were left untouched.

## What is worth retaining

Real elevation and authoritative boundaries produce recognizable geographic relief. Independently editable hydrography, borders, and labels keep the scene useful for documentary work. An ordinary driver-based camera rig supports pans, orbit, tilt, dolly, and lens changes without a persistent add-on. Packed textures/fonts make the finished scene convenient to open.

The archived optimization report documents terrain reduction from 8,345,780 to 1,851,872 vertices, with fine relief retained in normal textures. Its same-engine overview measurement improved from 9.35 to 6.76 seconds. This is evidence for separating geometry density from shading detail, not a performance prediction for another scene.

The current stability report records clean 5.2.2 LTS tests after intermittent final-render artifacts in 5.3 alpha. It does not establish a universal EEVEE geometry bug, and production animation remained untested. The revised workflow records the runtime version and prefers stable releases instead of making hardware or renderer claims from one test.

## Changes implemented here

| Previous friction | Refined approach | Why it matters |
|---|---|---|
| Absolute personal project paths | Skill-relative resources and explicit project/output/cache paths | Another LLM can use the package on another machine |
| Building from archived `.blend` scenes | Fresh deterministic scene construction from source assets | No hidden historical scene dependency |
| Separate experimental scripts/stale brief status | One staged entry point plus effective config and per-run reports | Clear source of truth and inspectable results |
| Web Mercator regional grid reused broadly | Appropriate projected metre CRS per region; separate inset projections | Better national composition and consistent distances within each panel |
| Very dense nested terrain | Overview-sized display mesh plus finer packed normal maps | Lower memory/file size while preserving visible relief |
| Raster extent used as sampled vertex endpoints | Explicit GeoTIFF pixel-center coordinates | Avoids half-pixel alignment shifts |
| Overlays sampled independently from visible mesh | Shared triangle interpolation and densified overlay segments | Reduces sinking/hovering after mesh simplification |
| NoData converted to zero in historical preparation | Mask missing terrain; fail if land coverage exceeds threshold | Avoids presenting fabricated flat terrain as measured data |
| Download scripts with hard-coded dates/unverified files | UTC acquisition timestamps, URL-keyed cache, atomic writes, SHA256 checks | Exact sources are traceable and partial downloads are rejected |
| Source-dependent external texture paths | Local sources plus packed textures and embedded provenance | Scene opens after relocation without original folders |
| Machine-specific EEVEE/Metal tuning | Defensive EEVEE settings and Blender discovery; measured backend reported | Avoids falsely promising one hardware path everywhere |
| Labels sampled only at a point | Local terrain-height check over billboard footprint | Prevents glyphs disappearing into nearby mountains |
| Save followed by informal visual review | Fresh-process checks for packed assets, drivers, counts, finite terrain, framing, plus image inspection | Save success and geographic/visual quality are verified separately |

## Scope and next extensions

The original release reference was a general national relief map. The detailed NC update now includes a packed template with NLCD land cover, NWI wetlands, counties, named rivers and the tuned ocean material; see [the update report](nc-update-test-report.md). The general downloader still does not automatically acquire these additional layers for every state. The portable importer supports attributed river lines and lake polygons; those data can be supplied as GeoJSON.

For matching the full Cape Fear aesthetic, add a separate preparation stage for aligned categorical land-cover/wetland masks and retain separate blend controls. For close river shots, acquire a regional DEM and local vectors rather than increasing the national scene's geometry everywhere. For a later multi-resolution terrain extension, align child edges, blend height transitions, and test the actual close camera; the current skill deliberately uses independent panels rather than untested nested seams.

The U.S. overview and Cape Fear scene differ in geography, resolution, camera, and overlays. Their file sizes, vertex counts, and render times are not comparable as a controlled benchmark.


The corrected V2 update preserves printed terrain ink for rivers and state borders,
coastal taper, shared terrain-depth nodes and 18 packed images. General maps use
editable flat ribbons. Checked binary parts avoid a large single Git asset; each
part and the assembled scene are hashed. See the latest NC test report.
