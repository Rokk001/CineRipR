# Release Notes - CineRipR 1.0.26

## Fixed
- Extraction target for series corrected:
  - `.../Download/<Series>/Season 01` → `.../_extracted/<Series>/Season 01/...`
  - No season folders created directly under `_extracted` root
- Change is isolated to extraction path computation; finished mirroring logic is unchanged

## Notes
- Finished continues to mirror downloads 1:1 under `<finished>/<ReleaseRoot>/...`
- Extracted remains the final destination for extracted content.
