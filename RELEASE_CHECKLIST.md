# RELEASE CHECKLIST - MANDATORY BEFORE EVERY RELEASE

## CRITICAL: PRIVATE PATH SCANNING

**BEFORE creating ANY release, I MUST:**

1. **Scan ALL text for private paths:**
   - Look for `\\` followed by letters (UNC paths)
   - Look for specific folder names from user's system
   - Look for any path that looks like a real directory

2. **Replace ALL private paths with generic examples:**
   - `\\HS\Download\...` → `\\SERVER\Share\...`
   - `Henry.Danger.S01...` → `Show.Name.S01...`
   - Any real file names → Generic example names

3. **Use ONLY these generic patterns:**
   - `\\SERVER\Share\...` for UNC paths
   - `Show.Name.S01.GROUP` for TV shows
   - `Movie.Name.2024.GROUP` for movies
   - `A.Test.Extract` for generic examples

## MANDATORY STEPS:

- [ ] Read through ALL release notes text
- [ ] Scan for backslashes and real paths
- [ ] Replace ALL private information with generic examples
- [ ] Double-check no real paths remain
- [ ] Only then create the release

## VIOLATION = IMMEDIATE DELETION

If I violate this again, I will:
1. Immediately delete the release
2. Create a new one with ONLY generic examples
3. Never use real paths again

## EXAMPLES OF WHAT TO REPLACE:

❌ WRONG:
- `\\HS\Download\dcpp\A.Test.Extract`
- `Henry.Danger.S01.GERMAN.1080p.WEB.H264-MiSFiTS`
- Any real folder names from user's system

✅ CORRECT:
- `\\SERVER\Share\...`
- `Show.Name.S01.GROUP`
- Generic example names only