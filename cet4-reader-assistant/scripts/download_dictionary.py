from __future__ import annotations

import argparse
import csv
import shutil
import sqlite3
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parents[1]
DICT_DIR = BASE_DIR / "data" / "dictionaries"

ECDICT_URL = "https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv"
LEMMA_URL = "https://raw.githubusercontent.com/skywind3000/ECDICT/master/lemma.en.txt"

MIN_EXPECTED_ROWS = 100_000
REQUIRED_WORDS = {"relevant", "important", "music", "classical", "society", "study", "orchestra"}


def download_file(url: str, destination: Path) -> None:
    request = Request(url, headers={"User-Agent": "CET4ReaderAssistant/1.0"})
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(request, timeout=20) as response, tempfile.NamedTemporaryFile(
        "wb",
        delete=False,
        dir=destination.parent,
        prefix=f"{destination.name}.",
        suffix=".tmp",
    ) as temp_file:
        shutil.copyfileobj(response, temp_file)
        temp_path = Path(temp_file.name)
    temp_path.replace(destination)


def inspect_dictionary(path: Path) -> tuple[int, set[str]]:
    if not path.exists():
        return 0, set()
    rows = 0
    words: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows += 1
            word = (row.get("word") or "").strip().lower()
            if word in REQUIRED_WORDS:
                words.add(word)
    return rows, words


def is_valid_dictionary(path: Path) -> bool:
    rows, words = inspect_dictionary(path)
    return rows >= MIN_EXPECTED_ROWS and REQUIRED_WORDS.issubset(words)


def ensure_dictionary(force: bool = False) -> Path:
    target = DICT_DIR / "ecdict.csv"
    if not force and is_valid_dictionary(target):
        return target
    download_file(ECDICT_URL, target)
    if not is_valid_dictionary(target):
        raise RuntimeError(f"Downloaded dictionary failed validation: {target}")
    return target


def ensure_lemma_file(force: bool = False) -> Path:
    target = DICT_DIR / "lemma.en.txt"
    if target.exists() and not force and target.stat().st_size > 0:
        return target
    download_file(LEMMA_URL, target)
    if target.stat().st_size == 0:
        raise RuntimeError(f"Downloaded lemma file is empty: {target}")
    return target


def build_common_dictionary(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("r", encoding="utf-8-sig", newline="") as source_handle, destination.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as destination_handle:
        reader = csv.DictReader(source_handle)
        if reader.fieldnames is None:
            raise RuntimeError("Dictionary source has no header.")
        writer = csv.DictWriter(destination_handle, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            tags = set((row.get("tag") or "").split())
            if tags.intersection({"gk", "cet4", "cet6"}):
                writer.writerow(row)
    return destination


def build_sqlite_dictionary(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "wb",
        delete=False,
        dir=destination.parent,
        prefix=f"{destination.name}.",
        suffix=".tmp",
    ) as temp_file:
        temp_path = Path(temp_file.name)

    connection = sqlite3.connect(temp_path)
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
        connection.execute("CREATE INDEX idx_entries_word ON entries(word)")

        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows: list[tuple[str, str, str, str, str]] = []
            for row in reader:
                word = (row.get("word") or "").strip().lower()
                if not word:
                    continue
                rows.append(
                    (
                        word,
                        (row.get("phonetic") or "").strip(),
                        (row.get("translation") or "").strip(),
                        (row.get("pos") or "").strip(),
                        (row.get("exchange") or "").strip(),
                    )
                )
                if len(rows) >= 5000:
                    connection.executemany(
                        """
                        INSERT OR REPLACE INTO entries(word, phonetic, translation, pos, exchange)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        rows,
                    )
                    rows.clear()
            if rows:
                connection.executemany(
                    """
                    INSERT OR REPLACE INTO entries(word, phonetic, translation, pos, exchange)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    rows,
                )
        connection.commit()
    finally:
        connection.close()

    temp_path.replace(destination)
    return destination


def sqlite_contains_required_words(path: Path) -> bool:
    if not path.exists():
        return False
    connection = sqlite3.connect(path)
    try:
        found = {
            row[0]
            for row in connection.execute(
                f"SELECT word FROM entries WHERE word IN ({','.join('?' for _ in REQUIRED_WORDS)})",
                tuple(REQUIRED_WORDS),
            )
        }
    finally:
        connection.close()
    return REQUIRED_WORDS.issubset(found)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download ECDICT data for CET-4 Reader Assistant.")
    parser.add_argument("--force", action="store_true", help="Re-download dictionary files even if they look valid.")
    parser.add_argument(
        "--build-common",
        action="store_true",
        help="Regenerate data/dictionaries/cet_common.csv from ecdict.csv.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dictionary_path = ensure_dictionary(force=args.force)
    lemma_path = ensure_lemma_file(force=args.force)
    sqlite_path = DICT_DIR / "ecdict.sqlite3"
    if args.force or not sqlite_contains_required_words(sqlite_path):
        sqlite_path = build_sqlite_dictionary(dictionary_path, sqlite_path)
    print(f"Dictionary ready: {dictionary_path}")
    print(f"SQLite dictionary ready: {sqlite_path}")
    print(f"Lemma map ready: {lemma_path}")
    if args.build_common:
        common_path = build_common_dictionary(dictionary_path, DICT_DIR / "cet_common.csv")
        rows, words = inspect_dictionary(common_path)
        print(f"Common dictionary ready: {common_path} ({rows} rows, required words={sorted(words)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
