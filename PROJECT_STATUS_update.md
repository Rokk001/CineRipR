
## Session Notes - Scraped Statistic (2026-02-13)

### 🎯 Implementierte Features

#### 1. 📊 New Statistic: Scraped
- **Added "Scraped" count to dashboard**:
    - Tracks the number of titles successfully scraped from TMDB.
    - Displayed as a new card "🎬 Scraped" in the Statistics section.
    - Persisted to database and survives restarts.
- **Backend Integration**:
    - Count increments automatically when NFO files are successfully created via TMDB integration.
    - Works for both Movies and TV Episodes.

### 🔧 Geänderte Dateien
- **`src/cineripr/web/settings_db.py`**: Database schema update for `scraped_count`.
- **`src/cineripr/web/status.py`**: Added `scraped_count` to `GlobalStatus` and `StatusTracker`.
- **`src/cineripr/core/archives.py`**: Trigger increment on successful NFO generation.
- **`src/cineripr/web/templates/index.html`**: Added UI card for the new statistic.
- **`src/cineripr/web/static/js/app.js`**: Frontend logic to display the new count.

---
