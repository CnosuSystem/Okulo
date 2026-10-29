# Copyright Cnosu System 2026. GPLv3 license, see the LICENSE.md file.

import math
import sys
import zipfile
from pathlib import Path, PurePosixPath

import yaml
from config_editor import ConfigEditor
from model_generator import ModelGenerator
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QMovie, QPainter, QRadialGradient
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QWidget

# -------------------------
# Paths and configuration
# -------------------------

ROOT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = ROOT_DIR / "assets" / "config.yaml"

with CONFIG_PATH.open("r", encoding="utf-8") as file:
    config = yaml.safe_load(file)

MODEL_PATH = ROOT_DIR / config["directories"]["model"]


def load_model(model_path):
    """Load setup.yaml and the idle GIF from a ZIP-based model archive."""

    # Check if the model even exists
    if not model_path.is_file():
        raise FileNotFoundError(f"Model archive not found: {MODEL_PATH}")

    with zipfile.ZipFile(model_path, "r") as archive:
        files = set(archive.namelist())

        # Read the model configuration.
        if "setup.yaml" not in files:
            raise FileNotFoundError(f"'setup.yaml' is missing from {model_path}")

        with archive.open("setup.yaml") as file:
            setup = yaml.safe_load(file)

        if not isinstance(setup, dict):
            raise TypeError("setup.yaml must contain a YAML mapping.")

        # Find the configured idle animation.
        idle_config = setup["anim"]["idle"]
        configured_path = idle_config.get("directory", "")

        # Prevent absolute paths and parent-directory traversal.
        relative_path = PurePosixPath(configured_path)

        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"Invalid animation path: {configured_path}")

        # Support both a file path in 'directory' and an optional
        # separate 'name' field.
        candidates = []

        if idle_config.get("name"):
            candidates.append(relative_path / idle_config["name"])
        else:
            candidates.append(relative_path)

        # The archive in this project uses resources/idle.gif.
        # Fall back to that location if setup.yaml uses another
        # directory, such as sprites/idle.gif.
        filename = relative_path.name

        candidates.extend(
            [
                PurePosixPath("resources") / filename,
                PurePosixPath("resources/idle.gif"),
            ]
        )

        gif_path = next(
            (
                path.as_posix()
                for path in candidates
                if path.as_posix() in files
                and not path.is_absolute()
                and ".." not in path.parts
            ),
            None,
        )

        if gif_path is None:
            raise FileNotFoundError(
                "Could not find the idle animation in the model.\n"
                f"Configured path: {configured_path}\n"
                f"Archive contents: {archive.namelist()}"
            )

        gif_data = archive.read(gif_path)

        # Sleep is optional. If the section is absent, it is disabled.
        anim_config = setup.get("anim", {})
        sleep_config = anim_config.get("sleep", {})

        if not isinstance(sleep_config, dict):
            sleep_config = {}

        sleep_enabled = sleep_config.get("enabled", False) is True
        sleep_gif_data = None

        # Do not inspect the sleep path or wait setting unless enabled.
        if sleep_enabled:
            sleep_path = sleep_config.get("directory", "")

            if not isinstance(sleep_path, str) or not sleep_path:
                raise ValueError(
                    "Sleep is enabled, but anim.sleep.directory is missing."
                )

            relative_sleep_path = PurePosixPath(sleep_path)

            if relative_sleep_path.is_absolute() or ".." in relative_sleep_path.parts:
                raise ValueError(f"Invalid sleep animation path: {sleep_path}")

            sleep_candidates = [relative_sleep_path]

            # Allow the same resources fallback used for idle.
            sleep_candidates.extend(
                [
                    PurePosixPath("resources") / relative_sleep_path.name,
                ]
            )

            sleep_gif_path = next(
                (
                    path.as_posix()
                    for path in sleep_candidates
                    if path.as_posix() in files
                    and not path.is_absolute()
                    and ".." not in path.parts
                ),
                None,
            )

            if sleep_gif_path is None:
                raise FileNotFoundError(f"Sleep animation not found: {sleep_path}")

            sleep_gif_data = archive.read(sleep_gif_path)

    return setup, gif_data, sleep_gif_data


# Load the model once, keeping the GIF bytes in memory.
setup, idle_gif_data, sleep_gif_data = load_model(MODEL_PATH)


class Entity(QWidget):
    def __init__(self):
        super().__init__()

        # -------------------------
        # Window configuration
        # -------------------------

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # -------------------------
        # Animation configuration
        # -------------------------

        sprite_config = setup["sprite"]
        bob_config = sprite_config["bob"]
        shadow_config = sprite_config["shadow"]

        self.sprite_size = int(sprite_config["size"])
        self.bob_time = 0.0
        self.bob_speed = float(bob_config["speed"])
        self.bob_height = float(bob_config["height"])
        self.shadow_enabled = bool(shadow_config["enabled"])
        self.shadow_height = int(shadow_config["height"])

        self.top_padding = int(self.bob_height) + 2

        anim_config = setup.get("anim", {})
        sleep_config = anim_config.get("sleep", {})

        if not isinstance(sleep_config, dict):
            sleep_config = {}

        self.sleep_enabled = sleep_config.get("enabled", False) is True

        self.sleep_wait = (
            float(sleep_config.get("wait", 60)) if self.sleep_enabled else None
        )

        if self.sleep_enabled and self.sleep_wait < 0:
            raise ValueError("Sleep wait cannot be negative.")

        # -------------------------
        # Load GIF from memory
        # -------------------------

        # QMovie needs a readable QIODevice. Keep both the buffer
        # and its backing data alive for the lifetime of the widget.
        self.gif_buffer = QBuffer(self)
        self.gif_buffer.setData(QByteArray(idle_gif_data))

        if not self.gif_buffer.open(QIODevice.OpenModeFlag.ReadOnly):
            raise RuntimeError("Could not open the GIF data buffer.")

        self.movie = QMovie(self.gif_buffer, QByteArray(b"gif"), self)

        self.idle_movie = self.movie

        if not self.movie.isValid():
            raise RuntimeError(
                f"Qt could not load the idle animation from {MODEL_PATH}"
            )

        self.sleep_movie = None
        self.sleep_buffer = None

        self.sleep_timer = None

        if self.sleep_enabled:
            self.sleep_buffer = QBuffer(self)
            self.sleep_buffer.setData(QByteArray(sleep_gif_data))

            if not self.sleep_buffer.open(QIODevice.OpenModeFlag.ReadOnly):
                raise RuntimeError("Could not open the sleep GIF buffer.")

            self.sleep_movie = QMovie(
                self.sleep_buffer,
                QByteArray(b"gif"),
                self,
            )

            if not self.sleep_movie.isValid():
                raise RuntimeError("Qt could not load the sleep GIF.")

            self.sleep_movie.setScaledSize(QSize(self.sprite_size, self.sprite_size))

            self.sleep_movie.frameChanged.connect(self.update)

        self.movie.setScaledSize(QSize(self.sprite_size, self.sprite_size))

        self.resize(
            self.sprite_size,
            self.sprite_size + self.top_padding + self.shadow_height,
        )

        # -------------------------
        # Center on the screen
        # -------------------------

        screen = QApplication.primaryScreen()

        if screen:
            center = screen.availableGeometry().center()

            self.move(
                int(center.x() - self.width() / 2),
                int(center.y() - self.height() / 2),
            )

        self.drag_position = None

        # -------------------------
        # Start GIF animation
        # -------------------------

        self.movie.frameChanged.connect(self.update)
        self.movie.start()

        # Start the sleep countdown only when sleep is enabled.
        if self.sleep_enabled:
            self.sleep_timer = QTimer(self)
            self.sleep_timer.setSingleShot(True)
            self.sleep_timer.timeout.connect(self.start_sleep)

            # Configuration is in seconds; QTimer expects milliseconds.
            self.sleep_timer.start(round(self.sleep_wait * 1000))

        # -------------------------
        # Start bobbing animation
        # -------------------------

        self.bob_timer = QTimer(self)
        self.bob_timer.timeout.connect(self.update_bob)
        self.bob_timer.start(16)

    def draw_shadow(self, painter, bob_offset):
        """Calculate and draw the soft shadow beneath the sprite."""

        # Center the shadow horizontally beneath the character.
        shadow_center_x = self.width() / 2

        # Keep the shadow near the bottom of the sprite's movement area.
        shadow_center_y = self.top_padding + self.sprite_size + self.shadow_height / 2

        # Calculate how high the character is, normalized from 0 to 1.
        # The shadow becomes fainter as the character rises.
        if self.bob_height > 0:
            shadow_spread = 1.0 - (
                (bob_offset + self.bob_height) / (2 * self.bob_height)
            )
        else:
            shadow_spread = 1.0

        # Adjust the shadow's width and opacity.
        shadow_width = 64 * (1 + 0.25 * shadow_spread)
        shadow_alpha = int(65 * shadow_spread)

        # Create a radial gradient that fades toward the edges.
        gradient = QRadialGradient(
            shadow_center_x,
            shadow_center_y,
            shadow_width / 2,
        )

        gradient.setColorAt(
            0.0,
            QColor(0, 0, 0, shadow_alpha),
        )
        gradient.setColorAt(
            0.55,
            QColor(0, 0, 0, int(shadow_alpha * 0.5)),
        )
        gradient.setColorAt(
            1.0,
            QColor(0, 0, 0, 0),
        )

        # Draw the flattened, soft-edged shadow.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)

        painter.drawEllipse(
            int(shadow_center_x - shadow_width / 2),
            int(shadow_center_y - 7),
            int(shadow_width),
            14,
        )

    def update_bob(self):
        self.bob_time += self.bob_speed
        self.update()

    def start_sleep(self):
        """Switch from idle to sleep after the configured wait."""

        if not self.sleep_enabled or self.sleep_movie is None:
            return

        if self.movie is self.sleep_movie:
            return

        self.movie.stop()
        self.movie = self.sleep_movie
        self.movie.start()
        self.update()

    def wake_up(self):
        """Wake the sprite and restart its sleep countdown."""

        if self.sleep_enabled and self.sleep_timer is not None:
            self.sleep_timer.stop()

        # Already using idle? Just reset the countdown.
        if self.movie is not self.idle_movie:
            self.movie.stop()
            self.movie = self.idle_movie
            self.movie.start()

        # Start a fresh countdown only if sleep is enabled.
        if self.sleep_enabled and self.sleep_timer is not None:
            self.sleep_timer.start(round(self.sleep_wait * 1000))

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Calculate the sprite's bobbing position.
        bob_offset = math.sin(self.bob_time) * self.bob_height
        sprite_y = self.top_padding + bob_offset

        # Draw the shadow first so the sprite appears in front of it.
        if self.shadow_enabled:
            self.draw_shadow(painter, bob_offset)

        # Draw the current GIF frame.
        frame = self.movie.currentPixmap()

        if not frame.isNull():
            painter.drawPixmap(
                0,
                int(sprite_y),
                self.sprite_size,
                self.sprite_size,
                frame,
            )

        painter.end()

    def open_model_generator(self):
        """Open or activate the Model Generator."""

        if not hasattr(self, "model_generator"):
            self.model_generator = ModelGenerator(self)

        self.model_generator.show()
        self.model_generator.raise_()
        self.model_generator.activateWindow()

    def open_config_editor(self):
        """Open or activate the Config Editor."""

        if not hasattr(self, "config_editor"):
            self.config_editor = ConfigEditor(self)
            self.config_editor.config_applied.connect(self.reload_config)

        self.config_editor.show()
        self.config_editor.raise_()
        self.config_editor.activateWindow()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.wake_up()

            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

        elif event.button() == Qt.MouseButton.RightButton:
            menu = QMenu(self)
            generator_action = menu.addAction("Model Generator")
            config_action = menu.addAction("Config Editor")
            menu.addSeparator()
            kill_action = menu.addAction("Kill.")

            chosen = menu.exec(event.globalPosition().toPoint())

            if chosen == generator_action:
                self.open_model_generator()

            elif chosen == config_action:
                self.open_config_editor()

            elif chosen == kill_action:
                QApplication.quit()

    def mouseMoveEvent(self, event):
        if (
            self.drag_position is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            self.wake_up()

            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = None

    def reload_config(self):
        """Reload settings and animations without partially applying changes."""

        global config, setup, idle_gif_data, sleep_gif_data, MODEL_PATH

        new_buffer = None
        new_movie = None
        new_sleep_buffer = None
        new_sleep_movie = None
        new_sleep_timer = None

        try:
            # Read the latest application configuration.
            with CONFIG_PATH.open("r", encoding="utf-8") as file:
                new_config = yaml.safe_load(file) or {}

            if not isinstance(new_config, dict):
                raise TypeError("config.yaml must contain a YAML mapping.")

            directories = new_config.get("directories", {})
            if not isinstance(directories, dict):
                raise TypeError("'directories' must contain a YAML mapping.")

            model_value = directories.get("model")
            if not model_value:
                raise ValueError(
                    "The model directory is not configured in directories.model."
                )

            new_model_path = (ROOT_DIR / model_value).resolve()

            # Load the model and its optional sleep animation.
            new_setup, new_gif_data, new_sleep_gif_data = load_model(new_model_path)

            sprite = new_setup["sprite"]
            bob = sprite["bob"]
            shadow = sprite["shadow"]

            new_sprite_size = int(sprite["size"])
            new_bob_speed = float(bob["speed"])
            new_bob_height = float(bob["height"])
            new_shadow_enabled = bool(shadow["enabled"])
            new_shadow_height = int(shadow["height"])

            if new_sprite_size <= 0:
                raise ValueError("Sprite size must be greater than zero.")
            if new_bob_height < 0:
                raise ValueError("Bob height cannot be negative.")
            if new_shadow_height < 0:
                raise ValueError("Shadow height cannot be negative.")
            if new_bob_speed < 0:
                raise ValueError("Bob speed cannot be negative.")

            # Read sleep settings. Missing section means disabled.
            anim = new_setup.get("anim", {})
            sleep_config = anim.get("sleep", {})

            if not isinstance(sleep_config, dict):
                sleep_config = {}

            new_sleep_enabled = sleep_config.get("enabled", False) is True

            new_sleep_wait = (
                float(sleep_config.get("wait", 60)) if new_sleep_enabled else None
            )

            if new_sleep_enabled and new_sleep_wait < 0:
                raise ValueError("Sleep wait cannot be negative.")

            if new_sleep_enabled and new_sleep_gif_data is None:
                raise ValueError("Sleep is enabled, but no sleep animation was loaded.")

            # Build the new idle animation.
            new_buffer = QBuffer(self)
            new_buffer.setData(QByteArray(new_gif_data))

            if not new_buffer.open(QIODevice.OpenModeFlag.ReadOnly):
                raise RuntimeError("Could not open the new idle GIF buffer.")

            new_movie = QMovie(new_buffer, QByteArray(b"gif"), self)

            if not new_movie.isValid():
                raise RuntimeError("Qt could not load the new idle GIF.")

            new_movie.setScaledSize(QSize(new_sprite_size, new_sprite_size))

            # Build the sleep animation only when enabled.
            if new_sleep_enabled:
                new_sleep_buffer = QBuffer(self)
                new_sleep_buffer.setData(QByteArray(new_sleep_gif_data))

                if not new_sleep_buffer.open(QIODevice.OpenModeFlag.ReadOnly):
                    raise RuntimeError("Could not open the new sleep GIF buffer.")

                new_sleep_movie = QMovie(
                    new_sleep_buffer,
                    QByteArray(b"gif"),
                    self,
                )

                if not new_sleep_movie.isValid():
                    raise RuntimeError("Qt could not load the new sleep GIF.")

                new_sleep_movie.setScaledSize(QSize(new_sprite_size, new_sprite_size))
                new_sleep_movie.frameChanged.connect(self.update)

                # Prepare the new countdown before changing the current state.
                new_sleep_timer = QTimer(self)
                new_sleep_timer.setSingleShot(True)
                new_sleep_timer.timeout.connect(self.start_sleep)

            # Connect the idle animation.
            new_movie.frameChanged.connect(self.update)

            # All new resources are valid. Now replace the old ones.
            old_movies = (self.movie, self.sleep_movie)
            old_buffers = (self.gif_buffer, self.sleep_buffer)
            old_timer = self.sleep_timer

            if old_timer is not None:
                old_timer.stop()

            for movie in old_movies:
                if movie is not None:
                    movie.stop()

            # Commit the new configuration.
            config = new_config
            setup = new_setup
            idle_gif_data = new_gif_data
            sleep_gif_data = new_sleep_gif_data
            MODEL_PATH = new_model_path

            self.sprite_size = new_sprite_size
            self.bob_speed = new_bob_speed
            self.bob_height = new_bob_height
            self.shadow_enabled = new_shadow_enabled
            self.shadow_height = new_shadow_height
            self.top_padding = int(self.bob_height) + 2

            self.sleep_enabled = new_sleep_enabled
            self.sleep_wait = new_sleep_wait

            self.gif_buffer = new_buffer
            self.idle_movie = new_movie
            self.sleep_buffer = new_sleep_buffer
            self.sleep_movie = new_sleep_movie
            self.sleep_timer = new_sleep_timer

            # Idle is always the starting animation after a reload.
            self.movie = self.idle_movie

            self.resize(
                self.sprite_size,
                self.sprite_size + self.top_padding + self.shadow_height,
            )

            self.idle_movie.start()

            if self.sleep_enabled:
                self.sleep_timer.start(round(self.sleep_wait * 1000))

            # Release old resources after the replacement is running.
            if old_timer is not None:
                old_timer.deleteLater()

            for movie in old_movies:
                if movie is not None:
                    movie.deleteLater()

            for buffer in old_buffers:
                if buffer is not None:
                    buffer.close()
                    buffer.deleteLater()

            self.update()

        except (
            OSError,
            KeyError,
            TypeError,
            ValueError,
            yaml.YAMLError,
            zipfile.BadZipFile,
            RuntimeError,
        ) as error:
            # Dispose of any replacement resources created before failure.
            if new_sleep_timer is not None:
                new_sleep_timer.stop()
                new_sleep_timer.deleteLater()

            for movie in (new_movie, new_sleep_movie):
                if movie is not None:
                    movie.stop()
                    movie.deleteLater()

            for buffer in (new_buffer, new_sleep_buffer):
                if buffer is not None:
                    buffer.close()
                    buffer.deleteLater()

            QMessageBox.critical(
                self,
                "Reload Failed",
                f"Could not apply the configuration:\n{error}",
            )


# -------------------------
# Application entry point
# -------------------------


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Closing an editor must not terminate the application.
    app.setQuitOnLastWindowClosed(False)

    entity = Entity()
    entity.show()

    sys.exit(app.exec())
