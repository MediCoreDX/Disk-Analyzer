# Disk Analyzer

A lightweight Linux disk-usage browser built with Python and PySide6. It scans a
selected directory, lists its immediate files and subdirectories, and sorts
them by name, type, or size. Scanning runs in a background thread.

## Features

- Browse directories and navigate to the parent or home directory
- Show file and directory sizes and their share of the current directory
- Cancel an active scan
- Open the current directory in the desktop's default file manager
- Ignore symbolic links rather than following them

The application can scan any directory the current user can access. It does not
delete files or restrict navigation to the home directory.

## Requirements

- Linux
- Python 3.10 or newer
- PySide6

## Install and run

```bash
git clone https://github.com/MediCoreDX/Disk-Analyzer.git
cd Disk-Analyzer
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python Disk-Analyzer.py
```

## How sizes are calculated

Each listed directory is scanned recursively in the background. Symbolic links
are skipped. Files and directories that cannot be read are omitted from the
calculated size, so results may be lower than the actual size when permissions
are restricted.

## Project files

```text
Disk-Analyzer.py
README.md
requirements.txt
```

No license file is currently included.
