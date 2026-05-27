from __future__ import annotations

import csv
import json
import logging
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .core import normalize_word

logger = logging.getLogger(__name__)


class Lemmatizer:
    """Word form → lemma (headword) conversion using lemma.en.txt."""

    def __init__(self, lemma_path: Path) -> None:
        self._form_to_head: dict[str, list[str]] = {}
        self._load(lemma_path)

    def _load(self, path: Path) -> None:
        if not path.exists():
            logger.warning("Lemma file not found: %s", path)
            return
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith(";"):
                    continue
                left, marker, right = line.partition("->")
                if not marker:
                    continue
                # headword/frequency -> form1, form2, ...
                headword = normalize_word(left.split("/", 1)[0])
                if not headword:
                    continue
                # Split forms by comma or whitespace
                for raw_form in re.split(r"[,\s]+", right.strip()):
                    form = normalize_word(raw_form)
                    if form and form != headword:
                        bucket = self._form_to_head.setdefault(form, [])
                        if headword not in bucket:
                            bucket.append(headword)
        except OSError:
            logger.exception("Failed to load lemma file: %s", path)

    def lemmatize(self, word: str) -> str:
        """Return the lemma (headword) for a given word form.

        If the word is already a headword or not found, returns it unchanged.
        """
        key = normalize_word(word)
        if not key:
            return word
        # 1. Lookup in lemma map (authoritative)
        heads = self._form_to_head.get(key)
        if heads:
            return heads[0]
        # 2. Fallback: suffix-based rules for common inflections.
        #    Rules are conservative — they strip suffixes without trying to
        #    guess silent-'e' restoration (e.g. taking -> tak, not take).
        #    The _candidate_forms method in DictionaryService handles
        #    multiple variations for local dictionary lookup, so a
        #    close-enough stem here is acceptable for online fallback use.
        if key.endswith("ies") and len(key) > 4:
            return key[:-3] + "y"
        if key.endswith("ied") and len(key) > 4:
            return key[:-3] + "y"
        if key.endswith("ves") and len(key) > 4:
            return key[:-3] + "f"
        if key.endswith("ing") and len(key) > 4:
            stem = key[:-3]
            if len(stem) >= 2:
                # running -> run (double consonant)
                if stem[-1] == stem[-2]:
                    return stem[:-1]
                return stem
        if key.endswith("ed") and len(key) > 4:
            stem = key[:-2]
            if len(stem) >= 2:
                # stopped -> stop (double consonant)
                if stem[-1] == stem[-2]:
                    return stem[:-1]
                return stem
        if key.endswith("es") and len(key) > 4:
            stem = key[:-2]
            # matches -> match, boxes -> box
            if stem.endswith(("s", "x", "z", "sh", "ch")):
                return stem
            # goes -> go, does -> do
            if len(stem) <= 3:
                return stem
        if key.endswith("s") and len(key) > 3:
            return key[:-1]
        return word


@dataclass(frozen=True)
class DictionaryEntry:
    word: str
    headword: str
    phonetic: str
    translation: str
    pos: str
    source: str


class DictionaryService:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self._entries: dict[str, dict[str, str]] | None = None
        self._lemma_map: dict[str, list[str]] | None = None
        self.source_paths = self._find_csv_sources()
        self.sqlite_path = self._find_sqlite_source()
        self._sqlite_connection: sqlite3.Connection | None = None
        self.lemma_path = self.data_dir / "lemma.en.txt"
        self.lemmatizer = Lemmatizer(self.lemma_path)
        if not self.source_paths and self.sqlite_path is None:
            logger.warning("No local dictionary files found in %s", self.data_dir)

    def _find_csv_sources(self) -> list[Path]:
        paths: list[Path] = []
        preferred_names = ("cet_common.csv", "ecdict.mini.csv")
        fallback_names = ("ecdict.csv",)
        for name in preferred_names:
            candidate = self.data_dir / name
            if candidate.exists():
                paths.append(candidate)
        if paths:
            return paths
        for name in fallback_names:
            candidate = self.data_dir / name
            if candidate.exists():
                logger.warning("Using large CSV dictionary fallback: %s", candidate)
                paths.append(candidate)
        return paths

    def _find_sqlite_source(self) -> Path | None:
        candidate = self.data_dir / "ecdict.sqlite3"
        return candidate if candidate.exists() else None

    @property
    def available(self) -> bool:
        return bool(self.source_paths or self.sqlite_path)

    def close(self) -> None:
        if self._sqlite_connection is not None:
            self._sqlite_connection.close()
            self._sqlite_connection = None

    def _load(self) -> None:
        if self._entries is not None and self._lemma_map is not None:
            return

        self._entries = {}
        self._lemma_map = {}

        for source_path in self.source_paths:
            try:
                with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
                    reader = csv.DictReader(handle)
                    for row in reader:
                        key = normalize_word(row.get("word", ""))
                        if not key:
                            continue
                        self._entries.setdefault(key, row)
                        self._register_exchange_forms(key, row.get("exchange") or "")
            except OSError:
                logger.exception("Failed to load local dictionary file: %s", source_path)

        self._load_lemma_file()

    def lookup(self, raw_word: str) -> DictionaryEntry | None:
        word = normalize_word(raw_word)
        if not word:
            return None

        self._load()
        assert self._entries is not None

        for candidate in self._candidate_forms(word):
            row = self._entries.get(candidate)
            if row is not None:
                return self._entry_from_row(word, candidate, row, "本地词典")
            sqlite_row = self._lookup_sqlite_row(candidate)
            if sqlite_row is not None:
                return self._entry_from_row(word, candidate, sqlite_row, "本地词典")
        return None

    def lookup_online(self, raw_word: str) -> DictionaryEntry | None:
        word = normalize_word(raw_word)
        if not word:
            return None

        # 1. Try the original word through all providers
        entry = self._try_providers(word)
        if entry is not None:
            lemma = self.lemmatizer.lemmatize(word)
            if lemma and lemma != word:
                entry = DictionaryEntry(
                    word=entry.word,
                    headword=lemma,
                    phonetic=entry.phonetic,
                    translation=entry.translation,
                    pos=entry.pos,
                    source=entry.source,
                )
            return entry

        # 2. Try lemmatized form as fallback (e.g. "redesigned" -> "redesign")
        lemma = self.lemmatizer.lemmatize(word)
        if lemma and lemma != word:
            entry = self._try_providers(lemma)
            if entry is not None:
                return DictionaryEntry(
                    word=word,
                    headword=lemma,
                    phonetic=entry.phonetic,
                    translation=entry.translation,
                    pos=entry.pos,
                    source=entry.source,
                )

        # 3. Try simple suffix-stripping for forms the lemmatizer didn't catch
        for candidate in self._simple_online_fallbacks(word):
            if candidate == word or (lemma and candidate == lemma):
                continue
            entry = self._try_providers(candidate)
            if entry is not None:
                return DictionaryEntry(
                    word=word,
                    headword=candidate,
                    phonetic=entry.phonetic,
                    translation=entry.translation,
                    pos=entry.pos,
                    source=entry.source,
                )

        logger.warning("No dictionary result found for word=%s", word)
        return None

    def _try_providers(self, word: str) -> DictionaryEntry | None:
        """Run word through all online providers, returning first match."""
        for provider in (self._lookup_youdao, self._lookup_mymemory, self._lookup_freedict):
            try:
                entry = provider(word)
            except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
                logger.exception("Online dictionary provider failed for word=%s provider=%s", word, provider.__name__)
                continue
            except Exception:
                logger.exception("Unexpected online lookup failure for word=%s provider=%s", word, provider.__name__)
                continue
            if entry is not None:
                return entry
        return None

    @staticmethod
    def _simple_online_fallbacks(word: str) -> list[str]:
        """Generate simple suffix-stripping candidates for online lookup.

        Unlike _candidate_forms (used by local lookup), this is conservative
        and only strips well-known inflections without generating candidates
        that require silent-'e' restoration. Uses elif to avoid double-
        matching when a longer suffix (e.g. ``ies``) overlaps a shorter one
        (e.g. ``s``).
        """
        candidates: list[str] = []
        if word.endswith("ies") and len(word) > 4:
            candidates.append(word[:-3] + "y")
        elif word.endswith("ied") and len(word) > 4:
            candidates.append(word[:-3] + "y")
        elif word.endswith("ves") and len(word) > 4:
            candidates.append(word[:-3] + "f")
        elif word.endswith("ing") and len(word) > 5:
            stem = word[:-3]
            candidates.append(stem)
            if len(stem) >= 2 and stem[-1] == stem[-2]:
                candidates.append(stem[:-1])
        elif word.endswith("ed") and len(word) > 4:
            stem = word[:-2]
            candidates.append(stem)
            if len(stem) >= 2 and stem[-1] == stem[-2]:
                candidates.append(stem[:-1])
        elif word.endswith("es") and len(word) > 3:
            stem = word[:-2]
            if stem.endswith(("s", "x", "z", "sh", "ch")):
                candidates.append(stem)
            if len(stem) <= 3:
                candidates.append(stem)
        elif word.endswith("s") and len(word) > 3 and not word.endswith(("ss", "us")):
            candidates.append(word[:-1])
        # Deduplicate while preserving order
        seen: set[str] = set()
        return [c for c in candidates if not (c in seen or seen.add(c))]

    # ── Sentence-level translation ──────────────────────────────────────
    # Simple throttle: at most one request per 0.3s to avoid hitting rate limits.
    _last_translate_time: float = 0.0

    def translate_sentence(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "zh-CN",
    ) -> str | None:
        """Translate a sentence/paragraph via MyMemory API.

        Returns the translated text, or ``None`` on failure.
        """
        text = text.strip()
        if not text:
            return None

        # Throttle: ensure at least 300ms between API calls
        now = time.monotonic()
        elapsed = now - self.__class__._last_translate_time
        if elapsed < 0.3:
            time.sleep(0.3 - elapsed)
        self.__class__._last_translate_time = time.monotonic()

        try:
            payload = self._read_json(
                f"https://api.mymemory.translated.net/get"
                f"?q={quote(text)}&langpair={source_lang}|{target_lang}"
            )
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
            logger.exception("Sentence translation failed for text=%r", text[:60])
            return None

        response_data = payload.get("responseData")
        if not isinstance(response_data, dict):
            return None
        translated = str(response_data.get("translatedText") or "").strip()
        if not translated or translated.lower() == text.lower():
            return None
        return translated

    def _candidate_forms(self, word: str) -> list[str]:
        candidates: list[str] = []
        if self._lemma_map is not None:
            candidates.extend(self._lemma_map.get(word, []))

        suffixes = (
            ("ies", "y"),
            ("ied", "y"),
            ("ing", ""),
            ("ed", ""),
            ("es", ""),
            ("s", ""),
        )
        for suffix, replacement in suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                stem = word[: -len(suffix)] + replacement
                candidates.append(stem)
                if suffix in {"ing", "ed"} and len(stem) >= 2 and stem[-1] == stem[-2]:
                    candidates.append(stem[:-1])
                if suffix == "ing" and not stem.endswith("e"):
                    candidates.append(stem + "e")
        candidates.append(word)
        seen: set[str] = set()
        return [candidate for candidate in candidates if not (candidate in seen or seen.add(candidate))]

    def _register_exchange_forms(self, headword: str, raw_exchange: str) -> None:
        if self._lemma_map is None or not raw_exchange:
            return
        for item in raw_exchange.split("/"):
            code, _, forms = item.partition(":")
            if code not in {"s", "d", "p", "i", "3", "r", "t"}:
                continue
            for raw_form in forms.split(","):
                form = normalize_word(raw_form)
                if form and form != headword:
                    bucket = self._lemma_map.setdefault(form, [])
                    if headword not in bucket:
                        bucket.append(headword)

    def _load_lemma_file(self) -> None:
        if self._lemma_map is None or not self.lemma_path.exists():
            return
        # Use the same parsing as Lemmatizer
        try:
            for line in self.lemma_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith(";"):
                    continue
                left, marker, right = line.partition("->")
                if not marker:
                    continue
                headword = normalize_word(left.split("/", 1)[0])
                if not headword:
                    continue
                for raw_form in re.split(r"[,\s]+", right.strip()):
                    form = normalize_word(raw_form)
                    if form and form != headword:
                        bucket = self._lemma_map.setdefault(form, [])
                        if headword not in bucket:
                            bucket.append(headword)
        except OSError:
            logger.exception("Failed to load lemma file: %s", self.lemma_path)

    def _lookup_sqlite_row(self, candidate: str) -> dict[str, str] | None:
        if self.sqlite_path is None:
            return None
        if self._sqlite_connection is None:
            try:
                self._sqlite_connection = sqlite3.connect(self.sqlite_path)
                self._sqlite_connection.row_factory = sqlite3.Row
            except sqlite3.Error:
                logger.exception("Failed to open SQLite dictionary: %s", self.sqlite_path)
                self.sqlite_path = None
                return None
        try:
            row = self._sqlite_connection.execute(
                """
                SELECT word, phonetic, translation, pos, exchange
                FROM entries
                WHERE word = ?
                """,
                (candidate,),
            ).fetchone()
        except sqlite3.Error:
            logger.exception("Failed to query SQLite dictionary for word=%s", candidate)
            return None
        return dict(row) if row is not None else None

    def _lookup_youdao(self, word: str) -> DictionaryEntry | None:
        payload = self._read_json(f"https://dict.youdao.com/jsonapi?jsonversion=2&q={quote(word)}")
        ec = payload.get("ec")
        if not isinstance(ec, dict):
            return None
        raw_words = ec.get("word")
        if not isinstance(raw_words, list) or not raw_words:
            return None
        raw_entry = raw_words[0]
        if not isinstance(raw_entry, dict):
            return None

        translations: list[str] = []
        for trans_group in raw_entry.get("trs", []):
            if not isinstance(trans_group, dict):
                continue
            nested = trans_group.get("tr")
            if not isinstance(nested, list):
                continue
            for item in nested:
                if not isinstance(item, dict):
                    continue
                line = item.get("l")
                if not isinstance(line, dict):
                    continue
                values = line.get("i")
                if isinstance(values, list):
                    translations.extend(str(value).strip() for value in values if str(value).strip())
        if not translations:
            return None

        phonetic = str(raw_entry.get("usphone") or raw_entry.get("ukphone") or "").strip()
        pos = self._extract_pos_from_translations(translations)
        return DictionaryEntry(
            word=word,
            headword=word,
            phonetic=phonetic,
            translation="\n".join(translations),
            pos=pos,
            source="在线词典",
        )

    def _lookup_mymemory(self, word: str) -> DictionaryEntry | None:
        payload = self._read_json(
            f"https://api.mymemory.translated.net/get?q={quote(word)}&langpair=en|zh-CN"
        )
        response = payload.get("responseData")
        if not isinstance(response, dict):
            return None
        translated = str(response.get("translatedText") or "").strip()
        if not translated or translated.lower() == word:
            return None
        return DictionaryEntry(
            word=word,
            headword=word,
            phonetic="",
            translation=translated,
            pos="",
            source="在线词典",
        )

    def _lookup_freedict(self, word: str) -> DictionaryEntry | None:
        """Free Dictionary API (https://api.dictionaryapi.dev/) — no key required."""
        payload = self._read_json(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{quote(word)}"
        )
        if not isinstance(payload, list) or not payload:
            return None
        raw_entry = payload[0]
        if not isinstance(raw_entry, dict):
            return None

        word_str = str(raw_entry.get("word") or word)
        phonetic = str(raw_entry.get("phonetic") or "").strip()

        translations: list[str] = []
        pos_list: list[str] = []
        for meaning in raw_entry.get("meanings", []):
            if not isinstance(meaning, dict):
                continue
            part_of_speech = meaning.get("partOfSpeech", "")
            if part_of_speech:
                label = str(part_of_speech).strip()
                if label and label not in pos_list:
                    pos_list.append(label)
            for definition in meaning.get("definitions", []):
                if not isinstance(definition, dict):
                    continue
                def_text = str(definition.get("definition") or "").strip()
                if def_text:
                    translations.append(f"{part_of_speech}. {def_text}")
        if not translations:
            return None

        return DictionaryEntry(
            word=word,
            headword=word,
            phonetic=phonetic,
            translation="\n".join(translations[:5]),
            pos=" / ".join(pos_list),
            source="在线词典",
        )

    @staticmethod
    def _read_json(url: str) -> dict[str, object] | list[object]:
        """Fetch and parse a JSON response. Returns dict or list."""
        request = Request(url, headers={"User-Agent": "CET4ReaderAssistant/1.0"})
        with urlopen(request, timeout=4) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, (dict, list)):
            raise ValueError("Dictionary response must be a JSON object or array.")
        return payload  # type: ignore[return-value]

    @classmethod
    def _entry_from_row(
        cls,
        word: str,
        headword: str,
        row: dict[str, str],
        source: str,
    ) -> DictionaryEntry:
        return DictionaryEntry(
            word=word,
            headword=headword,
            phonetic=(row.get("phonetic") or "").strip(),
            translation=(row.get("translation") or "").strip(),
            pos=cls._format_pos(row.get("pos") or ""),
            source=source,
        )

    @classmethod
    def _extract_pos_from_translations(cls, translations: list[str]) -> str:
        labels: list[str] = []
        for translation in translations:
            if "." not in translation:
                continue
            raw_label, _, _ = translation.partition(".")
            label = raw_label.strip()
            if 1 <= len(label) <= 5 and label.isalpha() and label not in labels:
                labels.append(label)
        return " / ".join(labels)

    @staticmethod
    def _format_pos(raw_pos: str) -> str:
        if not raw_pos:
            return ""
        labels: list[str] = []
        for item in raw_pos.split("/"):
            label = item.split(":", 1)[0].strip()
            if label and label not in labels:
                labels.append(label)
        return " / ".join(labels)
