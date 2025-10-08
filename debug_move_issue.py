#!/usr/bin/env python3
"""
Debug-Script für das Verschieben-Problem
"""

import logging
from pathlib import Path
import shutil

# Logging konfigurieren
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def debug_move_issue():
    """Debug das Verschieben-Problem"""

    # Beispiel-Pfade (anpassen an Ihre Konfiguration)
    download_path = Path(
        "/data/downloads/Henry.Danger.S05.GERMAN.1080p.WEB.H264-MiSFiTS"
    )
    finished_path = Path(
        "/data/finished/Henry.Danger.S05.GERMAN.1080p.WEB.H264-MiSFiTS"
    )

    print("🔍 Debugging Move Issue")
    print(f"Download Path: {download_path}")
    print(f"Finished Path: {finished_path}")
    print()

    # 1. Prüfe ob Download-Ordner existiert
    if not download_path.exists():
        print("❌ Download-Ordner existiert nicht!")
        return

    # 2. Liste alle Dateien im Download-Ordner
    print("📁 Dateien im Download-Ordner:")
    for item in download_path.iterdir():
        if item.is_file():
            print(f"  📄 {item.name} ({item.stat().st_size} bytes)")
        elif item.is_dir():
            print(f"  📁 {item.name}/")
    print()

    # 3. Prüfe Berechtigungen
    print("🔐 Berechtigungen:")
    try:
        stat_info = download_path.stat()
        print(f"  Download-Ordner: {oct(stat_info.st_mode)}")
        print(f"  Owner: {stat_info.st_uid}, Group: {stat_info.st_gid}")
    except Exception as e:
        print(f"  ❌ Fehler beim Lesen der Berechtigungen: {e}")
    print()

    # 4. Teste Verschieben einer einzelnen Datei
    print("🧪 Teste Verschieben einer Datei:")
    test_file = None
    for item in download_path.iterdir():
        if item.is_file() and item.name.endswith(".rar"):
            test_file = item
            break

    if test_file:
        print(f"  Teste mit: {test_file.name}")

        # Erstelle Ziel-Ordner
        finished_path.mkdir(parents=True, exist_ok=True)
        destination = finished_path / test_file.name

        try:
            # Teste Verschieben
            shutil.move(str(test_file), str(destination))
            print(f"  ✅ Erfolgreich verschoben nach: {destination}")

            # Verschiebe zurück für weiteren Test
            shutil.move(str(destination), str(test_file))
            print(f"  ✅ Zurück verschoben nach: {test_file}")

        except Exception as e:
            print(f"  ❌ Fehler beim Verschieben: {e}")
            print(f"  Fehler-Typ: {type(e).__name__}")
    else:
        print("  ❌ Keine .rar-Datei zum Testen gefunden")

    print()

    # 5. Prüfe Docker-Umgebung
    print("🐳 Docker-Umgebung:")
    try:
        with open("/proc/1/cgroup", "r") as f:
            content = f.read()
            if "docker" in content or "containerd" in content:
                print("  ✅ Läuft in Docker-Container")
            else:
                print("  ❌ Läuft nicht in Docker-Container")
    except:
        print("  ❓ Kann Docker-Status nicht bestimmen")

    # 6. Prüfe verfügbaren Speicherplatz
    print("💾 Speicherplatz:")
    try:
        import shutil

        total, used, free = shutil.disk_usage(finished_path.parent)
        print(f"  Gesamt: {total // (1024**3)} GB")
        print(f"  Verwendet: {used // (1024**3)} GB")
        print(f"  Frei: {free // (1024**3)} GB")
    except Exception as e:
        print(f"  ❌ Fehler beim Prüfen des Speicherplatzes: {e}")


if __name__ == "__main__":
    debug_move_issue()
