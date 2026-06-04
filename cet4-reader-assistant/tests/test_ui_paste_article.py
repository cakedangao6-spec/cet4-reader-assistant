from __future__ import annotations

import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QMimeData, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QLabel, QMessageBox, QToolBar, QToolButton
from PyQt6.QtGui import QTextCursor

from cet4_reader.ui import MainWindow
from cet4_reader.listening import (
    ListeningAnalyzer,
    ListeningAnalysis,
    CPU_COMPUTE_TYPE,
    CPU_DEVICE,
    GPU_COMPUTE_TYPE,
    GPU_DEVICE,
    ListeningArticle,
    TranscriptSegment,
    TranscriptWord,
    build_article_export_text,
    default_listening_export_path,
    detect_listening_articles,
    format_gpu_status,
    transcribe_audio_with_fallback,
)


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
            self.assertIsNotNone(window.vocab_list.currentItem())
            self.assertEqual(window.vocab_list.currentItem().text(), "music")  # type: ignore[union-attr]
            self.assertIn("生词数  2", window.stats_label.text())

            window.export_vocab()
            self.assertEqual((base_dir / "vocab" / "vocab.txt").read_text(encoding="utf-8"), "music\nsociety\n")
            window.close()

    def test_add_word_selects_existing_vocab_item_on_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.vocab = {"music", "society"}
            window._refresh_vocab_list()

            with patch.object(window, "show_lookup"):
                window.add_word("music")

            self.assertEqual(window.vocab, {"music", "society"})
            self.assertIsNotNone(window.vocab_list.currentItem())
            self.assertEqual(window.vocab_list.currentItem().text(), "music")  # type: ignore[union-attr]
            window.close()

    def test_manual_add_clears_input_and_selects_added_word(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.manual_word_input.setText("Music!")

            with patch.object(window, "show_lookup"):
                window.add_manual_word()

            self.assertEqual(window.manual_word_input.text(), "")
            self.assertEqual(window.vocab, {"music"})
            self.assertIsNotNone(window.vocab_list.currentItem())
            self.assertEqual(window.vocab_list.currentItem().text(), "music")  # type: ignore[union-attr]
            window.close()

    def test_add_word_selects_lemmatized_saved_word(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))

            with patch.object(window, "show_lookup"):
                window.add_word("studying")

            self.assertEqual(window.vocab, {"study"})
            self.assertIsNotNone(window.vocab_list.currentItem())
            self.assertEqual(window.vocab_list.currentItem().text(), "study")  # type: ignore[union-attr]
            window.close()

    def test_edit_vocab_item_replaces_and_selects_new_word(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.vocab = {"study"}
            window._refresh_vocab_list()
            item = window.vocab_list.item(0)

            item.setText("studying")
            QApplication.processEvents()

            self.assertEqual(window.vocab, {"studying"})
            self.assertIsNotNone(window.vocab_list.currentItem())
            self.assertEqual(window.vocab_list.currentItem().text(), "studying")  # type: ignore[union-attr]
            window.close()

    def test_edit_vocab_item_merges_existing_word_and_selects_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.vocab = {"music", "society"}
            window._refresh_vocab_list()
            society_item = window.vocab_list.item(1)

            society_item.setText("music")
            QApplication.processEvents()

            self.assertEqual(window.vocab, {"music"})
            self.assertEqual(window.vocab_list.count(), 1)
            self.assertIsNotNone(window.vocab_list.currentItem())
            self.assertEqual(window.vocab_list.currentItem().text(), "music")  # type: ignore[union-attr]
            window.close()

    def test_edit_vocab_item_to_empty_deletes_word(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.vocab = {"music"}
            window._refresh_vocab_list()
            item = window.vocab_list.item(0)

            item.setText("")
            QApplication.processEvents()

            self.assertEqual(window.vocab, set())
            self.assertEqual(window.vocab_list.count(), 0)
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

    def test_listening_mode_paste_keeps_all_text_in_question_area(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.switch_mode("listening")
            pasted = "Listening prompt.\n\n1. First question?\n2. Second question?"
            mime = QMimeData()
            mime.setText(pasted)

            with patch.object(window, "_handle_article_paste") as split_handler:
                window.listening_question_view.insertFromMimeData(mime)

            split_handler.assert_not_called()
            self.assertEqual(window.listening_question_view.toPlainText(), pasted)
            self.assertEqual(window.article_view.toPlainText(), "")
            self.assertEqual(window.question_view.toPlainText(), "")
            window.close()

    def test_mode_actions_switch_between_reading_and_listening(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))

            window.listening_mode_action.trigger()
            self.assertEqual(window.mode, "listening")
            self.assertIs(window.mode_stack.currentWidget(), window.listening_page)
            self.assertFalse(window.reading_mode_action.isChecked())
            self.assertTrue(window.listening_mode_action.isChecked())

            window.reading_mode_action.trigger()
            self.assertEqual(window.mode, "reading")
            self.assertIs(window.mode_stack.currentWidget(), window.reading_page)
            self.assertTrue(window.reading_mode_action.isChecked())
            self.assertFalse(window.listening_mode_action.isChecked())
            window.close()

    def test_reading_mode_button_is_clickable_in_listening_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.show()
            self.app.processEvents()
            window.switch_mode("listening")
            self.app.processEvents()

            toolbar = window.findChildren(QToolBar)[0]
            action_rect = toolbar.actionGeometry(window.reading_mode_action)
            hit = window.childAt(toolbar.mapTo(window, action_rect.center()))
            self.assertNotIsInstance(hit, QLabel)

            button = next(
                child
                for child in toolbar.findChildren(QToolButton)
                if child.defaultAction() is window.reading_mode_action
            )
            QTest.mouseClick(button, Qt.MouseButton.LeftButton)
            self.app.processEvents()

            self.assertEqual(window.mode, "reading")
            self.assertIs(window.mode_stack.currentWidget(), window.reading_page)
            self.assertTrue(window.reading_mode_action.isChecked())
            self.assertFalse(window.listening_mode_action.isChecked())
            window.close()

    def test_audio_path_is_saved_when_imported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = self._make_base_dir(Path(tmp))
            audio_path = base_dir / "sample.mp3"
            audio_path.write_bytes(b"fake mp3")
            window = MainWindow(base_dir=base_dir)

            window.audio_player.set_audio_file(audio_path)

            payload = json.loads(window.session_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["audio_path"], str(audio_path))
            window.close()

    def test_audio_path_is_restored_on_startup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = self._make_base_dir(Path(tmp))
            audio_path = base_dir / "sample.mp3"
            audio_path.write_bytes(b"fake mp3")
            window = MainWindow(base_dir=base_dir)
            window.audio_player.set_audio_file(audio_path)
            window.close()

            restored = MainWindow(base_dir=base_dir)

            self.assertEqual(restored.saved_audio_path, audio_path)
            self.assertEqual(restored.audio_player.audio_path, audio_path)
            self.assertTrue(restored.audio_player.play_button.isEnabled())
            restored.close()

    def test_reset_session_clears_saved_audio_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = self._make_base_dir(Path(tmp))
            audio_path = base_dir / "sample.mp3"
            audio_path.write_bytes(b"fake mp3")
            window = MainWindow(base_dir=base_dir)
            window.audio_player.set_audio_file(audio_path)

            window.reset_session()

            payload = json.loads(window.session_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["audio_path"], "")
            window.close()

            restored = MainWindow(base_dir=base_dir)
            self.assertIsNone(restored.saved_audio_path)
            self.assertIsNone(restored.audio_player.audio_path)
            self.assertFalse(restored.audio_player.play_button.isEnabled())
            restored.close()

    def test_listening_markers_add_jump_and_delete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            player = window.audio_player

            with (
                patch.object(player.player, "position", return_value=65000),
                patch("cet4_reader.ui.QInputDialog.getText", return_value=("Q22", True)),
            ):
                player.add_marker()

            self.assertEqual(player.markers, [(65000, "Q22")])
            self.assertEqual(player.marker_list.count(), 1)
            self.assertEqual(player.marker_list.item(0).text(), "1. Q22 - 01:05")

            item = player.marker_list.item(0)
            with patch.object(player.player, "setPosition") as set_position:
                player.jump_to_marker(item)
            set_position.assert_called_once_with(65000)

            player.marker_list.setCurrentRow(0)
            player.delete_selected_marker()
            self.assertEqual(player.markers, [])
            self.assertEqual(player.marker_list.count(), 0)
            window.close()

    def test_listening_marker_empty_note_uses_time_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            player = window.audio_player

            with (
                patch.object(player.player, "position", return_value=116000),
                patch("cet4_reader.ui.QInputDialog.getText", return_value=("", True)),
            ):
                player.add_marker()

            self.assertEqual(player.markers, [(116000, "")])
            self.assertEqual(player.marker_list.item(0).text(), "1. 01:56")
            window.close()

    def test_listening_article_detection_skips_prompt_segments(self) -> None:
        segments = [
            TranscriptSegment(0.0, 5.0, "Directions. In this section, you will hear news reports."),
            TranscriptSegment(40.0, 43.0, "Questions 1 to 2 are based on the following news report."),
            TranscriptSegment(43.2, 56.0, "Good evening, this is BBC News."),
            TranscriptSegment(128.0, 131.0, "Questions 3 to 4 are based on the following conversation."),
            TranscriptSegment(131.7, 145.0, "W: Hi Tom, thanks for coming today."),
        ]

        articles = detect_listening_articles(segments)

        self.assertEqual([(item.title, round(item.start, 1)) for item in articles], [("文章1", 43.2), ("文章2", 131.7)])

    def test_listening_article_detection_uses_cet4_material_titles(self) -> None:
        segments = [
            TranscriptSegment(39.7, 41.0, "News Report 1"),
            TranscriptSegment(41.7, 45.4, "A terrified cat has survived a five-mile round trip."),
            TranscriptSegment(100.7, 105.3, "Questions 1 and 2 are based on the news report you have just heard."),
            TranscriptSegment(144.2, 145.1, "News report 2"),
            TranscriptSegment(145.9, 151.7, "In less than a month, the Special Olympics spring games will make a return."),
            TranscriptSegment(396.1, 398.2, "Section B. Directions"),
            TranscriptSegment(425.5, 426.4, "Conversation 1"),
            TranscriptSegment(427.9, 433.5, "Can you please hand me that book over there?"),
        ]

        articles = detect_listening_articles(segments)

        self.assertEqual(
            [(item.title, round(item.start, 1)) for item in articles],
            [("文章1", 41.7), ("文章2", 145.9), ("文章3", 427.9)],
        )

    def test_listening_article_detection_handles_title_prefix_and_section_first_material(self) -> None:
        segments = [
            TranscriptSegment(7.8, 10.0, "Section A, Directions"),
            TranscriptSegment(10.6, 14.1, "In this section, you will hear three news reports."),
            TranscriptSegment(24.5, 33.6, "After you hear a question, choose from four choices marked A, B, C and D."),
            TranscriptSegment(34.0, 40.4, "Then mark the corresponding letter on answer sheet 1 with a single line through the center."),
            TranscriptSegment(41.0, 49.0, "News Report 1 A Florida teenager won the race overall."),
            TranscriptSegment(121.7, 126.7, "Questions 1 and 2 are based on the news report you have just heard."),
            TranscriptSegment(148.7, 153.0, "Question 2 What do we learn about the April contest?"),
            TranscriptSegment(168.2, 174.2, "News report 2 British astronaut Tim Peake is stepping down permanently."),
            TranscriptSegment(559.5, 565.2, "Questions 8 to 11 are based on the conversation you have just heard."),
            TranscriptSegment(626.7, 631.7, "What does the man say he'll do at the end of the conversation?"),
            TranscriptSegment(646.6, 647.7, "Conversation 2."),
            TranscriptSegment(648.8, 655.0, "Good morning. I'm looking for a present for my nephew."),
        ]

        articles = detect_listening_articles(segments)

        self.assertEqual(
            [(item.title, round(item.start, 1)) for item in articles],
            [("文章1", 42.0), ("文章2", 169.2), ("文章3", 648.8)],
        )

    def test_listening_article_detection_handles_prompt_and_material_in_same_segment(self) -> None:
        segments = [
            TranscriptSegment(
                40.0,
                48.0,
                "Questions 1 to 2 are based on the following news report. Good evening, this is BBC News.",
                (
                    TranscriptWord("Questions", 40.0, 40.2),
                    TranscriptWord("1", 40.3, 40.4),
                    TranscriptWord("to", 40.5, 40.6),
                    TranscriptWord("2", 40.7, 40.8),
                    TranscriptWord("are", 40.9, 41.0),
                    TranscriptWord("based", 41.1, 41.3),
                    TranscriptWord("on", 41.4, 41.5),
                    TranscriptWord("the", 41.6, 41.7),
                    TranscriptWord("following", 41.8, 42.1),
                    TranscriptWord("news", 42.2, 42.4),
                    TranscriptWord("report", 42.5, 42.8),
                    TranscriptWord("Good", 43.2, 43.5),
                    TranscriptWord("evening", 43.6, 44.0),
                    TranscriptWord("this", 44.1, 44.2),
                    TranscriptWord("is", 44.3, 44.4),
                ),
            )
        ]

        articles = detect_listening_articles(segments)

        self.assertEqual(len(articles), 1)
        self.assertAlmostEqual(articles[0].start, 43.2)

    def test_listening_cache_reuses_existing_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            audio_path = base_dir / "cet4_2025_12_1.mp3"
            audio_path.write_bytes(b"fake encoded audio bytes")
            (base_dir / "cet4_2025_12_1.pdf").write_text("paper", encoding="utf-8")
            (base_dir / "cet4_2025_12_1_ans.pdf").write_text("answer", encoding="utf-8")
            analyzer = ListeningAnalyzer(base_dir / "cache")
            audio_hash = "not yet"
            cache_path = None
            with patch("cet4_reader.listening.transcribe_audio") as transcribe:
                transcribe.return_value = [
                    TranscriptSegment(40.0, 43.0, "Questions 1 to 2 are based on the following news report."),
                    TranscriptSegment(43.2, 50.0, "Good evening, this is BBC News."),
                ]
                first = analyzer.analyze(audio_path)
                audio_hash = json.loads(Path(first.cache_path).read_text(encoding="utf-8"))["audio_sha256"]
                cache_path = first.cache_path
            self.assertEqual(len(first.articles), 1)
            self.assertFalse(first.from_cache)
            self.assertEqual(Path(cache_path).parent, base_dir / "cache")
            self.assertEqual(audio_hash, json.loads(Path(cache_path).read_text(encoding="utf-8"))["audio_sha256"])

            with patch("cet4_reader.listening.transcribe_audio") as transcribe:
                second = analyzer.analyze(audio_path)
                transcribe.assert_not_called()
            self.assertTrue(second.from_cache)
            self.assertEqual(second.companion_files["paper_pdf"], str(base_dir / "cet4_2025_12_1.pdf"))
            self.assertEqual(second.companion_files["answer_pdf"], str(base_dir / "cet4_2025_12_1_ans.pdf"))
            self.assertEqual(second.runtime_device, CPU_DEVICE)
            self.assertEqual(second.compute_type, CPU_COMPUTE_TYPE)

    def test_listening_force_analysis_ignores_and_overwrites_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            audio_path = base_dir / "cet4_2025_06_2.mp3"
            audio_path.write_bytes(b"fake encoded audio bytes")
            analyzer = ListeningAnalyzer(base_dir / "cache")

            with patch("cet4_reader.listening.transcribe_audio") as transcribe:
                transcribe.return_value = [TranscriptSegment(1.0, 2.0, "First cached text.")]
                first = analyzer.analyze(audio_path)
            self.assertIn("First cached text", first.transcript_text)

            with patch("cet4_reader.listening.transcribe_audio") as transcribe:
                transcribe.return_value = [TranscriptSegment(1.0, 2.0, "Forced fresh text.")]
                second = analyzer.analyze(audio_path, force=True)

            self.assertFalse(second.from_cache)
            self.assertIn("Forced fresh text", second.transcript_text)
            cached_payload = json.loads(Path(second.cache_path).read_text(encoding="utf-8"))
            self.assertIn("Forced fresh text", cached_payload["transcript_text"])

    def test_listening_analysis_keeps_transcript_when_article_split_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            audio_path = base_dir / "sample.mp3"
            audio_path.write_bytes(b"fake encoded audio bytes")
            analyzer = ListeningAnalyzer(base_dir / "cache")

            with patch("cet4_reader.listening.transcribe_audio") as transcribe:
                transcribe.return_value = [
                    TranscriptSegment(1.0, 2.0, "This is raw listening text."),
                    TranscriptSegment(2.0, 3.0, "It has no CET section markers."),
                ]
                result = analyzer.analyze(audio_path)

            self.assertEqual(result.articles, ())
            self.assertEqual(result.segment_count, 2)
            self.assertIn("raw listening text", result.transcript_text)

            with patch("cet4_reader.listening.transcribe_audio") as transcribe:
                cached = analyzer.analyze(audio_path)
                transcribe.assert_not_called()
            self.assertTrue(cached.from_cache)
            self.assertIn("raw listening text", cached.transcript_text)

    def test_listening_analysis_without_articles_uses_raw_mode_without_touching_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.listening_question_view.setPlainText("My listening notes.")
            analysis = ListeningAnalysis(
                audio="sample.mp3",
                audio_path=str(Path(tmp) / "sample.mp3"),
                articles=(),
                companion_files={},
                model="small",
                model_cache="cache",
                requested_device="cpu",
                runtime_device=CPU_DEVICE,
                compute_type=CPU_COMPUTE_TYPE,
                fallback_reason="",
                transcript_text="[00:01] This is raw listening text.",
                segment_count=1,
                duration_seconds=2.0,
                cache_path=str(Path(tmp) / "cache.json"),
                elapsed_seconds=1.0,
                from_cache=False,
            )

            window.audio_player._on_analysis_finished(analysis)

            self.assertEqual(window.audio_player.current_result_mode, "raw")
            self.assertIn("raw listening text", window.audio_player.raw_transcript_view.toPlainText())
            self.assertEqual(window.listening_question_view.toPlainText(), "My listening notes.")
            window.close()

    def test_gpu_status_labels_are_user_readable(self) -> None:
        base = dict(
            audio="sample.mp3",
            audio_path="sample.mp3",
            articles=(),
            companion_files={},
            model="small",
            model_cache="cache",
            compute_type=CPU_COMPUTE_TYPE,
            transcript_text="raw",
            segment_count=1,
            duration_seconds=2.0,
            cache_path="cache.json",
            elapsed_seconds=1.0,
            from_cache=False,
        )
        cpu = ListeningAnalysis(
            **base,
            requested_device="cpu",
            runtime_device=CPU_DEVICE,
            fallback_reason="",
        )
        gpu = ListeningAnalysis(
            **{**base, "compute_type": GPU_COMPUTE_TYPE},
            requested_device="gpu",
            runtime_device=GPU_DEVICE,
            fallback_reason="",
        )
        cublas = ListeningAnalysis(
            **base,
            requested_device="gpu",
            runtime_device=CPU_DEVICE,
            fallback_reason="Library cublas64_12.dll is not found",
        )
        cached = ListeningAnalysis(**{**base, "requested_device": "cpu", "runtime_device": CPU_DEVICE, "fallback_reason": "", "from_cache": True})

        self.assertEqual(format_gpu_status(cpu), "CPU：稳定模式")
        self.assertEqual(format_gpu_status(gpu), "GPU：已启用")
        self.assertIn("cublas64_12.dll", format_gpu_status(cublas))
        self.assertEqual(format_gpu_status(cached), "缓存：已读取")

    def test_listening_export_helpers_build_article_and_raw_text(self) -> None:
        analysis = ListeningAnalysis(
            audio="cet4_2025_06_2.mp3",
            audio_path="cet4_2025_06_2.mp3",
            articles=(
                ListeningArticle("文章1", 43.0),
                ListeningArticle("文章2", 169.0),
            ),
            companion_files={},
            model="small",
            model_cache="cache",
            requested_device="cpu",
            runtime_device=CPU_DEVICE,
            compute_type=CPU_COMPUTE_TYPE,
            fallback_reason="",
            transcript_text="[00:43] First article text.\n[02:49] Second article text.",
            segment_count=2,
            duration_seconds=180.0,
            cache_path="cache.json",
            elapsed_seconds=1.23,
            from_cache=False,
        )

        exported = build_article_export_text(analysis)

        self.assertEqual(default_listening_export_path(Path("cet4_2025_06_2.mp3")).name, "cet4_2025_06_2_listening_articles.txt")
        self.assertIn("文章1 00:43", exported)
        self.assertIn("First article text", exported)
        self.assertIn("文章2 02:49", exported)
        self.assertIn("Second article text", exported)

        raw = build_article_export_text(
            ListeningAnalysis(
                **{
                    **analysis.__dict__,
                    "articles": (),
                    "transcript_text": "[00:01] Raw transcript only.",
                }
            )
        )
        self.assertIn("原始转写", raw)
        self.assertIn("Raw transcript only", raw)

    def test_audio_player_export_writes_txt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            out_path = Path(tmp) / "out.txt"
            window.audio_player.last_analysis = ListeningAnalysis(
                audio="cet4_2025_06_2.mp3",
                audio_path=str(Path(tmp) / "cet4_2025_06_2.mp3"),
                articles=(),
                companion_files={},
                model="small",
                model_cache="cache",
                requested_device="cpu",
                runtime_device=CPU_DEVICE,
                compute_type=CPU_COMPUTE_TYPE,
                fallback_reason="",
                transcript_text="[00:01] Raw transcript only.",
                segment_count=1,
                duration_seconds=2.0,
                cache_path=str(Path(tmp) / "cache.json"),
                elapsed_seconds=1.0,
                from_cache=False,
            )

            with patch("cet4_reader.ui.QFileDialog.getSaveFileName", return_value=(str(out_path), "文本文件 (*.txt)")):
                window.audio_player.export_listening_text()

            self.assertIn("Raw transcript only", out_path.read_text(encoding="utf-8"))
            window.close()

    def test_gpu_transcription_uses_cuda_when_available(self) -> None:
        audio_path = Path("sample.mp3")
        segments = [TranscriptSegment(1.0, 2.0, "News Report 1")]

        with (
            patch("cet4_reader.listening.cuda_is_available", return_value=(True, "")),
            patch("cet4_reader.listening.transcribe_audio", return_value=segments) as transcribe,
        ):
            result = transcribe_audio_with_fallback(audio_path, prefer_gpu=True)

        self.assertEqual(result.segments, segments)
        self.assertEqual(result.requested_device, "gpu")
        self.assertEqual(result.runtime_device, GPU_DEVICE)
        self.assertEqual(result.compute_type, GPU_COMPUTE_TYPE)
        transcribe.assert_called_once_with(
            audio_path,
            model_name="small",
            device=GPU_DEVICE,
            compute_type=GPU_COMPUTE_TYPE,
            progress_callback=None,
        )

    def test_gpu_transcription_falls_back_to_cpu_when_cuda_fails(self) -> None:
        audio_path = Path("sample.mp3")
        segments = [TranscriptSegment(1.0, 2.0, "News Report 1")]

        with (
            patch("cet4_reader.listening.cuda_is_available", return_value=(True, "")),
            patch(
                "cet4_reader.listening.transcribe_audio",
                side_effect=[RuntimeError("Library cublas64_12.dll is not found"), segments],
            ) as transcribe,
        ):
            result = transcribe_audio_with_fallback(audio_path, prefer_gpu=True)

        self.assertEqual(result.segments, segments)
        self.assertEqual(result.requested_device, "gpu")
        self.assertEqual(result.runtime_device, CPU_DEVICE)
        self.assertEqual(result.compute_type, CPU_COMPUTE_TYPE)
        self.assertIn("cublas64_12.dll", result.fallback_reason)
        self.assertEqual(transcribe.call_args_list[0].kwargs["device"], GPU_DEVICE)
        self.assertEqual(transcribe.call_args_list[1].kwargs["device"], CPU_DEVICE)

    def test_gpu_transcription_falls_back_before_init_when_cuda_unavailable(self) -> None:
        audio_path = Path("sample.mp3")
        segments = [TranscriptSegment(1.0, 2.0, "News Report 1")]

        with (
            patch("cet4_reader.listening.cuda_is_available", return_value=(False, "未检测到可用 CUDA 设备")),
            patch("cet4_reader.listening.transcribe_audio", return_value=segments) as transcribe,
        ):
            result = transcribe_audio_with_fallback(audio_path, prefer_gpu=True)

        self.assertEqual(result.segments, segments)
        self.assertEqual(result.requested_device, "gpu")
        self.assertEqual(result.runtime_device, CPU_DEVICE)
        self.assertEqual(result.compute_type, CPU_COMPUTE_TYPE)
        self.assertIn("CUDA", result.fallback_reason)
        transcribe.assert_called_once_with(
            audio_path,
            model_name="small",
            device=CPU_DEVICE,
            compute_type=CPU_COMPUTE_TYPE,
            progress_callback=None,
        )

    def test_audio_player_device_status_mentions_cpu_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            player = window.audio_player
            audio_path = Path(tmp) / "sample.mp3"
            audio_path.write_bytes(b"fake mp3")
            player.set_audio_file(audio_path)
            player.device_combo.setCurrentIndex(1)

            self.assertTrue(player.device_combo.currentData())

            window.close()

    def test_audio_player_article_list_jumps_and_plays(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            player = window.audio_player
            player.articles = [(43200, "文章1"), (131700, "文章2")]
            player._refresh_articles()

            item = player.article_list.item(1)
            with (
                patch.object(player.player, "setPosition") as set_position,
                patch.object(player.player, "play") as play,
                patch.object(player.player, "playbackState", return_value=player.player.PlaybackState.StoppedState),
            ):
                player.jump_to_article(item)

            set_position.assert_called_once_with(131700)
            play.assert_called_once()
            window.close()

    def test_clear_vocab_keeps_reading_article_and_question_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.article_view.setPlainText("Music shapes society.")
            window.question_view.setPlainText("46. What shapes society?")
            window.vocab = {"music", "society"}
            window._refresh_vocab_list()

            window.clear_vocab_button.click()

            self.assertEqual(window.vocab, set())
            self.assertEqual(window.article_view.toPlainText(), "Music shapes society.")
            self.assertEqual(window.question_view.toPlainText(), "46. What shapes society?")
            window.close()

    def test_clear_vocab_keeps_listening_question_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            window = MainWindow(base_dir=self._make_base_dir(Path(tmp)))
            window.switch_mode("listening")
            window.listening_question_view.setPlainText("Q22. What does the speaker mean?")
            window.vocab = {"speaker"}
            window._refresh_vocab_list()

            window.clear_vocab_button.click()

            self.assertEqual(window.vocab, set())
            self.assertEqual(window.listening_question_view.toPlainText(), "Q22. What does the speaker mean?")
            self.assertEqual(window.article_view.toPlainText(), "")
            self.assertEqual(window.question_view.toPlainText(), "")
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
