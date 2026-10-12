# Public-package privacy review — October 12, 2026

Prepared for the Made With Robots team's review of the corrected V2 release.

## Scope and results

Reviewed public scripts, tests, presets, documentation, image metadata and explicit
release contents. The corrected V2 packed template was inspected through Blender
fields and an uncompressed copy of its stored content. This is a targeted review,
not a universal secret scanner or an audit of GitHub account/history.

| Area | Preparation and result |
|---|---|
| Public text/code/configuration | No detected personal home paths, production identifiers, personal email addresses, private keys or access-token patterns |
| Old project notes | Replaced free-form Blender texts and string custom properties with public instructions and source credits |
| Packed assets | 18 images and one openly licensed font remain packed; no linked libraries or unpacked required assets |
| Packed filenames | Sanitized image paths and each packed-file record; nine obsolete production texture paths caught by the deeper V2 audit were removed |
| Stored Blender strings | Cleared stale fixed-buffer paths and legacy names/action slots; uncompressed inspection found no tested private-source remnants |
| Packed PNG metadata | Eleven images have no text/EXIF chunks; four ink and three normal images contain only 72-dpi X/Y resolution EXIF tags |
| Preview PNGs | Text, time and EXIF chunks stripped while retaining compressed pixel data |
| Font attribution | Golos OFL copyright/license supplied and embedded; production DIN font removed from the public copy |
| Public source requests | Government URLs, acquisition dates and geographic extents preserved; no detected credentials or tokens |
| Release contents | No environments, caches, output scenes, diagnostics, backups, compiled Python or Git internals |

The template field audit examined 5,135 strings and found no absolute private
asset paths. Generated scenes passed the same audit after reopening. The stored
scan tested private terms from the production context without copying those terms
into public scanners. See the [test report](nc-update-test-report.md) for relocation.

## Files to review and publish

The ZIP contains README, LICENSE, `.gitignore`, the skill, docs and tests.
The reviewed scene travels as three checked binary parts plus a manifest, source
credits and OFL license. Assembled `.blend` scenes remain ignored. The original
production archive and font folders are excluded.

Repeat the review after changing labels, media, configuration or template content.
Inspect embedded metadata and stale stored strings as well as visible properties.
Keep source and font notices. See [apply-nc-update.md](apply-nc-update.md).
