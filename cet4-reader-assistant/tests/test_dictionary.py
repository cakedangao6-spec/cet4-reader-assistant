from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
import sqlite3

from cet4_reader.dictionary import DictionaryEntry, DictionaryService


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

    def test_online_lookup_tries_global_dictionary_after_china_provider_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = DictionaryService(Path(tmp))
            calls: list[str] = []

            def china_provider(word: str) -> DictionaryEntry | None:
                calls.append(f"china:{word}")
                time.sleep(0.05)
                raise TimeoutError("timeout")

            def global_provider(word: str) -> DictionaryEntry | None:
                calls.append(f"global:{word}")
                return DictionaryEntry(
                    word=word,
                    headword=word,
                    phonetic="",
                    translation="a test definition",
                    pos="noun",
                    source="Free Dictionary",
                )

            def translation_provider(word: str) -> DictionaryEntry | None:
                calls.append(f"translation:{word}")
                return None

            service._primary_online_providers = lambda: (china_provider, global_provider)  # type: ignore[method-assign]
            service._fallback_online_providers = lambda: (translation_provider,)  # type: ignore[method-assign]

            entry = service.lookup_online("testing")

            self.assertIsNotNone(entry)
            assert entry is not None
            self.assertEqual(entry.translation, "a test definition")
            self.assertEqual(entry.source, "Free Dictionary")
            self.assertIn("china:testing", calls)
            self.assertIn("global:testing", calls)
            self.assertNotIn("translation:testing", calls)

    def test_online_lookup_continues_after_empty_and_parse_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = DictionaryService(Path(tmp))
            calls: list[str] = []

            def empty_provider(word: str) -> DictionaryEntry | None:
                calls.append(f"empty:{word}")
                return None

            def broken_provider(word: str) -> DictionaryEntry | None:
                calls.append(f"broken:{word}")
                raise ValueError("bad payload")

            def final_provider(word: str) -> DictionaryEntry | None:
                calls.append(f"final:{word}")
                return DictionaryEntry(
                    word=word,
                    headword=word,
                    phonetic="",
                    translation="final result",
                    pos="",
                    source="MyMemory",
                )

            service._primary_online_providers = lambda: (empty_provider, broken_provider)  # type: ignore[method-assign]
            service._fallback_online_providers = lambda: (final_provider,)  # type: ignore[method-assign]

            entry = service.lookup_online("stable")

            self.assertIsNotNone(entry)
            assert entry is not None
            self.assertEqual(entry.translation, "final result")
            self.assertEqual(entry.source, "MyMemory")
            self.assertIn("empty:stable", calls)
            self.assertIn("broken:stable", calls)
            self.assertEqual(calls[-1], "final:stable")

    def test_freedict_translates_definitions_and_simplifies_pos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = DictionaryService(Path(tmp))

            def fake_read_json(url: str, timeout: float = 2.5) -> object:
                if "dictionaryapi.dev" in url:
                    return [
                        {
                            "word": "disease",
                            "phonetic": "dɪˈziːz",
                            "meanings": [
                                {
                                    "partOfSpeech": "noun",
                                    "definitions": [
                                        {"definition": "An abnormal condition of a human, animal or plant."},
                                        {"definition": "A social problem."},
                                    ],
                                },
                                {
                                    "partOfSpeech": "verb",
                                    "definitions": [
                                        {"definition": "To infect with a disease."},
                                    ],
                                },
                            ],
                        }
                    ]
                if "An%20abnormal%20condition" in url:
                    return {"responseData": {"translatedText": "异常状况；疾病"}}
                if "To%20infect%20with%20a%20disease" in url:
                    return {"responseData": {"translatedText": "传染；使患病"}}
                return {"responseData": {"translatedText": ""}}

            service._read_json = fake_read_json  # type: ignore[method-assign]

            entry = service._lookup_freedict("disease")

            self.assertIsNotNone(entry)
            assert entry is not None
            self.assertEqual(entry.pos, "n / v")
            self.assertEqual(entry.translation, "n. 异常状况；疾病\nv. 传染；使患病")
            self.assertEqual(entry.source, "Free Dictionary + MyMemory")

    def test_freedict_keeps_short_english_when_definition_translation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = DictionaryService(Path(tmp))

            def fake_read_json(url: str, timeout: float = 2.5) -> object:
                if "dictionaryapi.dev" in url:
                    return [
                        {
                            "word": "disease",
                            "meanings": [
                                {
                                    "partOfSpeech": "noun",
                                    "definitions": [
                                        {"definition": "An abnormal condition of a human, animal or plant."},
                                    ],
                                },
                            ],
                        }
                    ]
                raise TimeoutError("translation timeout")

            service._read_json = fake_read_json  # type: ignore[method-assign]

            entry = service._lookup_freedict("disease")

            self.assertIsNotNone(entry)
            assert entry is not None
            self.assertEqual(entry.pos, "n")
            self.assertEqual(entry.translation, "n. An abnormal condition of a human, animal or plant.")
            self.assertEqual(entry.source, "Free Dictionary")


if __name__ == "__main__":
    unittest.main()
