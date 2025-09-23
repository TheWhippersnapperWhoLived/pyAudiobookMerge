# pyAudiobookMerge
Convert MP3 collections in subfolders into well-structured audiobook files with chapters, metadata, and cover art.

---

## Features

- Batch converts multiple folders of MP3 files into a single audiobook per folder.
- Supports multiple presets:
  - **Copy / Remux (Fast, Original Container)**
  - **Opus 32kbps Mono (Speech, Small File)**
  - **AAC 64kbps Mono (Low Bandwidth, Voice)**
  - **AAC 128kbps Stereo (Standard Listening)**
  - **Opus 128kbps Stereo (High Quality, Stereo)**
- Automatically detects chapters from MP3 filenames.
- The program uses the folder name as the audiobook title.
- Extracts metadata from MP3 files and applies it to the final audiobook.
- Embeds cover art (jpg/png) with automatic resizing.
- Works as both Python script and standalone EXE.

---

## Installation

1. Clone or download this repository.
2. Ensure **Python 3.10+** is installed.
3. Install required packages:

```bash
pip install -r requirements.txt
```
Or use the provided standalone EXE — no Python installation needed.
