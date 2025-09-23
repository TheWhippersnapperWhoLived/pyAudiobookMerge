import os
import glob
import argparse

from presets import get_preset_by_name, list_presets
from file_discovery import get_mp3_files, find_subfolders
from chapter_handler import detect_chapters
from metadata_manager import extract_metadata_from_mp3s as extract_metadata
from cover_art import get_cover_art_for_audiobook
from converter import convert_to_audiobook
from logger import info, warning

# -------------------------------
# Helper functions
# -------------------------------

def prompt_for_preset():
    """Display preset menu and loop until a valid preset is chosen."""
    presets = list_presets()
    
    while True:
        print("\nAvailable presets:\n")
        for idx, name in enumerate(presets, start=1):
            print(f"  {idx}. {name}")
        print()
        
        choice = input("Enter preset number: ").strip()
        
        if not choice:
            print("Please enter a number corresponding to a preset.\n")
            continue
        
        if not choice.isdigit():
            print("Invalid input. Enter a number.\n")
            continue
        
        idx = int(choice)
        if 1 <= idx <= len(presets):
            return presets[idx - 1]
        
        print(f"Invalid number. Enter a number between 1 and {len(presets)}.\n")


def cleanup_temp_files(folder):
    """Remove temporary files generated during conversion."""
    temp_patterns = ["temp_file_list.txt", "ffmetadata.txt", "*_resized.*"]
    for pattern in temp_patterns:
        full_pattern = os.path.join(folder, pattern)
        for temp_file in glob.glob(full_pattern):
            try:
                os.remove(temp_file)
                info(f"Deleted temp file: {temp_file}")
            except Exception as e:
                warning(f"Could not delete temp file {temp_file}: {e}")


def process_all_folders(root_dir, preset_name):
    """Process all subfolders and convert MP3s to audiobooks."""
    
    preset = get_preset_by_name(preset_name)
    if not preset:
        warning(f"Preset '{preset_name}' not found. Falling back to interactive selection.")
        preset_name = prompt_for_preset()
        preset = get_preset_by_name(preset_name)

    subfolders = find_subfolders(root_dir)
    if not subfolders:
        warning("No MP3 subfolders found. Exiting.")
        return

    for folder in subfolders:
        info(f"\nProcessing folder: {folder}")

        mp3_files = get_mp3_files(folder)
        if not mp3_files:
            warning(f"No MP3 files found in {folder}. Skipping.\n")
            continue

        chapters = detect_chapters(mp3_files)
        info(f"Detected {len(chapters)} chapters.")

        metadata = extract_metadata(mp3_files)
        metadata["title"] = os.path.basename(os.path.normpath(folder))  # Keep full folder name

        cover_art = get_cover_art_for_audiobook(folder)  # always full-res
        if cover_art:
            info(f"Found cover art: {cover_art}")

        # Determine output file
        book_title = metadata["title"]
        if preset.get("codec") == "libopus":
            output_file = os.path.join(root_dir, f"{book_title}.ogg")
        elif preset.get("codec") == "copy":
            input_ext = os.path.splitext(mp3_files[0])[1].lower()
            output_file = os.path.join(root_dir, f"{book_title}{input_ext}")
        else:
            output_file = os.path.join(root_dir, f"{book_title}.m4b")

        # pass cover_art to converter
        success = convert_to_audiobook(
            mp3_files=mp3_files,
            output_file=output_file,
            preset=preset,
            metadata=metadata,
            chapters=chapters,
            folder=folder   # 
        )

        # Clean up temp files
        cleanup_temp_files(folder)

        if not success:
            warning(f"Failed to create audiobook for folder: {folder}")
        else:
            info(f"Successfully created audiobook: {output_file}\n")


# -------------------------------
# Main execution
# -------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Batch convert MP3 folders into audiobooks.")
    parser.add_argument("root_dir", nargs='?', help="Root folder containing MP3 subfolders")
    parser.add_argument("-p", "--preset", help="Preset name")
    args = parser.parse_args()

    # --- Root folder handling ---
    if not args.root_dir:
        default_dir = os.getcwd()
        args.root_dir = input(f"Enter root folder containing MP3 subfolders [default: {default_dir}]: ").strip()
        if not args.root_dir:
            args.root_dir = default_dir
            info(f"No folder entered, using current directory: {args.root_dir}")

    # --- Preset handling ---
    if not args.preset or not get_preset_by_name(args.preset):
        args.preset = prompt_for_preset()

    # --- Start processing ---
    process_all_folders(args.root_dir, args.preset)
