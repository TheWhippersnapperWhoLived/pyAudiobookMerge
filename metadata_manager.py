# metadata_manager.py
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from logger import info, warning
from typing import Dict, Optional

DEFAULT_METADATA: Dict[str, Optional[str]] = {
    "title": None,
    "author": None,
    "narrator": None,
    "album": None,
    "genre": None,
    "year": None,
    "comment": None
}

def extract_metadata_from_mp3s(mp3_files: list) -> Dict[str, Optional[str]]:
    """
    Extract metadata from the first MP3 file in the list.
    Fallback to defaults if tags are missing.
    """
    metadata = DEFAULT_METADATA.copy()
    if not mp3_files:
        return metadata

    first_file = mp3_files[0]
    try:
        audio = MP3(first_file, ID3=EasyID3)
        metadata["title"] = audio.get("title", [None])[0]
        metadata["author"] = audio.get("artist", [None])[0]
        metadata["album"] = audio.get("album", [None])[0]
        metadata["genre"] = audio.get("genre", [None])[0]
        metadata["year"] = audio.get("date", [None])[0]
        metadata["comment"] = audio.get("comment", [None])[0]
        # Narrator is usually not stored, so default to Unknown
        metadata["narrator"] = "Unknown"
        info(f"Extracted metadata from MP3: {first_file}")
    except Exception as e:
        warning(f"Failed to extract metadata from {first_file}: {e}")

    # Fallback: if title is missing, use folder name
    if not metadata["title"]:
        metadata["title"] = os.path.basename(os.path.dirname(first_file))
    if not metadata["author"]:
        metadata["author"] = "Unknown"

    return metadata

def validate_metadata(metadata: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
    """Validate essential fields."""
    if not metadata.get("title"):
        warning("Metadata 'title' is missing. Audiobook may not display correctly.")
    if not metadata.get("author"):
        warning("Metadata 'author' is missing. Consider adding author info.")
    return metadata
