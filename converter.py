# converter.py
import os
import subprocess
from logger import info, warning, error
from cover_art import find_cover_art, generate_vorbis_picture_tag

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
    metadata_file = None
    vorbis_picture_file = None

    # Determine container type
    _, ext = os.path.splitext(output_file)
    ext = ext.lower()
    is_m4b = ext in [".m4b", ".m4a"]
    is_opus = ext in [".ogg", ".opus"] or (preset.get("codec") == "libopus")
    is_mp3 = ext == ".mp3"

    # Write MP3 file list
    try:
        with open(temp_list_file, "w", encoding="utf-8") as f:
            for mp3 in mp3_files:
                path = os.path.abspath(mp3).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path}'\n")
    except Exception as e:
        error(f"Failed to write temp file list: {e}")
        return False

    # Chapters metadata for FFmpeg
    if chapters:
        metadata_file = "ffmetadata.txt"
        try:
            with open(metadata_file, "w", encoding="utf-8") as f:
                f.write(";FFMETADATA1\n")
                start_time = 0.0
                for chapter in chapters:
                    duration = os.path.getsize(chapter['file']) / (128000 / 8)  # rough estimate
                    if is_opus:
                        start_ms = int(start_time * 1000)
                        end_ms = int((start_time + duration) * 1000)
                        f.write("[CHAPTER]\nTIMEBASE=1/1000\n")
                        f.write(f"START={start_ms}\nEND={end_ms}\n")
                        f.write(f"title={chapter['title']}\n")
                    else:
                        f.write("[CHAPTER]\nTIMEBASE=1/1\n")
                        f.write(f"START={int(start_time)}\nEND={int(start_time + duration)}\n")
                        f.write(f"title={chapter['title']}\n")
                    start_time += duration
        except Exception as e:
            warning(f"Failed to create chapter metadata: {e}")
            metadata_file = None

    # Cover art
    cover_art_path = find_cover_art(folder) if folder else None
    if cover_art_path:
        info(f"Found cover art: {cover_art_path}")
    if is_opus and cover_art_path:
        # For OGG/Opus, generate a temporary Vorbis picture file
        try:
            b64_tag = generate_vorbis_picture_tag(cover_art_path)
            vorbis_picture_file = "vorbis_picture.txt"
            with open(vorbis_picture_file, "w", encoding="utf-8") as f:
                f.write(f"METADATA_BLOCK_PICTURE={b64_tag}\n")
        except Exception as e:
            warning(f"Failed to generate Vorbis picture: {e}")
            vorbis_picture_file = None

    # Build FFmpeg command
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", temp_list_file]

    input_idx = 1  # next input index

    if metadata_file:
        cmd.extend(["-i", metadata_file])
        metadata_input_idx = input_idx
        input_idx += 1
    else:
        metadata_input_idx = None

    if is_mp3 or is_m4b:
        if cover_art_path:
            cmd.extend(["-i", cover_art_path])
            cover_art_idx = input_idx
            input_idx += 1
        else:
            cover_art_idx = None
    elif is_opus:
        if vorbis_picture_file:
            cmd.extend(["-i", vorbis_picture_file])
            metadata_input_idx = input_idx  # Vorbis picture counts as metadata
            input_idx += 1

    # Stream mapping
    cmd.extend(["-map", "0:a"])  # audio
    if cover_art_path and (is_mp3 or is_m4b):
        cmd.extend(["-map", f"{cover_art_idx}:v"])
    if metadata_input_idx is not None:
        cmd.extend(["-map_metadata", str(metadata_input_idx)])

    # Audio codec
    if preset.get("codec") != "copy":
        cmd.extend(["-c:a", preset["codec"]])
        if preset.get("bitrate"):
            cmd.extend(["-b:a", preset["bitrate"]])
        if preset.get("channels"):
            cmd.extend(["-ac", str(preset["channels"])])
    else:
        cmd.extend(["-c:a", "copy"])

    # Cover art for MP3/M4B
    if cover_art_path and (is_mp3 or is_m4b):
        cmd.extend(["-c:v", "mjpeg", "-disposition:v", "attached_pic"])
        if is_mp3:
            cmd.extend(["-id3v2_version", "3"])

    # Metadata tags
    if metadata:
        for key, value in metadata.items():
            if value:
                cmd.extend(["-metadata", f"{key}={value}"])

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
        for f in [temp_list_file, metadata_file, vorbis_picture_file]:
            if f and os.path.exists(f):
                os.remove(f)
                info(f"Removed temporary file: {f}")
