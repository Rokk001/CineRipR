# Development Notes - CineRipR

## Session History & Context

### Letzte Session (2025-01-27)
**Hauptprobleme behoben:**
1. **TV-Show-Organisation**: Falsche 1:1 Download-Struktur → Korrekte TV-Show-Struktur
2. **Docker Permission Errors**: `chown` Befehle entfernt
3. **Private Pfade**: Alle aus Codebase entfernt
4. **UNC-Pfad-Handling**: Windows-Netzwerkpfade in Docker

### Kritische Erkenntnisse
- **Zwei Logiken Problem**: `move_remaining_to_finished()` vs. direkte 1:1 Struktur
- **Docker chown Issue**: `PosixPath` hat kein `chown` Attribut
- **Private Pfade**: Immer generische Beispiele verwenden

### Code-Änderungen (Version 1.0.22)
```python
# VORHER (Bug):
finished_dir = paths.finished_root / release_name  # 1:1 Struktur

# NACHHER (Fix):
move_remaining_to_finished(
    source_dir,
    finished_root=paths.finished_root,
    download_root=download_root,
)  # Korrekte TV-Show-Struktur
```

### Permission Handling
```python
# VORHER (Error):
destination.chown(uid, gid)  # Fehler in Docker

# NACHHER (Fix):
destination.chmod(0o777)  # Nur Berechtigungen, keine Ownership
```

## Architektur-Übersicht

### Core Flow
```
Downloads → Scan → Extract → Organize → Move → Cleanup
    ↓         ↓       ↓         ↓        ↓       ↓
  Archive   Groups  Extracted  TV/Movie Finished Archive
  Files     Found   Files      Structure Files   Files
```

### Wichtige Funktionen
1. **`process_downloads()`**: Hauptorchestrierung
2. **`move_remaining_to_finished()`**: Zentrale finished-Pfad-Logik
3. **`_safe_move_with_retry()`**: Docker-sichere Datei-Operationen
4. **`build_tv_show_path()`**: TV-Show-Pfad-Erstellung

### TV-Show-Detection Logic
```python
def looks_like_tv_show(root: Path) -> bool:
    # Prüft auf:
    # - Season directories (S01, S02, etc.)
    # - TV tags in names (S01E01, etc.)
    # - Episode patterns
```

### Path Building Logic
```python
def build_tv_show_path(base_dir, download_root, base_prefix):
    # Konvertiert:
    # Show.Name.S01.GROUP → TV-Shows/Show Name/Season 01/
```

## Docker-Spezifika

### UNC-Pfad-Handling
```python
def _normalize_path_for_docker(path: Path) -> Path:
    # \\SERVER\Share\path → /data/downloads/path
```

### Safe Move Strategies
1. **Direct Move**: Standard `shutil.move()`
2. **Copy+Delete**: Für read-only filesystems
3. **Normalized Paths**: Für UNC-Pfade in Docker

## Error Patterns & Solutions

### Häufige Fehler
1. **"subpath validation error"**: `Path.relative_to()` auf falschen Pfaden
2. **"read-only file system"**: Docker-Container mit read-only mounts
3. **"PosixPath has no chown"**: Docker-Container ohne chown-Support
4. **"1:1 download structure"**: Falsche Logik in `process_downloads()`

### Lösungsansätze
1. **Try-Catch um `relative_to()`**: Fallback-Pfad-Extraktion
2. **Copy+Delete Fallback**: Für read-only filesystems
3. **Nur chmod, kein chown**: Docker-kompatible Berechtigungen
4. **Zentrale move_remaining_to_finished()**: Konsistente Logik

## Testing Strategy

### Was testen
1. **TV-Show-Organisation**: Korrekte `TV-Shows/Show Name/Season XX/` Struktur
2. **Movie-Organisation**: Korrekte `Movies/Movie.Name.GROUP/` Struktur
3. **Docker-Container**: UNC-Pfade und Berechtigungen
4. **Error-Handling**: Read-only filesystems, fehlende Pfade

### Test-Szenarien
1. **Normale TV-Show**: `Show.Name.S01.GROUP/` → `TV-Shows/Show Name/Season 01/`
2. **Movie**: `Movie.Name.2024.GROUP/` → `Movies/Movie.Name.2024.GROUP/`
3. **Docker UNC**: `\\SERVER\Share\...` → `/data/downloads/...`
4. **Read-only FS**: Copy+Delete Fallback

## Performance Considerations

### Optimierungen
1. **Batch-Processing**: Mehrere Archive gleichzeitig
2. **Progress-Tracking**: Echtzeit-Fortschritt
3. **Error-Recovery**: Teilweise fehlgeschlagene Extraktionen
4. **Memory-Efficiency**: Große Archive ohne Memory-Overflow

### Bottlenecks
1. **Archive-Extraktion**: 7-Zip-Prozess
2. **File-Moves**: Große Dateien
3. **Path-Validation**: Komplexe Pfad-Logik
4. **Docker-Overhead**: Container-Performance

## Code-Quality

### Linting Issues
- **"too general exception"**: Exception-Handling zu breit
- **"cell variable in loop"**: Loop-Variablen-Scope
- **"unused imports"**: Ungenutzte Imports

### Best Practices
1. **Specific Exceptions**: Konkrete Exception-Typen
2. **Proper Scoping**: Loop-Variablen korrekt definieren
3. **Clean Imports**: Nur benötigte Imports
4. **Type Hints**: Vollständige Type-Annotationen

## Release Management

### Versioning
- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Changelog**: Detaillierte Änderungshistorie
- **Git Tags**: `v1.0.22` Format
- **GitHub Releases**: Nur auf explizite Anweisung

### Release Process
1. **Code Changes** → Commit & Push
2. **Version Update** → pyproject.toml & __init__.py
3. **User Testing** → Warten auf Feedback
4. **Release Creation** → Nur auf Anweisung
5. **Documentation** → CHANGELOG.md Update

## Security & Privacy

### Private Path Protection
- **Mandatory Scanning**: Vor jedem Release
- **Generic Examples**: Nur `Show.Name.S01.GROUP` etc.
- **Release Checklist**: Verhindert private Pfad-Exposition
- **Git Template**: Sichere Commit-Messages

### Docker Security
- **Non-root User**: Container läuft als `cineripr` User
- **Minimal Permissions**: Nur notwendige Berechtigungen
- **Read-only Mounts**: Downloads-Verzeichnis read-only
- **UMASK**: Sichere Standard-Berechtigungen

## Next Session Preparation

### Was mitbringen
1. **PROJECT_STATUS.md**: Aktueller Stand
2. **DEVELOPMENT_NOTES.md**: Diese Notizen
3. **CHANGELOG.md**: Änderungshistorie
4. **FINISHED_PATH_LOGIC.md**: Pfad-Logik-Dokumentation

### Mögliche nächste Schritte
1. **Performance Testing**: Große Archive testen
2. **Error Handling**: Robustere Fehlerbehandlung
3. **Logging**: Verbesserte Debug-Ausgaben
4. **Documentation**: API-Dokumentation erweitern
5. **Testing**: Automatisierte Tests erweitern

### Wichtige Dateien im Auge behalten
- **`archives.py`**: Hauptorchestrierung
- **`file_operations.py`**: Datei-Operationen
- **`path_utils.py`**: TV-Show-Logik
- **`config.py`**: Konfiguration
- **`cli.py`**: Command-Line-Interface
