# utils.py
import os
import re
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from logger import info, warning
from typing import List, Dict, Tuple

def get_mp3_files(folder: str):
    """Return a sorted list of all MP3 files in a folder."""
    files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".mp3")]
    files.sort()
    return files

def extract_metadata(mp3_file: str):
    """Extract basic metadata from the first MP3 file."""
    try:
        audio = MP3(mp3_file, ID3=EasyID3)
        metadata = {
            "title": audio.get("title", [os.path.splitext(os.path.basename(mp3_file))[0]])[0],
            "author": audio.get("artist", ["Unknown"])[0],
            "narrator": audio.get("albumartist", ["Unknown"])[0],
            "album": audio.get("album", ["Unknown"])[0],
            "genre": audio.get("genre", ["Audiobook"])[0],
            "year": audio.get("date", ["Unknown"])[0]
        }
        return metadata
    except Exception as e:
        warning(f"Failed to extract metadata from {mp3_file}: {e}")
        return {
            "title": os.path.splitext(os.path.basename(mp3_file))[0],
            "author": "Unknown",
            "narrator": "Unknown",
            "album": "Unknown",
            "genre": "Audiobook",
            "year": "Unknown"
        }

def natural_sort_key(s: str):
    """
    Splits the string into text and numbers for natural sorting.
    Example: "11 - Chapter" comes after "2 - Chapter".
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def detect_chapters(mp3_files: list) -> list:
    """
    Detect chapters from a list of audio files.
    Returns [{'title': ..., 'file': ...}, ...]
    """
    if not mp3_files:
        return []

    # Natural sort
    mp3_files.sort(key=lambda f: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', os.path.basename(f))])

    chapters = []
    for f in mp3_files:
        title = os.path.splitext(os.path.basename(f))[0].lstrip("0123456789.-_ ").strip()
        chapters.append({"title": title or os.path.splitext(os.path.basename(f))[0], "file": f})

    return chapters

def find_cover_art(folder):
    """Search for jpg/png cover art in the folder."""
    for ext in [".jpg", ".jpeg", ".png"]:
        for file in os.listdir(folder):
            if file.lower().endswith(ext):
                return os.path.join(folder, file)
    return None

def extract_book_title_from_folder(folder_path: str) -> str:
    """
    Attempts to extract a clean book title from the folder name.
    Example:
        "Book 7 - The Winds of Winter (2025)" -> "The Winds of Winter"
    If the folder does not follow the "Book X - Title (Year)" pattern,
    the full folder name is returned unchanged.
    """
    folder_name = os.path.basename(os.path.normpath(folder_path))

    # Check if folder matches pattern
    if re.match(r'^Book\s*\d+\s*-\s*.*\(\d{4}\)$', folder_name, flags=re.IGNORECASE):
        title = re.sub(r'^Book\s*\d+\s*-\s*', '', folder_name, flags=re.IGNORECASE)
        title = re.sub(r'\s*\(\d{4}\)$', '', title)
        return title.strip()

    # Fallback → just return the folder name
    return folder_name.strip()

