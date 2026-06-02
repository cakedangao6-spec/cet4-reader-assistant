from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from .app_icon import apply_app_metadata, set_windows_app_user_model_id
from .ui import MainWindow


def main() -> int:
    set_windows_app_user_model_id()
    app = QApplication(sys.argv)
    apply_app_metadata(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
