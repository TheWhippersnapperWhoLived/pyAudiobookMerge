# file_discovery.py
import os
from logger import info, warning, error

SUPPORTED_EXTENSIONS = [".mp3"]

def find_subfolders(base_folder: str):
    """
    Return a list of all subfolders in the base folder that contain MP3 files.
    """
    subfolders = []
    for root, dirs, files in os.walk(base_folder):
        if any(f.lower().endswith(".mp3") for f in files):
            subfolders.append(root)
    if not subfolders:
        warning(f"No MP3 files found in '{base_folder}'.")
    else:
        info(f"Found {len(subfolders)} subfolder(s) with MP3 files.")
    return subfolders

def get_mp3_files(folder: str):
    """
    Return a sorted list of MP3 files in a folder.
    """
    try:
        files = [f for f in os.listdir(folder) if f.lower().endswith(".mp3")]
        files.sort()  # Sorting ensures correct chapter order
        if not files:
            warning(f"No MP3 files found in '{folder}'.")
        return [os.path.join(folder, f) for f in files]
    except Exception as e:
        error(f"Error reading folder '{folder}': {e}")
        return []

def validate_mp3_file(file_path: str):
    """
    Simple validation to check if the MP3 file exists and is non-empty.
    """
    if not os.path.exists(file_path):
        warning(f"File does not exist: {file_path}")
        return False
    if os.path.getsize(file_path) == 0:
        warning(f"File is empty: {file_path}")
        return False
    return True

def validate_mp3_files(file_list: list):
    """
    Validate a list of MP3 files.
    Returns a list of valid files.
    """
    valid_files = []
    for f in file_list:
        if validate_mp3_file(f):
            valid_files.append(f)
    return valid_files
