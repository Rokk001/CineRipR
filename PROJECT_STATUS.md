# CineRipR - Projekt Status & Struktur

## Aktueller Stand (Version 2.5.19)

### ✅ Behobene Probleme
1. **TV-Show-Organisation**: TV-Shows folgen jetzt korrekt der `TV-Shows/Show Name/Season XX/` Struktur
2. **1:1 Download-Struktur Bug**: Behoben - alle Dateien verwenden jetzt die zentrale `move_remaining_to_finished()` Logik
3. **Docker Permission Errors**: Alle `chown` Befehle entfernt - nur noch `chmod 777`
4. **File Stability Bug (v2.4.0)**: Dateien < 24h werden nicht mehr vorzeitig verschoben
5. **Leerer `_extracted` Ordner (v2.4.0)**: Dateien werden korrekt kopiert bevor Quelle verschoben wird
6. **Settings-Inkonsistenz (v2.4.1)**: WebGUI-Settings haben jetzt garantiert höchste Priorität
7. **Countdown nach Restart (v2.4.1)**: Countdown wird sofort nach Container-Start angezeigt
8. **"Run Now" Crash (v2.4.1)**: Container crasht nicht mehr bei "Run Now" Button
9. **Progressbar Live-Updates (v2.4.1)**: Extraction Progress wird in Echtzeit aktualisiert
10. **System Health (v2.4.1)**: CPU/Memory werden jetzt immer korrekt angezeigt
11. **Countdown Missing After Fresh Install (v2.4.2/v2.4.3)**: DEFAULT_SETTINGS werden jetzt korrekt geladen, DB-Migration für alte Werte, Countdown ist GARANTIERT sichtbar
12. **CompletedProcess Crash (v2.5.1)**: Variable Shadowing behoben - Container crasht nicht mehr mit `'CompletedProcess' object has no attribute 'processed'`
13. **Countdown Missing After Restart (v2.5.1)**: Enhanced fallback logic - Countdown immer sichtbar wenn repeat mode aktiv
14. **Disk Space Empty (v2.5.1)**: Background Health Monitor Thread - System Health Updates alle 30 Sekunden
15. **Queue Empty After Restart (v2.5.1)**: Queue Persistenz in SQLite DB - Queue überlebt Container-Restarts
16. **Countdown Live-Update (v2.5.2)**: Settings-Änderungen aktualisieren Countdown sofort ohne Container-Restart
17. **Settings Race Condition (v2.5.3)**: THE REAL FIX - DB-Werte werden nach JEDEM Setting-Save neu geladen, Countdown/Progressbar erscheinen sofort
18. **Queue Empty Bug (v2.5.3)**: Tracker wird immer initialisiert wenn WebGUI aktiv ist, Queue wird korrekt befüllt
19. **Main Loop Overwrites Settings (v2.5.5)**: THE REAL FIX - Loop liest jetzt IMMER aus DB, nicht aus settings object. WebGUI-Änderungen werden sofort übernommen!
20. **Queue/History Duplikate (v2.5.13)**: Queue und History zeigen jetzt jeden Titel nur einmal, mit Versuchsanzahl bei mehrfachen Versuchen
21. **Check Interval Problem (v2.5.13)**: Progressbar verwendet jetzt korrekt das konfigurierte Check Interval (z.B. 35 min)
22. **progress_callback NameError (v2.5.14)**: Kritischer Fehler behoben - Endlosschleife und hohe CPU-Last nach Fehlern
23. **Processing Status Bug (v2.5.14)**: GUI zeigt jetzt korrekt "Idle" statt "Processing" nach Fehlern
24. **History Duplikate beim Laden (v2.5.15)**: History wird jetzt beim Laden aus DB dedupliziert - jeder Release erscheint nur einmal
25. **Progress Live-Updates (v2.5.15)**: Progress wird jetzt kontinuierlich während Extraktion aktualisiert, nicht nur bei Prozentänderung
26. **On-Demand System Health (v2.5.16)**: Systemmetriken werden nur bei Bedarf über den Refresh-Button aktualisiert - Idle-CPU bleibt < 1%
27. **Idle CPU Optimierung (v2.5.17)**: Settings-Check-Intervall von 5 auf 30 Sekunden erhöht, Logging optimiert - reduziert DB-Abfragen von ~12/min auf ~2/min
28. **Movie Umbenennung basierend auf NFO (v2.5.18)**: Nach erfolgreicher Extraktion werden Film-Ordner und -Dateien automatisch basierend auf NFO-Metadaten umbenannt (nur Movies, nicht TV-Shows)
29. **Automatisches Verschieben zu Finalen Zielen (v2.5.19)**: Nach erfolgreicher Umbenennung werden Filme und TV-Shows automatisch in `movie_root` bzw. `tvshow_root` verschoben (mit Überschreiben bei existierenden Verzeichnissen)
4. **UNC-Pfad-Handling**: Windows UNC-Pfade werden korrekt in Docker-Containern verarbeitet
5. **Private Pfade**: Alle privaten Pfade aus dem Codebase entfernt
6. **Archive Movement Logic**: Korrekte Implementierung – Original-Quelldateien (aus Downloads) werden 1:1 nach `finished/<ReleaseName>/` gespiegelt; extrahierte Inhalte bleiben endgültig in `extracted/`
7. **File Completeness Check (v2.3.3)**: Dateien werden nur verarbeitet, wenn sie für konfigurierbare Stunden (Standard: 24h) unverändert sind. Verhindert Verarbeitung von noch nicht vollständig heruntergeladenen Dateien (z.B. MKV-Dateien bei TV-Shows)
8. **Import-Fehler behoben**: `from .archive_constants` → `from ..extraction.archive_constants` in `archives.py` und `file_operations.py`

### 🔖 Entscheidungen (wichtig fürs nächste Mal)
- `extracted` ist der finale, endgültige Zielpfad für extrahierte Inhalte.
- `finished` spiegelt die Download-Quelle 1:1 (alle Dateien/Unterordner) unter `finished/<ReleaseName>/`.
- Keine TV-spezifische Umstrukturierung im `finished`-Pfad.
- Companions (z. B. `Sample`, `Subs`) werden beim Verschieben nach `finished` unverändert übernommen.

### ⚠️ KRITISCHE REGEL - NIEMALS VERGESSEN!
**KEINE URHEBERRECHTLICH GESCHÜTZTEN INHALTE IN DOKUMENTATION!**
- ❌ **NIEMALS** echte Film-/Serien-Titel verwenden (z.B. "Goonies", "Monster", etc.)
- ✅ **NUR** generische Beispiele: `Release.Name.2024.1080p.BluRay.x264-GROUP`, `Show.Name.S01E01.1080p.WEB.x264-GROUP`, `Movie.Title.2024.1080p.WEB.x264-GROUP`
- ⚠️ **VOR JEDEM COMMIT**: Alle `.md` Dateien scannen mit `grep -i "goonies|monster|ed.gein" docs/ README.md CHANGELOG.md PROJECT_STATUS.md`
- 🔍 **AUTOMATED CHECK**: Diese Regel gilt für ALLE Dokumentationen, Kommentare, Beispiele, Release Notes, etc.

### 🔧 Aktuelle Architektur

#### Core Module
- **`archives.py`**: Hauptorchestrierung für Archive-Verarbeitung
- **`file_operations.py`**: Datei-Operationen mit Docker/UNC-Unterstützung
- **`path_utils.py`**: TV-Show-Pfad-Erkennung und -Organisation
- **`archive_extraction.py`**: Extraktionslogik für verschiedene Archive-Formate
- **`config.py`**: Konfigurationsverwaltung

#### Wichtige Funktionen
- **`process_downloads()`**: Hauptfunktion für Download-Verarbeitung
- **`move_remaining_to_finished()`**: Zentrale Logik für finished-Pfad-Organisation
- **`_safe_move_with_retry()`**: Docker-sichere Datei-Verschiebung
- **`build_tv_show_path()`**: TV-Show-Pfad-Erstellung

### 📁 Projektstruktur
```
src/cineripr/
├── __init__.py              # Version 2.5.17
├── cli.py                   # Command-Line-Interface
├── config.py                # Konfiguration
├── progress.py              # Progress-Tracking
├── core/                    # Core Business Logic
│   ├── archives.py         # Hauptorchestrierung
│   ├── file_operations.py  # Datei-Operationen
│   ├── path_utils.py        # Pfad-Utilities
│   └── cleanup.py          # Finished-Directory-Cleanup
├── extraction/              # Archive Handling
│   ├── archive_detection.py # Archive-Erkennung
│   ├── archive_extraction.py # Extraktionslogik
│   └── archive_constants.py  # Konstanten und Regex
└── web/                     # WebGUI (v2.5.7: Refactored)
    ├── __init__.py          # Exports
    ├── app.py               # Flask App Factory
    ├── webgui.py            # Legacy wrapper
    ├── status.py            # Status-Tracking
    ├── settings_db.py       # Settings DB
    ├── routes/              # Flask Blueprints
    │   ├── views.py         # HTML Views
    │   ├── api.py           # API Routes
    │   └── settings.py      # Settings Routes
    ├── templates/           # HTML Templates
    │   └── index.html       # Dashboard Template
    ├── static/              # Static Files
    │   ├── css/style.css    # CSS Styles
    │   ├── js/app.js        # JavaScript
    │   └── favicon.svg      # Favicon
    └── services/            # Services Layer
        └── status_tracker.py # Status Tracker Wrapper
```

### 🎯 TV-Show-Organisation (Funktioniert)
**Input:**
```
Download/
  Show.Name.S01.GROUP/
    Show.Name.S01E05.GROUP/
      episode.part01.rar
```

**Output:**
```
Finished/
  TV-Shows/
    Show Name/
      Season 01/
        episode.mkv
```

### 🎬 Movie-Organisation (Funktioniert)
**Input:**
```
Download/
  Movie.Name.2024.GROUP/
    movie.part01.rar
```

**Output:**
```
Finished/
  Movies/
    Movie.Name.2024.GROUP/
      movie.mkv
```

### 🔄 Prozess-Flow
1. **Scan**: Downloads-Verzeichnis scannen
2. **Extract**: Archive nach `extracted/` extrahieren (dies ist der finale Ort der extrahierten Inhalte)
3. **Move**: QUELL-DATEIEN aus dem Download-Release 1:1 nach `finished/<ReleaseName>/` verschieben (Spiegelung der Struktur)
4. **Cleanup**: Optionale Aufräum-/Retention-Logik im `finished`-Verzeichnis

## Session Notes (2025-11-09)

### Version 2.0.0 - Major Project Modernization 🎉
- **Komplette Projekt-Restrukturierung**: Moderne, professionelle Struktur
- **docs/** Verzeichnis erstellt mit 4 Unterkategorien (architecture, development, operations, releases)
- **examples/** mit docker-compose.yml und Config-Beispielen
- **scripts/** mit Build-, Test- und Release-Automatisierung
- **src/cineripr/** in 3 Module aufgeteilt:
  - `core/` - Business Logic (archives, file_operations, path_utils, cleanup)
  - `extraction/` - Archive-Handling (detection, extraction, constants)
  - `web/` - WebGUI (webgui, status)
- **tests/** erweitert mit unit/ und integration/ Struktur
- **.dockerignore** für optimierte Docker-Builds erstellt
- **Alle Imports** aktualisiert für neue Modulstruktur
- **README.md** komplett modernisiert und fancy gemacht mit:
  - Badges, Feature-Tabellen, Screenshots-Platzhalter
  - Quick-Start-Guides, Troubleshooting, Contributing
  - Professionelles Design und Struktur
- **Dokumentation** komplett neu organisiert (27 Dateien verschoben)
- **17 Release Notes** nach docs/releases/ verschoben
- **GitHub Actions** bereits vorhanden und funktionsfähig
- **Keine Breaking Changes** für End-User! Nur Developer-Imports geändert
- Alle Tests erfolgreich, keine Linter-Fehler!

### Version 1.0.37 - Critical 7-Zip Detection Fix
- **7-Zip Detection Fix**: Kritischer Fix für Docker-Container
- Enhanced `resolve_seven_zip_command()` mit expliziten Pfad-Fallbacks
- Docker-Container finden jetzt 7-Zip korrekt in `/usr/local/bin`
- Behebt "No such file or directory: '/usr/bin/7z'" Fehler
- Unterstützt offiziellen 7-Zip Binary (`/usr/local/bin/7z`, `/usr/local/bin/7zz`)
- Unterstützt p7zip Pakete (`/usr/bin/7z`, `/usr/bin/7za`, `/usr/bin/7zr`)
- GitHub-Link im WebGUI-Footer mit Icon hinzugefügt
- RAR-Extraktion funktioniert jetzt zuverlässig in Docker

### Version 1.0.36 - Complete WebGUI Feature Set
- **Release Detail View**: Detaillierte Modal-Ansicht für Queue-Items (Feature 5)
- **Timeline/History View**: Neuer History-Tab mit visueller Timeline (Feature 6)
- **Manual Control Panel**: Pause/Resume Buttons für Processing-Kontrolle (Feature 7)
- **Dark/Light Mode Toggle**: Theme-Switcher im Header mit Persistenz (Feature 8)
- **CPU & Memory Monitoring**: Echtzeit-System-Ressourcen-Tracking
- **Toast Sound Notifications**: Audio-Feedback für Benachrichtigungen (Web Audio API)
- Backend erweitert mit History-Tracking, Theme-Management und Control-Endpoints
- Vollständiges CSS-Variable-System für nahtloses Theming
- Enhanced StatusTracker mit `ReleaseHistory`, `is_paused`, `theme_preference`
- Neue API-Endpoints: `/api/theme`, `/api/control/pause`, `/api/control/resume`, `/api/history`
- Alle 8 geplanten WebGUI-Features vollständig implementiert! 🎉

### Version 1.0.35 - Major WebGUI Overhaul (Features 1-4)
- Toast Notifications für Echtzeit-Feedback
- Processing Queue Display zeigt anstehende Arbeit
- Log-Filtering & Search für einfaches Debugging
- System Health Monitoring mit Disk Space Tracking
- Tab-basierte Navigation (Overview, Queue, Health, Logs)
- Favicon mit CineRipR Branding hinzugefügt
- 7-Zip Version wird angezeigt
- Status-Display-Inkonsistenzen behoben
- Komplette Interface-Restrukturierung

### Core Logik (Unverändert)
- Klarstellung: `extracted` ist der finale Zielpfad für extrahierte Inhalte; `finished` spiegelt die Download-Quelle 1:1 pro Release-Root.
- Companion-Ordner (`Sample`, `Subs`, …) werden beim Verschieben nach `finished` unverändert übernommen.
- UNC-/Docker-Pfade: Safe-Move mit Fallback (copy+delete) bleibt aktiv; chmod 777, kein chown.

### Nächste sinnvolle Checks
- Stichprobe: `\\hs\Multimedia\Neu\_finished\Henry Danger\Season 01..` existiert unter dem Serien-Root (keine Seasons am Finished-Root).
- Bei Auffälligkeiten Logs mit `--debug` prüfen; ggf. konkrete Release-Pfade posten.

### Offene Hinweise (Low Priority)
- Lint-Warnungen zu "too general exception" vorhanden, funktional unkritisch.

### 🐳 Docker-Unterstützung
- **UNC-Pfade**: `\\SERVER\Share\...` → `/data/downloads/...`
- **Read-only Filesystem**: Copy+Delete Fallback
- **Permissions**: Nur `chmod 777`, keine `chown`
- **Safe Move**: Mehrere Retry-Strategien

### 📋 Nächste Schritte (TODO)
1. **Testing**: Aktuelle Version 1.0.29 testen
2. **Performance**: Große Archive-Performance optimieren
3. **Error Handling**: Robustere Fehlerbehandlung
4. **Documentation**: API-Dokumentation erweitern

### 🚨 Bekannte Issues
- **Linting Warnings**: Einige "too general exception" Warnings
- **Cell Variables**: Einige Loop-Variablen-Warnings
- **Performance**: Große Archive können langsam sein

### 📊 Code-Statistiken
- **Gesamt**: ~5000+ Zeilen Code
- **Hauptmodule**: 5 Core-Module
- **Tests**: 2 Test-Dateien
- **Dokumentation**: README, CHANGELOG, FINISHED_PATH_LOGIC

### 🔒 Sicherheit
- **Private Pfade**: Alle entfernt, nur generische Beispiele
- **Release Checklist**: Mandatory scanning vor Releases
- **Git Message Template**: Verhindert private Pfad-Exposition

### 🎛️ Konfiguration
- **TOML-basiert**: `cineripr.toml`
- **CLI-Overrides**: Alle Einstellungen überschreibbar
- **Docker-ready**: Container-Pfade unterstützt

## Entwicklungs-Workflow
1. **Änderungen machen** → Commit & Push
2. **Version erhöhen** → pyproject.toml & __init__.py
3. **Testen** → User testet
4. **Release** → Nur auf explizite Anweisung
5. **Dokumentation** → CHANGELOG.md aktualisieren

## Wichtige Dateien
- **RELEASE_CHECKLIST.md**: Verhindert private Pfad-Exposition
- **FINISHED_PATH_LOGIC.md**: Dokumentation der finished-Pfad-Logik
- **.gitmessage**: Template für sichere Commits
- **CHANGELOG.md**: Vollständige Änderungshistorie

---

## Session Notes - Version 2.1.0 (2025-11-10)

### 🎯 Implementierte Features

#### 1. ⏰ Next Run Countdown
- **Live countdown** im WebGUI mit sekündlichen Updates
- **Formatierte Zeitanzeige** (Stunden, Minuten, Sekunden)
- **Absolute Zeitanzeige** (z.B. "at 14:35:00")
- **Pulsing Animation** bei < 1 Minute verbleibend
- **Automatisches Ausblenden** während Processing

#### 2. 🎮 "Run Now" Button
- **Manueller Trigger** zum sofortigen Start
- **Bestätigungsdialog** vor Ausführung
- **Toast Notifications** für Feedback
- **Sofortiges Ausblenden** des Countdowns nach Trigger
- **Logging** als "Manual trigger" in Logs

#### 3. ⚙️ WebGUI Settings Management
- **SQLite-basierte Persistenz** (`/config/cineripr_settings.db`)
- **RESTful API** für Settings-Management
- **Echtzeit-Updates** ohne Container-Neustart
- **Input-Validierung** mit Fehlerbehandlung
- **Kategorisierte Settings** (Scheduling, Retention, Performance, etc.)

#### 4. 📊 API Endpoints (Neu)
- `GET /api/settings` - Alle Settings abrufen
- `GET/POST /api/settings/<key>` - Einzelnes Setting abrufen/setzen
- `GET/POST /api/settings/performance` - Performance-Settings
- `POST /api/control/trigger-now` - Manueller Trigger
- `GET /api/system/hardware` - Hardware-Erkennung
- `POST /api/setup/wizard` - Setup-Wizard (vorbereitet)

### 🔧 Geänderte Module

#### Neu erstellt:
- **`src/cineripr/web/settings_db.py`** - Settings-Persistenz mit SQLite
  - `SettingsDB` Klasse mit thread-sicheren Operationen
  - `DEFAULT_SETTINGS` Konstante mit allen Standardwerten
  - Metadaten-Tabelle für first-run-Detection

#### Erweitert:
- **`src/cineripr/web/status.py`**:
  - `GlobalStatus.next_run_time` - Nächster Run-Zeitpunkt
  - `GlobalStatus.repeat_mode` - Repeat-Modus Status
  - `GlobalStatus.repeat_interval_minutes` - Configured interval
  - `GlobalStatus.get_seconds_until_next_run()` - Verbleibende Zeit
  - `StatusTracker.set_next_run(minutes)` - Nächsten Run setzen
  - `StatusTracker.clear_next_run()` - Next Run löschen
  - `StatusTracker.set_repeat_mode(enabled)` - Repeat-Modus setzen
  - `StatusTracker.trigger_run_now()` - Manuellen Trigger anfordern
  - `StatusTracker.should_trigger_now()` - Trigger-Status prüfen

- **`src/cineripr/web/webgui.py`**:
  - **HTML**: Next Run Card mit Countdown-Display
  - **CSS**: Countdown-Styling mit Pulsing-Animation
  - **JavaScript**: 
    - `updateStatus()` erweitert mit Countdown-Logik
    - `triggerRunNow()` Funktion für manuellen Trigger
    - Update-Intervall: 2s → 1s (für Live-Countdown)
  - **API**: 6 neue Endpoints für Settings & Control

- **`src/cineripr/cli.py`**:
  - **Sleep-Loop**: Live Countdown mit 1-Sekunden-Updates
  - **Manual Trigger Check**: `tracker.should_trigger_now()` in Sleep-Loop
  - **Next Run Management**: `set_next_run()` / `clear_next_run()` Calls
  - **Repeat Mode**: `set_repeat_mode()` beim Start
  - **Logging**: Verbesserte Logging-Messages mit Emojis

### 📊 Default Settings Änderungen

| Setting                   | Alt     | Neu    | Begründung                    |
| ------------------------- | ------- | ------ | ----------------------------- |
| `repeat_forever`          | `false` | `true` | Docker-User erwarten Auto-Run |
| `repeat_after_minutes`    | `0`     | `30`   | Sinnvolles Standard-Intervall |
| `finished_retention_days` | -       | `15`   | User-Präferenz                |

### 📚 Dokumentation

**Aktualisiert:**
- `CHANGELOG.md` - Version 2.1.0 Entry
- `docs/README.md` - Latest version → v2.1.0
- `PROJECT_STATUS.md` - Session Notes hinzugefügt
- `pyproject.toml` - Version → 2.1.0

**Neu erstellt:**
- `docs/releases/v2.1.0.md` - Vollständige Release Notes

### 🚀 Deployment

- **Docker Image**: `ghcr.io/rokk001/cineripr:2.1.0`
- **Git Tag**: `v2.1.0`
- **Persistence**: `/config` Volume für Settings-DB erforderlich

### 📝 Hinweise

- **Parallel Extraction**: Infrastruktur vorbereitet, aber noch nicht aktiviert
  - Settings vorhanden: `parallel_extractions`, `cpu_cores_per_extraction`
  - API-Endpoints vorhanden: `/api/settings/performance`
  - Implementierung: Für v2.2.0 geplant

- **Settings UI**: API vorhanden, UI-Tab für v2.2.0 geplant

- **TOML Migration**: Automatisch beim ersten Start
  - `cineripr.toml` bleibt als Fallback unterstützt
  - WebGUI Settings haben Vorrang

- **Backward Compatibility**: Vollständig kompatibel mit v2.0.x

---

## Session Notes - Version 2.2.0 (2025-11-10)

### 🎯 Implementierte Features

#### 1. ⚙️ Settings UI Tab (Vollständig)
- **Komplettes Settings-Interface** im WebGUI
- **5 Kategorien** mit allen konfigurierbaren Settings
- **Echtzeit-Validierung** für numerische Eingaben
- **Save All Settings** Funktion mit Bulk-API-Calls
- **Reset to Defaults** mit Bestätigungsdialog
- **Auto-Load** beim Tab-Wechsel

### 🔧 Settings Kategorien

**🕐 Scheduling:**
- `repeat_forever` - Auto-Run aktivieren/deaktivieren
- `repeat_after_minutes` - Check-Intervall (1-1440 Min.)

**🗑️ Retention & Cleanup:**
- `finished_retention_days` - Aufbewahrungstage (1-365)
- `enable_delete` - Auto-Delete aktivieren

**📂 Subfolder Processing:**
- `include_sample` - Sample-Verzeichnisse verarbeiten
- `include_sub` - Subtitle-Verzeichnisse verarbeiten
- `include_other` - Andere Unterverzeichnisse

**🎨 UI Preferences:**
- `toast_notifications` - Toast-Benachrichtigungen
- `toast_sound` - Benachrichtigungs-Sounds

**🔧 Advanced:**
- `demo_mode` - Demo-Modus (nur simulieren)

### 📝 Code Changes

**WebGUI (`webgui.py`):**
- Neuer Navigation Tab "Settings"
- Kompletter Settings Tab Content (HTML)
- CSS für Settings-Kategorien und Formulare
- JavaScript Functions:
  - `loadSettings()` - Settings von API laden
  - `saveAllSettings()` - Alle Settings speichern mit Validierung
  - `resetSettings()` - Auf Defaults zurücksetzen
  - `switchTab()` erweitert für Auto-Load

### 🎨 UI/UX

- **Card-basiertes Layout** mit Glassmorphism
- **Farbcodierte Kategorien** mit Emoji-Icons
- **Inline-Hilfe** für jedes Setting
- **Visual Feedback** bei Save/Reset
- **Responsive Design** für Mobile
- **Validierungs-Messages** für ungültige Eingaben

### 📊 Status

✅ **Vollständig implementiert:**
- Settings UI Tab
- Load/Save/Reset Funktionen
- API-Integration
- Validation
- User Feedback

❌ **Nicht implementiert (verschoben):**
- Parallel Extraction - Zu komplex für dieses Release
- Hardware Auto-Detection - Bereits vorbereitet, aber noch nicht aktiviert

### 🚀 Deployment

- **Version:** 2.2.3
- **Features:** Settings UI vollständig + Alle Import-Fehler behoben
- **Backward Compatible:** Ja
- **Breaking Changes:** Keine

---

## Session Notes - Version 2.2.1-2.2.3 (2025-11-10) - Import-Fehler Fixes

### 🐛 Problem

Nach dem v2.0.0 Refactoring gab es mehrere Import-Fehler in den `__init__.py` Dateien, die nicht-existierende Funktionen importierten.

### ✅ Behobene Import-Fehler

#### v2.1.1 - extraction/__init__.py
- **Entfernt:** `ARCHIVE_EXTENSIONS`, `RAR_EXTENSIONS`, `ZIP_EXTENSIONS` (existierten nicht)
- **Hinzugefügt:** `SUPPORTED_ARCHIVE_SUFFIXES`, `TV_TAG_RE` (korrekte Constants)

#### v2.2.1 - extraction/__init__.py
- **Entfernt:** `detect_archives`, `group_related_archives`, `is_archive` (existierten nicht)
- **Hinzugefügt:** `split_directory_entries`, `build_archive_groups`, `is_supported_archive` (korrekte Funktionen)

#### v2.2.2 - core/__init__.py
- **Entfernt:** `chmod_recursive`, `copy_file_with_metadata`, `delete_empty_directories`, `move_directory_contents` (existierten nicht)
- Diese Funktionen werden nirgendwo verwendet

#### v2.2.3 - core/__init__.py
- **Entfernt:** `detect_show_and_season`, `is_tv_show_release` (existierten nicht)
- **Behalten:** `build_tv_show_path` (wird verwendet)

### 📊 Finale Validierung

**Alle `__init__.py` Dateien validiert:**
- ✅ `core/__init__.py` - Alle Imports korrekt
- ✅ `extraction/__init__.py` - Alle Imports korrekt
- ✅ `web/__init__.py` - Alle Imports korrekt
- ✅ `cli.py` - Alle Imports korrekt

**Alle importierten Funktionen existieren:**
- ✅ `ProcessResult`, `process_downloads` - existieren in `archives.py`
- ✅ `cleanup_finished` - existiert in `cleanup.py`
- ✅ `build_tv_show_path` - existiert in `path_utils.py`
- ✅ `resolve_seven_zip_command` - existiert in `archive_extraction.py`
- ✅ `get_status_tracker` - existiert in `status.py`
- ✅ `create_app`, `run_webgui` - existieren in `webgui.py`

### 🎯 Ergebnis

**Alle Import-Fehler aus dem v2.0.0 Refactoring sind jetzt behoben!**

Der Container sollte jetzt ohne Fehler starten.

---

## Session Notes - Version 2.3.0 (2025-11-10)

### 🚀 Major Changes

#### TOML Configuration Optional
- **`--config` ist jetzt optional**
  - Wenn nicht vorhanden, müssen Pfade über CLI-Args gesetzt werden
  - Alle anderen Settings können über WebGUI verwaltet werden
  - TOML-Datei ist für Docker-Deployments nicht mehr erforderlich

#### WebGUI Settings Priority
- **WebGUI-Settings überschreiben jetzt TOML/CLI-Settings**
  - Priority-Order: **WebGUI (SQLite) > CLI args > TOML file > Defaults**
  - Settings aus SQLite-Datenbank haben höchste Priorität
  - Behebt Problem, dass TOML-Settings WebGUI-Settings überschrieben haben

### 🔧 Technische Änderungen

#### `cli.py` - `load_and_merge_settings()`
- **Umschreibung der Settings-Loading-Logik:**
  1. TOML-Datei optional laden (wenn vorhanden)
  2. Pfade aus CLI-Args setzen (erforderlich wenn keine TOML)
  3. WebGUI-Settings aus SQLite-Datenbank laden
  4. WebGUI-Settings überschreiben TOML/CLI-Settings

#### `--config` Argument
- **Jetzt optional** (default: `None` statt `DEFAULT_CONFIG`)
- Wenn nicht vorhanden, müssen Pfade über CLI-Args gesetzt werden

### 📝 Docker Deployment

**Vorher (v2.2.5):**
```yaml
command: ["umask 000 && exec python -m cineripr.cli --config /config/cineripr.toml"]
volumes:
  - /mnt/user/appdata/cineripr/cineripr.toml:/config/cineripr.toml:ro
```

**Nachher (v2.3.0):**
```yaml
command: ["umask 000 && exec python -m cineripr.cli --download-root /data/downloads --extracted-root /data/extracted --finished-root /data/finished"]
volumes:
  - /mnt/user/appdata/cineripr:/config  # Für Settings-DB
```

### ✅ Behobene Probleme

- **TOML-Settings überschrieben WebGUI-Settings**
  - Jetzt haben WebGUI-Settings höchste Priorität
  - 30 Minuten aus WebGUI werden jetzt verwendet (nicht mehr 60 Minuten aus TOML)

### 🎯 Migration

**Für Docker-User:**
- TOML-Datei aus Dockerfile entfernen
- Pfade über CLI-Args setzen: `--download-root`, `--extracted-root`, `--finished-root`
- Alle anderen Settings über WebGUI konfigurieren
- Settings-Datenbank wird automatisch in `/config` Volume erstellt

**Für TOML-User:**
- TOML-Dateien funktionieren weiterhin (backward compatible)
- WebGUI-Settings überschreiben TOML-Settings, wenn konfiguriert

---

## 🔴 Offene Probleme (Stand: 2025-11-10)

### ❌ KRITISCH: Progressbar erscheint nicht

**Problem:**
- Progressbar wird nicht angezeigt obwohl "Enable Auto-Run (Repeat Forever)" aktiviert ist
- Header zeigt "Idle (Manual Mode)" statt Countdown-Progressbar
- `data.seconds_until_next_run` ist `null` obwohl `repeat_mode` aktiv ist

**Ursache:**
- `set_repeat_mode()` setzt jetzt `repeat_interval_minutes` (v2.5.5 Fix)
- ABER: `next_run_time` wird nicht gesetzt wenn Settings geändert werden
- Frontend zeigt Progressbar nur wenn `seconds_until_next_run !== null`

**Status:**
- ✅ Code geändert: `set_repeat_mode()` akzeptiert jetzt `interval_minutes` Parameter
- ✅ Code geändert: Progressbar-Logik zeigt Progressbar wenn `repeat_mode && repeat_interval_minutes > 0`
- ❌ **NOCH NICHT GETESTET** - Container zeigt 502 Bad Gateway Errors

**Nächste Schritte:**
1. Container-Logs prüfen: `docker logs cineripr`
2. Prüfen ob Container läuft: `docker ps`
3. Falls Container crasht: Logs analysieren und Runtime-Fehler fixen
4. Falls Container läuft: Prüfen ob `repeat_interval_minutes` im API-Response enthalten ist

---

### ⚠️ Container zeigt 502 Bad Gateway Errors

**Problem:**
- Browser Console zeigt: `GET https://cineripr.zhome.ch/api/status 502 (Bad Gateway)`
- `SyntaxError: Unexpected token '<', "<html>... is not valid JSON"`
- Flask-App crasht oder startet nicht

**Mögliche Ursachen:**
1. Container läuft noch alte Version (v2.5.4 oder älter)
2. Runtime-Fehler beim Start (Syntax OK, aber Import/Logic-Fehler)
3. Flask-App crasht beim Initialisieren

**Status:**
- ✅ Syntax-Checks: Alle Dateien kompilieren ohne Fehler
- ❌ **Container-Logs nicht geprüft** - Runtime-Fehler unbekannt

**Nächste Schritte:**
1. Container-Logs prüfen: `docker logs cineripr --tail 100`
2. Prüfen ob neue Version deployed: `docker ps` → Image-Version
3. Falls alte Version: `docker pull ghcr.io/rokk001/cineripr:2.5.5`
4. Falls neue Version: Logs analysieren und Runtime-Fehler fixen

---

### 📋 Was heute gemacht wurde (v2.5.5)

**Versuche:**
1. ✅ Main Loop liest jetzt Settings aus DB (nicht mehr aus `settings` object)
2. ✅ Settings werden während Sleep-Loop geprüft (alle 5 Sekunden)
3. ✅ `set_repeat_mode()` setzt jetzt `repeat_interval_minutes`
4. ✅ Progressbar-Logik zeigt Progressbar wenn `repeat_mode && repeat_interval_minutes > 0`
5. ✅ Debug-Logging hinzugefügt für Settings-Update
6. ✅ JavaScript Interval auf 2 Sekunden reduziert (Performance)

**Commits:**
- `f229b0f`: Main Loop reads from DB
- `c1b3fd2`: Fix excessive API calls
- `2296824`: Fix JavaScript scope issue
- `4020dc9`: Check settings during sleep
- `500840c`: Progressbar MUST show when Auto-Run enabled
- `fd97c37`: set_repeat_mode now sets repeat_interval_minutes

**Status:**
- ❌ **NOCH NICHT FUNKTIONIEREND** - Container zeigt 502 Errors
- ❌ **NOCH NICHT GETESTET** - Progressbar erscheint nicht

---

### 🔧 Technische Details

**Geänderte Dateien:**
- `src/cineripr/cli.py`: Main Loop liest Settings aus DB, prüft Settings während Sleep
- `src/cineripr/web/webgui.py`: Settings-Update setzt `repeat_interval_minutes`, Progressbar-Logik erweitert
- `src/cineripr/web/status.py`: `set_repeat_mode()` akzeptiert `interval_minutes` Parameter

**Offene Fragen:**
1. Warum crasht der Container? (502 Bad Gateway)
2. Warum ist `seconds_until_next_run` null obwohl `repeat_mode` aktiv ist?
3. Wird `set_next_run()` aufgerufen wenn Settings gespeichert werden?
4. Funktioniert der Settings-Update-Mechanismus überhaupt?

**Debug-Info:**
- Debug-Logging in `webgui.py` Line 2591-2631
- Debug-Logging in `status.py` Line 797-802
- Logs sollten zeigen ob `set_next_run()` aufgerufen wird

---

## Session Notes - TMDB Integration (2025-02-13)

### 🎯 Implementierte Features

### 🎯 Implementierte Features

#### 1. 🎥 TMDB Integration
- **Automatische NFO-Erstellung**: Nach dem Extrahieren und Verschieben von Filmen **und TV-Serien** wird auf TMDB gesucht.
- **Metadaten-Download**: 
    - **Movies**: Titel, Jahr, Plot, Bewertung, Cast & Crew -> `movie.nfo`
    - **TV Episodes**: Episodentitel, Plot, Air Date, Rating, Guest Stars -> `Dateiname.nfo`
- **Graceful Failure**: Wenn kein API-Token gesetzt ist oder der Film nicht gefunden wird, läuft der Prozess normal weiter.

#### 2. 🔒 Secure Configuration
- **Environment Variables**: `CINERIPR_TMDB_API_TOKEN` wird unterstützt (für Docker).
- **Local Config**: `cineripr.local.toml` (gitignored) überschreibt Einstellungen für lokale Entwicklung.
- **Config-Ladereihenfolge**: Env Var > Local Config > Main Config > Default.

### 🔧 Geänderte Module
- **`src/cineripr/core/tmdb.py`**: Neues Modul für API-Interaktion.
- **`src/cineripr/config.py`**: Erweiterte Ladelogik für Env-Vars und lokale Configs.
- **`src/cineripr/core/archives.py`**: Integration des TMDB-Checks in den Workflow.
- **`src/cineripr/cli.py`**: Durchreichen des API-Tokens.

### 📝 Dokumentation
- **README.md**: Features und Konfiguration aktualisiert.
- **.gitignore**: `cineripr.local.toml` hinzugefügt.

---

## Session Notes - History Display Fix (2025-02-13)

### 🐛 Problem
- **History View**: Zeigte nur fehlgeschlagene Items an.
- **Unreadable Status**: Status-Dropdown im History-Tab war im Dark Mode unlesbar (weiße Schrift auf weißem Hintergrund).
- **Missing Entries**: Erfolgreiche Releases und Details fehlten in der Historie.

### ✅ Behobene Probleme
1. **History Tracking Logic Refactor**:
   - Die History-Logik wurde von `cli.py` (Batch-basiert) nach `archives.py` (Release-basiert) verschoben.
   - **Ergebnis**: Jedes Release wird jetzt individuell als "Completed" oder "Failed" aufgezeichnet, anstatt dass der gesamte Batch als ein einziger "Processing Run" erscheint.
2.  **CSS Fix**:
    - Variable `--bg-secondary` in `style.css` definiert und auf `<select>`-Elemente angewendet.
    - **Ergebnis**: Status-Filtering Dropdown ist jetzt in Dark- und Light-Mode gut lesbar.

### 🔧 Geänderte Dateien
- **`src/cineripr/core/archives.py`**: `add_to_history()` Aufruf in die Loop integriert.
- **`src/cineripr/cli.py`**: Redundanten History-Aufruf entfernt.
- **`src/cineripr/web/static/css/style.css`**: CSS-Variablen-Fix für Dropdowns.

---

## Session Notes - UnboundLocalError Fix (2026-02-13)

### 🐛 Problem
- **UnboundLocalError**: `cannot access local variable 'extracted_ok' where it is not associated with a value`.
- Occurred when `process_downloads` encountered a release directory that resulted in no extraction contexts (e.g. empty directory or only files that didn't trigger extraction), causing the loop where `extracted_ok` is set to be skipped.
- The history logging at the end of the release processing attempted to access `extracted_ok`, causing the crash.

### ✅ Solution
- **Initialize Variable**: `extracted_ok` is now initialized to `False` *before* the context processing loop in `src/cineripr/core/archives.py`.
- This ensures the variable is always defined, even if the loop is skipped.

### 🔧 Geänderte Dateien
- **`src/cineripr/core/archives.py`**: Initialization of `extracted_ok` added.

---

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

## Session Notes - SettingsDB Syntax Fix (2026-02-13)

### 🐛 Problem
- **SyntaxError**: `unterminated triple-quoted string literal` in `src/cineripr/web/settings_db.py`.
- The error was detected at the end of the file or at random locations, but was caused by invisible characters or corrupted docstrings/SQL strings througout the file.
- A duplicate `conn.execute("""` block in `_init_db` was also found and fixed.

### ✅ Solution
- **Removed all docstrings** from `settings_db.py` methods to eliminate potential invisible characters.
- **Replaced all triple-quoted SQL strings** with standard strings (concatenated) to avoid parser confusion.
- **Fixed duplicate code** in `_init_db`.
- **Restored corrupted function body** for `load_history`.

### 🔧 Geänderte Dateien
- **`src/cineripr/web/settings_db.py`**: Massive cleanup of strings and docstrings.

