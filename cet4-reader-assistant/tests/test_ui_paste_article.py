from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QMessageBox, QToolBar
from PyQt6.QtGui import QTextCursor

from cet4_reader.ui import MainWindow


class PasteArticleFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _make_base_dir(self, temp_dir: Path) -> Path:
        data_dir = temp_dir / "data" / "dictionaries"
        data_dir.mkdir(parents=True)
        (data_dir / "cet_common.csv").write_text(
            "word,phonetic,translation,pos,exchange\n"
            "music,ˈmjuːzɪk,音乐,n:1,\n"
            "society,səˈsaɪəti,社会,n:1,\n",
            encoding="utf-8",
        )
        return temp_dir

    def _select_text(self, editor, text: str) -> None:
        cursor = editor.textCursor()
        start = editor.toPlainText().index(text)
        cursor.setPosition(start)
        cursor.setPosition(start + len(text), QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)

    def test_paste_lookup_add_and_export_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = self._make_base_dir(Path(tmp))
            window = MainWindow(base_dir=base_dir)
            window.vocab = {"society"}
            window._refresh_vocab_list()
            window._refresh_stats()

            window.article_view.setPlainText("Relevant music supports society.")

            self.assertEqual(window.article_text, "Relevant music supports society.")
            self.assertIn("总词数  4", window.stats_label.text())
            self.assertIn("生词数  1", window.stats_label.text())
            self.assertIn("生词比例  25.0%", window.stats_label.text())

            entry = window.dictionary.lookup("music")
            self.assertIsNotNone(entry)
            assert entry is not None
            self.assertIn("音乐", entry.translation)

            with patch.object(window, "show_lookup"):
                window.add_word("music")
            self.assertIn("music", window.vocab)
            self.assertIn("生词数  2", window.stats_label.text())

            window.export_vocab()
            self.assertEqual((base_dir / "vocab" / "vocab.txt").read_text(encoding="utf-8"), "music\nsociety\n")
            window.close()

    def test_repeated_exports_merge_into_daily_and_summary_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = self._make_base_dir(Path(tmp))
            window = MainWindow(base_dir=base_dir)
            window.vocab = {"music"}

            window.export_vocab()
            window.vocab = {"society"}
            window.export_vocab()
            window.vocab = {"Music!"}
            window.export_vocab()

            history_files = sorted((base_dir / "vocab" / "history").glob("*_vocab*.txt"))
            names = [path.name for path in history_files]
            daily_files = [name for name in names if name != "AAA_vocab.txt"]
            self.assertEqual(len(daily_files), 1)
            self.assertRegex(daily_files[0], r"^202\d-\d{2}-\d{2}_vocab\.txt$")
            self.assertEqual(
                (base_dir / "vocab" / "history" / daily_files[0]).read_text(encoding="utf-8"),
                "music\nsociety\n",
            )
            self.assertEqual(
                (base_dir / "vocab" / "history" / "AAA_vocab.txt").read_text(encoding="utf-8"),
                "music\nsociety\n",
            )
            window.close()

    def test_toolbar_hides_advanced_split_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            labels = [action.text() for toolbar in window.findChildren(QToolBar) for action in toolbar.actions()]
            self.assertNotIn("\u91cd\u65b0\u8bc6\u522b", labels)
            self.assertNotIn("\u9009\u4e2d\u2192\u9898\u76ee\u533a", labels)
            self.assertNotIn("\u9009\u4e2d\u2192\u6587\u7ae0\u533a", labels)
            window.close()

    def test_toolbar_does_not_show_persistent_search_ui(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            labels = [
                action.text()
                for toolbar in window.findChildren(QToolBar)
                for action in toolbar.actions()
                if action.text()
            ]
            self.assertNotIn("搜索", labels)
            self.assertFalse(window.search_input.isVisible())
            window.close()

    def test_question_area_lookup_and_double_click_add_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            clicked: list[str] = []
            added: list[str] = []
            window.question_view.word_clicked.disconnect(window.show_lookup)
            window.question_view.word_added.disconnect(window.add_word)
            window.question_view.word_clicked.connect(clicked.append)
            window.question_view.word_added.connect(added.append)
            window.question_view.setPlainText("36. Music matters.")
            cursor = window.question_view.textCursor()
            start = window.question_view.toPlainText().index("Music")
            cursor.setPosition(start)
            window.question_view.setTextCursor(cursor)
            self.assertEqual(window.question_view.current_word(), "Music")
            window.question_view.word_clicked.emit(window.question_view.current_word())
            window.question_view.word_added.emit(window.question_view.current_word())
            self.assertEqual(clicked, ["Music"])
            self.assertEqual(added, ["Music"])
            window.close()

    def test_translate_toolbar_uses_question_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.article_view.setPlainText("Article sentence.")
            window.question_view.setPlainText("A 46. What shapes society?")
            self._select_text(window.question_view, "What shapes society?")

            with patch.object(window, "_on_translate_selection") as translate:
                window._on_translate_toolbar()

            translate.assert_called_once_with("What shapes society?")
            window.close()

    def test_translate_toolbar_prefers_focused_selection_when_both_selected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.article_view.setPlainText("Article sentence.")
            window.question_view.setPlainText("Question sentence.")
            self._select_text(window.article_view, "Article sentence.")
            self._select_text(window.question_view, "Question sentence.")
            window._set_last_text_editor(window.question_view)

            with patch.object(window, "_on_translate_selection") as translate:
                window._on_translate_toolbar()

            translate.assert_called_once_with("Question sentence.")
            window.close()

    def test_toolbar_has_no_file_import_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            labels = [action.text() for toolbar in window.findChildren(QToolBar) for action in toolbar.actions()]
            self.assertNotIn("上传图片", labels)
            self.assertNotIn("导入TXT", labels)
            window.close()

    def test_startup_does_not_initialize_dictionary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            self.assertIsNone(window._dictionary)
            window.close()

    def test_session_restore_and_reset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = self._make_base_dir(Path(tmp))
            window = MainWindow(base_dir=base_dir)
            window.article_view.setPlainText("Music shapes society.")
            window.question_view.setPlainText("A 46. What shapes society?")
            with patch.object(window, "show_lookup"):
                window.add_word("music")
            window.save_session()
            window.close()

            restored = MainWindow(base_dir=base_dir)
            self.assertEqual(restored.article_text, "Music shapes society.")
            self.assertEqual(restored.question_view.toPlainText(), "A 46. What shapes society?")
            self.assertEqual(restored.vocab, {"music"})
            restored.reset_session()
            restored.close()

            empty = MainWindow(base_dir=base_dir)
            self.assertEqual(empty.article_text, "")
            self.assertEqual(empty.question_view.toPlainText(), "")
            self.assertEqual(empty.vocab, set())
            empty.close()

    def test_right_click_highlight_toggle_and_session_restore(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = self._make_base_dir(Path(tmp))
            window = MainWindow(base_dir=base_dir)
            window.article_view.setPlainText("Music shapes society.")
            cursor = window.article_view.textCursor()
            cursor.setPosition(0)
            cursor.setPosition(5, QTextCursor.MoveMode.KeepAnchor)
            window.article_view.setTextCursor(cursor)

            window.article_view.toggle_selection_highlight()
            self.assertTrue(window.article_view.selection_is_highlighted())
            window.save_session()
            window.close()

            restored = MainWindow(base_dir=base_dir)
            cursor = restored.article_view.textCursor()
            cursor.setPosition(0)
            cursor.setPosition(5, QTextCursor.MoveMode.KeepAnchor)
            restored.article_view.setTextCursor(cursor)
            self.assertTrue(restored.article_view.selection_is_highlighted())

            restored.article_view.toggle_selection_highlight()
            self.assertFalse(restored.article_view.selection_is_highlighted())
            restored.close()

    def test_question_area_highlight_toggle_and_session_restore(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = self._make_base_dir(Path(tmp))
            window = MainWindow(base_dir=base_dir)
            window.question_view.setPlainText("A 46. What shapes society?")
            self._select_text(window.question_view, "What shapes society")

            window.question_view.toggle_selection_highlight()
            self.assertTrue(window.question_view.selection_is_highlighted())
            window.save_session()
            window.close()

            restored = MainWindow(base_dir=base_dir)
            self._select_text(restored.question_view, "What shapes society")
            self.assertTrue(restored.question_view.selection_is_highlighted())

            restored.question_view.toggle_selection_highlight()
            self.assertFalse(restored.question_view.selection_is_highlighted())
            restored.close()

    def test_no_custom_shortcut_settings_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            menu_labels = [action.text() for action in window.menuBar().actions()]
            self.assertNotIn("设置", menu_labels)
            self.assertFalse(hasattr(window, "hot" + "keys"))
            self.assertFalse((Path(tmp) / "runtime" / ("hot" + "keys.json")).exists())
            window.close()

    def test_paste_splits_article_and_questions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window._handle_article_paste(
                "Classical music matters.\n\n46. What is the passage about?\n47. What does the author imply?"
            )
            self.assertEqual(window.article_view.toPlainText(), "Classical music matters.")
            self.assertIn("46. What is the passage about?", window.question_view.toPlainText())
            self.assertIn("47. What does the author imply?", window.question_view.toPlainText())
            window.close()

    def test_paste_splits_on_consecutive_question_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window._handle_article_paste(
                "Reading builds confidence.\n\n1. First question?\n2. Second question?"
            )
            self.assertEqual(window.article_view.toPlainText(), "Reading builds confidence.")
            self.assertIn("1. First question?", window.question_view.toPlainText())
            window.close()

    def test_move_selected_text_between_article_and_questions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.article_view.setPlainText("Article text.\n46. Question text?")
            cursor = window.article_view.textCursor()
            start = window.article_view.toPlainText().index("46.")
            cursor.setPosition(start)
            cursor.setPosition(len(window.article_view.toPlainText()), QTextCursor.MoveMode.KeepAnchor)
            window.article_view.setTextCursor(cursor)
            window.move_selection_to_questions()
            self.assertEqual(window.article_view.toPlainText(), "Article text.\n")
            self.assertEqual(window.question_view.toPlainText(), "46. Question text?")

            cursor = window.question_view.textCursor()
            cursor.setPosition(0)
            cursor.setPosition(len(window.question_view.toPlainText()), QTextCursor.MoveMode.KeepAnchor)
            window.question_view.setTextCursor(cursor)
            window.move_selection_to_article()
            self.assertEqual(window.question_view.toPlainText(), "")
            self.assertIn("46. Question text?", window.article_view.toPlainText())
            window.close()

    def test_reidentify_splits_questions_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.article_view.setPlainText(
                "The passage discusses music.\n\nQuestions 36-40\n36. What is discussed?\n37. What follows?"
            )
            window.reidentify_sections()
            self.assertEqual(window.article_view.toPlainText(), "The passage discusses music.")
            self.assertIn("Questions 36-40", window.question_view.toPlainText())
            self.assertIn("36. What is discussed?", window.question_view.toPlainText())
            window.close()

    def test_reidentify_splits_question_one_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.article_view.setPlainText(
                "A short passage.\n\nQuestion 1\n1. What is the answer?"
            )
            window.reidentify_sections()
            self.assertEqual(window.article_view.toPlainText(), "A short passage.")
            self.assertIn("Question 1", window.question_view.toPlainText())
            window.close()

    def test_reidentify_splits_chinese_question_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.article_view.setPlainText(
                "Body text.\n\n\u5bf9\u5e94\u9898\u76ee\n36. First item?\n37. Second item?"
            )
            window.reidentify_sections()
            self.assertEqual(window.article_view.toPlainText(), "Body text.")
            self.assertIn("\u5bf9\u5e94\u9898\u76ee", window.question_view.toPlainText())
            window.close()

    def test_reidentify_does_not_overwrite_answers_when_cancelled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            original_article = "New body.\n\nQuestions 36-40\n36. New question?"
            original_questions = "A 36.\nC 37."
            window.article_view.setPlainText(original_article)
            window.question_view.setPlainText(original_questions)
            with patch("cet4_reader.ui.QMessageBox.question", return_value=QMessageBox.StandardButton.No):
                window.reidentify_sections()
            self.assertEqual(window.article_view.toPlainText(), original_article)
            self.assertEqual(window.question_view.toPlainText(), original_questions)
            window.close()

    def test_search_highlights_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.article_view.setPlainText("Music helps. Classical music matters.")
            window.search_input.setText("music")
            self.assertEqual(len(window._search_matches), 2)
            window.find_next()
            self.assertEqual(window.search_status.text(), "1/2")
            window.close()

    def test_search_includes_question_area(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.article_view.setPlainText("No target here.")
            window.question_view.setPlainText("A 46. Music shapes society.")
            window.search_input.setText("music")
            self.assertEqual(len(window._search_matches), 1)

            window.find_next()

            self.assertEqual(window.question_view.textCursor().selectedText(), "Music")
            self.assertEqual(window.search_status.text(), "1/1")
            window.close()

    def test_open_vocab_dir_creates_folder_and_uses_explorer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = self._make_base_dir(Path(tmp))
            window = MainWindow(base_dir=base_dir)
            with patch("cet4_reader.ui.subprocess.Popen") as popen:
                window.open_vocab_dir()
            self.assertTrue((base_dir / "vocab").exists())
            self.assertEqual(popen.call_args.args[0][0], "explorer.exe")
            window.close()


if __name__ == "__main__":
    unittest.main()
