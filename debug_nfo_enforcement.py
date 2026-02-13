
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
from cineripr.core.tmdb import TMDbClient

logging.basicConfig(level=logging.INFO)

def test_enforcement():
    client = TMDbClient("dummy_token")
    
    # Test Data
    data = {
        "name": "Test Episode",
        "overview": "Test Plot",
        "season_number": 1,
        "episode_number": 1,
        "air_date": "2023-01-01",
        "vote_average": 8.5,
        "id": 12345
    }
    
    # 1. Test Movie enforcement
    target_path = Path("force_test_movie.info")
    print(f"Requesting Movie NFO at: {target_path}")
    client.create_nfo({"title": "Test Movie", "id": 1}, target_path)
    
    if Path("force_test_movie.nfo").exists():
        print("SUCCESS: Movie .info -> .nfo enforcement worked.")
        Path("force_test_movie.nfo").unlink()
    elif Path("force_test_movie.info").exists():
        print("FAILURE: Movie created as .info!")
        Path("force_test_movie.info").unlink()
    else:
        print("FAILURE: No movie file created.")

    # 2. Test Episode enforcement
    target_path = Path("force_test_episode.info")
    print(f"Requesting Episode NFO at: {target_path}")
    client.create_episode_nfo(data, "Test Show", target_path)
    
    if Path("force_test_episode.nfo").exists():
        print("SUCCESS: Episode .info -> .nfo enforcement worked.")
        Path("force_test_episode.nfo").unlink()
    elif Path("force_test_episode.info").exists():
        print("FAILURE: Episode created as .info!")
        Path("force_test_episode.info").unlink()
    else:
        print("FAILURE: No episode file created.")

if __name__ == "__main__":
    test_enforcement()
