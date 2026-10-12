# Corrected NC V2 update test report — October 12, 2026

The initial public state preset did not reproduce the finished map. This update
uses the corrected V2 reference, including printed river/state-border ink,
coastal taper, terrain-depth nodes and retained camera/ocean controls.

## Tested environment and preservation

Blender 5.2.2 LTS, EEVEE, macOS/Metal. Detailed runs use ordinary Python without
GIS packages or network requests. General regressions reused checked terrain
assets rather than repeating downloads. Other platforms remain unverified.

- Three nested terrain meshes, **1,851,872 base vertices**, retain source mesh
  coordinates/topology. Source subdivisions and depth geometry nodes are retained.
- All **18 packed images** and material connections match the V2 snapshot.
  Four ink masks replace visible raised river/state-border curves, whose archives
  remain hidden; three coast masks and six height/relief fields are retained.
- 100 county boundaries, 315 water bodies, river geography, labels, lighting,
  compositor, land cover/wetlands and feathered terrain transitions remain present.
- Default frame **38**, **60 mm**, DOF **f/0.75**. Wide preset: frame 1,
  Distance 65, DOF off. Cape Fear preset: frame 238. Camera/target actions retained.
- Moving the shared aim/focus null correctly aims the camera. Ocean drift timing
  follows frame rate. Drivers are valid. Full animation was not exhaustively tested.
- Public typography substitutes OFL **Golos Text Medium** for DIN Alternate Bold.
  Text remains editable and white, with different font metrics. Source geometry,
  images, camera pose and material connections survive that substitution.
- Template: **124,738,506 bytes**, split into three checked parts. SHA256:
  `31f25f0d68a8aceb6653636bbfed4b46d79dcba15c2d26d7d6bed178a2d4c26f`.

## Results

| Test | Result | Reopened still render |
|---|---|---|
| V2 stored shot, 2560 × 1440 | All 21 checks passed | 9.75 s |
| V2 wide view, 2560 × 1440 | All 21 checks passed | 8.57 s |
| V2 Cape Fear, 2560 × 1440 | All 21 checks passed | 8.59 s |
| Relocated V2 scene + project.json only | All 21 checks passed | 10.00 s |
| General NC regression | All 24 checks passed, including flat geographic strokes | 5.33 s |
| General U.S., 51 state/DC boundaries, 3 panels | All 24 checks passed | 2.72 s |
| Focused automated tests | Six passed, including complete part integrity, corrupt-part rejection and unsupported region fields | — |
| Skill validation | Passed | — |

Initial V2 stored-shot rendering took 9.82 s. Timing reflects one host and some
concurrent regression activity; it is not an animation throughput promise.
Visual review covered the stored, wide and Cape Fear shots. The tight shot retains
source framing and shallow focus, including cropped peripheral labels. Public
font substitution can alter label spacing; review typography before final delivery.
The relocated scene needed no external images, fonts, template parts or cache.

## Privacy and data limits

Both field and uncompressed stored-content audits passed after removing notes,
private names and stale asset paths, including packed-file records. Preview
metadata was stripped; font licenses supplied. See [privacy-review.md](privacy-review.md).

This is a processed NC snapshot, not an automatic nationwide documentary-layer
builder. Native NLCD is 30 m; its styled packed display is about 252 projected
metres per texel. The source's numeric year label is 2009, but its packed data
matches NLCD 2025. Changing the label does not load historical data. New regions
or closer views may require new DEM and categorical/hydrography processing.
