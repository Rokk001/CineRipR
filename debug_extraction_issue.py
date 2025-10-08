#!/usr/bin/env python3
"""
Debug script to help diagnose extraction and file system issues
"""

import os
import stat
from pathlib import Path


def check_permissions(path: Path) -> dict:
    """Check file/directory permissions"""
    try:
        stat_info = path.stat()
        return {
            "exists": True,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "readable": os.access(path, os.R_OK),
            "writable": os.access(path, os.W_OK),
            "executable": os.access(path, os.X_OK),
            "mode": oct(stat_info.st_mode),
            "uid": stat_info.st_uid,
            "gid": stat_info.st_gid,
        }
    except Exception as e:
        return {"exists": False, "error": str(e)}


def main():
    print("=== CineRipR File System Debug ===")

    # Check common paths
    paths_to_check = [
        "/data",
        "/data/downloads",
        "/data/extracted",
        "/data/finished",
        "/tmp",
        "/work",
    ]

    for path_str in paths_to_check:
        path = Path(path_str)
        print(f"\n--- {path_str} ---")
        perms = check_permissions(path)
        for key, value in perms.items():
            print(f"  {key}: {value}")

    # Check current working directory
    print(f"\n--- Current Working Directory ---")
    cwd = Path.cwd()
    print(f"  Path: {cwd}")
    perms = check_permissions(cwd)
    for key, value in perms.items():
        print(f"  {key}: {value}")

    # Check environment
    print(f"\n--- Environment ---")
    print(f"  USER: {os.environ.get('USER', 'Not set')}")
    print(f"  UID: {os.getuid()}")
    print(f"  GID: {os.getgid()}")
    print(f"  UMASK: {os.environ.get('UMASK', 'Not set')}")

    # Test write permissions
    print(f"\n--- Write Test ---")
    test_file = Path("/tmp/cineripr_test.txt")
    try:
        test_file.write_text("test")
        print(f"  Write to /tmp: SUCCESS")
        test_file.unlink()
    except Exception as e:
        print(f"  Write to /tmp: FAILED - {e}")

    # Test 7-Zip
    print(f"\n--- 7-Zip Test ---")
    import subprocess

    try:
        result = subprocess.run(["7z"], capture_output=True, text=True, timeout=5)
        print(f"  7-Zip available: YES (exit code: {result.returncode})")
    except Exception as e:
        print(f"  7-Zip available: NO - {e}")


if __name__ == "__main__":
    main()
