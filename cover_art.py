# cover_art.py
import os
import base64
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

def generate_vorbis_picture_tag(image_path: str) -> str:
    """
    Generate a METADATA_BLOCK_PICTURE VorbisComment for Ogg/Opus embedding.
    Returns the Base64 string to be added as the value of METADATA_BLOCK_PICTURE.
    """
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()

        picture_type = 3  # front cover
        mime_type = b"image/jpeg" if image_path.lower().endswith((".jpg", ".jpeg")) else b"image/png"
        description = b"Cover Art"

        with Image.open(image_path) as img:
            width, height = img.size
            depth = 24 if img.mode in ("RGB", "RGBA") else 8
            colors = 0

        block = b""
        block += picture_type.to_bytes(4, "big")
        block += len(mime_type).to_bytes(4, "big") + mime_type
        block += len(description).to_bytes(4, "big") + description
        block += width.to_bytes(4, "big")
        block += height.to_bytes(4, "big")
        block += depth.to_bytes(4, "big")
        block += colors.to_bytes(4, "big")
        block += len(image_data).to_bytes(4, "big") + image_data

        return base64.b64encode(block).decode("utf-8")

    except Exception as e:
        error(f"Failed to generate Vorbis picture tag: {e}")
        return None

def get_cover_art_for_audiobook(folder: str) -> str:
    """
    Main function to get cover art path for embedding.
    Returns None if no cover art is found.
    """
    return find_cover_art(folder)
