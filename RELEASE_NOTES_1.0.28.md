# Release Notes - CineRipR 1.0.28

## Fixed
- Extracted category name corrected to `TV-Shows`
- TV shows extracted under `_extracted/TV-Shows/<Series>/Season XX/...` even when the source path contains a season folder like `S01`
- Extraction is skipped (with error log) when no valid archive groups are found (likely incomplete download)

## Notes
- Finished archiving logic remains unchanged (1:1 mirror of downloads per release)
- `extracted` is the final destination for extracted content.
