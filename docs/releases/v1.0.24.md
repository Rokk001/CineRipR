# Release Notes - CineRipR 1.0.24

## Fixed
- Finished movement now mirrors the download release directory 1:1 into `finished/<ReleaseName>/` for movies and series
- Removed accidental movement of extracted content into finished
- Companion folders like `Sample` and `Subs` are preserved exactly during the move

## Changed
- Simplified finished move logic (no TV-specific restructuring)

## Notes
- Extraction still writes to `extracted/`, then original files are moved from downloads to `finished/` 1:1.
