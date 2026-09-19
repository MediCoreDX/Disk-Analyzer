import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QObject, Signal, Slot, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QProgressBar,
    QTreeWidget,
    QTreeWidgetItem,
    QMessageBox,
    QHeaderView,
    QLineEdit,
    QStyle,
    QFrame,
)


APP_NAME = "Disk Analyzer"
VERSION = "1.0.0"


def format_size(size):
    if size < 1024:
        return f"{size} B"

    if size < 1024 ** 2:
        return f"{size / 1024:.1f} KB"

    if size < 1024 ** 3:
        return f"{size / (1024 ** 2):.1f} MB"

    if size < 1024 ** 4:
        return f"{size / (1024 ** 3):.2f} GB"

    return f"{size / (1024 ** 4):.2f} TB"


def get_directory_size(path, stop_function):
    total = 0

    try:
        for root, dirs, files in os.walk(
            path,
            topdown=True,
            followlinks=False,
        ):
            if stop_function():
                return total

            dirs[:] = [
                directory
                for directory in dirs
                if not os.path.islink(
                    os.path.join(root, directory)
                )
            ]

            for filename in files:
                if stop_function():
                    return total

                file_path = os.path.join(
                    root,
                    filename,
                )

                try:
                    if os.path.islink(file_path):
                        continue

                    total += os.path.getsize(
                        file_path
                    )

                except (OSError, PermissionError):
                    pass

    except (OSError, PermissionError):
        pass

    return total


def open_file_manager(path):
    QDesktopServices.openUrl(
        QUrl.fromLocalFile(path)
    )


class ScanWorker(QObject):

    progress = Signal(int)
    status = Signal(str)
    finished = Signal(list, int)
    cancelled = Signal()

    def __init__(self, path):
        super().__init__()

        self.path = os.path.abspath(
            os.path.expanduser(path)
        )

        self.stop_requested = False

    def stop(self):
        self.stop_requested = True

    def stopped(self):
        return self.stop_requested

    @Slot()
    def run(self):

        items = []

        try:
            self.status.emit(
                "Lese Verzeichnis..."
            )

            try:
                entries = list(
                    os.scandir(self.path)
                )

            except (OSError, PermissionError) as error:
                self.status.emit(
                    f"Fehler: {error}"
                )

                self.finished.emit(
                    [],
                    0,
                )

                return

            folders = []
            files = []

            for entry in entries:

                if self.stopped():
                    self.cancelled.emit()
                    return

                try:
                    if entry.is_symlink():
                        continue

                    if entry.is_dir(
                        follow_symlinks=False
                    ):
                        folders.append(entry)

                    elif entry.is_file(
                        follow_symlinks=False
                    ):
                        files.append(entry)

                except (OSError, PermissionError):
                    continue

            total_entries = (
                len(folders)
                + len(files)
            )

            if total_entries == 0:

                self.status.emit(
                    "Verzeichnis ist leer."
                )

                self.progress.emit(100)

                self.finished.emit(
                    [],
                    0,
                )

                return

            processed = 0

            # Dateien scannen
            for entry in files:

                if self.stopped():
                    self.cancelled.emit()
                    return

                try:
                    size = entry.stat(
                        follow_symlinks=False
                    ).st_size

                except (OSError, PermissionError):
                    size = 0

                items.append(
                    {
                        "name": entry.name,
                        "type": "Datei",
                        "path": entry.path,
                        "size": size,
                    }
                )

                processed += 1

                self.progress.emit(
                    int(
                        processed
                        / total_entries
                        * 100
                    )
                )

            # Ordner scannen
            for entry in folders:

                if self.stopped():
                    self.cancelled.emit()
                    return

                self.status.emit(
                    f"Scanne: {entry.name}"
                )

                size = get_directory_size(
                    entry.path,
                    self.stopped,
                )

                if self.stopped():
                    self.cancelled.emit()
                    return

                items.append(
                    {
                        "name": entry.name,
                        "type": "Ordner",
                        "path": entry.path,
                        "size": size,
                    }
                )

                processed += 1

                self.progress.emit(
                    int(
                        processed
                        / total_entries
                        * 100
                    )
                )

            total_size = sum(
                item["size"]
                for item in items
            )

            self.progress.emit(100)

            self.status.emit(
                "Scan abgeschlossen."
            )

            self.finished.emit(
                items,
                total_size,
            )

        except Exception as error:

            self.status.emit(
                f"Scan-Fehler: {error}"
            )

            self.finished.emit(
                [],
                0,
            )


class DiskAnalyzer(QMainWindow):

    def __init__(self):
        super().__init__()

        self.current_path = str(
            Path.home()
        )

        self.worker = None
        self.thread = None

        self.scan_items = []
        self.total_size = 0

        # Eigene Python-Sortierung.
        # Qt-interne Sortierung wird NICHT verwendet.
        self.sort_column = 2
        self.sort_order = Qt.DescendingOrder

        self.setup_window()
        self.setup_ui()

        self.start_scan()

    def setup_window(self):

        self.setWindowTitle(
            f"{APP_NAME} {VERSION}"
        )

        self.resize(
            1050,
            700,
        )

        self.setMinimumSize(
            800,
            500,
        )

    def setup_ui(self):

        central = QWidget()

        self.setCentralWidget(
            central
        )

        main_layout = QVBoxLayout(
            central
        )

        main_layout.setContentsMargins(
            15,
            15,
            15,
            15,
        )

        main_layout.setSpacing(10)

        # Titel
        title_layout = QHBoxLayout()

        title = QLabel(
            "Disk Analyzer"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: bold;
            }
            """
        )

        title_layout.addWidget(title)
        title_layout.addStretch()

        self.total_label = QLabel(
            "Gesamt: 0 B"
        )

        self.total_label.setStyleSheet(
            """
            QLabel {
                font-size: 15px;
                font-weight: bold;
            }
            """
        )

        title_layout.addWidget(
            self.total_label
        )

        main_layout.addLayout(
            title_layout
        )

        # Pfad
        path_layout = QHBoxLayout()

        self.path_edit = QLineEdit(
            self.current_path
        )

        self.path_edit.setPlaceholderText(
            "Pfad eingeben..."
        )

        path_layout.addWidget(
            self.path_edit
        )

        self.scan_button = QPushButton(
            "Scannen"
        )

        self.scan_button.clicked.connect(
            self.start_scan
        )

        path_layout.addWidget(
            self.scan_button
        )

        self.home_button = QPushButton(
            "Home"
        )

        self.home_button.clicked.connect(
            self.go_home
        )

        path_layout.addWidget(
            self.home_button
        )

        main_layout.addLayout(
            path_layout
        )

        # Navigation
        navigation_layout = QHBoxLayout()

        self.back_button = QPushButton(
            "← Zurück"
        )

        self.back_button.clicked.connect(
            self.go_back
        )

        navigation_layout.addWidget(
            self.back_button
        )

        self.open_button = QPushButton(
            "Im Dateimanager öffnen"
        )

        self.open_button.clicked.connect(
            self.open_current_folder
        )

        navigation_layout.addWidget(
            self.open_button
        )

        self.cancel_button = QPushButton(
            "Scan abbrechen"
        )

        self.cancel_button.clicked.connect(
            self.cancel_scan
        )

        self.cancel_button.setEnabled(
            False
        )

        navigation_layout.addWidget(
            self.cancel_button
        )

        navigation_layout.addStretch()

        main_layout.addLayout(
            navigation_layout
        )

        # Trennlinie
        line = QFrame()

        line.setFrameShape(
            QFrame.HLine
        )

        line.setFrameShadow(
            QFrame.Sunken
        )

        main_layout.addWidget(line)

        # Tabelle
        self.tree = QTreeWidget()

        self.tree.setColumnCount(4)

        self.tree.setHeaderLabels(
            [
                "Name",
                "Typ",
                "Größe",
                "Anteil",
            ]
        )

        # WICHTIG:
        # Keine Qt-interne Sortierung!
        self.tree.setSortingEnabled(False)

        self.tree.setAlternatingRowColors(
            True
        )

        self.tree.setUniformRowHeights(
            True
        )

        self.tree.setRootIsDecorated(
            False
        )

        header = self.tree.header()

        header.setStretchLastSection(
            False
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.Stretch
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents
        )

        # Eigene Sortierung
        header.sectionClicked.connect(
            self.header_clicked
        )

        self.tree.itemDoubleClicked.connect(
            self.item_double_clicked
        )

        main_layout.addWidget(
            self.tree
        )

        # Fortschrittsbalken
        self.progress_bar = QProgressBar()

        self.progress_bar.setRange(
            0,
            100,
        )

        self.progress_bar.setValue(
            0
        )

        main_layout.addWidget(
            self.progress_bar
        )

        # Status
        self.status_label = QLabel(
            "Bereit."
        )

        main_layout.addWidget(
            self.status_label
        )

        self.update_navigation_buttons()

    def start_scan(self):

        if self.thread is not None:
            return

        path = self.path_edit.text().strip()

        if not path:
            path = str(Path.home())

        path = os.path.abspath(
            os.path.expanduser(path)
        )

        if not os.path.isdir(path):

            QMessageBox.warning(
                self,
                "Ungültiger Pfad",
                f"Der Ordner existiert nicht:\n\n{path}",
            )

            return

        self.current_path = path

        self.path_edit.setText(
            path
        )

        self.tree.clear()

        self.scan_items = []
        self.total_size = 0

        self.total_label.setText(
            "Gesamt: 0 B"
        )

        self.progress_bar.setValue(
            0
        )

        self.status_label.setText(
            "Scan wird gestartet..."
        )

        self.scan_button.setEnabled(
            False
        )

        self.cancel_button.setEnabled(
            True
        )

        self.home_button.setEnabled(
            False
        )

        self.back_button.setEnabled(
            False
        )

        # Thread erstellen
        self.thread = QThread()

        self.worker = ScanWorker(
            self.current_path
        )

        self.worker.moveToThread(
            self.thread
        )

        self.thread.started.connect(
            self.worker.run
        )

        self.worker.progress.connect(
            self.progress_bar.setValue
        )

        self.worker.status.connect(
            self.status_label.setText
        )

        self.worker.finished.connect(
            self.scan_completed
        )

        self.worker.finished.connect(
            self.thread.quit
        )

        self.worker.cancelled.connect(
            self.scan_cancelled
        )

        self.worker.cancelled.connect(
            self.thread.quit
        )

        self.thread.finished.connect(
            self.thread_finished
        )

        self.thread.start()

    @Slot(list, int)
    def scan_completed(
        self,
        items,
        total_size,
    ):

        self.scan_items = items
        self.total_size = total_size

        self.populate_tree()

        self.total_label.setText(
            f"Gesamt: {format_size(total_size)}"
        )

        self.status_label.setText(
            f"Scan abgeschlossen – "
            f"{len(items)} Einträge."
        )

        self.progress_bar.setValue(
            100
        )

        self.scan_button.setEnabled(
            True
        )

        self.cancel_button.setEnabled(
            False
        )

        self.home_button.setEnabled(
            True
        )

        self.update_navigation_buttons()

    @Slot()
    def scan_cancelled(self):

        self.status_label.setText(
            "Scan wurde abgebrochen."
        )

        self.scan_button.setEnabled(
            True
        )

        self.cancel_button.setEnabled(
            False
        )

        self.home_button.setEnabled(
            True
        )

    @Slot()
    def thread_finished(self):

        if self.worker is not None:
            self.worker.deleteLater()

        if self.thread is not None:
            self.thread.deleteLater()

        self.worker = None
        self.thread = None

        self.update_navigation_buttons()

    def cancel_scan(self):

        if self.worker is None:
            return

        self.status_label.setText(
            "Scan wird abgebrochen..."
        )

        self.cancel_button.setEnabled(
            False
        )

        self.worker.stop()

    def populate_tree(self):

        self.tree.setUpdatesEnabled(
            False
        )

        try:

            self.tree.clear()

            sorted_items = (
                self.get_sorted_items()
            )

            for data in sorted_items:

                size = data["size"]

                if self.total_size > 0:
                    percentage = (
                        size
                        / self.total_size
                        * 100
                    )
                else:
                    percentage = 0

                item = QTreeWidgetItem(
                    [
                        data["name"],
                        data["type"],
                        format_size(size),
                        f"{percentage:.1f} %",
                    ]
                )

                item.setData(
                    0,
                    Qt.UserRole,
                    data["path"],
                )

                item.setData(
                    2,
                    Qt.UserRole,
                    size,
                )

                self.set_item_icon(
                    item,
                    data["type"],
                )

                self.tree.addTopLevelItem(
                    item
                )

        finally:

            self.tree.setUpdatesEnabled(
                True
            )

        header = self.tree.header()

        header.setSortIndicator(
            self.sort_column,
            self.sort_order,
        )

        header.setSortIndicatorShown(
            True
        )

    def get_sorted_items(self):

        items = list(
            self.scan_items
        )

        if self.sort_column == 0:

            key_function = (
                lambda item:
                item["name"].lower()
            )

        elif self.sort_column == 1:

            key_function = (
                lambda item:
                item["type"].lower()
            )

        elif self.sort_column in (2, 3):

            key_function = (
                lambda item:
                item["size"]
            )

        else:

            key_function = (
                lambda item:
                item["name"].lower()
            )

        reverse = (
            self.sort_order
            == Qt.DescendingOrder
        )

        return sorted(
            items,
            key=key_function,
            reverse=reverse,
        )

    def header_clicked(
        self,
        column,
    ):

        if column == self.sort_column:

            if (
                self.sort_order
                == Qt.AscendingOrder
            ):

                self.sort_order = (
                    Qt.DescendingOrder
                )

            else:

                self.sort_order = (
                    Qt.AscendingOrder
                )

        else:

            self.sort_column = column

            if column in (2, 3):

                self.sort_order = (
                    Qt.DescendingOrder
                )

            else:

                self.sort_order = (
                    Qt.AscendingOrder
                )

        self.populate_tree()

    def set_item_icon(
        self,
        item,
        item_type,
    ):

        style = self.style()

        if item_type == "Ordner":

            icon = style.standardIcon(
                QStyle.SP_DirIcon
            )

        else:

            icon = style.standardIcon(
                QStyle.SP_FileIcon
            )

        item.setIcon(
            0,
            icon
        )

    def item_double_clicked(
        self,
        item,
        column,
    ):

        path = item.data(
            0,
            Qt.UserRole,
        )

        if not path:
            return

        if os.path.isdir(path):

            self.current_path = (
                os.path.abspath(path)
            )

            self.path_edit.setText(
                self.current_path
            )

            self.start_scan()

        else:

            open_file_manager(path)

    def go_home(self):

        home = str(
            Path.home()
        )

        self.current_path = home

        self.path_edit.setText(
            home
        )

        self.start_scan()

    def go_back(self):

        if self.thread is not None:
            return

        current = os.path.abspath(
            self.current_path
        )

        parent = os.path.dirname(
            current
        )

        if parent == current:
            return

        self.current_path = parent

        self.path_edit.setText(
            parent
        )

        self.start_scan()

    def open_current_folder(self):

        open_file_manager(
            self.current_path
        )

    def update_navigation_buttons(self):

        if self.thread is not None:
            return

        current = os.path.abspath(
            self.current_path
        )

        parent = os.path.dirname(
            current
        )

        self.back_button.setEnabled(
            current != parent
        )

    def closeEvent(self, event):

        if self.worker is not None:
            self.worker.stop()

        if self.thread is not None:

            self.thread.quit()

            self.thread.wait(3000)

        event.accept()


def main():

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        APP_NAME
    )

    app.setApplicationDisplayName(
        APP_NAME
    )

    window = DiskAnalyzer()

    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
