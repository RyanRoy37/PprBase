"""Screen 1: choose a format to start a paper, or load one from disk."""

from __future__ import annotations

import os
import shutil
from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.format_loader import FormatError, list_available_formats, load_format
from core.word_template import WordTemplateError, inspect_word_template, install_word_template, revise_word_template
from ui.format_wizard import FormatWizard, save_new_format, update_format


class FormatCard(QFrame):
    clicked = pyqtSignal(str)  # emits path
    duplicate_requested = pyqtSignal(str)
    edit_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)

    def __init__(self, entry: dict[str, Any], parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.entry = entry
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(280, 180)

        layout = QVBoxLayout(self)
        if entry.get("valid", True):
            title = QLabel(entry.get("display_name", ""))
            title.setObjectName("CardTitle")
            title.setWordWrap(True)
            title.setMinimumHeight(38)
            sub = QLabel(f"{entry.get('subject','')}  ·  Class {entry.get('class','')}")
            sub.setObjectName("CardSub")
            layout.addWidget(title)
            layout.addWidget(sub)
            layout.addStretch()
            open_btn = QPushButton("New paper" if entry.get("word_template") else "Open")
            open_btn.clicked.connect(lambda: self.clicked.emit(entry["path"]))
            actions = QHBoxLayout()
            duplicate_btn = QPushButton("Duplicate")
            duplicate_btn.setObjectName("Ghost")
            duplicate_btn.clicked.connect(lambda: self.duplicate_requested.emit(entry["path"]))
            actions.addWidget(duplicate_btn)
            actions.addWidget(open_btn)
            layout.addLayout(actions)
            manage = QHBoxLayout()
            edit_btn = QPushButton("Edit Template" if entry.get("word_template") else "Edit")
            edit_btn.setObjectName("Ghost")
            edit_btn.clicked.connect(lambda: self.edit_requested.emit(entry["path"]))
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("Danger")
            delete_btn.clicked.connect(lambda: self.delete_requested.emit(entry["path"]))
            manage.addWidget(edit_btn)
            manage.addWidget(delete_btn)
            layout.addLayout(manage)
        else:
            title = QLabel(f"⚠  {entry.get('display_name','')}")
            title.setObjectName("CardTitle")
            err = QLabel(entry.get("error", "Invalid format"))
            err.setObjectName("CardSub")
            err.setWordWrap(True)
            layout.addWidget(title)
            layout.addWidget(err)
            delete_btn = QPushButton("Remove invalid format")
            delete_btn.setObjectName("Danger")
            delete_btn.clicked.connect(lambda: self.delete_requested.emit(entry["path"]))
            layout.addWidget(delete_btn)


class FormatSelector(QWidget):
    format_chosen = pyqtSignal(dict, str)  # (format dict, path)
    draft_chosen = pyqtSignal(str)

    def __init__(self, formats_dir: str, parent=None) -> None:
        super().__init__(parent)
        self.formats_dir = formats_dir
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("Choose a question paper format")
        title.setObjectName("AppTitle")
        header.addWidget(title)
        header.addStretch()
        create_btn = QPushButton("Create Format")
        create_btn.clicked.connect(self._create_format)
        header.addWidget(create_btn)
        import_word_btn = QPushButton("Import Word Template")
        import_word_btn.setObjectName("Ghost")
        import_word_btn.clicked.connect(self._import_word_template)
        header.addWidget(import_word_btn)
        add_btn = QPushButton("Add New Format")
        add_btn.setObjectName("Ghost")
        add_btn.clicked.connect(self._add_format)
        header.addWidget(add_btn)
        layout.addLayout(header)

        hint = QLabel("Pick a format to start building a paper. Each card is a class and subject.")
        hint.setObjectName("Hint")
        layout.addWidget(hint)

        self.drafts_title = QLabel("Continue a draft")
        self.drafts_title.setObjectName("FieldLabel")
        layout.addWidget(self.drafts_title)
        self.drafts_row = QHBoxLayout()
        layout.addLayout(self.drafts_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setSpacing(14)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self.grid_host)
        layout.addWidget(scroll, 1)

    def reload(self) -> None:
        # Clear existing cards.
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        entries = list_available_formats(self.formats_dir)
        if not entries:
            empty = QLabel("No formats yet. Import a Word template or create a format to begin.")
            empty.setObjectName("Hint")
            self.grid.addWidget(empty, 0, 0)
            return

        cols = 3
        for i, entry in enumerate(entries):
            card = FormatCard(entry)
            card.clicked.connect(self._open_path)
            card.duplicate_requested.connect(self._duplicate_format)
            card.edit_requested.connect(self._edit_format)
            card.delete_requested.connect(self._delete_format)
            self.grid.addWidget(card, i // cols, i % cols)

    def set_drafts(self, drafts: list[dict]) -> None:
        self._all_drafts = drafts
        while self.drafts_row.count():
            item = self.drafts_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.drafts_title.setVisible(bool(drafts))
        for draft in drafts[:3]:
            label = draft["display_name"]
            date = draft.get("updated_at", "")[:10]
            button = QPushButton(f"{label}\nSaved {date}")
            button.setObjectName("Ghost")
            button.clicked.connect(lambda _checked=False, did=draft["draft_id"]: self.draft_chosen.emit(did))
            self.drafts_row.addWidget(button)
        if len(drafts) > 3:
            more = QPushButton(f"More drafts ({len(drafts) - 3})…")
            more.setObjectName("Ghost")
            more.clicked.connect(self._choose_older_draft)
            self.drafts_row.addWidget(more)
        self.drafts_row.addStretch()

    def _choose_older_draft(self) -> None:
        older = self._all_drafts[3:]
        labels = [f"{d['display_name']} — {d.get('updated_at', '')[:16]} — {d['draft_id'][:8]}" for d in older]
        choice, ok = QInputDialog.getItem(self, "Open a draft", "Choose a saved paper", labels, 0, False)
        if ok and choice in labels:
            self.draft_chosen.emit(older[labels.index(choice)]["draft_id"])

    def _create_format(self, source: dict | None = None) -> None:
        dialog = FormatWizard(self, source=source)
        dialog.setWindowTitle("Duplicate Word template" if source and source.get("docx_template") else "Create paper format")
        if not dialog.exec():
            return
        try:
            new_format = dialog.format_data()
            old_word = (source or {}).get("docx_template")
            new_word = new_format.get("docx_template")
            if new_word and (not old_word or os.path.abspath(new_word) != os.path.abspath(old_word)):
                path = install_word_template(new_format, new_word, self.formats_dir)
            else:
                path = save_new_format(new_format, self.formats_dir)
            fmt = load_format(path)
        except (WordTemplateError, FormatError, OSError, ValueError) as exc:
            QMessageBox.warning(self, "Couldn't create format", str(exc))
            return
        self.reload()
        self.format_chosen.emit(fmt, path)

    def _import_word_template(self) -> None:
        source, _ = QFileDialog.getOpenFileName(
            self, "Choose a sample Word paper", "", "Word documents (*.docx)"
        )
        if not source:
            return
        try:
            proposal = inspect_word_template(source)
        except (WordTemplateError, OSError, ValueError) as exc:
            QMessageBox.warning(self, "Couldn't read template", str(exc))
            return
        dialog = FormatWizard(self, source=proposal)
        dialog.setWindowTitle("Review the imported Word template")
        if not dialog.exec():
            return
        try:
            reviewed = dialog.format_data()
            path = install_word_template(reviewed, reviewed["docx_template"], self.formats_dir)
            fmt = load_format(path)
        except (WordTemplateError, FormatError, OSError, ValueError) as exc:
            QMessageBox.warning(self, "Couldn't save template", str(exc))
            return
        self.reload()
        self.format_chosen.emit(fmt, path)

    def _duplicate_format(self, path: str) -> None:
        try:
            source = load_format(path)
        except FormatError as exc:
            QMessageBox.warning(self, "Couldn't duplicate format", str(exc))
            return
        self._create_format(source)

    def _edit_format(self, path: str) -> None:
        try:
            source = load_format(path)
        except FormatError as exc:
            QMessageBox.warning(self, "Couldn't edit format", str(exc))
            return
        dialog = FormatWizard(self, source=source)
        dialog.setWindowTitle("Edit saved Word template" if source.get("docx_template") else "Edit paper format")
        if not dialog.exec():
            return
        updated = dialog.format_data()
        updated["format_id"] = source["format_id"]
        try:
            original_word = source.get("docx_template")
            revised_word = updated.get("docx_template")
            if original_word and revised_word and os.path.abspath(revised_word) != os.path.abspath(original_word):
                revise_word_template(updated, revised_word, path)
            else:
                update_format(updated, path)
        except (WordTemplateError, FormatError, OSError, ValueError) as exc:
            QMessageBox.warning(self, "Couldn't save format", str(exc))
            return
        self.reload()

    def _delete_format(self, path: str) -> None:
        answer = QMessageBox.question(
            self, "Delete format", f"Delete {os.path.basename(path)} from the format list? Saved drafts will still open.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            os.remove(path)
        except OSError as exc:
            QMessageBox.warning(self, "Couldn't delete format", str(exc))
            return
        self.reload()

    def _open_path(self, path: str) -> None:
        try:
            fmt = load_format(path)
        except FormatError as exc:
            QMessageBox.warning(self, "Couldn't open format", str(exc))
            return
        self.format_chosen.emit(fmt, path)

    def _add_format(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load a format file", "", "Format files (*.json)"
        )
        if not path:
            return
        try:
            load_format(path)  # validate before copying
        except FormatError as exc:
            QMessageBox.warning(self, "That format isn't valid", str(exc))
            return
        # Copy into the formats folder so it shows up next time too.
        dest = os.path.join(self.formats_dir, os.path.basename(path))
        if os.path.abspath(dest) != os.path.abspath(path):
            if os.path.exists(dest):
                QMessageBox.warning(self, "Format already exists", "A format with that file name already exists. Rename the file before adding it.")
                return
            try:
                os.makedirs(self.formats_dir, exist_ok=True)
                shutil.copy2(path, dest)
            except OSError as exc:
                QMessageBox.warning(self, "Couldn't add format", str(exc))
                return
        self.reload()
