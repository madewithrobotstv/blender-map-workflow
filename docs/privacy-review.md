# Public-package privacy review — October 12, 2026

The release is prepared for an independent Made With Robots review. No GitHub upload was performed.

## Scope

Reviewed the public Python scripts, tests, JSON presets, skill metadata, Markdown documentation, preview-image metadata, and release-archive contents. Also inspected local runtime categories to identify material that must stay outside the upload. This is a targeted privacy and secret-pattern review, not a guarantee against every possible disclosure.

## Findings and preparation

| Area | Result |
|---|---|
| Public code, presets, and documentation | No detected personal usernames, home-directory paths, email addresses, private keys, access-token patterns, or credential assignments after preparation |
| Previous production context | Private project-name references removed from public documentation; general geographic examples and workflow findings retained |
| Preview image | Renderer text, timestamps, and EXIF metadata removed; compressed pixel data preserved exactly |
| Public data URLs | Official public USGS, Census, and NC OneMap references; no detected embedded account credentials or signed authentication tokens |
| Local Python environment | Contains machine-specific installation paths; excluded from both archives and the clean export |
| Local output/log/backup files | Include personal filesystem paths in diagnostics; excluded from public packages and retained locally for ongoing work |
| Source caches | Excluded from public packages; the presets obtain public source data directly |
| Compiled Python files | Can embed local source paths; excluded from public packages |
| Git history/configuration | None included in the release; posting-account commit attribution is outside this file scan |
| Archive structure | Explicit public-file export; no environments, caches, output scenes, logs, backups, credential files, or hidden local configuration included |

## Files to give the reviewing team

Use `dist/github-upload/` or the extracted `dist/blender-map-workflow-source.zip`. Both include `README.md`, `.gitignore`, the `blender-map-workflow/` skill folder, `docs/`, and `tests/`. The skill-only ZIP contains just the skill folder and its executable resources.

The source preview is the only published media asset. Original reference-project files, regional test inputs, and generated Blender scenes are excluded. Preserve dataset credits in the README and the image's visible attribution.

If adding new data, logs, media, configuration, or generated scenes before publishing, include those additions in the team's scan. Runtime logs and compiled files may contain personal paths even when the reusable scripts use portable paths.
