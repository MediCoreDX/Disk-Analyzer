# Disk Analyzer

A simple and lightweight disk usage analyzer built with **Python** and **PySide6**.

Disk Analyzer allows you to explore the storage usage of your home directory, find large folders and files, navigate through directories, open folders in Dolphin, and remove files or folders.

The application uses a background thread for disk scanning, so the graphical user interface remains responsive while large directories are being analyzed.

## Features

*  Analyze disk usage
*  Browse directories
*  Display files and folders
*  Display file and folder sizes
*  Sort results by size
*  Refresh the current directory
*  Navigate back to parent directories
*  Open folders with Dolphin
*  Delete files and directories
*  Background scanning using `QThread`
*  Restricts navigation and deletion to the user's home directory
*  Symbolic links are ignored during scanning

## Screenshots

Add screenshots of the application here.

Example:

```text
screenshots/
└── disk-analyzer.png
```

Then add an image to this section:

```markdown
![Disk Analyzer](screenshots/disk-analyzer.png)
```

## Requirements

* Linux
* Python 3.10 or newer
* PySide6
* KDE Dolphin (optional, for the "Open Folder" feature)

The application was developed and tested on **Manjaro Linux with KDE Plasma**.

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/DiskAnalyzer.git
```

Enter the project directory:

```bash
cd DiskAnalyzer
```

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Running the application

Start Disk Analyzer with:

```bash
python disk_analyzer.py
```

## requirements.txt

The project currently requires:

```text
PySide6>=6.8
```

## How it works

Disk Analyzer scans the selected directory and calculates the size of its files and subdirectories.

The scan is performed in a separate `QThread`.

This is important because disk scanning can take some time, especially when a directory contains thousands of files.

Instead of doing the scan directly in the graphical user interface thread:

```text
GUI
 │
 ├── User interface
 ├── Buttons
 └── File tree
```

the application uses:

```text
GUI Thread
 │
 ├── User interface
 ├── Buttons
 └── File tree
       │
       │ signals
       ▼
Background Thread
 │
 └── Disk scanning
```

This keeps the interface responsive while the scan is running.

## Safety

Disk Analyzer is designed to operate inside the user's home directory.

The application prevents navigation outside the home directory and blocks deletion of the home directory itself.

Symbolic links are ignored during scanning to avoid accidentally following links to other locations.

### Important

The current delete function performs **permanent deletion** using Python's filesystem functions.

Deleted files and directories are **not moved to the desktop trash/recycle bin**.

Use the delete function carefully.

## Project structure

```text
DiskAnalyzer/
│
├── disk_analyzer.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
│
└── screenshots/
    └── disk-analyzer.png
```

## Future improvements

Possible future features include:

* 🗑️ Move deleted files to the Trash instead of permanently deleting them
* 📊 Graphical disk usage charts
* 🍩 Pie chart / donut chart
* 📈 Storage usage visualization
* 🔎 Search for files
* 📏 Minimum/maximum size filters
* 🧹 Duplicate file detection
* 💾 Drive selection
* 📂 Better directory tree navigation
* ⏹️ Cancel scan button
* 🌍 Multi-language support
* 🎨 Light and dark themes
* ⚙️ Application settings
* 📦 Linux package

## Contributing

Contributions, suggestions and bug reports are welcome.

If you find a bug or have an idea for a new feature, feel free to open an issue.

Pull requests are also welcome.

## License

This project is licensed under the MIT License.

See the `LICENSE` file for more information.

## Author

Created as a Python and Linux learning project.

Built with:

* Python
* PySide6
* Qt
* Linux

---

⭐ If you find this project useful, consider giving the repository a star.
