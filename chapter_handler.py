# chapter_handler.py
import os
import re
from logger import info, warning

def detect_chapters_from_filenames(mp3_files: list):
    """
    Detect chapters based on MP3 filenames.
    Filenames can have a pattern like '01 - Chapter Title.mp3'.
    Returns a list of dictionaries: [{'title': 'Chapter Title', 'file': 'path/to/file.mp3'}, ...]
    """
    chapters = []
    chapter_pattern = re.compile(r'^\d+\s*[-_]\s*(.+)\.mp3$', re.IGNORECASE)
    
    for f in mp3_files:
        filename = os.path.basename(f)
        match = chapter_pattern.match(filename)
        if match:
            title = match.group(1).strip()
        else:
            title = os.path.splitext(filename)[0]  # Fallback to filename without extension
        chapters.append({"title": title, "file": f})
    
    info(f"Detected {len(chapters)} chapters.")
    return chapters

def load_chapter_mapping(mapping_file: str, mp3_files: list):
    """
    Load a user-provided mapping file (CSV or simple text) mapping filenames to chapter titles.
    Format example (CSV): filename.mp3,Chapter Title
    Returns a list of dictionaries similar to detect_chapters_from_filenames.
    """
    if not os.path.exists(mapping_file):
        warning(f"Mapping file '{mapping_file}' not found. Using filename detection.")
        return detect_chapters_from_filenames(mp3_files)
    
    chapters = []
    file_lookup = {os.path.basename(f): f for f in mp3_files}
    
    try:
        with open(mapping_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or ',' not in line:
                    continue
                filename, title = line.split(',', 1)
                filename = filename.strip()
                title = title.strip()
                file_path = file_lookup.get(filename)
                if file_path:
                    chapters.append({"title": title, "file": file_path})
                else:
                    warning(f"Mapping file references unknown file: {filename}")
        info(f"Loaded {len(chapters)} chapters from mapping file.")
        return chapters
    except Exception as e:
        warning(f"Failed to read mapping file: {e}. Falling back to filename detection.")
        return detect_chapters_from_filenames(mp3_files)
