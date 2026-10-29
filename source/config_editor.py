# Copyright Cnosu System 2026. GPLv3 license, see the LICENSE.md file.

from pathlib import Path

import yaml
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

ROOT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = ROOT_DIR / "assets" / "config.yaml"


class ConfigEditor(QDialog):
    config_applied = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Config Editor")
        self.resize(650, 220)

        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        self.path_inputs = {}

        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        fields = [
            ("model", "Model Archive", "model"),
            ("config editor", "Config Editor Icon", "image"),
            ("model generator", "Model Generator Icon", "image"),
        ]

        for key, label, file_type in fields:
            row = QHBoxLayout()

            path_input = QLineEdit()
            path_input.setPlaceholderText(f"Path to {label.lower()}...")
            self.path_inputs[key] = path_input

            browse_button = QPushButton("Browse...")
            browse_button.clicked.connect(
                lambda checked=False, k=key, t=file_type: self.browse_path(k, t)
            )

            row.addWidget(path_input)
            row.addWidget(browse_button)

            form.addRow(f"{label}:", row)

        layout.addLayout(form)

        buttons = QHBoxLayout()

        reload_button = QPushButton("Reload")
        save_button = QPushButton("Save")

        reload_button.clicked.connect(self.reload_config)
        save_button.clicked.connect(self.save_config)

        buttons.addWidget(reload_button)
        buttons.addWidget(save_button)

        layout.addLayout(buttons)

    def browse_path(self, key, file_type):
        """Browse for an icon image or model archive."""

        if file_type == "image":
            file_filter = "Image files (*.png *.ico *.jpg *.jpeg *.svg);;All files (*)"
        else:
            file_filter = "Model archives (*.oef *.oemf);;All files (*)"

        current = self.path_inputs[key].text().strip()
        start_dir = str(ROOT_DIR / current) if current else str(ROOT_DIR)

        if not Path(start_dir).is_dir():
            start_dir = str(Path(start_dir).parent)

        path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {key}",
            start_dir,
            file_filter,
        )

        if path:
            try:
                relative_path = Path(path).resolve().relative_to(ROOT_DIR)
                display_path = relative_path.as_posix()
            except ValueError:
                display_path = path

            self.path_inputs[key].setText(display_path)

    def load_config(self):
        """Load directory and icon paths from config.yaml."""

        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as file:
                config = yaml.safe_load(file) or {}

            if not isinstance(config, dict):
                raise TypeError("Configuration must be a YAML mapping.")

            directories = config.get("directories", {})

            if not isinstance(directories, dict):
                raise TypeError("'directories' must be a YAML mapping.")

            icons = directories.get("icons", {})

            if not isinstance(icons, dict):
                raise TypeError("'directories.icons' must be a YAML mapping.")

            self.path_inputs["model"].setText(str(directories.get("model", "")))
            self.path_inputs["config editor"].setText(
                str(icons.get("config editor", ""))
            )
            self.path_inputs["model generator"].setText(
                str(icons.get("model generator", ""))
            )

            icon_path = icons.get("config editor", "")
            if icon_path:
                self.setWindowIcon(QIcon(str(ROOT_DIR / icon_path)))

            icons = directories.get("icons", {})
            icon_path = icons.get("config editor", "")

            if icon_path:
                self.setWindowIcon(QIcon(str(ROOT_DIR / icon_path)))

            return True

        except (OSError, yaml.YAMLError, TypeError, ValueError) as error:
            QMessageBox.critical(
                self,
                "Configuration Error",
                f"Could not load configuration:\n{error}",
            )
            return False

    def reload_config(self):
        """Discard edits and reload saved settings."""

        if self.load_config():
            self.config_applied.emit()

    def save_config(self):
        """Save model and nested icon paths."""

        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as file:
                config = yaml.safe_load(file) or {}

            if not isinstance(config, dict):
                raise TypeError("Configuration must be a YAML mapping.")

            directories = config.setdefault("directories", {})

            if not isinstance(directories, dict):
                raise TypeError("'directories' must be a YAML mapping.")

            icons = directories.setdefault("icons", {})

            if not isinstance(icons, dict):
                raise TypeError("'directories.icons' must be a YAML mapping.")

            directories["model"] = self.path_inputs["model"].text().strip()

            icons["config editor"] = self.path_inputs["config editor"].text().strip()
            icons["model generator"] = (
                self.path_inputs["model generator"].text().strip()
            )

            with CONFIG_PATH.open("w", encoding="utf-8") as file:
                yaml.safe_dump(
                    config,
                    file,
                    sort_keys=False,
                    allow_unicode=True,
                )

        except (OSError, yaml.YAMLError, TypeError, ValueError) as error:
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Could not save configuration:\n{error}",
            )
            return

        QMessageBox.information(
            self,
            "Configuration Saved",
            "Directory paths saved. Click Reload to apply changes.",
        )
