import os
import sys
import argparse
import subprocess
import logging
from pathlib import Path
import re

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("audiobook_converter.log"),
                              logging.StreamHandler()])

# Define presets
PRESETS = {
    "aac_high": {"codec": "aac", "bitrate": "128k", "channels": 2, "description": "AAC 128 kbps, 2-channel (high-quality stereo)"},
    "opus_low": {"codec": "libopus", "bitrate": "32k", "channels": 1, "description": "Opus 32 kbps, 1-channel (mono, low bitrate)"},
    "opus_std": {"codec": "libopus", "bitrate": "128k", "channels": 2, "description": "Opus 128 kbps, 2-channel (stereo, standard quality)"},
    "copy": {"codec": "copy", "bitrate": None, "channels": None, "description": "Copy / original (fast merge without re-encoding if compatible)"},
}

def find_audiobook_folders(input_dir):
    """
    Finds subfolders containing MP3 files within the input directory.
    Returns a list of paths to these subfolders.
    """
    audiobook_folders = []
    for root, dirs, files in os.walk(input_dir):
        if any(f.lower().endswith('.mp3') for f in files):
            audiobook_folders.append(Path(root))
    return audiobook_folders

def parse_chapters(mp3_files):
    """
    Parses chapter information from MP3 filenames.
    Assumes filenames are like "NN - Chapter Title.mp3" or "NN Chapter Title.mp3".
    Returns a list of chapter dicts, each with 'title' and 'start_time'.
    """
    chapters = []
    current_time = 0.0
    for i, mp3_file in enumerate(mp3_files):
        match = re.match(r"(\d+)[-_\s]+(.*)\.mp3", mp3_file.name, re.IGNORECASE)
        if match:
            chapter_title = match.group(2).strip()
        else:
            chapter_title = f"Chapter {i+1}"

        chapters.append({
            "title": chapter_title,
            "start_time": current_time
        })
        # In a real scenario, we'd need to calculate the duration of each file
        # to accurately set the start_time for the next chapter.
        # For now, we'll just increment by a placeholder value.
        current_time += 1.0 # Placeholder, needs actual duration calculation

    return chapters

def convert_audio(input_files, output_file, preset_name, chapters=None, metadata=None, cover_art_path=None):
    """
    Converts a list of input audio files to a single output file using ffmpeg.
    Optionally embeds chapters, metadata, and cover art.
    """
    preset = PRESETS.get(preset_name)
    if not preset:
        logging.error(f"Unknown preset: {preset_name}")
        return False

    # Check if input files exist
    for f in input_files:
        if not f.exists():
            logging.error(f"Input file not found: {f}")
            return False

    # Construct ffmpeg command
    cmd = ["ffmpeg", "-y"] # -y to overwrite output file if it exists

    # Add input files
    for f in input_files:
        cmd.extend(["-i", str(f)])

    chapter_file_path = None # Initialize to None

    # Add chapter information if provided
    if chapters:
        # Create a temporary file for chapter metadata
        chapter_file_path = Path("temp_chapters.txt")
        try:
            with open(chapter_file_path, "w", encoding="utf-8") as cf:
                for chapter in chapters:
                    # Format: HH:MM:SS.ms
                    # This needs to be formatted correctly. For now, using a placeholder.
                    # A more robust solution would involve calculating actual durations.
                    start_time_str = str(chapter['start_time'])
                    cf.write(f"Chapter ;{chapter['title']}\n")
                    cf.write(f"start ;{start_time_str}\n")
            cmd.extend(["-i", str(chapter_file_path)])
            cmd.extend(["-map_metadata", "1"]) # Map metadata from the chapter file
            cmd.extend(["-map_chapters", "1"]) # Map chapters from the chapter file
        except IOError as e:
            logging.error(f"Error creating temporary chapter file: {e}")
            return False

    # Add cover art if provided
    if cover_art_path:
        if not cover_art_path.exists():
            logging.warning(f"Cover art not found at {cover_art_path}. Skipping cover art embedding.")
        else:
            cmd.extend(["-i", str(cover_art_path)])
            # Map the cover art as the second input stream (index 1)
            # This assumes the cover art is the last input added.
            cmd.extend(["-map", "0:a", "-map", "1:v"]) # Map all audio streams from input 0 and video from input 1
            cmd.extend(["-disposition:v:0", "attached_pic"]) # Attach the first video stream as cover art

    # Add metadata if provided
    if metadata:
        for key, value in metadata.items():
            if value:
                cmd.extend([f"-metadata:{key}", value])

    # Add codec and bitrate options
    if preset["codec"] == "copy":
        cmd.append("-c")
        cmd.append("copy")
    else:
        cmd.extend(["-c:a", preset["codec"]])
        if preset["bitrate"]:
            cmd.extend(["-b:a", preset["bitrate"]])
        if preset["channels"]:
            cmd.extend(["-ac", str(preset["channels"])])

    # Add output file
    cmd.append(str(output_file))

    logging.info(f"Executing ffmpeg command: {' '.join(cmd)}")

    try:
        # Execute ffmpeg command
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Progress monitoring
        total_duration = None
        # Ensure stderr is not None before iterating
        if process.stderr:
            for line in iter(process.stderr.readline, ''):
                if "Duration:" in line:
                    duration_match = re.search(r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})", line)
                    if duration_match:
                        total_duration = duration_match.group(1)
                        logging.info(f"Total duration: {total_duration}")
                
                progress_match = re.search(r"frame=\s*(\d+)\s+fps=\s*(\d+)\s+q=\s*([\d\.]+)\s+Lsize=\s*([\d\.]+)(?:kB)?\s+time=\s*([\d:.]+)\s+bitrate=\s*([\d\.]+)(?:k|M)bits/s", line)
                if progress_match:
                    current_time_str = progress_match.group(5)
                    bitrate = progress_match.group(6)
                    
                    if total_duration:
                        # Calculate percentage
                        try:
                            # Convert HH:MM:SS.ms to seconds
                            h, m, s_ms = map(float, current_time_str.split(':'))
                            current_seconds = h * 3600 + m * 60 + s_ms
                            
                            h_total, m_total, s_ms_total = map(float, total_duration.split(':'))
                            total_seconds = h_total * 3600 + m_total * 60 + s_ms_total
                            
                            percentage = (current_seconds / total_seconds) * 100
                            logging.info(f"Progress: {percentage:.2f}% ({current_time_str}/{total_duration}) - Bitrate: {bitrate}")
                        except ValueError:
                            logging.warning(f"Could not parse time or duration for progress update: time={current_time_str}, duration={total_duration}")
                    else:
                        logging.info(f"Progress: {current_time_str} - Bitrate: {bitrate}")

        stdout, stderr = process.communicate() # Ensure we get the rest of the output

        # Clean up temporary chapter file if it was created
        if chapter_file_path and chapter_file_path.exists():
            try:
                os.remove(chapter_file_path)
            except OSError as e:
                logging.error(f"Error removing temporary chapter file {chapter_file_path}: {e}")

        if process.returncode == 0:
            logging.info(f"Successfully converted to {output_file}")
            return True
        else:
            logging.error(f"ffmpeg failed with error code {process.returncode}:\n{stderr}")
            # Log specific errors if possible from stderr
            if "No such file or directory" in stderr:
                logging.error("ffmpeg error: Input file not found or path incorrect.")
            elif "Invalid data found when processing input" in stderr:
                logging.error("ffmpeg error: Corrupted input file detected.")
            elif "Permission denied" in stderr:
                logging.error("ffmpeg error: Permission denied. Check write permissions for the output directory.")
            return False
    except FileNotFoundError:
        logging.error("ffmpeg command not found. Please ensure ffmpeg is installed and in your PATH.")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during ffmpeg execution: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Convert MP3 files in subfolders to formatted audiobook files.",
        formatter_class=argparse.RawTextHelpFormatter # Use RawTextHelpFormatter for better help text formatting
    )
    parser.add_argument("input_dir", help="Directory containing MP3 files (or subfolders with MP3s).")
    parser.add_argument("-o", "--output_dir", default="output", help="Directory to save the converted audiobook files.")
    
    # Preset selection
    preset_choices = list(PRESETS.keys())
    preset_help = "Audio encoding preset:\n"
    for key, value in PRESETS.items():
        preset_help += f"  {key}: {value['description']}\n"
    parser.add_argument("-p", "--preset", choices=preset_choices, default="aac_high", help=preset_help)
    
    parser.add_argument("-t", "--title", help="Audiobook title (defaults to folder name).")
    parser.add_argument("-a", "--author", help="Audiobook author.")
    parser.add_argument("-n", "--narrator", help="Audiobook narrator.")
    
    # Arguments for custom presets
    parser.add_argument("--custom-codec", help="Custom audio codec (e.g., aac, libopus). Overrides preset codec.")
    parser.add_argument("--custom-bitrate", help="Custom audio bitrate (e.g., 128k). Overrides preset bitrate.")
    parser.add_argument("--custom-channels", type=int, help="Custom number of audio channels (1 for mono, 2 for stereo). Overrides preset channels.")

    args = parser.parse_args()

    # Handle custom preset if provided
    if args.custom_codec or args.custom_bitrate or args.custom_channels:
        custom_preset_config = {}
        if args.custom_codec:
            custom_preset_config["codec"] = args.custom_codec
        if args.custom_bitrate:
            custom_preset_config["bitrate"] = args.custom_bitrate
        if args.custom_channels is not None: # Check for None explicitly as 0 channels is valid
            custom_preset_config["channels"] = args.custom_channels
        
        # Add or update the custom preset
        PRESETS["custom"] = custom_preset_config
        args.preset = "custom" # Force the use of the custom preset

    logging.info(f"Starting audiobook conversion process from '{args.input_dir}' to '{args.output_dir}' using preset '{args.preset}'.")

    audiobook_folders = find_audiobook_folders(args.input_dir)

    if not audiobook_folders:
        logging.warning(f"No subfolders with MP3 files found in '{args.input_dir}'. Exiting.")
        sys.exit(0)

    logging.info(f"Found {len(audiobook_folders)} audiobook folders to process.")

    # Create output directory if it doesn't exist
    try:
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logging.error(f"Error creating output directory {args.output_dir}: {e}")
        sys.exit(1)

    for folder_path in audiobook_folders:
        logging.info(f"Processing folder: {folder_path.name}")

        # Find MP3 files and sort them
        mp3_files = sorted([f for f in folder_path.glob("*.mp3")])

        if not mp3_files:
            logging.warning(f"No MP3 files found in {folder_path}. Skipping.")
            continue

        # Parse chapters
        chapters = parse_chapters(mp3_files)

        # Determine output filename (folder name + .m4a or .mp3 depending on codec)
        # For now, let's assume .m4a for audiobooks
        output_filename = f"{folder_path.name}.m4a"
        output_filepath = Path(args.output_dir) / output_filename

        # Prepare metadata
        metadata = {
            "title": args.title if args.title else folder_path.name,
            "artist": args.author,
            "album_artist": args.narrator, # Using album_artist for narrator as a common practice
            # Add other metadata fields as needed
        }

        # Find cover art
        cover_art_path = None
        for ext in ["jpg", "png"]:
            potential_cover = folder_path / f"album_art.{ext}"
            if potential_cover.exists():
                cover_art_path = potential_cover
                break

        # Convert audio
        if not convert_audio(mp3_files, output_filepath, args.preset, chapters, metadata, cover_art_path):
            logging.error(f"Failed to convert audio for folder: {folder_path.name}")
            # Continue to the next folder even if one fails
            continue

    logging.info("Audiobook conversion process finished.")

if __name__ == "__main__":
    main()