# Docker-Berechtigungen - Lösung

## Problem
Wenn Cineripr in einem Docker-Container läuft, werden extrahierte Dateien oft mit falschen Berechtigungen erstellt (schreibgeschützt für normale Benutzer).

## Ursache
- Docker-Container läuft standardmäßig als `root`
- Extrahierte Dateien werden mit root-Berechtigungen erstellt
- Auf dem Host-System sind diese Dateien dann schreibgeschützt

## Lösung

### 1. Dockerfile-Verbesserungen
Das Dockerfile wurde erweitert um:
- **Non-root User**: Erstellt einen `cineripr`-Benutzer
- **UMASK**: Setzt `UMASK=002` für bessere Standard-Berechtigungen
- **User Switch**: Container läuft als `cineripr` statt `root`

### 2. Code-seitige Berechtigungskorrektur
- **`fix_file_permissions()`**: Neue Funktion korrigiert Berechtigungen nach Extraktion
- **Automatische Anwendung**: Wird nach jeder erfolgreichen Extraktion aufgerufen
- **Berechtigungen**: 
  - Dateien: `644` (rw-r--r--)
  - Verzeichnisse: `755` (rwxr-xr-x)

## Verwendung

### Docker-Container neu bauen:
```bash
docker build -t cineripr:latest .
```

### Container ausführen:
```bash
docker run --rm \
  -v /pfad/zu/downloads:/data/downloads:ro \
  -v /pfad/zu/extracted:/data/extracted \
  -v /pfad/zu/finished:/data/finished \
  -v /pfad/zu/cineripr.toml:/config/cineripr.toml:ro \
  cineripr:latest \
  --config /config/cineripr.toml
```

## Berechtigungen nach der Lösung

### Vorher:
```
-rw-r--r-- 1 root root 46G extracted/movie.mkv
```

### Nachher:
```
-rw-r--r-- 1 cineripr cineripr 46G extracted/movie.mkv
```

## Zusätzliche Optionen

### Benutzer-ID anpassen:
Falls Sie eine spezifische Benutzer-ID benötigen:
```bash
docker run --rm \
  --user $(id -u):$(id -g) \
  -v /pfad/zu/downloads:/data/downloads:ro \
  -v /pfad/zu/extracted:/data/extracted \
  -v /pfad/zu/finished:/data/finished \
  cineripr:latest
```

### Berechtigungen manuell korrigieren:
Falls bereits Dateien mit falschen Berechtigungen existieren:
```bash
# Alle Dateien in extracted-Ordner korrigieren
find /pfad/zu/extracted -type f -exec chmod 644 {} \;
find /pfad/zu/extracted -type d -exec chmod 755 {} \;

# Besitzer ändern (falls nötig)
sudo chown -R $USER:$USER /pfad/zu/extracted
```

## Technische Details

### UMASK-Werte:
- `002`: Dateien werden mit 664, Verzeichnisse mit 775 erstellt
- `022`: Dateien werden mit 644, Verzeichnisse mit 755 erstellt (Standard)

### Berechtigungsmodi:
- `644`: rw-r--r-- (Dateien)
- `755`: rwxr-xr-x (Verzeichnisse)
- `664`: rw-rw-r-- (Dateien mit Gruppen-Schreibzugriff)

Die Lösung stellt sicher, dass alle extrahierten Dateien für normale Benutzer lesbar und beschreibbar sind.
