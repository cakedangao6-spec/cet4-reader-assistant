from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from cet4_reader.app_icon import app_icon_path, load_app_icon
from cet4_reader.ui import MainWindow


class AppIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _make_base_dir(self, temp_dir: Path) -> Path:
        data_dir = temp_dir / "data" / "dictionaries"
        data_dir.mkdir(parents=True)
        (data_dir / "cet_common.csv").write_text(
            "word,phonetic,translation,pos,exchange\n",
            encoding="utf-8",
        )
        return temp_dir

    def test_app_icon_path_falls_back_to_project_asset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            icon_path = app_icon_path(Path(tmp))

        self.assertIsNotNone(icon_path)
        assert icon_path is not None
        self.assertEqual(icon_path.name, "app.ico")
        self.assertTrue(icon_path.exists())

    def test_app_icon_loads_from_ico_asset(self) -> None:
        self.assertFalse(load_app_icon().isNull())

    def test_main_window_sets_runtime_window_icon(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            self.assertFalse(window.windowIcon().isNull())


if __name__ == "__main__":
    unittest.main()
