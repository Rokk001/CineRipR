# Release Notes - CineRipR 1.0.25

## Fixed
- Finished move for series now mirrors the release root correctly:
  - `.../Download/<Series>/Season 01` → `.../finished/<Series>/Season 01` (not to finished root)
- Robust derivation of the release root when moving original source files

## Changed
- No changes to extraction behavior (`extracted` remains the final destination for extracted content)

## Notes
- This release addresses misplacement of season folders directly under the finished root for series.
