# Apply the corrected NC V2 workflow update

The package reproduces the corrected V2 reference: printed river/state-border ink,
coastal taper, terrain-depth nodes, detailed geography and the retained camera/ocean
controls. These steps also apply when transferring the reviewed ZIP into another
checkout.

1. Extract the update ZIP and review the README, skill and detailed-map guide.
   Keep all three `north-carolina-detailed.blend.partNN` files, the manifest,
   `sources.json` and Golos font license. The parts assemble to about 119 MiB;
   each part is under 40 MiB and can be stored in ordinary Git.
2. Create an update branch in your repository checkout. Copy `README.md`,
   `.gitignore`, `blender-map-workflow/`, `docs/` and `tests/` from the package,
   preserving unrelated work. Remove any older distributable
   `templates/north-carolina-detailed.blend`; the runner now uses checked parts.
   Do not copy local Git configuration, outputs, caches, environments or logs.
3. Review the diff and run the focused tests and detailed README command.
   Inspect the default V2 shot, overview and Cape Fear presets. The integrity
   test checks all parts and their assembled hash against the manifest.
4. Run the team's privacy review on the complete content, including an assembled
   scene. This release's checks are documented in `privacy-review.md`.
5. Commit and push through the team's normal process. Clone the published repo
   into a fresh folder and run the detailed preset to confirm the new asset parts
   are present and the corrected ink treatment appears.

The default preset preserves frame 38, 60 mm and f/0.75. The overview uses frame 1,
Distance 65 and DOF off; the Cape Fear preset uses frame 238. All preserve camera
and target actions. The first run assembles a checked scene into the local cache.
Generated scenes pack their own assets and can be relocated without that cache.
No production folder is needed. Another state's full detail still requires the
regional preparation recipe. The public scene replaces DIN with openly licensed
Golos Text Medium; editable label metrics therefore differ from the reference.
