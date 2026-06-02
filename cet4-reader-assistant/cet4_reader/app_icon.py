from __future__ import annotations

import ctypes
import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

APP_NAME = "CET-4 阅读助手"
APP_USER_MODEL_ID = "CET4.ReaderAssistant"
APP_ICON_RELATIVE_PATH = Path("assets") / "app.ico"


def app_icon_path(base_dir: Path | None = None) -> Path | None:
    candidates: list[Path] = []

    if base_dir is not None:
        candidates.append(base_dir / APP_ICON_RELATIVE_PATH)

    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        candidates.append(Path(bundle_dir) / APP_ICON_RELATIVE_PATH)

    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / APP_ICON_RELATIVE_PATH)

    candidates.append(Path(__file__).resolve().parents[1] / APP_ICON_RELATIVE_PATH)

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def load_app_icon(base_dir: Path | None = None) -> QIcon:
    icon_path = app_icon_path(base_dir)
    if icon_path is None:
        return QIcon()
    return QIcon(str(icon_path))


def set_windows_app_user_model_id() -> None:
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except (AttributeError, OSError):
        return


def apply_app_metadata(app: QApplication, base_dir: Path | None = None) -> None:
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("CET-4")

    icon = load_app_icon(base_dir)
    if not icon.isNull():
        app.setWindowIcon(icon)
