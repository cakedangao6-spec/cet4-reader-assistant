from __future__ import annotations

import unittest
from datetime import datetime
from pathlib import Path
import tempfile

from cet4_reader.core import (
    calculate_stats,
    clean_ocr_text,
    decode_text_bytes,
    history_filename,
    normalize_word,
    read_text_file,
    sort_vocab,
    update_daily_history_file,
    update_summary_history_file,
    unique_history_path,
)


class CoreTests(unittest.TestCase):
    def test_normalize_word(self) -> None:
        self.assertEqual(normalize_word("Students,"), "students")
        self.assertEqual(normalize_word("(APPLE)"), "apple")

    def test_clean_ocr_text_removes_exam_noise(self) -> None:
        raw = """
        Section B
        Questions 46-50
        Passage Two
        Questions 51 to 55 are based on the following passage.
        Reading is useful.
        A.choose one answer
        B
        46.
        2
        2025 年 6 月大学英语四级考试真题
        It also builds confi-
        dence.
        Part IV
        Translation
        """
        self.assertEqual(clean_ocr_text(raw), "Reading is useful.\nIt also builds confidence.")

    def test_clean_ocr_text_joins_wrapped_article_lines(self) -> None:
        raw = """
        Passage Two
        Chocolates save us from many things, especially emotional distress. They comfort us in times of trouble,
        calming down
        a racing heart by channeling happy calories inside us. We all have faith in chocolates to delight us in an
        instant!
        Recently, chocolate lovers were heartbroken as scientists claimed that they can become extinct by 2050! But
        hey, we
        have some happy news for you. Chocolate
        trees, whose seeds
        are used to make chocolate, grow in the tropical plant world.
        51. What do people believe chocolates can do?
        A) Cheer them up instantly.
        """
        self.assertEqual(
            clean_ocr_text(raw),
            (
                "Chocolates save us from many things, especially emotional distress. "
                "They comfort us in times of trouble, calming down a racing heart by channeling "
                "happy calories inside us. We all have faith in chocolates to delight us in an instant!\n"
                "Recently, chocolate lovers were heartbroken as scientists claimed that they can become "
                "extinct by 2050! But hey, we have some happy news for you. Chocolate trees, whose seeds "
                "are used to make chocolate, grow in the tropical plant world."
            ),
        )

    def test_sort_vocab(self) -> None:
        self.assertEqual(sort_vocab(["pear", "apple", "pear"]), ["apple", "pear"])

    def test_calculate_stats(self) -> None:
        stats = calculate_stats("One two three four.", {"one", "three", "outside"})
        self.assertEqual(stats.total_words, 4)
        self.assertEqual(stats.unknown_words, 2)
        self.assertEqual(stats.unknown_ratio, 0.5)

    def test_history_filename(self) -> None:
        self.assertEqual(
            history_filename(datetime(2026, 5, 15, 20, 11, 35)),
            "2026-05-15_vocab.txt",
        )
        self.assertEqual(
            history_filename(datetime(2026, 5, 15, 20, 11, 35), 2),
            "2026-05-15_vocab.txt",
        )

    def test_unique_history_path_uses_daily_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            history_dir = Path(tmp)
            moment = datetime(2026, 5, 15, 20, 11, 35)
            first = unique_history_path(history_dir, moment)
            first.write_text("first", encoding="utf-8")
            second = unique_history_path(history_dir, moment)
            self.assertEqual(first.name, "2026-05-15_vocab.txt")
            self.assertEqual(second.name, "2026-05-15_vocab.txt")

    def test_update_daily_history_file_merges_and_cleans_old_timestamp_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            history_dir = Path(tmp)
            old_path = history_dir / "2026-05-15_20-11-35_vocab.txt"
            old_path.write_text("Apple!\n123\nmusic\n", encoding="utf-8")

            path = update_daily_history_file(history_dir, {"banana", "Music"}, datetime(2026, 5, 15, 21, 0, 0))

            self.assertEqual(path.name, "2026-05-15_vocab.txt")
            self.assertEqual(path.read_text(encoding="utf-8"), "apple\nbanana\nmusic\n")
            self.assertFalse(old_path.exists())

    def test_update_summary_history_file_collects_all_history_and_current_vocab(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            history_dir = Path(tmp)
            (history_dir / "2026-05-14_vocab.txt").write_text("Pear\nmusic\n", encoding="utf-8")
            (history_dir / "2026-05-15_vocab.txt").write_text("apple\n", encoding="utf-8")

            path = update_summary_history_file(history_dir, {"banana", "music"})

            self.assertEqual(path.name, "AAA_vocab.txt")
            self.assertEqual(path.read_text(encoding="utf-8"), "apple\nbanana\nmusic\npear\n")

    def test_decode_text_bytes_supports_utf8_and_gbk(self) -> None:
        self.assertEqual(decode_text_bytes("Reading is useful.".encode("utf-8")), "Reading is useful.")
        self.assertEqual(decode_text_bytes("阅读 Reading".encode("gbk")), "阅读 Reading")

    def test_read_text_file_normalizes_line_endings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "article.txt"
            path.write_bytes("Music\r\nhelps\rstudy.".encode("utf-8"))
            self.assertEqual(read_text_file(path), "Music\nhelps\nstudy.")


if __name__ == "__main__":
    unittest.main()
