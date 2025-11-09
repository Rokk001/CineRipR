# CineRipR - Projekt Status & Struktur

## Aktueller Stand (Version 1.0.35)

### ✅ Behobene Probleme
1. **TV-Show-Organisation**: TV-Shows folgen jetzt korrekt der `TV-Shows/Show Name/Season XX/` Struktur
2. **1:1 Download-Struktur Bug**: Behoben - alle Dateien verwenden jetzt die zentrale `move_remaining_to_finished()` Logik
3. **Docker Permission Errors**: Alle `chown` Befehle entfernt - nur noch `chmod 777`
4. **UNC-Pfad-Handling**: Windows UNC-Pfade werden korrekt in Docker-Containern verarbeitet
5. **Private Pfade**: Alle privaten Pfade aus dem Codebase entfernt
6. **Archive Movement Logic**: Korrekte Implementierung – Original-Quelldateien (aus Downloads) werden 1:1 nach `finished/<ReleaseName>/` gespiegelt; extrahierte Inhalte bleiben endgültig in `extracted/`

### 🔖 Entscheidungen (wichtig fürs nächste Mal)
- `extracted` ist der finale, endgültige Zielpfad für extrahierte Inhalte.
- `finished` spiegelt die Download-Quelle 1:1 (alle Dateien/Unterordner) unter `finished/<ReleaseName>/`.
- Keine TV-spezifische Umstrukturierung im `finished`-Pfad.
- Companions (z. B. `Sample`, `Subs`) werden beim Verschieben nach `finished` unverändert übernommen.

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
├── __init__.py              # Version 1.0.29
├── archives.py              # Hauptorchestrierung
├── file_operations.py       # Datei-Operationen
├── path_utils.py            # Pfad-Utilities
├── archive_extraction.py    # Extraktionslogik
├── archive_detection.py     # Archive-Erkennung
├── archive_constants.py     # Konstanten und Regex
├── config.py                # Konfiguration
├── cli.py                   # Command-Line-Interface
├── progress.py              # Progress-Tracking
├── status.py                # Status-Tracking für WebGUI
├── webgui.py                # WebGUI für Status-Monitoring
└── cleanup.py               # Finished-Directory-Cleanup
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
- Version 1.0.35 veröffentlicht mit Major WebGUI Overhaul
- Toast Notifications für Echtzeit-Feedback
- Processing Queue Display zeigt anstehende Arbeit
- Log-Filtering & Search für einfaches Debugging
- System Health Monitoring mit Disk Space Tracking
- Tab-basierte Navigation (Overview, Queue, Health, Logs)
- Favicon mit CineRipR Branding hinzugefügt
- 7-Zip Version wird angezeigt
- Status-Display-Inkonsistenzen behoben
- Komplette Interface-Restrukturierung
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
