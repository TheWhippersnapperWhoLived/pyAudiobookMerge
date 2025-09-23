# utils.py
import os
import re
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from logger import info, warning

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

def detect_chapters(mp3_files):
    """
    Detect chapters based on filenames.
    Returns a list of dicts: [{'title': 'Chapter Name', 'file': 'path'}, ...]
    """
    chapters = []
    for mp3 in mp3_files:
        # Remove leading numbers and dashes for a clean title
        base = os.path.basename(mp3)
        title = os.path.splitext(base)[0]
        title = title.lstrip("0123456789.-_ ").strip()
        chapters.append({"title": title, "file": mp3})
    return chapters

def find_cover_art(folder):
    """Search for jpg/png cover art in the folder."""
    for ext in [".jpg", ".jpeg", ".png"]:
        for file in os.listdir(folder):
            if file.lower().endswith(ext):
                return os.path.join(folder, file)
    return None

def extract_book_title_from_folder(folder_path: str):
    """
    Extracts a clean book title from the folder name.
    Example:
        "Book 7 - Harry Potter and the Deathly Hallows (2007)"
        -> "Harry Potter and the Deathly Hallows"
    """
    folder_name = os.path.basename(os.path.normpath(folder_path))

    # Remove leading "Book X - " if present
    title = re.sub(r'^Book\s*\d+\s*-\s*', '', folder_name, flags=re.IGNORECASE)

    # Remove trailing year in parentheses
    title = re.sub(r'\s*\(\d{4}\)$', '', title)

    return title.strip()

