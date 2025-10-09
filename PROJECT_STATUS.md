# CineRipR - Project Status & Context

## Aktueller Stand (Version 1.0.18)

**Letzter Commit**: `fc16f27` - "Release 1.0.18: Fix read-only filesystem support, subpath validation, and Docker permissions"

## Was das Tool macht

CineRipR ist ein automatisiertes Tool zum Extrahieren von Multi-Part Downloads und zur Bereinigung von Finished-Ordnern für Medienbibliotheken.

### Hauptfunktionen:
1. **Archive-Extraktion**: Extrahiert RAR, ZIP und andere Archive
2. **Datei-Organisation**: Organisiert extrahierte Dateien in TV-Shows/Movies Struktur
3. **Finished-Bereinigung**: Verschiebt verarbeitete Archive in Finished-Ordner
4. **Docker-Support**: Funktioniert in Docker-Containern (besonders Unraid)

## Wichtige Fixes die implementiert wurden

### Version 1.0.18 (Aktuell)
- **Read-only File System Support**: Behebt kritische Fehler beim Verschieben von Dateien auf schreibgeschützten Dateisystemen (errno 30)
- **Subpath Validation Error**: Behebt persistente "is not in the subpath" Fehler
- **Docker Permissions**: Setzt korrekte Dateiberechtigungen (777) und Gruppenzugehörigkeit ('users')
- **Cross-platform Compatibility**: Verbesserte Kompatibilität zwischen Unix/Linux und Windows

### Version 1.0.17
- **Subpath Validation Error**: Behebt "is not in the subpath" Fehler bei der Verarbeitung extrahierter Dateien
- **Archive Moving Logic**: Korrigiert die Archive- und Datei-Verschiebelogik

### Version 1.0.16
- **Finished Directory Structure**: Behebt unerwünschte "Movies" Unterordner-Erstellung
- **Release Name Logic**: Verwendet nur Release-Namen statt vollständiger Pfadstruktur

## Technische Details

### Dateiberechtigungen
- **777 Berechtigungen**: Alle extrahierten/verschobenen Dateien erhalten 777 Berechtigungen
- **Gruppe 'users'**: Dateien werden der Gruppe 'users' zugewiesen
- **Cross-platform**: Funktioniert sowohl unter Windows als auch Unix/Linux

### Docker-Support
- **Unraid-kompatibel**: Speziell für Unraid Docker Container optimiert
- **Read-only Filesystem**: Fallback auf Copy+Delete bei schreibgeschützten Dateisystemen
- **Berechtigungen**: Automatische Berechtigungskorrektur für Container-Umgebungen

### Pfad-Handling
- **Subpath Validation**: Robuste Pfad-Validierung verhindert "is not in the subpath" Fehler
- **Release Name Extraction**: Intelligente Extraktion von Release-Namen aus Pfaden
- **Fallback Logic**: Mehrere Fallback-Strategien für Edge Cases

## Wichtige Regeln & Logik

### Release-Erstellung
- **Titel-Format**: "CineRipR X.X.X" (z.B. "CineRipR 1.0.18")
- **Keine zusätzlichen Beschreibungen**: Einfach nur "Release X.X.X" als Commit-Message
- **GitHub Release**: Erstelle sowohl Git Tag als auch GitHub Release

### Datei-Operationen
- **Move-First**: Versuche zuerst normale Move-Operation
- **Copy+Delete Fallback**: Bei Fehlern verwende Copy+Delete
- **Permission Fix**: Setze immer 777 + 'users' Gruppe nach Move/Copy
- **Error Handling**: Graceful Degradation bei Fehlern

### Pfad-Struktur
- **Finished Directory**: `finished/ReleaseName/` (nicht `finished/Movies/ReleaseName/`)
- **Extracted Directory**: `extracted/TV-Shows/ShowName/Season XX/` oder `extracted/Movies/MovieName/`
- **Release Name**: Nur der letzte Teil des Pfades, nicht die vollständige Struktur

## Bekannte Probleme & Lösungen

### Read-only File System (errno 30)
- **Problem**: Dateien können nicht verschoben werden
- **Lösung**: Fallback auf Copy+Delete mit Warnung im Log

### Subpath Validation Error
- **Problem**: `/data/extracted/TV-Shows/Release` ist nicht in `/data/downloads`
- **Lösung**: Robuste Pfad-Parsing mit Fallback-Strategien

### Docker Permissions
- **Problem**: Dateien werden mit falschen Berechtigungen erstellt
- **Lösung**: Automatische 777 + 'users' Gruppe nach jeder Operation

## Aktuelle Probleme

### Unraid Docker Container
- **Status**: Das Verschieben von Dateien nach "finished" funktioniert unter Windows einwandfrei
- **Problem**: In Unraid Docker Containern funktioniert es nicht
- **Nächster Schritt**: Docker-spezifische Debugging und Fixes

## Wichtige Dateien

### Core Files
- `src/cineripr/archives.py`: Hauptlogik für Archive-Verarbeitung
- `src/cineripr/file_operations.py`: Datei-Operationen und Berechtigungen
- `src/cineripr/path_utils.py`: Pfad-Utilities und TV-Show-Organisation
- `src/cineripr/config.py`: Konfiguration und Pfad-Management

### Configuration
- `pyproject.toml`: Projekt-Konfiguration und Version
- `src/cineripr/__init__.py`: Version-Information
- `cineripr.toml`: Benutzer-Konfiguration

## Nächste Schritte

1. **Docker-Unraid Problem lösen**: Das Verschieben von Dateien in Unraid Docker Containern
2. **Testing**: Verifikation dass alle Fixes in verschiedenen Umgebungen funktionieren
3. **Documentation**: Weitere Verbesserung der Dokumentation

## Wichtige Commands

### Release erstellen
```bash
# Version in pyproject.toml und __init__.py aktualisieren
git add .
git commit -m "Release X.X.X"
git push origin main
gh release create vX.X.X --title "CineRipR X.X.X"
```

### Debugging
- Logs zeigen detaillierte Informationen über Move-Operationen
- Docker-Umgebung wird automatisch erkannt
- Fehlermeldungen enthalten spezifische Details für Troubleshooting

---

**Letzte Aktualisierung**: Nach Reset auf Version 1.0.18
**Nächste Session**: Weiterarbeit am Docker-Unraid Problem
