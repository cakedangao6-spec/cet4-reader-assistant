from __future__ import annotations

import collections
import html
import json
import logging
import re
import subprocess
from pathlib import Path

from PyQt6.QtCore import QObject, QPoint, QRunnable, QTimer, Qt, QThreadPool, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QColor,
    QMouseEvent,
    QTextCharFormat,
    QTextCursor,
)
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTextBrowser,
    QTextEdit,
    QToolButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .core import (
    calculate_stats,
    normalize_word,
    sort_vocab,
    update_daily_history_file,
    update_summary_history_file,
    write_vocab_file,
)
from .dictionary import DictionaryEntry, DictionaryService

logger = logging.getLogger(__name__)

DEFAULT_HIGHLIGHT_COLOR = "#fff3b0"
SESSION_SAVE_INTERVAL_MS = 30_000
QUESTION_NUMBER_RE = re.compile(r"^\s*(\d{1,3})[\.\)](?:\s+|$)")
QUESTION_MARKER_RE = re.compile(
    "^\\s*(?:"
    "questions?\\s+\\d{1,3}\\s*(?:[-\\u2013\\u2014]|to)\\s*\\d{1,3}"
    "|questions?\\s+\\d{1,3}"
    "|questions?"
    "|\\u5bf9\\u5e94\\u9898\\u76ee"
    "|\\u9898\\u76ee"
    ")\\s*[:\\uff1a]?\\s*$",
    re.IGNORECASE,
)


class LookupSignals(QObject):
    finished = pyqtSignal(str, object)
    failed = pyqtSignal(str, str)


class LookupWorker(QRunnable):
    def __init__(self, service: DictionaryService, word: str) -> None:
        super().__init__()
        self.service = service
        self.word = word
        self.signals = LookupSignals()

    def run(self) -> None:
        try:
            entry = self.service.lookup_online(self.word)
            self.signals.finished.emit(self.word, entry)
        except Exception as exc:
            logger.exception("Lookup worker failed for word=%s", self.word)
            self.signals.failed.emit(self.word, str(exc))


class TranslateSignals(QObject):
    finished = pyqtSignal(str, str)
    failed = pyqtSignal(str, str)


class TranslateWorker(QRunnable):
    def __init__(self, service: DictionaryService, text: str) -> None:
        super().__init__()
        self.service = service
        self.text = text
        self.signals = TranslateSignals()

    def run(self) -> None:
        try:
            result = self.service.translate_sentence(self.text)
            self.signals.finished.emit(self.text, result or "")
        except Exception as exc:
            self.signals.failed.emit(self.text, str(exc))


class ArticleView(QTextEdit):
    word_clicked = pyqtSignal(str)
    word_added = pyqtSignal(str)
    translate_selected = pyqtSignal(str)
    formatting_changed = pyqtSignal()
    pasted_text = pyqtSignal(str)
    focused = pyqtSignal()

    def __init__(self, intercept_paste: bool = False) -> None:
        super().__init__()
        self.setReadOnly(False)
        self.setAcceptRichText(False)
        self.setPlaceholderText("粘贴文章\n\n直接按 Ctrl+V 把英文文章粘贴到这里。")
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._lemmatize_fn = None
        self._highlight_color = QColor(DEFAULT_HIGHLIGHT_COLOR)
        self._intercept_paste = intercept_paste

    def set_lemmatizer(self, fn: collections.abc.Callable[[str], str] | None) -> None:
        self._lemmatize_fn = fn

    def insertFromMimeData(self, source) -> None:  # type: ignore[override]
        if self._intercept_paste and source.hasText():
            self.pasted_text.emit(source.text())
            return
        super().insertFromMimeData(source)

    def focusInEvent(self, event) -> None:  # type: ignore[override]
        super().focusInEvent(event)
        self.focused.emit()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            word = self._word_at(event.position().toPoint())
            if word:
                self.word_clicked.emit(word)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        raw = self._word_at(event.position().toPoint())
        super().mouseDoubleClickEvent(event)
        if raw:
            normal = normalize_word(raw)
            lemma = self._lemmatize_fn(normal) if self._lemmatize_fn else normal
            # Prefer lemma on double-click; if different, also show lookup for context
            self.word_added.emit(lemma or normal)
            if lemma and lemma != normal:
                self.word_clicked.emit(raw)

    # ── Formatting helpers (used by toolbar & context menu) ─────────────

    def highlight_selection(self, color: QColor) -> None:
        """Apply background highlight color to the current selection."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        fmt = QTextCharFormat()
        fmt.setBackground(color)
        cursor.mergeCharFormat(fmt)
        self.setTextCursor(cursor)
        self.formatting_changed.emit()

    def set_highlight_color(self, color: QColor) -> None:
        self._highlight_color = color

    def set_selection_color(self, color: QColor) -> None:
        """Change font color of the current selection."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        cursor.mergeCharFormat(fmt)
        self.setTextCursor(cursor)
        self.formatting_changed.emit()

    def clear_selection_highlight(self) -> None:
        """Remove background highlight from the current selection."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(Qt.GlobalColor.transparent))
        cursor.mergeCharFormat(fmt)
        self.setTextCursor(cursor)
        self.formatting_changed.emit()

    def selection_is_highlighted(self) -> bool:
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return False

        document = self.document()
        probe = QTextCursor(document)
        has_text = False
        for position in range(cursor.selectionStart(), cursor.selectionEnd()):
            probe.setPosition(position)
            probe.movePosition(QTextCursor.MoveOperation.NextCharacter, QTextCursor.MoveMode.KeepAnchor)
            selected = probe.selectedText()
            if not selected or not selected.strip():
                continue
            has_text = True
            background = probe.charFormat().background()
            if background.style() == Qt.BrushStyle.NoBrush:
                return False
            color = background.color()
            if not color.isValid() or color.alpha() == 0:
                return False
        return has_text

    def toggle_selection_highlight(self) -> None:
        if self.selection_is_highlighted():
            self.clear_selection_highlight()
        else:
            self.highlight_selection(self._highlight_color)

    def clear_selection_formatting(self) -> None:
        """Reset background and foreground on the current selection."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(Qt.GlobalColor.transparent))
        fmt.setForeground(QColor(Qt.GlobalColor.black))
        cursor.mergeCharFormat(fmt)
        self.setTextCursor(cursor)
        self.formatting_changed.emit()

    def contextMenuEvent(self, event) -> None:  # type: ignore[override]
        if self.textCursor().hasSelection():
            self.toggle_selection_highlight()
            event.accept()
            return
        self.createStandardContextMenu().exec(event.globalPos())

    def _emit_translate_selected(self) -> None:
        """Emit ``translate_selected`` with the currently selected text."""
        text = self.textCursor().selectedText().strip()
        if text:
            self.translate_selected.emit(text)

    def _word_at(self, point: QPoint) -> str:
        cursor = self.cursorForPosition(point)
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        return cursor.selectedText()

    def _word_at_cursor(self) -> str:
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        return cursor.selectedText()

    def current_word(self) -> str:
        selected = self.textCursor().selectedText()
        return selected or self._word_at_cursor()


class MainWindow(QMainWindow):
    def __init__(self, base_dir: Path | None = None) -> None:
        super().__init__()
        self.base_dir = base_dir or Path(__file__).resolve().parents[1]
        self.runtime_dir = self.base_dir / "runtime"
        self.session_path = self.runtime_dir / "session.json"
        self.history_dir = self.base_dir / "vocab" / "history"
        self.legacy_history_dir = self.base_dir / "data" / "history"
        self.export_path = self.base_dir / "vocab" / "vocab.txt"
        self.thread_pool = QThreadPool.globalInstance()
        self._dictionary: DictionaryService | None = None
        self.vocab: set[str] = set()
        self.article_text = ""
        self._active_lookup_word = ""
        self._search_matches: list[tuple[ArticleView, int, int]] = []
        self._search_index = -1
        self._current_highlight_color = QColor(DEFAULT_HIGHLIGHT_COLOR)
        self._last_text_editor: ArticleView | None = None

        self.setWindowTitle("CET-4 阅读助手")
        self.resize(1180, 760)
        self._build_ui()
        self._install_shortcuts()
        self._restore_session()
        self._refresh_vocab_list()
        self._refresh_stats()
        self.session_timer = QTimer(self)
        self.session_timer.timeout.connect(self.save_session)
        self.session_timer.start(SESSION_SAVE_INTERVAL_MS)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.save_session()
        if self._dictionary is not None:
            self._dictionary.close()
        super().closeEvent(event)

    @property
    def dictionary(self) -> DictionaryService:
        if self._dictionary is None:
            self._dictionary = DictionaryService(self.base_dir / "data" / "dictionaries")
        return self._dictionary

    def _build_ui(self) -> None:
        toolbar = QToolBar("main", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.open_vocab_dir_action = QAction("打开生词本目录", self)
        self.open_vocab_dir_action.triggered.connect(self.open_vocab_dir)
        toolbar.addAction(self.open_vocab_dir_action)

        self.export_action = QAction("导出 vocab.txt", self)
        self.export_action.triggered.connect(self.export_vocab)
        toolbar.addAction(self.export_action)

        self.reset_action = QAction("一键清空 / 重新开始", self)
        self.reset_action.triggered.connect(self.reset_session)
        toolbar.addAction(self.reset_action)

        self.search_input = QLineEdit(self)
        self.search_input.returnPressed.connect(self.find_next)
        self.search_input.textChanged.connect(self._update_search_results)
        self.search_input.hide()
        self.search_status = QLabel("", self)

        root = QSplitter(Qt.Orientation.Horizontal, self)
        self.setCentralWidget(root)

        left_splitter = QSplitter(Qt.Orientation.Vertical, self)
        root.addWidget(left_splitter)

        article_section = QWidget(self)
        article_layout = QVBoxLayout(article_section)
        article_layout.setContentsMargins(0, 0, 0, 0)
        article_layout.setSpacing(6)
        article_layout.addWidget(QLabel("\u6587\u7ae0\u533a"))

        self.article_view = ArticleView(intercept_paste=True)
        self.article_view.word_clicked.connect(self.show_lookup)
        self.article_view.word_added.connect(self.add_word)
        self.article_view.translate_selected.connect(self._on_translate_selection)
        self.article_view.formatting_changed.connect(self.save_session)
        self.article_view.pasted_text.connect(self._handle_article_paste)
        self.article_view.textChanged.connect(self._on_article_text_changed)
        self.article_view.focused.connect(lambda: self._set_last_text_editor(self.article_view))
        self.article_view.set_lemmatizer(None)
        article_layout.addWidget(self.article_view)
        left_splitter.addWidget(article_section)

        question_section = QWidget(self)
        question_layout = QVBoxLayout(question_section)
        question_layout.setContentsMargins(0, 0, 0, 0)
        question_layout.setSpacing(6)
        question_layout.addWidget(QLabel("\u9898\u76ee\u533a"))
        self.question_view = ArticleView()
        self.question_view.setPlaceholderText("\u9898\u76ee\u533a\uff0c\u53ef\u76f4\u63a5\u5199\u7b54\u6848\uff0c\u4f8b\u5982\uff1aA 46.")
        self.question_view.word_clicked.connect(self.show_lookup)
        self.question_view.word_added.connect(self.add_word)
        self.question_view.translate_selected.connect(self._on_translate_selection)
        self.question_view.formatting_changed.connect(self.save_session)
        self.question_view.textChanged.connect(self._on_question_text_changed)
        self.question_view.focused.connect(lambda: self._set_last_text_editor(self.question_view))
        self.question_view.set_lemmatizer(None)
        question_layout.addWidget(self.question_view)
        left_splitter.addWidget(question_section)
        left_splitter.setSizes([520, 240])

        # ── Formatting toolbar ──
        fmt_toolbar = QToolBar("format", self)
        fmt_toolbar.setMovable(False)
        self.addToolBar(fmt_toolbar)

        hl_btn = QToolButton(self)
        hl_btn.setText("🖍 高亮")
        hl_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        hl_menu = QMenu(self)
        hl_colors: list[tuple[str, QColor]] = [
            ("黄色", QColor("#fff3b0")),
            ("绿色", QColor("#b5e6b5")),
            ("粉色", QColor("#ffccd5")),
            ("蓝色", QColor("#b3d9ff")),
            ("橙色", QColor("#ffddb3")),
        ]
        for label, color in hl_colors:
            act = hl_menu.addAction(label)
            act.triggered.connect(
                lambda _checked, c=color: self.set_highlight_color(c)
            )
        default_hl_act = hl_menu.addAction("恢复默认颜色")
        default_hl_act.triggered.connect(lambda: self.set_highlight_color(QColor(DEFAULT_HIGHLIGHT_COLOR)))
        hl_btn.setMenu(hl_menu)
        fmt_toolbar.addWidget(hl_btn)

        fg_btn = QToolButton(self)
        fg_btn.setText("🎨 字体色")
        fg_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        fg_menu = QMenu(self)
        fg_colors: list[tuple[str, QColor]] = [
            ("红色", QColor("#e63946")),
            ("蓝色", QColor("#1d3557")),
            ("绿色", QColor("#2d6a4f")),
            ("紫色", QColor("#7b2cbf")),
            ("灰色", QColor("#6c757d")),
        ]
        for label, color in fg_colors:
            act = fg_menu.addAction(label)
            act.triggered.connect(
                lambda _checked, c=color: self.set_selection_text_color(c)
            )
        fg_btn.setMenu(fg_menu)
        fmt_toolbar.addWidget(fg_btn)

        clear_fmt_act = QAction("✕ 清除格式", self)
        clear_fmt_act.triggered.connect(self.clear_selection_formatting)
        fmt_toolbar.addAction(clear_fmt_act)

        fmt_toolbar.addSeparator()

        translate_act = QAction("🌐 翻译选中", self)
        translate_act.triggered.connect(self._on_translate_toolbar)
        fmt_toolbar.addAction(translate_act)

        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 14, 14, 14)
        sidebar_layout.setSpacing(12)

        self.stats_label = QLabel()
        self.stats_label.setFrameShape(QFrame.Shape.StyledPanel)
        self.stats_label.setContentsMargins(12, 10, 12, 10)
        sidebar_layout.addWidget(self.stats_label)

        vocab_header = QLabel("生词")
        sidebar_layout.addWidget(vocab_header)

        manual_add_row = QHBoxLayout()
        self.manual_word_input = QLineEdit(self)
        self.manual_word_input.setPlaceholderText("手动添加单词")
        self.manual_word_input.returnPressed.connect(self.add_manual_word)
        manual_add_row.addWidget(self.manual_word_input, 1)
        add_button = QPushButton("添加", self)
        add_button.clicked.connect(self.add_manual_word)
        manual_add_row.addWidget(add_button)
        sidebar_layout.addLayout(manual_add_row)

        self.vocab_list = QListWidget()
        self.vocab_list.itemClicked.connect(self._on_vocab_item_clicked)
        self.vocab_list.itemDoubleClicked.connect(self._on_vocab_item_double_clicked)
        self.vocab_list.itemChanged.connect(self._on_vocab_item_changed)
        sidebar_layout.addWidget(self.vocab_list, 1)

        remove_button = QPushButton("移除选中")
        remove_button.clicked.connect(self.remove_selected_word)
        sidebar_layout.addWidget(remove_button)

        clear_all_button = QPushButton("清空全部")
        clear_all_button.clicked.connect(self.reset_session)
        sidebar_layout.addWidget(clear_all_button)

        detail_header = QLabel("查词")
        sidebar_layout.addWidget(detail_header)

        self.detail_view = QTextBrowser()
        self.detail_view.setOpenExternalLinks(False)
        self.detail_view.setMinimumHeight(190)
        sidebar_layout.addWidget(self.detail_view)

        root.addWidget(sidebar)
        root.setSizes([820, 360])

        status = QStatusBar(self)
        self.setStatusBar(status)

        self.setStyleSheet(
            """
            QTextEdit, QListWidget, QTextBrowser {
                font-size: 15px;
            }
            QLabel {
                font-size: 14px;
            }
            QPushButton {
                min-height: 30px;
            }
            """
        )

    def _set_article_text(self, text: str) -> None:
        if self.article_view.toPlainText() != text:
            self.article_view.setPlainText(text)
        else:
            self.article_text = text
            self._refresh_stats()

    def _on_article_text_changed(self) -> None:
        self.article_text = self.article_view.toPlainText()
        self._refresh_stats()
        self._update_search_results()

    def _on_question_text_changed(self) -> None:
        self._update_search_results()

    def _handle_article_paste(self, text: str) -> None:
        article_text, question_text = self._split_article_questions(text)
        if question_text:
            cursor = self.article_view.textCursor()
            if cursor.hasSelection():
                cursor.insertText(article_text)
                self.article_view.setTextCursor(cursor)
            elif not self.article_view.toPlainText().strip():
                self.article_view.setPlainText(article_text.strip())
            else:
                self._insert_plain_text(self.article_view, article_text)
            self._append_plain_text(self.question_view, question_text.strip())
            self.statusBar().showMessage("\u5df2\u81ea\u52a8\u62c6\u5206\u6587\u7ae0\u548c\u9898\u76ee\u3002", 3000)
            self.save_session()
            return
        self._insert_plain_text(self.article_view, text)

    @staticmethod
    def _split_article_questions(text: str) -> tuple[str, str]:
        lines = text.splitlines(keepends=True)
        candidates: list[tuple[int, int, int]] = []
        marker_offsets: list[int] = []
        offset = 0
        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped and QUESTION_MARKER_RE.match(stripped):
                marker_offsets.append(offset)
            match = QUESTION_NUMBER_RE.match(line)
            if match:
                candidates.append((index, offset, int(match.group(1))))
            offset += len(line)

        if marker_offsets:
            start = marker_offsets[0]
            return text[:start].rstrip(), text[start:].lstrip("\n")

        for pos, (_line_index, start, number) in enumerate(candidates[:-1]):
            next_number = number + 1
            for _next_line, _next_start, candidate_number in candidates[pos + 1:]:
                if candidate_number == next_number:
                    return text[:start].rstrip(), text[start:].lstrip("\n")
                if candidate_number > next_number:
                    break
        return text, ""

    def reidentify_sections(self) -> None:
        question_text = self.question_view.toPlainText()
        article_text = self.article_view.toPlainText()
        if question_text.strip():
            answer = QMessageBox.question(
                self,
                "\u91cd\u65b0\u8bc6\u522b",
                "\u68c0\u6d4b\u5230\u9898\u76ee\u533a\u5df2\u6709\u5185\u5bb9\uff1a\n\u91cd\u65b0\u8bc6\u522b\uff1f",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            source = f"{article_text.rstrip()}\n\n{question_text.lstrip()}" if article_text.strip() else question_text
        else:
            source = article_text

        new_article, new_questions = self._split_article_questions(source)
        if new_questions:
            self.article_view.setPlainText(new_article.strip())
            self.question_view.setPlainText(new_questions.strip())
            self.statusBar().showMessage("\u5df2\u91cd\u65b0\u8bc6\u522b\u5e76\u62c6\u5206\u6587\u7ae0\u548c\u9898\u76ee\u3002", 3000)
        else:
            self.article_view.setPlainText(source)
            self.question_view.clear()
            self.statusBar().showMessage("\u672a\u8bc6\u522b\u5230\u9898\u76ee\uff0c\u5df2\u4fdd\u7559\u5728\u6587\u7ae0\u533a\u3002", 3000)
        self._clear_search_highlights()
        self._search_matches = []
        self._search_index = -1
        self.save_session()

    @staticmethod
    def _selected_plain_text(editor: QTextEdit) -> str:
        return editor.textCursor().selectedText().replace("\u2029", "\n")

    def _text_editors(self) -> list[ArticleView]:
        editors: list[ArticleView] = []
        for name in ("article_view", "question_view"):
            editor = getattr(self, name, None)
            if isinstance(editor, ArticleView):
                editors.append(editor)
        return editors

    def _set_last_text_editor(self, editor: ArticleView) -> None:
        self._last_text_editor = editor

    def _focused_text_editor(self) -> ArticleView | None:
        focused = self.focusWidget()
        for editor in self._text_editors():
            if editor.hasFocus() or focused is editor or focused is editor.viewport():
                self._last_text_editor = editor
                return editor
            if focused is not None and editor.isAncestorOf(focused):
                self._last_text_editor = editor
                return editor
        if self._last_text_editor in self._text_editors():
            return self._last_text_editor
        return None

    def _selected_text_editor(self) -> ArticleView | None:
        focused = self._focused_text_editor()
        if focused is not None and focused.textCursor().hasSelection():
            return focused
        selected_editors = [
            editor for editor in self._text_editors()
            if editor.textCursor().hasSelection()
        ]
        if len(selected_editors) == 1:
            return selected_editors[0]
        if focused in selected_editors:
            return focused
        return selected_editors[0] if selected_editors else None

    def _current_selected_text(self) -> str:
        editor = self._selected_text_editor()
        if editor is None:
            return ""
        return self._selected_plain_text(editor).strip()

    def _clear_search_highlights(self) -> None:
        for editor in self._text_editors():
            editor.setExtraSelections([])

    @staticmethod
    def _insert_plain_text(editor: QTextEdit, text: str) -> None:
        cursor = editor.textCursor()
        cursor.insertText(text)
        editor.setTextCursor(cursor)

    @staticmethod
    def _append_plain_text(editor: QTextEdit, text: str) -> None:
        if not text:
            return
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        existing = editor.toPlainText()
        prefix = "" if not existing or existing.endswith("\n") or text.startswith("\n") else "\n"
        cursor.insertText(prefix + text)
        editor.setTextCursor(cursor)

    def move_selection_to_questions(self) -> None:
        cursor = self.article_view.textCursor()
        if not cursor.hasSelection():
            self.statusBar().showMessage("\u8bf7\u5148\u5728\u6587\u7ae0\u533a\u9009\u4e2d\u5185\u5bb9\u3002", 3000)
            return
        selected = self._selected_plain_text(self.article_view)
        cursor.removeSelectedText()
        self.article_view.setTextCursor(cursor)
        self._append_plain_text(self.question_view, selected)
        self.save_session()

    def move_selection_to_article(self) -> None:
        cursor = self.question_view.textCursor()
        if not cursor.hasSelection():
            self.statusBar().showMessage("\u8bf7\u5148\u5728\u9898\u76ee\u533a\u9009\u4e2d\u5185\u5bb9\u3002", 3000)
            return
        selected = self._selected_plain_text(self.question_view)
        cursor.removeSelectedText()
        self.question_view.setTextCursor(cursor)
        self._append_plain_text(self.article_view, selected)
        self.save_session()

    def open_vocab_dir(self) -> None:
        folder = self.export_path.parent
        folder.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(["explorer.exe", str(folder)])

    def add_manual_word(self) -> None:
        word = normalize_word(self.manual_word_input.text())
        if not word:
            return
        self.manual_word_input.clear()
        self.add_word(word)

    def set_highlight_color(self, color: QColor) -> None:
        self._current_highlight_color = color
        for editor in self._text_editors():
            editor.set_highlight_color(color)
        editor = self._selected_text_editor()
        if editor is not None and editor.textCursor().hasSelection():
            editor.highlight_selection(color)
            self.save_session()

    def set_selection_text_color(self, color: QColor) -> None:
        editor = self._selected_text_editor()
        if editor is not None and editor.textCursor().hasSelection():
            editor.set_selection_color(color)

    def clear_selection_formatting(self) -> None:
        editor = self._selected_text_editor()
        if editor is not None and editor.textCursor().hasSelection():
            editor.clear_selection_formatting()

    def focus_search(self) -> None:
        query, accepted = QInputDialog.getText(
            self,
            "搜索",
            "输入单词或短语",
            text=self.search_input.text(),
        )
        if not accepted:
            return
        self.search_input.setText(query)
        if query:
            self.find_next()

    def _update_search_results(self) -> None:
        query = self.search_input.text() if hasattr(self, "search_input") else ""
        self._search_matches = []
        self._search_index = -1
        if not query:
            self._clear_search_highlights()
            if hasattr(self, "search_status"):
                self.search_status.setText("")
            return

        lower_query = query.lower()
        for editor in self._text_editors():
            lower_text = editor.toPlainText().lower()
            start = 0
            while True:
                index = lower_text.find(lower_query, start)
                if index < 0:
                    break
                self._search_matches.append((editor, index, index + len(query)))
                start = index + max(1, len(query))

        self._render_search_highlights()
        if self._search_matches:
            self.search_status.setText(f"{len(self._search_matches)}")
        else:
            self.search_status.setText("未找到")
            self.statusBar().showMessage("未找到", 2000)

    def _render_search_highlights(self) -> None:
        for editor in self._text_editors():
            selections: list[QTextEdit.ExtraSelection] = []
            document = editor.document()
            for index, (match_editor, start, end) in enumerate(self._search_matches):
                if match_editor is not editor:
                    continue
                cursor = QTextCursor(document)
                cursor.setPosition(start)
                cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format.setBackground(QColor("#cde8ff" if index != self._search_index else "#78c2ff"))
                selections.append(selection)
            editor.setExtraSelections(selections)

    def find_next(self) -> None:
        if not self.search_input.text():
            self.focus_search()
            return
        if not self._search_matches:
            self.statusBar().showMessage("未找到", 2000)
            self.search_status.setText("未找到")
            return
        self._search_index = (self._search_index + 1) % len(self._search_matches)
        editor, start, end = self._search_matches[self._search_index]
        cursor = QTextCursor(editor.document())
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        editor.setFocus(Qt.FocusReason.ShortcutFocusReason)
        editor.ensureCursorVisible()
        self.search_status.setText(f"{self._search_index + 1}/{len(self._search_matches)}")
        self._render_search_highlights()

    def add_word(self, raw_word: str) -> None:
        word = normalize_word(raw_word)
        if not word:
            return

        # Lemmatize before saving to vocab: redesigned → redesign, customers → customer
        lemma = self.dictionary.lemmatizer.lemmatize(word)
        save_word = lemma if lemma and lemma != word else word

        if save_word not in self.vocab:
            self.vocab.add(save_word)
            self._refresh_vocab_list()
            self._refresh_stats()
            self.save_session()
        self.show_lookup(word)

    def show_lookup(self, raw_word: str) -> None:
        word = normalize_word(raw_word)
        if not word:
            return
        self._active_lookup_word = word

        # 1. Immediately show "查询中…" while online runs in background
        self.detail_view.setHtml(self._format_pending_lookup(word))

        # 2. Fire online lookup first
        worker = LookupWorker(self.dictionary, word)
        worker.signals.finished.connect(self._on_lookup_finished)
        worker.signals.failed.connect(self._on_lookup_failed)
        self.thread_pool.start(worker)

    def export_vocab(self) -> None:
        write_vocab_file(
            self.export_path,
            self.vocab,
            lemmatize=self.dictionary.lemmatizer.lemmatize,
        )
        self._save_history_snapshot()
        lemmatized_count = len(set(
            normalize_word(self.dictionary.lemmatizer.lemmatize(w))
            for w in self.vocab
        ))
        self.statusBar().showMessage(
            f"已导出 {lemmatized_count} 个原型词 → {self.export_path}", 4000
        )
        self.save_session()

    def clear_vocab(self) -> None:
        if not self.vocab:
            return
        self.vocab.clear()
        self._refresh_vocab_list()
        self._refresh_stats()
        self.save_session()
        self.detail_view.clear()

    def reset_session(self) -> None:
        self.article_view.clear()
        self.question_view.clear()
        self.vocab.clear()
        self._refresh_vocab_list()
        self.search_input.clear()
        self._clear_search_highlights()
        self.detail_view.clear()
        self._active_lookup_word = ""
        self._search_matches = []
        self._search_index = -1
        self._refresh_stats()
        self.save_session()
        self.statusBar().showMessage("已重新开始。", 3000)

    def remove_selected_word(self) -> None:
        item = self.vocab_list.currentItem()
        if item is None:
            return
        word = item.text()
        self.vocab.discard(word)
        self._refresh_vocab_list()
        self._refresh_stats()
        self.save_session()

    def _on_vocab_item_clicked(self, item: QListWidgetItem) -> None:
        self.show_lookup(item.text())

    def _on_vocab_item_double_clicked(self, item: QListWidgetItem) -> None:
        # Enter edit mode on double-click instead of removing
        self.vocab_list.editItem(item)

    def _on_vocab_item_changed(self, item: QListWidgetItem) -> None:
        old_text = item.data(Qt.ItemDataRole.UserRole) or ""
        new_text = normalize_word(item.text())
        if not new_text:
            # Empty → remove the word
            if old_text:
                self.vocab.discard(old_text)
            self._refresh_vocab_list()
        elif new_text != old_text:
            # Word changed
            if old_text:
                self.vocab.discard(old_text)
            self.vocab.add(new_text)
            self._refresh_vocab_list()
            # Re-select the new word
            for i in range(self.vocab_list.count()):
                if self.vocab_list.item(i).text() == new_text:
                    self.vocab_list.setCurrentRow(i)
                    break
        self._refresh_stats()
        self.save_session()

    def _refresh_vocab_list(self) -> None:
        self.vocab_list.blockSignals(True)
        self.vocab_list.clear()
        for word in sort_vocab(self.vocab):
            item = QListWidgetItem(word)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            item.setData(Qt.ItemDataRole.UserRole, word)  # store original for edit diff
            self.vocab_list.addItem(item)
        self.vocab_list.blockSignals(False)

    def _refresh_stats(self) -> None:
        stats = calculate_stats(self.article_text, self.vocab)
        self.stats_label.setText(
            f"总词数  {stats.total_words}\n"
            f"生词数  {stats.unknown_words}\n"
            f"生词比例  {stats.unknown_ratio:.1%}"
        )

    def _save_history_snapshot(self) -> None:
        update_daily_history_file(self.history_dir, self.vocab)
        update_summary_history_file(self.history_dir, self.vocab)

    def _install_shortcuts(self) -> None:
        search_action = QAction(self)
        search_action.setShortcut("Ctrl+F")
        search_action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        search_action.triggered.connect(self.focus_search)
        self.addAction(search_action)

    def _restore_session(self) -> None:
        if not self.session_path.exists():
            return
        try:
            payload = json.loads(self.session_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            print("[Session Error] failed to read session.json")
            return
        if not isinstance(payload, dict):
            return

        text = str(payload.get("article_text") or "")
        html_payload = payload.get("article_html")
        if isinstance(html_payload, str) and html_payload.strip():
            self.article_view.setHtml(html_payload)
            self.article_text = self.article_view.toPlainText()
        else:
            self.article_view.setPlainText(text)
            self.article_text = text

        question_text = str(payload.get("question_text") or payload.get("questions_text") or "")
        question_html = payload.get("question_html")
        if isinstance(question_html, str) and question_html.strip():
            self.question_view.setHtml(question_html)
        else:
            self.question_view.setPlainText(question_text)

        raw_vocab = payload.get("vocab")
        if isinstance(raw_vocab, list):
            self.vocab = {normalize_word(str(word)) for word in raw_vocab if normalize_word(str(word))}
        self._refresh_vocab_list()
        self._refresh_stats()

    def save_session(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "article_text": self.article_view.toPlainText(),
            "article_html": self.article_view.toHtml(),
            "question_text": self.question_view.toPlainText(),
            "question_html": self.question_view.toHtml(),
            "vocab": sort_vocab(self.vocab),
        }
        self.session_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _on_lookup_finished(self, word: str, entry: DictionaryEntry | None) -> None:
        if word != self._active_lookup_word:
            return
        if entry is not None:
            # Online found a result
            self.detail_view.setHtml(self._format_lookup(word, entry))
        else:
            # Online returned nothing → fall back to local dictionary
            local_entry = self.dictionary.lookup(word)
            if local_entry is not None:
                self.detail_view.setHtml(self._format_lookup(word, local_entry))
            else:
                self.detail_view.setHtml(self._format_lookup(word, None))

    def _on_lookup_failed(self, word: str, message: str) -> None:
        logger.warning("Lookup failed for word=%s error=%s", word, message)
        if word != self._active_lookup_word:
            return
        # Online lookup failed (network error etc.) → fall back to local dictionary
        local_entry = self.dictionary.lookup(word)
        if local_entry is not None:
            self.detail_view.setHtml(self._format_lookup(word, local_entry))
        else:
            self.detail_view.setHtml(self._format_lookup(word, None))

    def _format_pending_lookup(self, word: str) -> str:
        safe_word = html.escape(word)
        return (
            f"<h3>{safe_word}</h3>"
            "<p><b>音标</b> -</p>"
            "<p><b>词性</b> -</p>"
            "<p><b>中文</b><br>查询中...</p>"
            "<p><b>来源</b> 在线词典</p>"
        )

    def _format_lookup(self, word: str, entry: DictionaryEntry | None) -> str:
        safe_word = html.escape(word)
        if entry is None:
            return (
                f"<h3>{safe_word}</h3>"
                "<p><b>音标</b> -</p>"
                "<p><b>词性</b> -</p>"
                "<p><b>中文</b><br>暂无释义</p>"
                "<p><b>来源</b> -</p>"
            )

        headword_note = ""
        if entry.headword != word:
            headword_note = f"<p><b>词形还原</b> {html.escape(entry.headword)}</p>"

        translation = html.escape(entry.translation).replace("\n", "<br>")
        phonetic = html.escape(entry.phonetic) if entry.phonetic else "-"
        pos = html.escape(entry.pos) if entry.pos else "-"
        translation_html = translation or "-"
        return (
            f"<h3>{safe_word}</h3>"
            f"{headword_note}"
            f"<p><b>音标</b> {phonetic}</p>"
            f"<p><b>词性</b> {pos}</p>"
            f"<p><b>中文</b><br>{translation_html}</p>"
            f"<p><b>来源</b> {html.escape(entry.source)}</p>"
        )

    # ── Sentence translation ────────────────────────────────────────────

    def _on_translate_selection(self, text: str) -> None:
        """Called when the user requests translation via context menu or signal."""
        self.detail_view.setHtml(
            "<h3>🌐 翻译中...</h3>"
            f"<p>{html.escape(text[:200])}</p>"
        )
        worker = TranslateWorker(self.dictionary, text)
        worker.signals.finished.connect(self._on_translate_finished)
        worker.signals.failed.connect(self._on_translate_failed)
        self.thread_pool.start(worker)

    def _on_translate_toolbar(self) -> None:
        """Called when the translate toolbar button is clicked — uses selection."""
        text = self._current_selected_text()
        if text:
            self._on_translate_selection(text)
        else:
            self.statusBar().showMessage("请先选中要翻译的文本。", 3000)

    def _on_translate_finished(self, original: str, translated: str) -> None:
        safe_orig = html.escape(original)
        safe_trans = html.escape(translated).replace("\n", "<br>")
        self.detail_view.setHtml(
            "<h3>🌐 翻译结果</h3>"
            f"<p><b>原文</b><br>{safe_orig}</p>"
            f"<p><b>译文</b><br>{safe_trans}</p>"
            "<p><b>来源</b> MyMemory 在线翻译</p>"
        )

    def _on_translate_failed(self, original: str, message: str) -> None:
        self.detail_view.setHtml(
            "<h3>🌐 翻译失败</h3>"
            f"<p><b>原文</b><br>{html.escape(original)}</p>"
            f"<p><b>错误</b> {html.escape(message)}</p>"
        )
