from __future__ import annotations

import collections
import locale
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable


WORD_RE = re.compile(r"[A-Za-z]+")
QUESTION_RANGE_RE = re.compile(
    r"^\s*questions?\s+\d+\s*(?:[-–—]|to)\s*\d+\s*$", re.IGNORECASE
)
QUESTION_RANGE_SENTENCE_RE = re.compile(
    r"^\s*questions?\s+\d+\s*(?:[-–—]|to)\s*\d+\s+are\s+based\s+on\s+the\s+following\s+passage\.?\s*$",
    re.IGNORECASE,
)
SECTION_RE = re.compile(r"^\s*section\s+[A-C]\s*$", re.IGNORECASE)
PASSAGE_RE = re.compile(r"^\s*passage\s+(?:one|two|three|[1-3])\s*$", re.IGNORECASE)
OPTION_RE = re.compile(r"^\s*[A-D][\.\)\]、]\s*.+$")
OPTION_MARKER_RE = re.compile(r"^\s*[A-D]\s*$")
OPTION_NO_PUNCT_RE = re.compile(r"^\s*[A-D][A-Z].+$")
PAGE_RE = re.compile(r"^\s*(?:page\s*)?-?\s*\d+\s*-?\s*$", re.IGNORECASE)
QUESTION_NUMBER_RE = re.compile(r"^\s*\d{1,3}[\.\)]?\s*$")
QUESTION_LINE_RE = re.compile(r"^\s*\d{1,3}[\.\)]\s+.+\?\s*$")
SECTION_END_RE = re.compile(r"^\s*(?:part\s+[ivx]+|translation)\b.*$", re.IGNORECASE)
SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class ReadingStats:
    total_words: int
    unknown_words: int
    unknown_ratio: float


def normalize_word(raw: str) -> str:
    return re.sub(r"[^A-Za-z]", "", raw).lower()


def extract_words(text: str) -> list[str]:
    return [word.lower() for word in WORD_RE.findall(text)]


def sort_vocab(words: Iterable[str]) -> list[str]:
    return sorted({word for word in words if word})


def is_noise_line(line: str) -> bool:
    if not line:
        return False
    return any(
        pattern.match(line)
        for pattern in (
            QUESTION_RANGE_RE,
            QUESTION_RANGE_SENTENCE_RE,
            SECTION_RE,
            PASSAGE_RE,
            OPTION_RE,
            OPTION_MARKER_RE,
            OPTION_NO_PUNCT_RE,
            PAGE_RE,
            QUESTION_NUMBER_RE,
            QUESTION_LINE_RE,
        )
    )


def clean_ocr_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"([A-Za-z])-\s*\n\s*([A-Za-z])", r"\1\2", normalized)

    prepared_lines = [SPACE_RE.sub(" ", raw_line).strip() for raw_line in normalized.split("\n")]
    passage_markers = [index for index, line in enumerate(prepared_lines) if PASSAGE_RE.match(line)]
    if passage_markers:
        start = passage_markers[-1] + 1
        end = next(
            (
                index
                for index in range(start, len(prepared_lines))
                if SECTION_END_RE.match(prepared_lines[index])
            ),
            len(prepared_lines),
        )
        prepared_lines = prepared_lines[start:end]

    cleaned_lines: list[str] = []
    for line in prepared_lines:
        if not re.search(r"[A-Za-z]", line):
            continue
        if is_noise_line(line):
            continue
        if not line:
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            continue
        cleaned_lines.append(line)

    while cleaned_lines and cleaned_lines[-1] == "":
        cleaned_lines.pop()

    return "\n".join(cleaned_lines).strip()


def decode_text_bytes(raw: bytes) -> str:
    encodings = ["utf-8-sig", "utf-8", "gbk"]
    preferred = locale.getpreferredencoding(False)
    for encoding in (preferred, "mbcs"):
        if encoding and encoding.lower() not in {item.lower() for item in encodings}:
            encodings.append(encoding)

    last_error: UnicodeDecodeError | None = None
    for encoding in encodings:
        try:
            return raw.decode(encoding)
        except (LookupError, UnicodeDecodeError) as exc:
            if isinstance(exc, UnicodeDecodeError):
                last_error = exc
            continue

    if last_error is not None:
        raise last_error
    return raw.decode()


def read_text_file(path: Path) -> str:
    text = decode_text_bytes(path.read_bytes())
    return text.replace("\r\n", "\n").replace("\r", "\n")


def calculate_stats(article_text: str, vocab: Iterable[str]) -> ReadingStats:
    words = extract_words(article_text)
    normalized_vocab = {normalize_word(word) for word in vocab if normalize_word(word)}
    article_vocab = set(words)
    total_words = len(words)
    unknown_words = len(normalized_vocab & article_vocab)
    unknown_ratio = (unknown_words / total_words) if total_words else 0.0
    return ReadingStats(
        total_words=total_words,
        unknown_words=unknown_words,
        unknown_ratio=unknown_ratio,
    )


def write_vocab_file(
    path: Path,
    vocab: Iterable[str],
    lemmatize: collections.abc.Callable[[str], str] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    words: list[str] = []
    for word in sort_vocab(normalize_word(word) for word in vocab):
        if lemmatize:
            lemma = normalize_word(lemmatize(word))
            if lemma:
                words.append(lemma)
        else:
            words.append(word)
    # Deduplicate after lemmatization
    words = sort_vocab(words)
    path.write_text("\n".join(words) + ("\n" if words else ""), encoding="utf-8")


def load_vocab_file(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {normalize_word(line) for line in path.read_text(encoding="utf-8").splitlines() if normalize_word(line)}


def history_filename(moment: datetime | date | None = None, sequence: int | None = None) -> str:
    chosen = moment or datetime.now()
    if isinstance(chosen, datetime):
        stem = chosen.strftime("%Y-%m-%d_vocab")
    else:
        stem = f"{chosen.isoformat()}_vocab"
    return f"{stem}.txt"


def unique_history_path(history_dir: Path, moment: datetime | None = None) -> Path:
    chosen = moment or datetime.now()
    return history_dir / history_filename(chosen)


def timestamped_history_paths(history_dir: Path, moment: datetime | date | None = None) -> list[Path]:
    chosen = moment or datetime.now()
    day = chosen.date() if isinstance(chosen, datetime) else chosen
    daily_name = history_filename(day)
    prefix = f"{day.isoformat()}_"
    return sorted(
        path
        for path in history_dir.glob(f"{prefix}*_vocab*.txt")
        if path.name != daily_name
    )


def update_daily_history_file(
    history_dir: Path,
    vocab: Iterable[str],
    moment: datetime | date | None = None,
) -> Path:
    history_dir.mkdir(parents=True, exist_ok=True)
    path = unique_history_path(history_dir, moment if isinstance(moment, datetime) else None)
    if isinstance(moment, date) and not isinstance(moment, datetime):
        path = history_dir / history_filename(moment)

    merged = load_vocab_file(path)
    for old_path in timestamped_history_paths(history_dir, moment):
        merged.update(load_vocab_file(old_path))
    merged.update(vocab)
    write_vocab_file(path, merged)

    for old_path in timestamped_history_paths(history_dir, moment):
        old_path.unlink(missing_ok=True)
    return path


def update_summary_history_file(history_dir: Path, vocab: Iterable[str]) -> Path:
    history_dir.mkdir(parents=True, exist_ok=True)
    summary_path = history_dir / "AAA_vocab.txt"
    merged = set()
    for path in history_dir.glob("*_vocab*.txt"):
        if path.name == summary_path.name:
            continue
        merged.update(load_vocab_file(path))
    merged.update(vocab)
    write_vocab_file(summary_path, merged)
    return summary_path
