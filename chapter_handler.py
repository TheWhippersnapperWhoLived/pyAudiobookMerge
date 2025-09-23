# chapter_handler.py
import os
import re
from logger import info, warning

def detect_chapters(mp3_files: list):
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

