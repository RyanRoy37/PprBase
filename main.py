"""PprBase — application entry point.

Launches the PyQt6 desktop app: a guided question-paper builder for teachers.
"""

from __future__ import annotations

import json
import os
import shutil
import sys

# Make sure the project root is importable when run as a script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication  # noqa: E402
from PyQt6.QtCore import QSettings  # noqa: E402

from ui.main_window import MainWindow  # noqa: E402
from ui import styles  # noqa: E402

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUNDLE_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
CONFIG_PATH = os.path.join(BUNDLE_DIR, "config", "settings.json")


def load_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            config = json.load(fh)
    except (OSError, json.JSONDecodeError):
        # Sensible defaults if config is missing or broken.
        config = {
            "paths": {"formats_dir": "formats", "output_dir": "output"},
            "editor": {"font_size": 11},
        }

    if getattr(sys, "frozen", False):
        app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
        data_root = os.path.join(app_data, "PprBase")
        legacy_root = os.path.join(app_data, "QuestionCraft")
        if os.path.isdir(legacy_root) and not os.path.exists(data_root):
            shutil.copytree(legacy_root, data_root)
    else:
        data_root = BASE_DIR
    paths = config.setdefault("paths", {})
    for key, default in (("formats_dir", "formats"), ("output_dir", "output"), ("drafts_dir", "drafts")):
        value = paths.get(key, default)
        paths[key] = value if os.path.isabs(value) else os.path.join(data_root, value)
        os.makedirs(paths[key], exist_ok=True)

    if getattr(sys, "frozen", False):
        bundled_formats = os.path.join(BUNDLE_DIR, "formats")
        for name in os.listdir(bundled_formats):
            if name.endswith(".json"):
                target = os.path.join(paths["formats_dir"], name)
                if not os.path.exists(target):
                    shutil.copy2(os.path.join(bundled_formats, name), target)
        bundled_templates = os.path.join(BUNDLE_DIR, "templates")
        if os.path.isdir(bundled_templates):
            user_templates = os.path.join(data_root, "templates")
            os.makedirs(user_templates, exist_ok=True)
            for name in os.listdir(bundled_templates):
                if name.lower().endswith(".docx"):
                    target = os.path.join(user_templates, name)
                    if not os.path.exists(target):
                        shutil.copy2(os.path.join(bundled_templates, name), target)
    return config


def main() -> int:
    config = load_config()
    settings = QSettings("PprBase", "PprBase")
    saved_font = settings.value("font_size")
    if saved_font is None:
        saved_font = QSettings("QuestionCraft", "QuestionCraft").value("font_size")
        if saved_font is not None:
            settings.setValue("font_size", saved_font)
    try:
        font_size = max(9, min(20, int(saved_font))) if saved_font is not None else int(config.get("editor", {}).get("font_size", 11))
    except (TypeError, ValueError):
        font_size = 11
    config.setdefault("editor", {})["font_size"] = font_size

    app = QApplication(sys.argv)
    app.setApplicationName("PprBase")
    app.setStyleSheet(styles.app_stylesheet(font_size))

    window = MainWindow(config)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
