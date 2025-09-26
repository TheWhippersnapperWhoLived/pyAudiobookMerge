# cover_art.py
import os
import base64
from PIL import Image
from logger import info, warning, error

SUPPORTED_FORMATS = [".jpg", ".jpeg", ".png"]

# Prefer common cover filenames first
PREFERRED_NAMES = [
    "cover", "album_art", "albumart", "folder", "front"
]

def find_cover_art(folder: str) -> str:
    """
    Search for cover art in the folder.
    Prefer common names (cover.jpg, album_art.png, folder.jpg, etc.),
    otherwise return the first supported image found.
    """
    if not folder or not os.path.isdir(folder):
        return None

    # First pass: preferred names
    for name in PREFERRED_NAMES:
        for ext in SUPPORTED_FORMATS:
            candidate = os.path.join(folder, f"{name}{ext}")
            if os.path.isfile(candidate):
                return candidate

    # Second pass: any supported image
    for file in sorted(os.listdir(folder)):
        _, ext = os.path.splitext(file)
        if ext.lower() in SUPPORTED_FORMATS:
            cover_path = os.path.join(folder, file)
            return cover_path

    warning(f"No cover art found in '{folder}'.")
    return None


def generate_vorbis_picture_tag(image_path: str) -> str:
    """
    Generate a METADATA_BLOCK_PICTURE VorbisComment value (Base64-encoded)
    using the FLAC/ogg picture binary structure, suitable for ffmetadata.

    Returns:
        base64 string or None on failure.
    """
    try:
        # Read raw image bytes
        with open(image_path, "rb") as f:
            image_data = f.read()

        # Use PIL to get format and size/mode
        with Image.open(image_path) as img:
            width, height = img.size
            img_mode = img.mode
            # Bits per pixel depth:
            if img_mode == "RGBA":
                depth = 32
            elif img_mode == "RGB":
                depth = 24
            elif img_mode in ("LA", "LA;16"):
                depth = 16
            else:
                # grayscale/others
                depth = 8
            colors = 0  # typically 0 for non-paletted

            pil_format = (img.format or "").upper()

        # Determine MIME type from PIL format, fallback to extension
        if pil_format == "JPEG" or image_path.lower().endswith((".jpg", ".jpeg")):
            mime_type = b"image/jpeg"
        elif pil_format == "PNG" or image_path.lower().endswith(".png"):
            mime_type = b"image/png"
        else:
            # fallback
            mime_type = b"image/jpeg" if image_path.lower().endswith((".jpg", ".jpeg")) else b"image/png"

        picture_type = 3  # front cover
        description = b""  # empty description is fine

        # Build binary picture block (FLAC-style)
        block = b""
        block += picture_type.to_bytes(4, "big")
        block += len(mime_type).to_bytes(4, "big") + mime_type
        block += len(description).to_bytes(4, "big") + description
        block += width.to_bytes(4, "big")
        block += height.to_bytes(4, "big")
        block += depth.to_bytes(4, "big")
        block += colors.to_bytes(4, "big")
        block += len(image_data).to_bytes(4, "big") + image_data

        # Base64 encode (ascii-safe)
        b64 = base64.b64encode(block).decode("ascii")
        return b64

    except Exception as e:
        error(f"Failed to generate Vorbis picture tag: {e}")
        return None


def get_cover_art_for_audiobook(folder: str) -> str:
    """Wrapper to return the chosen cover art path or None."""
    return find_cover_art(folder)
