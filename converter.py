# converter.py
import os
import subprocess
from logger import info, warning, error

def convert_to_audiobook(
    mp3_files: list,
    output_file: str,
    preset: dict,
    metadata: dict = None,
    cover_art: str = None,
    chapters: list = None
):
    """
    Convert MP3 files into an audiobook (M4B or Opus) with chapters and metadata.
    """
    if not mp3_files:
        warning("No MP3 files provided for conversion.")
        return False

    temp_list_file = "temp_file_list.txt"
    metadata_file = None

        # Determine container type
    _, ext = os.path.splitext(output_file)
    ext = ext.lower()
    is_m4b = ext in [".m4b", ".m4a"]
    is_opus = ext == ".opus"

    # If using Copy, keep input container
    if preset.get("codec") == "copy":
        # Use the same container as the first MP3 file
        input_ext = os.path.splitext(mp3_files[0])[1].lower()
        output_file = os.path.splitext(output_file)[0] + input_ext
        info(f"Copy preset selected, keeping container as {input_ext}")

    # Adjust preset for container
    if is_opus and preset.get("codec") != "libopus":
        warning(f"Switching codec to libopus for Opus container")
        preset["codec"] = "libopus"
    elif is_m4b and preset.get("codec") not in ["aac", "copy"]:
        warning(f"Switching codec to AAC for M4B container")
        preset["codec"] = "aac"
        preset["bitrate"] = "128k"
        preset["channels"] = 2

    try:
        # Write MP3 file list
        with open(temp_list_file, "w", encoding="utf-8") as f:
            for mp3 in mp3_files:
                path = os.path.abspath(mp3).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path}'\n")

        # Create metadata file for chapters
        if chapters:
            metadata_file = "ffmetadata.txt"
            with open(metadata_file, "w", encoding="utf-8") as f:
                f.write(";FFMETADATA1\n")
                start_time = 0.0
                if is_opus:
                    # Vorbis chapters (Opus)
                    f.write(";FFMETADATA1\n")
                    for chapter in chapters:
                        duration = os.path.getsize(chapter['file']) / (128000 / 8)
                        start_ms = int(start_time * 1000)
                        end_ms = int((start_time + duration) * 1000)
                        f.write("[CHAPTER]\n")
                        f.write("TIMEBASE=1/1000\n")
                        f.write(f"START={start_ms}\n")
                        f.write(f"END={end_ms}\n")
                        f.write(f"title={chapter['title']}\n")
                        start_time += duration
                else:
                    # M4B chapters (FFmetadata works)
                    for chapter in chapters:
                        duration = os.path.getsize(chapter['file']) / (128000 / 8)
                        f.write("[CHAPTER]\n")
                        f.write("TIMEBASE=1/1\n")
                        f.write(f"START={int(start_time)}\n")
                        f.write(f"END={int(start_time + duration)}\n")
                        f.write(f"title={chapter['title']}\n")
                        start_time += duration

        # Build FFmpeg command
        cmd = ["ffmpeg", "-y"]

        # Inputs
        cmd.extend(["-f", "concat", "-safe", "0", "-i", temp_list_file])
        if cover_art and is_m4b:
            cmd.extend(["-i", cover_art])
        if chapters:
            cmd.extend(["-i", metadata_file])

        # Stream mapping
        cmd.extend(["-map", "0:a"])
        if cover_art and is_m4b:
            cmd.extend(["-map", "1:v"])
        if chapters:
            cmd.extend(["-map_metadata", str(2 if (cover_art and is_m4b) else 1 if chapters else 0)])

        # Audio codec
        if preset.get("codec") != "copy":
            cmd.extend(["-c:a", preset["codec"]])
            if preset.get("bitrate"):
                cmd.extend(["-b:a", preset["bitrate"]])
            if preset.get("channels"):
                cmd.extend(["-ac", str(preset["channels"])])
        else:
            cmd.extend(["-c:a", "copy"])

        # Cover art options (only for M4B)
        if cover_art and is_m4b:
            cmd.extend(["-c:v", "mjpeg", "-disposition:v", "attached_pic"])

        # Metadata tags
        if metadata:
            for key, value in metadata.items():
                if value:
                    cmd.extend(["-metadata", f"{key}={value}"])

        # Output file
        cmd.append(output_file)

        info(f"Running FFmpeg: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        info(f"Audiobook created successfully: {output_file}")
        return True

    except subprocess.CalledProcessError as e:
        error(f"FFmpeg failed: {e}")
        return False
    except Exception as e:
        error(f"Conversion error: {e}")
        return False
    finally:
        # Clean up temp files
        temp_files = ["temp_file_list.txt", "ffmetadata.txt"]
        
        # Include resized cover if it was created
        if cover_art and cover_art.endswith("_resized.jpg") and os.path.exists(cover_art):
            temp_files.append(cover_art)
        
        for f in temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
                    info(f"Removed temporary file: {f}")
            except Exception as e:
                warning(f"Failed to remove temp file {f}: {e}")

