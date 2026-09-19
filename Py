import os
import shutil
import subprocess
import sys

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
QApplication,
QHBoxLayout,
QLabel,
QMainWindow,
QMessageBox,
QProgressBar,
QPushButton,
QTreeWidget,
QTreeWidgetItem,
QVBoxLayout,
QWidget,
)

APP_NAME = "Disk Analyzer"
HOME = os.path.expanduser("~")

def format_size(size):
"""Convert bytes into a human-readable size."""

```
units = [
    "B",
    "KB",
    "MB",
    "GB",
    "TB",
    "PB",
]

size = float(size)

for unit in units:
    if size < 1024:
        return f"{size:.1f} {unit}"

    size /= 1024

return f"{size:.1f} EB"
```

def get_folder_size(path):
"""
Calculate the total size of a directory.

```
Symbolic links are ignored to prevent following links
outside the scanned directory.
"""

total = 0

try:
    for root, directories, files in os.walk(
        path,
        followlinks=False,
    ):
        directories[:] = [
            directory
            for directory in directories
            if not os.path.islink(
                os.path.join(root, directory)
            )
        ]

        for filename in files:
            file_path = os.path.join(
                root,
                filename,
            )

            try:
                if os.path.islink(file_path):
                    continue

                total += os.path.getsize(
                    file_path,
                )

            except (
                OSError,
                PermissionError,
            ):
                continue

except (
    OSError,
    PermissionError,
):
    pass

return total
```

class ScanWorker(QThread):
"""
Performs the disk scan in a background thread.

```
This prevents the graphical interface from freezing
while large directories are being analyzed.
"""

scan_finished = Signal(
    list,
    list,
    int,
)

scan_error = Signal(str)

def __init__(self, path):
    super().__init__()

    self.path = path
    self._stop_requested = False

def stop(self):
    """Request the worker to stop."""

    self._stop_requested = True

def run(self):
    """Perform the directory scan."""

    try:
        folders = []
        files = []
        total_size = 0

        try:
            entries = list(
                os.scandir(self.path)
            )

        except (
            OSError,
            PermissionError,
        ) as error:

            self.scan_error.emit(
                f"Unable to access:\n"
                f"{self.path}\n\n"
                f"{error}"
            )

            return

        for entry in entries:

            if self._stop_requested:
                return

            try:

                if entry.is_symlink():
                    continue

                if entry.is_dir(
                    follow_symlinks=False
                ):

                    size = get_folder_size(
                        entry.path
                    )

                    folders.append({
                        "name": entry.name,
                        "path": entry.path,
                        "size": size,
                    })

                    total_size += size

                elif entry.is_file(
                    follow_symlinks=False
                ):

                    size = entry.stat(
                        follow_symlinks=False
                    ).st_size

                    files.append({
                        "name": entry.name,
                        "path": entry.path,
                        "size": size,
                    })

                    total_size += size

            except (
                OSError,
                PermissionError,
            ):
                continue

        folders.sort(
            key=lambda item: item["size"],
            reverse=True,
        )

        files.sort(
            key=lambda item: item["size"],
            reverse=True,
        )

        if self._stop_requested:
            return

        self.scan_finished.emit(
            folders,
            files,
            total_size,
        )

    except Exception as error:
        self.scan_error.emit(
            str(error)
        )
```

class DiskAnalyzer(QMainWindow):
"""Main application window."""

```
def __init__(self):
    super().__init__()

    self.current_path = HOME
    self.selected_path = None
    self.worker = None

    self.setWindowTitle(
        APP_NAME
    )

    self.resize(
        1000,
        700,
    )

    self.setup_ui()
    self.apply_style()

    self.scan_home()

def setup_ui(self):
    """Create the graphical interface."""

    central_widget = QWidget()

    self.setCentralWidget(
        central_widget
    )

    main_layout = QVBoxLayout(
        central_widget
    )

    main_layout.setContentsMargins(
        20,
        20,
        20,
        20,
    )

    main_layout.setSpacing(
        12
    )

    # Title
    title = QLabel(
        APP_NAME
    )

    title.setObjectName(
        "title"
    )

    main_layout.addWidget(
        title
    )

    # Description
    subtitle = QLabel(
        "Analyze disk usage in your home directory."
    )

    subtitle.setObjectName(
        "subtitle"
    )

    main_layout.addWidget(
        subtitle
    )

    # Current path
    self.path_label = QLabel(
        self.current_path
    )

    self.path_label.setObjectName(
        "pathLabel"
    )

    main_layout.addWidget(
        self.path_label
    )

    # Storage information
    self.storage_label = QLabel(
        "Scanning..."
    )

    self.storage_label.setObjectName(
        "storageLabel"
    )

    main_layout.addWidget(
        self.storage_label
    )

    # Progress bar
    self.progress = QProgressBar()

    self.progress.setRange(
        0,
        0,
    )

    self.progress.setVisible(
        False
    )

    main_layout.addWidget(
        self.progress
    )

    # File tree
    self.tree = QTreeWidget()

    self.tree.setColumnCount(
        3
    )

    self.tree.setHeaderLabels([
        "Name",
        "Type",
        "Size",
    ])

    self.tree.setAlternatingRowColors(
        True
    )

    self.tree.setSortingEnabled(
        True
    )

    self.tree.setSelectionMode(
        QTreeWidget.SingleSelection
    )

    self.tree.itemSelectionChanged.connect(
        self.selection_changed
    )

    self.tree.itemDoubleClicked.connect(
        self.open_folder
    )

    main_layout.addWidget(
        self.tree
    )

    # Buttons
    button_layout = QHBoxLayout()

    self.back_button = QPushButton(
        "Back"
    )

    self.back_button.clicked.connect(
        self.go_back
    )

    self.scan_button = QPushButton(
        "Analyze"
    )

    self.scan_button.clicked.connect(
        self.scan_current_path
    )

    self.refresh_button = QPushButton(
        "Refresh"
    )

    self.refresh_button.clicked.connect(
        self.refresh
    )

    self.open_button = QPushButton(
        "Open Folder"
    )

    self.open_button.clicked.connect(
        self.open_selected_folder
    )

    self.delete_button = QPushButton(
        "Delete"
    )

    self.delete_button.clicked.connect(
        self.delete_selected
    )

    button_layout.addWidget(
        self.back_button
    )

    button_layout.addWidget(
        self.scan_button
    )

    button_layout.addWidget(
        self.refresh_button
    )

    button_layout.addStretch()

    button_layout.addWidget(
        self.open_button
    )

    button_layout.addWidget(
        self.delete_button
    )

    main_layout.addLayout(
        button_layout
    )

    self.update_buttons()

def apply_style(self):
    """Apply the application stylesheet."""

    self.setStyleSheet(
        """
        QMainWindow {
            background: #0f172a;
        }

        QWidget {
            color: #e5e7eb;
            font-size: 14px;
        }

        QLabel#title {
            font-size: 28px;
            font-weight: bold;
            color: #ffffff;
        }

        QLabel#subtitle {
            color: #94a3b8;
            font-size: 14px;
        }

        QLabel#pathLabel {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 10px;
            color: #93c5fd;
        }

        QLabel#storageLabel {
            font-size: 15px;
            font-weight: bold;
            padding: 5px;
        }

        QTreeWidget {
            background: #111827;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 5px;
            alternate-background-color: #172033;
            selection-background-color: #2563eb;
            selection-color: white;
        }

        QTreeWidget::item {
            padding: 8px;
        }

        QHeaderView::section {
            background: #1e293b;
            color: #e5e7eb;
            border: none;
            padding: 8px;
            font-weight: bold;
        }

        QPushButton {
            background: #1e293b;
            border: 1px solid #475569;
            border-radius: 8px;
            padding: 9px 14px;
        }

        QPushButton:hover {
            background: #334155;
        }

        QPushButton:pressed {
            background: #475569;
        }

        QPushButton:disabled {
            color: #64748b;
            background: #111827;
        }

        QProgressBar {
            border: 1px solid #334155;
            border-radius: 5px;
            background: #111827;
            height: 8px;
        }

        QProgressBar::chunk {
            background: #2563eb;
            border-radius: 5px;
        }
        """
    )

def scan_home(self):
    """Start a scan of the home directory."""

    self.current_path = HOME

    self.path_label.setText(
        self.current_path
    )

    self.start_scan(
        self.current_path
    )

def scan_current_path(self):
    """Scan the currently displayed directory."""

    self.start_scan(
        self.current_path
    )

def refresh(self):
    """Refresh the current directory."""

    self.start_scan(
        self.current_path
    )

def start_scan(self, path):
    """Start a background scan."""

    if (
        self.worker is not None
        and self.worker.isRunning()
    ):
        return

    if not os.path.isdir(path):

        QMessageBox.warning(
            self,
            "Error",
            f"Directory does not exist:\n{path}",
        )

        return

    self.current_path = os.path.abspath(
        path
    )

    self.path_label.setText(
        self.current_path
    )

    self.tree.clear()

    self.selected_path = None

    self.storage_label.setText(
        "Scanning..."
    )

    self.progress.setVisible(
        True
    )

    self.update_buttons(
        scanning=True
    )

    self.worker = ScanWorker(
        self.current_path
    )

    self.worker.scan_finished.connect(
        self.scan_completed
    )

    self.worker.scan_error.connect(
        self.scan_failed
    )

    self.worker.finished.connect(
        self.worker_finished
    )

    self.worker.start()

def worker_finished(self):
    """Clean up after the worker finishes."""

    if self.worker is not None:
        self.worker.deleteLater()
        self.worker = None

def scan_failed(self, message):
    """Handle scan errors."""

    self.progress.setVisible(
        False
    )

    self.storage_label.setText(
        "Scan failed."
    )

    self.update_buttons()

    QMessageBox.warning(
        self,
        "Scan Error",
        message,
    )

def scan_completed(
    self,
    folders,
    files,
    total_size,
):
    """Display the scan results."""

    self.tree.clear()

    self.tree.setSortingEnabled(
        False
    )

    for folder in folders:

        item = QTreeWidgetItem([
            folder["name"],
            "Folder",
            format_size(
                folder["size"]
            ),
        ])

        item.setData(
            0,
            Qt.UserRole,
            folder["path"],
        )

        self.tree.addTopLevelItem(
            item
        )

    for file in files:

        item = QTreeWidgetItem([
            file["name"],
            "File",
            format_size(
                file["size"]
            ),
        ])

        item.setData(
            0,
            Qt.UserRole,
            file["path"],
        )

        self.tree.addTopLevelItem(
            item
        )

    self.tree.setSortingEnabled(
        True
    )

    self.tree.sortItems(
        2,
        Qt.DescendingOrder,
    )

    self.progress.setVisible(
        False
    )

    self.storage_label.setText(
        f"Total: {format_size(total_size)}"
    )

    self.update_buttons()

def update_buttons(
    self,
    scanning=False,
):
    """Update button states."""

    has_selection = (
        self.selected_path is not None
        and os.path.exists(
            self.selected_path
        )
    )

    self.back_button.setEnabled(
        not scanning
        and self.current_path != HOME
    )

    self.scan_button.setEnabled(
        not scanning
    )

    self.refresh_button.setEnabled(
        not scanning
    )

    self.open_button.setEnabled(
        not scanning
        and has_selection
        and os.path.isdir(
            self.selected_path
        )
    )

    self.delete_button.setEnabled(
        not scanning
        and has_selection
    )

def selection_changed(self):
    """Handle tree selection changes."""

    items = self.tree.selectedItems()

    if not items:

        self.selected_path = None

        self.update_buttons()

        return

    self.selected_path = items[0].data(
        0,
        Qt.UserRole,
    )

    self.update_buttons()

def open_selected_folder(self):
    """Open the selected directory in the file manager."""

    if not self.selected_path:
        return

    if not os.path.isdir(
        self.selected_path
    ):
        return

    try:

        subprocess.Popen([
            "dolphin",
            self.selected_path,
        ])

    except FileNotFoundError:

        QMessageBox.warning(
            self,
            "File Manager Not Found",
            "Dolphin could not be started.",
        )

def open_folder(
    self,
    item,
    column,
):
    """Enter a directory by double-clicking it."""

    path = item.data(
        0,
        Qt.UserRole,
    )

    if not path:
        return

    if not os.path.isdir(path):
        return

    if not self.is_safe_path(path):
        QMessageBox.warning(
            self,
            "Access denied",
            "This directory is outside "
            "your home directory.",
        )

        return

    self.start_scan(
        path
    )

def go_back(self):
    """Navigate to the parent directory."""

    if self.current_path == HOME:
        return

    parent = os.path.dirname(
        self.current_path
    )

    if not self.is_safe_path(parent):
        parent = HOME

    self.start_scan(
        parent
    )

def is_safe_path(self, path):
    """
    Ensure that a path stays inside HOME.

    This prevents the application from navigating
    outside the user's home directory.
    """

    try:

        home = os.path.realpath(
            HOME
        )

        target = os.path.realpath(
            path
        )

        return os.path.commonpath([
            home,
            target,
        ]) == home

    except (
        ValueError,
        OSError,
    ):

        return False

def delete_selected(self):
    """Delete the selected file or directory."""

    if not self.selected_path:
        return

    path = os.path.abspath(
        self.selected_path
    )

    if not self.is_safe_path(path):

        QMessageBox.warning(
            self,
            "Access denied",
            "Only files and directories inside "
            "your home directory can be deleted.",
        )

        return

    if path == os.path.abspath(HOME):

        QMessageBox.warning(
            self,
            "Operation blocked",
            "Your home directory cannot be deleted.",
        )

        return

    if not os.path.exists(path):

        self.refresh()

        return

    name = os.path.basename(
        path
    )

    answer = QMessageBox.question(
        self,
        "Confirm deletion",
        f"Delete this item?\n\n"
        f"{name}\n\n"
        "This action cannot be undone.",
        QMessageBox.Yes
        | QMessageBox.No,
        QMessageBox.No,
    )

    if answer != QMessageBox.Yes:
        return

    try:

        if os.path.isdir(path):

            shutil.rmtree(
                path
            )

        else:

            os.remove(
                path
            )

        self.selected_path = None

        self.refresh()

    except (
        PermissionError,
        OSError,
    ) as error:

        QMessageBox.critical(
            self,
            "Delete failed",
            str(error),
        )

def closeEvent(self, event):
    """Stop the scan when the application closes."""

    if (
        self.worker is not None
        and self.worker.isRunning()
    ):

        self.worker.stop()

        self.worker.wait()

    event.accept()
```

def main():
"""Application entry point."""

```
app = QApplication(
    sys.argv
)

app.setApplicationName(
    APP_NAME
)

window = DiskAnalyzer()

window.show()

sys.exit(
    app.exec()
)
```

if **name** == "**main**":
main()
