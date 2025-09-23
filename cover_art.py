# cover_art.py
import os
from PIL import Image
from logger import info, warning, error

SUPPORTED_FORMATS = [".jpg", ".jpeg", ".png"]

def find_cover_art(folder: str) -> str:
    """
    Search for cover art in the folder.
    Returns the first matching image path or None if not found.
    """
    for file in os.listdir(folder):
        if os.path.splitext(file)[1].lower() in SUPPORTED_FORMATS:
            cover_path = os.path.join(folder, file)
            info(f"Found cover art: {cover_path}")
            return cover_path
    warning(f"No cover art found in '{folder}'.")
    return None

def resize_cover_art(image_path: str, max_size: tuple = (600, 600)) -> str:
    """
    Resize cover art to fit within max_size, keeping aspect ratio.
    Saves a temporary resized image and returns its path.
    """
    try:
        with Image.open(image_path) as img:
            img.thumbnail(max_size)
            base, ext = os.path.splitext(image_path)
            resized_path = f"{base}_resized{ext}"
            img.save(resized_path)
            info(f"Resized cover art saved to: {resized_path}")
            return resized_path
    except Exception as e:
        error(f"Failed to resize cover art '{image_path}': {e}")
        return image_path  # fallback to original

def get_cover_art_for_audiobook(folder: str, resize: bool = True) -> str:
    """
    Main function to get cover art path for embedding.
    Returns None if no cover art is found.
    """
    cover_path = find_cover_art(folder)
    if cover_path and resize:
        cover_path = resize_cover_art(cover_path)
    return cover_path
