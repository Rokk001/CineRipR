
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))

from cineripr.config import load_settings
from cineripr.core.tmdb import TMDbClient

logging.basicConfig(level=logging.INFO)

def test_info_extension():
    try:
        config_path = Path("cineripr.toml")
        if not config_path.exists():
             with open(config_path, "w") as f:
                 f.write('[paths]\ndownload_roots=["."]\nextracted_root="."\nfinished_root="."\n')
        
        settings = load_settings(config_path)
    except Exception:
        pass

    api_token = settings.tmdb_api_token
    if not api_token:
        print("ERROR: TMDB API Token missing.")
        return

    client = TMDbClient(api_token)
    
    # Dummy data
    details = {
        "title": "Test Movie",
        "original_title": "Test Movie Original",
        "release_date": "2023-01-01",
        "overview": "This is a test plot.",
        "id": 12345,
        "imdb_id": "tt1234567"
    }
    
    output_path = Path("test_movie.info")
    print(f"Generating INFO file at {output_path}...")
    
    if client.create_nfo(details, output_path):
        if output_path.exists():
            print(f"SUCCESS: File created at {output_path}")
            output_path.unlink()
        else:
            print(f"ERROR: File not found at expected path {output_path}")
            # Check if .nfo was created instead
            wrong_path = output_path.with_suffix(".nfo")
            if wrong_path.exists():
                print(f"ERROR: File was created with wrong extension: {wrong_path}")
                wrong_path.unlink()
    else:
        print("ERROR: Failed to create file.")

if __name__ == "__main__":
    test_info_extension()
