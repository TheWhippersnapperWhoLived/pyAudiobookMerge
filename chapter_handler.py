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

from mutagen.id3 import ID3, CHAP, CTOC, TIT2, Encoding
import logging

log = logging.getLogger(__name__)

def write_mp3_chapters(mp3_file, chapters):
    """
    Add proper ID3v2 chapter frames to an MP3 file using Mutagen.
    `chapters` is a list of dicts: {'title': ..., 'file': ..., 'start_time': ..., 'duration': ...}
    """
    try:
        audio = ID3(mp3_file)

        chap_ids = []
        for idx, chapter in enumerate(chapters, start=1):
            chap_id = f'chp{idx:02d}'
            start_ms = int(chapter['start_time'] * 1000)
            end_ms = int((chapter['start_time'] + chapter['duration']) * 1000)

            # CHAP frame
            chap_frame = CHAP(
                element_id=chap_id,
                start_time=start_ms,
                end_time=end_ms,
                sub_frames=[TIT2(encoding=Encoding.UTF8, text=chapter['title'])]
            )
            audio.add(chap_frame)
            chap_ids.append(chap_id)

            log.info(f"Written MP3 chapter: '{chapter['title']}' -> START={start_ms}ms END={end_ms}ms")

        # CTOC frame (table of contents)
        ctoc = CTOC(
            element_id='toc',
            flags=0,
            child_element_ids=chap_ids,
            sub_frames=[TIT2(encoding=Encoding.UTF8, text='Table of Contents')]
        )
        audio.add(ctoc)

        audio.save(v2_version=3)  # ID3v2.3 for widest compatibility
        log.info(f"MP3 chapters written successfully to {mp3_file}")

    except Exception as e:
        log.warning(f"Failed to write MP3 chapters: {e}")

