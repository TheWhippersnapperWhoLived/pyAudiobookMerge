# presets.py

PRESETS = {
    "Copy / Remux (Fast, Original Container)": {
        "codec": "copy",
        "bitrate": None,
        "channels": None
    },
    "Opus 32kbps Mono (Speech, Small File)": {
        "codec": "libopus",
        "bitrate": "32k",
        "channels": 1
    },
    "AAC 64kbps Mono (Low Bandwidth, Voice)": {
        "codec": "aac",
        "bitrate": "64k",
        "channels": 1
    },
    "AAC 128kbps Stereo (Standard Listening)": {
        "codec": "aac",
        "bitrate": "128k",
        "channels": 2
    },
    "Opus 128kbps Stereo (High Quality, Stereo)": {
        "codec": "libopus",
        "bitrate": "128k",
        "channels": 2
    }
}

def get_preset_by_name(name: str):
    """
    Return the preset dictionary for the given name.
    """
    return PRESETS.get(name)

def list_presets():
    """Return a list of all preset names."""
    return list(PRESETS.keys())