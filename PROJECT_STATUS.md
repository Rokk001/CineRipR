# CineRipR - Projekt Status & Struktur

## Aktueller Stand (Version 1.0.22)

### ✅ Behobene Probleme
1. **TV-Show-Organisation**: TV-Shows folgen jetzt korrekt der `TV-Shows/Show Name/Season XX/` Struktur
2. **1:1 Download-Struktur Bug**: Behoben - alle Dateien verwenden jetzt die zentrale `move_remaining_to_finished()` Logik
3. **Docker Permission Errors**: Alle `chown` Befehle entfernt - nur noch `chmod 777`
4. **UNC-Pfad-Handling**: Windows UNC-Pfade werden korrekt in Docker-Containern verarbeitet
5. **Private Pfade**: Alle privaten Pfade aus dem Codebase entfernt

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
├── __init__.py              # Version 1.0.22
├── archives.py              # Hauptorchestrierung (972 Zeilen)
├── file_operations.py       # Datei-Operationen (589 Zeilen)
├── path_utils.py            # Pfad-Utilities
├── archive_extraction.py    # Extraktionslogik
├── archive_detection.py     # Archive-Erkennung
├── archive_constants.py     # Konstanten und Regex
├── config.py                # Konfiguration
├── cli.py                   # Command-Line-Interface
└── progress.py              # Progress-Tracking
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
2. **Extract**: Archive in `extracted/` extrahieren
3. **Organize**: TV-Shows/Movies korrekt strukturieren
4. **Move**: Von `extracted/` zu `finished/` mit korrekter Struktur
5. **Cleanup**: Original-Archive zu `finished/` verschieben

### 🐳 Docker-Unterstützung
- **UNC-Pfade**: `\\SERVER\Share\...` → `/data/downloads/...`
- **Read-only Filesystem**: Copy+Delete Fallback
- **Permissions**: Nur `chmod 777`, keine `chown`
- **Safe Move**: Mehrere Retry-Strategien

### 📋 Nächste Schritte (TODO)
1. **Testing**: Aktuelle Version 1.0.22 testen
2. **Performance**: Große Archive-Performance optimieren
3. **Logging**: Verbesserte Debug-Ausgaben
4. **Error Handling**: Robustere Fehlerbehandlung
5. **Documentation**: API-Dokumentation erweitern

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
