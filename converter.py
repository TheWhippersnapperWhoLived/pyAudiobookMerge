# converter.py
import os
import subprocess
from logger import info, warning, error
from cover_art import find_cover_art, generate_vorbis_picture_tag
from mutagen import File
from mutagen.mp3 import MP3

def convert_to_audiobook(
    mp3_files: list,
    output_file: str,
    preset: dict,
    metadata: dict = None,
    chapters: list = None,
    folder: str = None
):
    """
    Convert MP3 files into an audiobook with chapters, metadata, and cover art.
    Supports M4B/AAC, MP3, and OGG/Opus containers.
    """
    if not mp3_files:
        warning("No MP3 files provided for conversion.")
        return False

    temp_list_file = "temp_file_list.txt"
    metadata_file = "ffmetadata.txt"
    vorbis_picture_tag = None

    # Determine container type
    _, ext = os.path.splitext(output_file)
    ext = ext.lower()
    is_m4b = ext in [".m4b", ".m4a"]
    is_opus = ext in [".ogg", ".opus"] or (preset.get("codec") == "libopus")
    is_mp3 = ext == ".mp3"

    # Write MP3 file list for FFmpeg concat
    try:
        with open(temp_list_file, "w", encoding="utf-8") as f:
            for mp3 in mp3_files:
                path = os.path.abspath(mp3).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path}'\n")
    except Exception as e:
        error(f"Failed to write temp file list: {e}")
        return False

    # Cover art
    cover_art_path = find_cover_art(folder) if folder else None
    if cover_art_path:
        info(f"Found cover art: {cover_art_path}")
        if is_opus:
            vorbis_picture_tag = generate_vorbis_picture_tag(cover_art_path)
            if vorbis_picture_tag:
                info(f"Added Vorbis picture tag to metadata for {cover_art_path}")
            else:
                warning("Failed to generate Vorbis picture tag. Cover art will be skipped.")

        # Chapters and metadata
    if chapters:
        metadata_file = "ffmetadata.txt"
        try:
            with open(metadata_file, "w", encoding="utf-8") as f:
                # Always start with FFmetadata header
                f.write(";FFMETADATA1\n")

                if metadata.get("title"):
                    f.write(f"title={metadata['title']}\n")
                if metadata.get("author"):
                    f.write(f"artist={metadata['author']}\n")  # AAC players use 'artist'
                if metadata.get("album"):
                    f.write(f"album={metadata['album']}\n")
                if metadata.get("genre"):
                    f.write(f"genre={metadata['genre']}\n")
                if metadata.get("year"):
                    f.write(f"date={metadata['year']}\n")
                if metadata.get("comment"):
                    f.write(f"comment={metadata['comment']}\n")

                # For OGG/Opus: put the Vorbis picture tag *first*
                if is_opus and vorbis_picture_tag:
                    f.write(f"METADATA_BLOCK_PICTURE={vorbis_picture_tag}\n")

                start_time = 0.0
                for idx, chapter in enumerate(chapters, start=1):
                    audio = MP3(chapter['file'])
                    duration = audio.info.length

                    if is_opus:
                        # ms precision
                        start_ms = int(start_time * 1000)
                        end_ms = int((start_time + duration) * 1000)

                        f.write("[CHAPTER]\nTIMEBASE=1/1000\n")
                        f.write(f"START={start_ms}\nEND={end_ms}\n")
                        f.write(f"title={chapter['title']}\n")
                    else:
                        # whole seconds
                        start_sec = int(start_time)
                        end_sec = int(start_time + duration)

                        f.write("[CHAPTER]\nTIMEBASE=1/1\n")
                        f.write(f"START={start_sec}\nEND={end_sec}\n")
                        f.write(f"title={chapter['title']}\n")

                    start_time += duration

        except Exception as e:
            error(f"Failed to create chapter metadata: {e}")
            metadata_file = None


    # Build FFmpeg command
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", temp_list_file]

    input_idx = 1  # tracks next input index

    if metadata_file:
        cmd.extend(["-i", metadata_file])
        metadata_input_idx = input_idx
        input_idx += 1
    else:
        metadata_input_idx = None

    cover_art_idx = None
    if cover_art_path and (is_mp3 or is_m4b):
        cmd.extend(["-i", cover_art_path])
        cover_art_idx = input_idx
        input_idx += 1

    # Audio codec
    if preset.get("codec") != "copy":
        cmd.extend(["-c:a", preset["codec"]])
        if preset.get("bitrate"):
            cmd.extend(["-b:a", preset["bitrate"]])
        if preset.get("channels"):
            cmd.extend(["-ac", str(preset["channels"])])
    else:
        cmd.extend(["-c:a", "copy"])

    # Map audio
    cmd.extend(["-map", "0:a"])

    # Map metadata and cover
    if metadata_input_idx is not None and not is_opus:
        # Add metadata
        if metadata.get("title"):
            cmd.extend(["-metadata", f"title={metadata['title']}"])
        if metadata.get("author"):
            cmd.extend(["-metadata", f"artist={metadata['author']}"])  # AAC players use 'artist'
        if metadata.get("album"):
            cmd.extend(["-metadata", f"album={metadata['album']}"])
        if metadata.get("genre"):
            cmd.extend(["-metadata", f"genre={metadata['genre']}"])
        if metadata.get("year"):
            cmd.extend(["-metadata", f"date={metadata['year']}"])
        if metadata.get("comment"):
            cmd.extend(["-metadata", f"comment={metadata['comment']}"])
    else:
        cmd.extend(['-map_metadata', '1'])

    if cover_art_idx is not None:
        cmd.extend(["-map", f"{cover_art_idx}:v"])
        cmd.extend(["-c:v", "mjpeg", "-disposition:v", "attached_pic"])
        if is_mp3:
            cmd.extend(["-id3v2_version", "3"])
    

    # Output
    cmd.append(output_file)

    try:
        info(f"Running FFmpeg: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        info(f"Audiobook created successfully: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        error(f"FFmpeg failed: {e}")
        return False
    finally:
        # Cleanup
        for f in [temp_list_file, metadata_file]:
            if f and os.path.exists(f):
                os.remove(f)
                info(f"Removed temporary file: {f}")
