from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sqlite3

from cet4_reader.dictionary import DictionaryService


class DictionaryTests(unittest.TestCase):
    def test_lookup_formats_entry_and_handles_ing_form(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            (data_dir / "ecdict.mini.csv").write_text(
                "word,phonetic,translation,pos\n"
                'study,ˈstʌdi,"学习\\n研究",v:0.8/n:0.2\n',
                encoding="utf-8",
            )
            service = DictionaryService(data_dir)
            entry = service.lookup("studying")

            self.assertIsNotNone(entry)
            assert entry is not None
            self.assertEqual(entry.headword, "study")
            self.assertEqual(entry.phonetic, "ˈstʌdi")
            self.assertEqual(entry.pos, "v / n")
            self.assertEqual(entry.source, "本地词典")

    def test_lookup_handles_common_word_forms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            (data_dir / "ecdict.mini.csv").write_text(
                "word,phonetic,translation,pos,exchange\n"
                'study,ˈstʌdi,"学习\\n研究",v:0.8/n:0.2,p:studied/d:studied/i:studying/3:studies\n'
                'orchestra,ˈɔːkɪstrə,管弦乐队,n:1,s:orchestras\n',
                encoding="utf-8",
            )
            service = DictionaryService(data_dir)

            self.assertEqual(service.lookup("studies").headword, "study")  # type: ignore[union-attr]
            self.assertEqual(service.lookup("studied").headword, "study")  # type: ignore[union-attr]
            self.assertEqual(service.lookup("studying").headword, "study")  # type: ignore[union-attr]
            self.assertEqual(service.lookup("orchestras").headword, "orchestra")  # type: ignore[union-attr]

    def test_bundled_common_dictionary_covers_required_words(self) -> None:
        data_dir = Path(__file__).resolve().parents[1] / "data" / "dictionaries"
        service = DictionaryService(data_dir)
        for word in ("relevant", "important", "music", "classical", "society"):
            with self.subTest(word=word):
                entry = service.lookup(word)
                self.assertIsNotNone(entry)
                assert entry is not None
                self.assertTrue(entry.translation)

    def test_lookup_falls_back_to_sqlite_dictionary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            connection = sqlite3.connect(data_dir / "ecdict.sqlite3")
            try:
                connection.execute(
                    """
                    CREATE TABLE entries (
                        word TEXT PRIMARY KEY,
                        phonetic TEXT NOT NULL,
                        translation TEXT NOT NULL,
                        pos TEXT NOT NULL,
                        exchange TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    INSERT INTO entries(word, phonetic, translation, pos, exchange)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    ("xylophone", "ˈzaɪləfəʊn", "木琴", "n:1", ""),
                )
                connection.commit()
            finally:
                connection.close()

            service = DictionaryService(data_dir)
            entry = service.lookup("xylophone")

            self.assertIsNotNone(entry)
            assert entry is not None
            self.assertEqual(entry.translation, "木琴")
            self.assertEqual(entry.source, "本地词典")
            service.close()


if __name__ == "__main__":
    unittest.main()
