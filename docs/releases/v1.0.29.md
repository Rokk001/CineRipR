# Release Notes - CineRipR 1.0.29

## Fixed
- Extracted TV shows: show name derived correctly when season folders like `S01` are present (targets `_extracted/TV-Shows/<Series>/Season XX/...`)
- Move related episode artifacts (Subs/Sample/Sonstige/Proof) that match the episode tag alongside the episode into finished

## Notes
- Extraction is skipped for contexts without valid archive groups (likely incomplete downloads)
- Finished archiving logic unchanged (1:1 mirror of downloads)
- Extracted remains final destination for extracted content.
