
import sys
import logging
from pathlib import Path
import shutil

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))

from cineripr.config import load_settings
from cineripr.core.tmdb import TMDbClient
from cineripr.core.path_utils import parse_tv_show_info

logging.basicConfig(level=logging.INFO)

def test_tv_integration():
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

    print("--- Testing TV Show Parsing ---")
    filename = "Breaking.Bad.S01E01.Pilot.1080p.mkv"
    parsed = parse_tv_show_info(filename)
    print(f"File: {filename} -> Parsed: {parsed}")
    if not parsed or parsed[0] != "Breaking Bad" or parsed[1] != 1 or parsed[2] != 1:
        print("ERROR: Parsing failed.")
        return
    print("SUCCESS: Parsing correct.")

    print("\n--- Testing TMDB API ---")
    client = TMDbClient(api_token)
    
    show_name = parsed[0]
    print(f"Searching for show '{show_name}'...")
    show_id = client.search_tv_show(show_name)
    print(f"Show ID: {show_id}")
    
    if not show_id:
        print("ERROR: Show not found.")
        return

    print(f"Fetching details for S{parsed[1]}E{parsed[2]}...")
    details = client.get_episode_details(show_id, parsed[1], parsed[2])
    
    if details:
        print(f"SUCCESS: Found episode '{details.get('name')}' (Air Date: {details.get('air_date')})")
        
        output_path = Path("Breaking.Bad.S01E01.info")
        print(f"Creating NFO at {output_path}...")
        if client.create_episode_nfo(details, show_name, output_path):
            if output_path.exists():
                print(f"SUCCESS: File created at {output_path}")
                output_path.unlink()
            else:
                print("ERROR: File not created.")
    else:
        print("ERROR: Episode details not found.")

if __name__ == "__main__":
    test_tv_integration()
