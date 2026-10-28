# Copyright Cnosu System 2026. GPLv3 license, see the LICENSE.md file.

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
)
import yaml


class ModelGenerator(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        root_dir = Path(__file__).resolve().parent
        config_path = root_dir / "assets" / "config.yaml"

        try:
            with config_path.open("r", encoding="utf-8") as file:
                config = yaml.safe_load(file) or {}

            icon_path = config.get("directories", {}).get(
                "icons", {}
            ).get("model generator", "")

            if icon_path:
                self.setWindowIcon(QIcon(str(root_dir / icon_path)))

        except (OSError, yaml.YAMLError, AttributeError):
            pass

        self.setWindowTitle("Model Generator")
        self.resize(600, 450)

        # Keep the window above Entity and other normal windows.
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        self.setup_ui()

    def setup_ui(self):
        """Build the Model Generator interface."""

        layout = QVBoxLayout(self)

        title = QLabel("Model Generator")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")

        description = QLabel(
            "Create, configure, and export .oef character models. I'll make it work next update I promise."
        )
        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)

        # TODO: Add model creation controls.
        # TODO: Add setup.yaml editing.
        # TODO: Add sprite/resource management.
        # TODO: Add .oef export functionality.
