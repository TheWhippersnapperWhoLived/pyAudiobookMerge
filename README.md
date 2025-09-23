# pyAudiobookMerge
Convert MP3 collections in subfolders into well-structured audiobook files with chapters, metadata, and cover art.

---

## ⚠️ Experimental Software

This tool is still **experimental**. While it might work for some use cases, it may not handle all MP3 collections or metadata perfectly. Expect bugs, edge cases, and/or occasional FFmpeg errors.

You are currently limited to the presets provided in the program. You can edit this by adding to the presets.py file.

Only works with .mp3s at the moment..

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

## Usage

Python version:

```bash
python main.py [root_folder] [-p PRESET]
```
- root_folder (optional): Folder containing MP3 subfolders. Defaults to the current directory if not provided.
- -p PRESET (optional): Preset name from the available presets. If omitted, the script will prompt you to choose.

EXE version:
- Double-click the .exe file.
- Follow the interactive prompts to select folder and preset.
