"""TMDB API integration for retrieving movie metadata."""

from __future__ import annotations

import logging
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Optional

_logger = logging.getLogger(__name__)

TMDB_BASE_URL = "https://api.themoviedb.org/3"

class TMDbClient:
    """Client for interactions with the TMDB API."""

    def __init__(self, api_token: str):
        """Initialize the client with an API read access token."""
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json;charset=utf-8",
        }

    def search_movie(self, title: str, year: str | None = None) -> int | None:
        """Search for a movie by title and optional year.

        Args:
            title: Movie title to search for.
            year: Optional release year to refine search.

        Returns:
            TMDB ID of the first match, or None if not found.
        """
        url = f"{TMDB_BASE_URL}/search/movie"
        params = {"query": title, "language": "de-DE", "include_adult": "true"}
        if year:
            params["year"] = year

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            
            if results:
                # Return the ID of the first result (most relevant)
                return results[0]["id"]
            
            _logger.debug("No TMDB results found for '%s' (year: %s)", title, year)
            return None
            
        except requests.RequestException as e:
            _logger.error("TMDB search failed for '%s': %s", title, e)
            return None

    def get_movie_details(self, tmdb_id: int) -> Dict[str, Any] | None:
        """Fetch detailed metadata for a movie by TMDB ID.

        Args:
            tmdb_id: The TMDB movie ID.

        Returns:
            Dictionary with movie details, or None if request fails.
        """
        url = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
        params = {
            "language": "de-DE",
            "append_to_response": "credits,release_dates"
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            _logger.error("Failed to get TMDB details for ID %s: %s", tmdb_id, e)
            return None

    def create_nfo(self, movie_data: Dict[str, Any], output_path: Path) -> bool:
        """Create a Kodi/Emby compatible NFO file from movie data.

        Args:
            movie_data: Dictionary containing TMDB movie details.
            output_path: Path where the .nfo file should be saved.

        Returns:
            True if successful, False otherwise.
        """
        try:
            root = ET.Element("movie")
            
            # Helper to add simple text elements
            def add_elem(parent, tag, text):
                if text:
                    elem = ET.SubElement(parent, tag)
                    elem.text = str(text)

            add_elem(root, "title", movie_data.get("title"))
            add_elem(root, "originaltitle", movie_data.get("original_title"))
            add_elem(root, "sorttitle", movie_data.get("title"))
            
            rating = movie_data.get("vote_average")
            if rating:
                add_elem(root, "rating", str(rating))
                add_elem(root, "userrating", str(rating))
            
            add_elem(root, "year", movie_data.get("release_date", "")[:4])
            add_elem(root, "plot", movie_data.get("overview"))
            add_elem(root, "tagline", movie_data.get("tagline"))
            add_elem(root, "runtime", movie_data.get("runtime"))
            add_elem(root, "mpaa", self._get_certification(movie_data))
            
            # IDs
            add_elem(root, "id", movie_data.get("imdb_id"))
            add_elem(root, "tmdbid", movie_data.get("id"))
            uniqueid_tmdb = ET.SubElement(root, "uniqueid", type="tmdb", default="true")
            uniqueid_tmdb.text = str(movie_data.get("id"))
            if movie_data.get("imdb_id"):
                uniqueid_imdb = ET.SubElement(root, "uniqueid", type="imdb")
                uniqueid_imdb.text = movie_data.get("imdb_id")

            # Genres
            for genre in movie_data.get("genres", []):
                add_elem(root, "genre", genre.get("name"))

            # Credits
            credits = movie_data.get("credits", {})
            for cast in credits.get("cast", [])[:15]: # Limit cast to top 15
                actor_elem = ET.SubElement(root, "actor")
                add_elem(actor_elem, "name", cast.get("name"))
                add_elem(actor_elem, "role", cast.get("character"))
                if cast.get("profile_path"):
                    add_elem(actor_elem, "thumb", f"https://image.tmdb.org/t/p/original{cast.get('profile_path')}")

            for crew in credits.get("crew", []):
                if crew.get("job") == "Director":
                    add_elem(root, "director", crew.get("name"))
                elif crew.get("job") == "Writer" or crew.get("job") == "Screenplay":
                    add_elem(root, "writer", crew.get("name"))

            # Save XML
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ", level=0)
            
            # Ensure output file has .nfo extension
            if output_path.suffix.lower() != ".nfo":
                output_path = output_path.with_suffix(".nfo")
                
            tree.write(output_path, encoding="utf-8", xml_declaration=True)
            _logger.info("Created NFO file at: %s", output_path)
            return True

        except Exception as e:
            _logger.error("Failed to create NFO file: %s", e)
            return False

    def _get_certification(self, movie_data: Dict[str, Any]) -> str:
        """Extract German certification (FSK) or fall back to US."""
        release_dates = movie_data.get("release_dates", {}).get("results", [])
        
        # Try German certification first
        for country in release_dates:
            if country["iso_3166_1"] == "DE":
                for release in country["release_dates"]:
                    if release.get("certification"):
                        return f"FSK {release['certification']}"
        
        # Fallback to US
        for country in release_dates:
            if country["iso_3166_1"] == "US":
                for release in country["release_dates"]:
                    if release.get("certification"):
                        return release['certification']
                        
        return ""

    def search_tv_show(self, query: str) -> int | None:
        """Search for a TV show by title.

        Args:
            query: TV show title to search for.

        Returns:
            TMDB ID of the first match, or None if not found.
        """
        url = f"{TMDB_BASE_URL}/search/tv"
        params = {"query": query, "language": "de-DE", "include_adult": "true"}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            
            if results:
                return results[0]["id"]
            
            _logger.debug("No TMDB results found for TV show '%s'", query)
            return None
            
        except requests.RequestException as e:
            _logger.error("TMDB TV search failed for '%s': %s", query, e)
            return None

    def get_episode_details(self, tv_id: int, season: int, episode: int) -> Dict[str, Any] | None:
        """Fetch details for a specific TV show episode.

        Args:
            tv_id: The TMDB TV show ID.
            season: Season number.
            episode: Episode number.

        Returns:
            Dictionary with episode details, or None if request fails.
        """
        url = f"{TMDB_BASE_URL}/tv/{tv_id}/season/{season}/episode/{episode}"
        params = {"language": "de-DE"}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            _logger.error("Failed to get TMDB episode details for ID %s S%sE%s: %s", tv_id, season, episode, e)
            return None

    def create_episode_nfo(self, episode_data: Dict[str, Any], show_name: str, output_path: Path) -> bool:
        """Create a Kodi/Emby compatible NFO file for an episode.

        Args:
            episode_data: Dictionary containing TMDB episode details.
            show_name: Name of the TV show (since episode data might not have it).
            output_path: Path where the .info file should be saved.

        Returns:
            True if successful, False otherwise.
        """
        try:
            root = ET.Element("episodedetails")
            
            # Helper to add simple text elements
            def add_elem(parent, tag, text):
                if text:
                    elem = ET.SubElement(parent, tag)
                    elem.text = str(text)

            add_elem(root, "title", episode_data.get("name"))
            add_elem(root, "showtitle", show_name)
            
            rating = episode_data.get("vote_average")
            if rating:
                add_elem(root, "rating", str(rating))
                add_elem(root, "userrating", str(rating))
            
            add_elem(root, "season", str(episode_data.get("season_number")))
            add_elem(root, "episode", str(episode_data.get("episode_number")))
            add_elem(root, "plot", episode_data.get("overview"))
            add_elem(root, "aired", episode_data.get("air_date"))
            add_elem(root, "runtime", str(episode_data.get("runtime")))
            
            # IDs
            if episode_data.get("id"):
                add_elem(root, "id", str(episode_data.get("id")))
                add_elem(root, "tmdbid", str(episode_data.get("id")))
                uniqueid = ET.SubElement(root, "uniqueid", type="tmdb", default="true")
                uniqueid.text = str(episode_data.get("id"))

            # Credits (Guest Stars / Crew)
            for guest in episode_data.get("guest_stars", [])[:10]:
                actor_elem = ET.SubElement(root, "actor")
                add_elem(actor_elem, "name", guest.get("name"))
                add_elem(actor_elem, "role", guest.get("character"))
                if guest.get("profile_path"):
                    add_elem(actor_elem, "thumb", f"https://image.tmdb.org/t/p/original{guest.get('profile_path')}")

            # Save XML
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ", level=0)
            
            # Ensure output file has .nfo extension
            if output_path.suffix.lower() != ".nfo":
                output_path = output_path.with_suffix(".nfo")
                
            tree.write(output_path, encoding="utf-8", xml_declaration=True)
            _logger.info("Created Episode NFO file at: %s", output_path)
            return True

        except Exception as e:
            _logger.error("Failed to create Episode NFO file: %s", e)
            return False
