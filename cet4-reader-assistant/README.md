# CET-4 Reader Assistant

English | [简体中文](./README.zh-CN.md)

`CET-4 Reader Assistant` is a Windows desktop study tool for College English Test Band 4 preparation. It combines reading practice, listening practice, vocabulary management, OCR-assisted text cleanup, and Whisper-based listening transcription in one local-first PyQt6 application.

The project is designed for students and self-study users who work with real CET-4 materials: reading passages need word lookup and vocabulary export, paper or screenshot materials need OCR cleanup, and listening audio needs playback, markers, transcription, and article-level navigation.

The only active showcase project is `cet4-reader-assistant`. `cet4-abloop-player` is a deprecated early experiment and is not part of the current project storyline.

## Features

### Reading Mode

- Passage/question splitting: pasted reading materials are automatically split into a reading area and a question area when question markers such as `Questions ...`, `Question 1`, numbered items, or Chinese prompts are detected.
- Exam PDF import: import a text-based CET-4 paper PDF, then choose Section A, Section B, Passage One, or Passage Two from the reading passage list.
- Word lookup: click an English word in the passage or question area to query its meaning.
- Vocabulary notebook: double-click a word to add it, or add words manually from the side panel; export the current list to `vocab/vocab.txt` with timestamped history snapshots.
- Search and highlighting: use `Ctrl+F` for search; select text and right-click to add or remove highlights.
- TXT import and cleanup: supports common text encodings and cleans page numbers, question numbers, option lines, Section/Passage noise, and OCR-style artifacts.
- Session restore: restores the previous passage, questions, answers, vocabulary, highlights, and selected runtime state from `runtime/session.json`.

### OCR

- OCR recognition: uses PaddleOCR to recognize English reading materials from images.
- Text cleanup: normalizes OCR output before passing it into the reading workflow.
- Reading-area organization: cleaned OCR text can be reviewed, edited, split, searched, highlighted, and used for vocabulary collection.
- Layout handling: large images are resized before OCR; when Passage markers are detected, the service prefers the primary reading-text column.

### Listening Mode

- Audio playback: import local audio files, play/pause, drag or click the progress bar, and jump through the audio.
- Progress markers: add, jump to, and delete listening markers.
- Whisper transcription: uses faster-whisper to transcribe listening audio locally.
- Automatic article detection: detects CET-4 listening material entry points and creates an `Article 1 / Article 2 / ...` navigation list.
- Raw transcript view: preserves the original Whisper transcript even when automatic article splitting fails.
- Listening text export: exports article-split text, or the full raw transcript when no article split is available.
- Result cache: stores analysis results under `cache/listening/` so the same audio does not need to be transcribed repeatedly.

### GPU Support

- Optional GPU acceleration: CPU + int8 is the default stable mode; GPU can be selected from the listening workflow.
- CPU fallback: if CUDA is unavailable, `float16` is unsupported, or GPU transcription fails, the app falls back to CPU + int8.
- Runtime summary: transcription results show the actual device, model, elapsed time, article count, and Whisper segment count.
- Diagnostics tool: `scripts/whisper_gpu_diagnostics.py` checks `nvidia-smi`, faster-whisper, ctranslate2, and local audio inference paths.

## Tech Stack

| Area | Technology |
| --- | --- |
| Language | Python |
| Desktop UI | PyQt6 |
| OCR | PaddleOCR |
| PDF parsing | pypdf |
| Listening transcription | faster-whisper |
| Local data | CSV, SQLite |
| Testing | unittest |

## Project Structure

```text
cet4-reader-assistant/
├─ cet4_reader/
│  ├─ main.py              # Application entry point
│  ├─ ui.py                # PyQt6 UI and reading/listening interactions
│  ├─ core.py              # Text processing and vocabulary export
│  ├─ dictionary.py        # Local/online dictionary and lemmatization
│  ├─ exam_paper.py        # CET-4 paper PDF parsing and reading passage splitting
│  ├─ ocr_service.py       # PaddleOCR service and OCR text extraction
│  └─ listening.py         # Whisper transcription, article splitting, GPU fallback
├─ scripts/
│  ├─ download_dictionary.py
│  ├─ build_usage_guide.py
│  └─ whisper_gpu_diagnostics.py
├─ tests/                  # unittest tests
├─ docs/                   # User guides and implementation reports
├─ data/dictionaries/      # Dictionary data
├─ assets/                 # Icons and screenshot assets
├─ install.ps1             # Windows setup script
├─ run.bat                 # Recommended launcher
├─ run_app.bat             # Launcher for an installed environment
├─ run_tests.ps1           # Test runner
├─ requirements.txt
├─ README.md               # English overview
└─ README.zh-CN.md         # Chinese overview
```

Runtime files such as `.venv/`, `runtime/`, `cache/`, `vocab/`, OCR model caches, and Whisper model caches are local artifacts and should not be committed.

## Installation

The current setup and launcher scripts are Windows-oriented.

Requirements:

- Windows
- Python 3.9-3.13
- PowerShell

Recommended startup:

```powershell
cd cet4-reader-assistant
.\run.bat
```

On first run, `run.bat` calls `install.ps1` when the virtual environment or PyQt6 is missing. The installer:

- creates `.venv/`
- upgrades pip
- installs `paddlepaddle==3.3.1`
- installs `requirements.txt`
- attempts to download and build the extended offline dictionary
- runs the unit test suite

Manual setup:

```powershell
cd cet4-reader-assistant
powershell -ExecutionPolicy Bypass -File .\install.ps1
.\run_app.bat
```

Dictionary download failure does not block the app. The repository includes `data/dictionaries/cet_common.csv` as a small built-in offline word list.

## Usage

### Reading Mode

1. Start the app and use the default reading mode.
2. Paste English reading material into the passage area.
3. Let the app split passage and questions automatically, then adjust the text manually if needed.
4. Click words to look them up and double-click words to add them to the vocabulary notebook.
5. Use `Ctrl+F` for search and right-click selected text to highlight.
6. Export vocabulary to `vocab/vocab.txt`; history snapshots are written to `vocab/history/`.

### OCR

1. Use OCR on a screenshot or photo of a CET-4 reading material.
2. The app runs PaddleOCR and applies cleanup rules to the recognized text.
3. Continue in the reading workflow for splitting, lookup, vocabulary, search, and highlighting.
4. OCR output remains editable so recognition errors or complex layouts can be corrected manually.

### Listening Mode

1. Switch to `Listening Mode` from the top toolbar.
2. Import a local audio file.
3. Use playback controls, the progress bar, and markers for intensive listening.
4. Run automatic article recognition with faster-whisper.
5. Use article mode to jump to detected article starts, or raw transcript mode to inspect the full Whisper output.
6. Export the listening text when needed.

GPU is optional. CPU mode is the default stable path. If GPU mode is selected but the local CUDA / ctranslate2 environment is not ready, the app falls back to CPU automatically.

## Tests

The test suite covers core text processing, dictionary behavior, OCR service logic, reading/listening UI flows, Whisper article splitting, cache behavior, and GPU fallback paths.

```powershell
cd cet4-reader-assistant
.\run_tests.ps1
```

Or run unittest directly:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Development History

The project history is organized by functional milestones rather than invented semantic versions:

- Reading assistant baseline: passage paste, question splitting, word lookup, vocabulary export, search highlighting, and session restore.
- Dictionary improvements: offline dictionary, SQLite lookup, online fallback, lemmatization, and lookup fallback handling.
- Text cleanup expansion: TXT import, encoding compatibility, OCR noise cleanup, and reading/question boundary detection.
- OCR integration: PaddleOCR, large-image resizing, and primary text-column selection.
- Listening mode: reading/listening mode switch, local audio playback, and progress markers.
- Whisper analysis: faster-whisper background transcription, caching, article splitting, raw transcript view, and text export.
- GPU support: CUDA detection, `float16` capability checks, CPU fallback, and diagnostics tooling.
- Launching experience: Windows launchers, hidden/logged startup helpers, and icon resources.

See [PROJECT_TIMELINE.md](../PROJECT_TIMELINE.md) and [CHANGELOG.md](../CHANGELOG.md) for more context.

## Highlights

- Local-first workflow for CET-4 reading and listening practice.
- Offline-friendly dictionary path with a built-in word list and optional extended local data.
- OCR-assisted cleanup for paper, screenshot, and messy copied materials.
- Whisper-based listening transcription with article navigation and export.
- Optional GPU acceleration with automatic CPU fallback.
- Maintenance-oriented repository with tests, reports, scripts, and documentation.

## Current Limitations

- The setup flow is primarily designed for Windows.
- First-time installation of PaddleOCR, PaddlePaddle, faster-whisper, dictionaries, or model caches can take time.
- GPU acceleration depends on the user's NVIDIA CUDA / cuBLAS / ctranslate2 environment; the app detects and falls back but does not modify system GPU runtime libraries.
- README screenshots are intentionally not included yet. The current `assets/screenshots` files are paper-material OCR inputs, not application UI showcase images.
- Future work should add UI screenshots, GitHub Actions, release packaging notes, and further UI module separation.

## Documentation

- [中文说明](./README.zh-CN.md)
- [QUICK_START.md](./QUICK_START.md)
- [FAQ.md](./FAQ.md)
- [docs/listening_article_auto_detect_report.md](./docs/listening_article_auto_detect_report.md)
- [docs/whisper_gpu_support_report.md](./docs/whisper_gpu_support_report.md)
