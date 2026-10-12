# Blender Map Workflow

A portable Made With Robots skill and reproducible GIS-to-Blender pipeline for another LLM to create editable relief maps. No standalone application, custom GUI, or required Blender add-on.

## Start here when opening this folder

Read the [first-use guide](blender-map-workflow/references/user-guide.md). It explains what to request, what the LLM will do, how state maps and close-ups get their detail, and where to find the results.

1. Open this folder as your LLM's working project.
2. Have Blender and Python installed, and give the LLM access to the project files and a way to run Blender. The guide covers setup.
3. Paste the request below, replacing the region and features with what you want.
4. Review the preview before requesting closer views or animation.

> Read `blender-map-workflow/SKILL.md` and its `references/user-guide.md`. Create an editable relief map of North Carolina in a new output folder. Choose data and detail appropriate for a statewide overview, preserve the state boundary as a separate object, and include one camera rig. Set up any missing project dependencies, inspect the preview, reopen and verify the scene, and return links to the map and reports. No animation yet.

For another state, change the name; the LLM will need to adapt the state preset. For a city or river close-up, name the exact area and closest intended view. The workflow rebuilds suitable regional terrain when needed; moving the camera alone does not load additional detail.

![United States reference relief map](docs/united-states-preview.png)

Start with [the skill](blender-map-workflow/SKILL.md). A generic LLM can read it directly; Codex users can copy the `blender-map-workflow/` folder into their configured skills directory. The scripts and references travel with the skill.

## Quick start

Install a stable Blender release >= 4.5 and Python >= 3.11. From this directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r blender-map-workflow/requirements.txt
.venv/bin/python blender-map-workflow/scripts/map.py doctor
.venv/bin/python blender-map-workflow/scripts/map.py run \
  --config blender-map-workflow/presets/united-states.json \
  --output outputs/us-test --cache cache --render
```

On Windows use `.venv\Scripts\python.exe`. Pass `--blender` for an explicit executable or set `BLENDER_BIN`. See [execution and Blender MCP guide](blender-map-workflow/references/workflow.md) for setup, separate stages, offline builds, relocation testing, and live Blender controls.

## Ask an LLM

> Read `blender-map-workflow/SKILL.md` and use its workflow to build a United States relief map in a new output folder. Use real elevation and boundaries, retain editable terrain and geographic layers, and set up one camera rig. Inspect the rendered image, reopen the saved file, verify portability, and return the scene, preview, and measured results. No animation yet.

The U.S. preset contains the contiguous states, Alaska, and Hawaii's main islands, plus D.C. Insets use separate projections and scales. Colors are stylized elevation colors; relief is exaggerated. The North Carolina preset is a simpler state-scale starting point; additional documentary layers require their own preparation.

## Adapt a map

Follow the [state and close-up process](blender-map-workflow/references/user-guide.md#how-a-state-map-is-created). The LLM copies a preset to your project and changes the region, projection, palette, detail, and camera. [Configuration guide](blender-map-workflow/references/configuration.md) explains resolution, NoData, insets, river/lake GeoJSON, and optional detail extensions. [Troubleshooting](blender-map-workflow/references/troubleshooting.md) covers bounded recovery.

The bundled downloader supports U.S. Census boundaries and USGS 3DEP elevation. Other countries need an authoritative data adapter; the scene construction principles remain portable. Network acquisition needs internet access; complete checked caches allow offline repeats.

## Data sources and credits

The national example and bundled presets use openly available government geographic data. The workflow downloads elevation and boundaries directly from the providers; the displayed colors, lighting, and exaggerated relief are this workflow's visual treatment.

| Data | Provider and citation | Used for |
|---|---|---|
| Bare-earth elevation | U.S. Geological Survey, **3D Elevation Program (3DEP)**, [3DEPElevation ImageServer](https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer), accessed October 12, 2026 | Real terrain elevations and relief textures in the U.S. example and state presets |
| State boundaries | U.S. Census Bureau, **2024 Cartographic Boundary Files**, `cb_2024_us_state_500k.zip`, [program documentation](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html) and [exact source download](https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_state_500k.zip), accessed October 12, 2026 | State outlines, land masks, and Alaska/Hawaii inset geography |

USGS describes its agency-produced data as being in the U.S. public domain and requests source acknowledgment; see its [copyright and credit guidance](https://www.usgs.gov/faqs/are-usgs-reportspublications-copyrighted) and [data-licensing guidance](https://www.usgs.gov/data-management/data-licensing). Census citation details follow its [geographic-product citation guidance](https://www.census.gov/about/policies/citation.html). Keep any dataset-specific notices when adding other sources; public availability alone does not determine their reuse terms.

Suggested credit for the example image: **Elevation: U.S. Geological Survey, 3DEP. State boundaries: U.S. Census Bureau, 2024 Cartographic Boundary Files. Map styling: Made With Robots.** The agencies supply geographic data; this visualization does not imply their endorsement.

The separate regional importer test used selected [USGS NHD flowlines](https://www.usgs.gov/3d-hydrography-program/access-3dhp-data-products) and an [NC OneMap major-hydrography polygon](https://services.nconemap.gov/secure/rest/services/NC1Map_Hydrography/FeatureServer/2), originally acquired October 10, 2026. These optional test inputs are excluded from the public source package. Additional land-cover and wetland layers are documented extensions, not inputs to the national example. Per-map `project.json` records source URLs, acquisition dates, and SHA256 hashes.

## Review and test artifacts

- [Workflow review and improvements](docs/workflow-review.md)
- [Reference test report](docs/test-report.md)
- [Reference preview image](docs/united-states-preview.png)
- Reference scene: built locally by the workflow, not included in this repository

Runtime output, source cache, and virtual environments are excluded from version control. The skill package contains no personal installation paths, source project files, or machine-specific dependencies. Only Blender 5.2.2 LTS/macOS Metal is tested end to end; other supported environments should run their own saved-file and visual checks.

To run the focused tests after setup: `.venv/bin/python -m unittest discover -s tests -v`.

## What is not in this repository

The skill, instructions, code, tests, source credits, and preview are all here. Local Python environments, source caches, rendered scenes, logs, backups, compiled Python files, and the original reference project's assets are excluded, and `.gitignore` also covers common credential-file types. See the [privacy review](docs/privacy-review.md) for the scan scope and results.

## License

Released under the [MIT License](LICENSE). The workflow's code, instructions, and styling are Made With Robots' own work; the underlying elevation and boundary data stays with its providers' terms, described in [Data sources and credits](#data-sources-and-credits).
