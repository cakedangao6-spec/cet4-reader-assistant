from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import collections.abc
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


logger = logging.getLogger(__name__)

DEFAULT_WHISPER_MODEL = "small"
CACHE_VERSION = 3
CPU_DEVICE = "cpu"
CPU_COMPUTE_TYPE = "int8"
GPU_DEVICE = "cuda"
GPU_COMPUTE_TYPE = "float16"
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg", ".opus", ".wma", ".mp4"}

PROMPT_RE = re.compile(
    r"\bquestions?\s+\d{1,2}\s*(?:-|–|—|to)\s*\d{1,2}\s+are\s+based\s+on\s+"
    r"(?:the\s+)?following\s+(?:news\s+report|conversation|passage)\b",
    re.IGNORECASE,
)
MATERIAL_TITLE_RE = re.compile(
    r"^\s*(?:news\s+report|conversation|passage)\s+(?:one|two|three|four|five|six|seven|eight|nine|\d{1,2})\s*\.?\s*$",
    re.IGNORECASE,
)
MATERIAL_TITLE_PREFIX_RE = re.compile(
    r"\b(?:news\s+report|conversation|passage)\s+(?:one|two|three|four|five|six|seven|eight|nine|\d{1,2})\s*[\.:,]?\s*",
    re.IGNORECASE,
)
FOLLOWING_MATERIAL_RE = re.compile(
    r"\b(?:the\s+)?following\s+(?:news\s+report|conversation|passage)\b",
    re.IGNORECASE,
)
QUESTION_PROMPT_RE = re.compile(r"\bquestions?\s+\d{1,2}\s*(?:-|–|—|to|and)\s*\d{1,2}\b", re.IGNORECASE)
QUESTION_LINE_RE = re.compile(r"^\s*question\s+\d{1,2}\b|^\s*\d{1,2}\s*[\.)]\s", re.IGNORECASE)
SECTION_MARKER_RE = re.compile(r"\bsection\s+[abc]\b", re.IGNORECASE)
LISTENING_END_RE = re.compile(r"\bthat's\s+the\s+end\s+of\s+listening\s+comprehension\b", re.IGNORECASE)
DIRECTIONS_RE = re.compile(
    r"\b(?:directions|section\s+[abc]|now\s+listen|look\s+at\s+|read\s+the\s+questions|"
    r"mark\s+the\s+corresponding\s+letter|you\s+will\s+hear|at\s+the\s+end\s+of|"
    r"four\s+choices|answer\s+sheet|single\s+line|spoken\s+only\s+once|"
    r"after\s+you\s+hear\s+a\s+question|marked\s+a\s*,?\s*b\s*,?\s*c\s*(?:and|,)\s*d)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TranscriptWord:
    word: str
    start: float
    end: float


@dataclass(frozen=True)
class TranscriptSegment:
    start: float
    end: float
    text: str
    words: tuple[TranscriptWord, ...] = ()


@dataclass(frozen=True)
class ListeningArticle:
    title: str
    start: float


@dataclass(frozen=True)
class ListeningAnalysis:
    audio: str
    audio_path: str
    articles: tuple[ListeningArticle, ...]
    companion_files: dict[str, str]
    model: str
    model_cache: str
    requested_device: str
    runtime_device: str
    compute_type: str
    fallback_reason: str
    transcript_text: str
    segment_count: int
    duration_seconds: float
    cache_path: str
    elapsed_seconds: float
    from_cache: bool


@dataclass(frozen=True)
class TranscriptionResult:
    segments: list[TranscriptSegment]
    requested_device: str
    runtime_device: str
    compute_type: str
    fallback_reason: str = ""


@dataclass(frozen=True)
class RuntimeSelection:
    requested_device: str
    runtime_device: str
    compute_type: str
    fallback_reason: str = ""


def discover_companion_files(audio_path: Path) -> dict[str, str]:
    stem = audio_path.stem
    directory = audio_path.parent
    candidates = {
        "paper_pdf": directory / f"{stem}.pdf",
        "answer_pdf": directory / f"{stem}_ans.pdf",
    }
    return {key: str(path) for key, path in candidates.items() if path.exists()}


def model_cache_hint() -> str:
    return "%USERPROFILE%\\.cache\\huggingface\\hub"


class ListeningAnalyzer:
    def __init__(
        self,
        cache_dir: Path,
        model_name: str = DEFAULT_WHISPER_MODEL,
        prefer_gpu: bool = False,
    ) -> None:
        self.cache_dir = cache_dir
        self.model_name = model_name
        self.prefer_gpu = prefer_gpu

    def analyze(
        self,
        audio_path: Path,
        progress_callback: collections.abc.Callable[[float, str], None] | None = None,
        force: bool = False,
    ) -> ListeningAnalysis:
        started = time.perf_counter()
        audio_hash = file_sha256(audio_path)
        cache_path = self._cache_path(audio_path, audio_hash)
        companion_files = discover_companion_files(audio_path)

        if not force:
            cached = self._load_cache(cache_path, audio_path, audio_hash, started, companion_files)
            if cached is not None:
                return cached

        transcription = transcribe_audio_with_fallback(
            audio_path,
            model_name=self.model_name,
            prefer_gpu=self.prefer_gpu,
            progress_callback=progress_callback,
        )
        segments = transcription.segments
        transcript_text = build_transcript_text(segments)
        articles = detect_listening_articles(segments)
        if not segments or not transcript_text.strip():
            raise RuntimeError("Whisper 没有输出转写文本。请确认音频可播放，或检查 ffmpeg/音频解码能力。")

        payload = {
            "audio": audio_path.name,
            "cache_version": CACHE_VERSION,
            "audio_path": str(audio_path),
            "audio_sha256": audio_hash,
            "audio_size": audio_path.stat().st_size,
            "model": self.model_name,
            "model_cache": model_cache_hint(),
            "requested_device": transcription.requested_device,
            "runtime_device": transcription.runtime_device,
            "compute_type": transcription.compute_type,
            "fallback_reason": transcription.fallback_reason,
            "transcript_text": transcript_text,
            "segment_count": len(segments),
            "duration_seconds": segments[-1].end if segments else 0.0,
            "companion_files": companion_files,
            "articles": [{"title": item.title, "start": item.start} for item in articles],
        }
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        return ListeningAnalysis(
            audio=audio_path.name,
            audio_path=str(audio_path),
            articles=tuple(articles),
            companion_files=companion_files,
            model=self.model_name,
            model_cache=model_cache_hint(),
            requested_device=transcription.requested_device,
            runtime_device=transcription.runtime_device,
            compute_type=transcription.compute_type,
            fallback_reason=transcription.fallback_reason,
            transcript_text=transcript_text,
            segment_count=len(segments),
            duration_seconds=segments[-1].end if segments else 0.0,
            cache_path=str(cache_path),
            elapsed_seconds=time.perf_counter() - started,
            from_cache=False,
        )

    def _cache_path(self, audio_path: Path, audio_hash: str) -> Path:
        safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", audio_path.stem).strip("_") or "audio"
        return self.cache_dir / f"{safe_stem}-{audio_hash[:16]}.json"

    def _load_cache(
        self,
        cache_path: Path,
        audio_path: Path,
        audio_hash: str,
        started: float,
        companion_files: dict[str, str],
    ) -> ListeningAnalysis | None:
        if not cache_path.exists():
            return None
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if payload.get("audio_sha256") != audio_hash:
            return None
        if int(payload.get("cache_version") or 1) != CACHE_VERSION:
            return None
        raw_articles = payload.get("articles")
        if not isinstance(raw_articles, list):
            raw_articles = []
        articles = tuple(
            ListeningArticle(str(item.get("title") or f"文章{index}"), float(item.get("start") or 0.0))
            for index, item in enumerate(raw_articles, start=1)
            if isinstance(item, dict)
        )
        transcript_text = str(payload.get("transcript_text") or "")
        if not articles and not transcript_text.strip():
            return None
        return ListeningAnalysis(
            audio=str(payload.get("audio") or audio_path.name),
            audio_path=str(payload.get("audio_path") or audio_path),
            articles=articles,
            companion_files=companion_files or dict(payload.get("companion_files") or {}),
            model=str(payload.get("model") or self.model_name),
            model_cache=str(payload.get("model_cache") or model_cache_hint()),
            requested_device=str(payload.get("requested_device") or ("gpu" if payload.get("runtime_device") == GPU_DEVICE else "cpu")),
            runtime_device=str(payload.get("runtime_device") or CPU_DEVICE),
            compute_type=str(payload.get("compute_type") or CPU_COMPUTE_TYPE),
            fallback_reason=str(payload.get("fallback_reason") or ""),
            transcript_text=transcript_text,
            segment_count=int(payload.get("segment_count") or 0),
            duration_seconds=float(payload.get("duration_seconds") or 0.0),
            cache_path=str(cache_path),
            elapsed_seconds=time.perf_counter() - started,
            from_cache=True,
        )


def transcribe_audio_with_fallback(
    audio_path: Path,
    model_name: str = DEFAULT_WHISPER_MODEL,
    prefer_gpu: bool = False,
    progress_callback: collections.abc.Callable[[float, str], None] | None = None,
) -> TranscriptionResult:
    runtime = select_transcription_runtime(prefer_gpu)
    if runtime.runtime_device == GPU_DEVICE:
        try:
            segments = transcribe_audio(
                audio_path,
                model_name=model_name,
                device=runtime.runtime_device,
                compute_type=runtime.compute_type,
                progress_callback=progress_callback,
            )
            return TranscriptionResult(
                segments=segments,
                requested_device=runtime.requested_device,
                runtime_device=runtime.runtime_device,
                compute_type=runtime.compute_type,
            )
        except Exception as exc:
            fallback_reason = str(exc)
            logger.warning("GPU transcription failed; falling back to CPU. error=%s", fallback_reason)
            segments = transcribe_audio(
                audio_path,
                model_name=model_name,
                device=CPU_DEVICE,
                compute_type=CPU_COMPUTE_TYPE,
                progress_callback=progress_callback,
            )
            return TranscriptionResult(
                segments=segments,
                requested_device=runtime.requested_device,
                runtime_device=CPU_DEVICE,
                compute_type=CPU_COMPUTE_TYPE,
                fallback_reason=fallback_reason,
            )

    segments = transcribe_audio(
        audio_path,
        model_name=model_name,
        device=CPU_DEVICE,
        compute_type=CPU_COMPUTE_TYPE,
        progress_callback=progress_callback,
    )
    return TranscriptionResult(
        segments=segments,
        requested_device=runtime.requested_device,
        runtime_device=CPU_DEVICE,
        compute_type=CPU_COMPUTE_TYPE,
        fallback_reason=runtime.fallback_reason,
    )


def select_transcription_runtime(prefer_gpu: bool = False) -> RuntimeSelection:
    requested_device = "gpu" if prefer_gpu else "cpu"
    if not prefer_gpu:
        return RuntimeSelection(
            requested_device=requested_device,
            runtime_device=CPU_DEVICE,
            compute_type=CPU_COMPUTE_TYPE,
        )

    available, reason = cuda_is_available()
    if not available:
        return RuntimeSelection(
            requested_device=requested_device,
            runtime_device=CPU_DEVICE,
            compute_type=CPU_COMPUTE_TYPE,
            fallback_reason=reason,
        )
    return RuntimeSelection(
        requested_device=requested_device,
        runtime_device=GPU_DEVICE,
        compute_type=GPU_COMPUTE_TYPE,
    )


def cuda_is_available() -> tuple[bool, str]:
    try:
        import ctranslate2
    except ImportError as exc:
        return False, f"缺少 ctranslate2：{exc}"

    try:
        count = int(ctranslate2.get_cuda_device_count())
    except Exception as exc:
        return False, f"CUDA 检测失败：{exc}"
    if count <= 0:
        return False, "未检测到可用 CUDA 设备"

    try:
        supported = ctranslate2.get_supported_compute_types(GPU_DEVICE)
    except Exception as exc:
        return False, f"CUDA 计算精度检测失败：{exc}"
    if GPU_COMPUTE_TYPE not in supported:
        return False, f"当前 CUDA 后端不支持 {GPU_COMPUTE_TYPE}"

    return True, ""


def transcribe_audio(
    audio_path: Path,
    model_name: str = DEFAULT_WHISPER_MODEL,
    device: str = CPU_DEVICE,
    compute_type: str = CPU_COMPUTE_TYPE,
    progress_callback: collections.abc.Callable[[float, str], None] | None = None,
) -> list[TranscriptSegment]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("缺少 faster-whisper。请先安装依赖：pip install -r requirements.txt") from exc

    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    raw_segments, info = model.transcribe(
        str(audio_path),
        language="en",
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        word_timestamps=True,
        initial_prompt=(
            "College English Test Band 4 listening comprehension. "
            "News reports, long conversations, passages, questions and answers."
        ),
        temperature=0.0,
        condition_on_previous_text=True,
    )
    duration = float(getattr(info, "duration", 0.0) or 0.0)
    segments: list[TranscriptSegment] = []
    for segment in raw_segments:
        words = tuple(
            TranscriptWord(str(word.word), float(word.start), float(word.end))
            for word in (getattr(segment, "words", None) or [])
            if getattr(word, "start", None) is not None and getattr(word, "end", None) is not None
        )
        segments.append(
            TranscriptSegment(
                start=float(segment.start),
                end=float(segment.end),
                text=str(segment.text or "").strip(),
                words=words,
            )
        )
        if progress_callback is not None and duration > 0:
            percent = min(99.0, max(0.0, (float(segment.end) / duration) * 100.0))
            progress_callback(percent, str(segment.text or "").strip())
    return segments


def detect_listening_articles(segments: Iterable[TranscriptSegment]) -> list[ListeningArticle]:
    segment_list = list(segments)
    starts: list[float] = []
    for index, segment in enumerate(segment_list):
        if has_material_title(segment.text):
            start = estimate_title_material_start(segment)
            if start is None:
                start = find_next_material_start(segment_list, index + 1)
        elif is_material_prompt(segment.text):
            start = estimate_material_start(segment)
            if start is None:
                start = find_next_material_start(segment_list, index + 1)
        elif is_section_marker(segment.text):
            start = find_first_material_after_section(segment_list, index + 1)
        else:
            continue
        if start is None:
            continue
        if not starts or abs(start - starts[-1]) > 8:
            starts.append(start)

    for start in detect_gap_based_material_starts(segment_list):
        if all(abs(start - existing) > 8 for existing in starts):
            starts.append(start)

    starts.sort()
    return [ListeningArticle(f"文章{index}", start) for index, start in enumerate(starts, start=1)]


def is_material_prompt(text: str) -> bool:
    normalized = normalize_transcript_text(text)
    return bool(PROMPT_RE.search(normalized) or (QUESTION_PROMPT_RE.search(normalized) and FOLLOWING_MATERIAL_RE.search(normalized)))


def is_material_title(text: str) -> bool:
    return bool(MATERIAL_TITLE_RE.match(normalize_transcript_text(text)))


def has_material_title(text: str) -> bool:
    return bool(MATERIAL_TITLE_PREFIX_RE.search(normalize_transcript_text(text)))


def is_section_marker(text: str) -> bool:
    return bool(SECTION_MARKER_RE.search(normalize_transcript_text(text)))


def estimate_title_material_start(segment: TranscriptSegment) -> float | None:
    normalized = normalize_transcript_text(segment.text)
    match = MATERIAL_TITLE_PREFIX_RE.search(normalized)
    if match is None:
        return None
    tail = segment.text[match.end() :].strip(" .,:;")
    if len(tail.split()) < 4 or is_non_material_text(tail):
        return None
    if not segment.words:
        return max(segment.start, min(segment.end, segment.start + 1.0))
    tail_words = normalize_words(tail.split())
    segment_words = [normalize_word(word.word) for word in segment.words]
    start_index = find_subsequence(segment_words, tail_words[: min(4, len(tail_words))])
    if start_index is None:
        return max(segment.start, min(segment.end, segment.start + 1.0))
    return max(segment.start, segment.words[start_index].start)


def estimate_material_start(segment: TranscriptSegment) -> float | None:
    match = PROMPT_RE.search(normalize_transcript_text(segment.text))
    if match is None:
        return None
    tail = segment.text[match.end() :].strip(" .,:;")
    if len(tail.split()) < 4:
        return None
    if is_non_material_text(tail):
        return None
    if not segment.words:
        return max(segment.start, min(segment.end, segment.start + 1.0))
    tail_words = normalize_words(tail.split())
    segment_words = [normalize_word(word.word) for word in segment.words]
    start_index = find_subsequence(segment_words, tail_words[: min(4, len(tail_words))])
    if start_index is None:
        return max(segment.start, min(segment.end, segment.start + 1.0))
    return max(segment.start, segment.words[start_index].start)


def find_next_material_start(segments: list[TranscriptSegment], start_index: int) -> float | None:
    for segment in segments[start_index : start_index + 8]:
        if is_non_material_text(segment.text):
            continue
        return max(0.0, segment.start)
    return None


def find_first_material_after_section(segments: list[TranscriptSegment], start_index: int) -> float | None:
    saw_directions = False
    for segment in segments[start_index : start_index + 14]:
        title_start = estimate_title_material_start(segment) if has_material_title(segment.text) else None
        if title_start is not None:
            return title_start
        if DIRECTIONS_RE.search(normalize_transcript_text(segment.text)):
            saw_directions = True
            continue
        if not saw_directions and is_non_material_text(segment.text):
            continue
        if has_material_title(segment.text) and estimate_title_material_start(segment) is None:
            continue
        if is_non_material_text(segment.text):
            continue
        return max(0.0, segment.start)
    return None


def detect_gap_based_material_starts(segments: list[TranscriptSegment]) -> list[float]:
    starts: list[float] = []
    for previous, current in zip(segments, segments[1:]):
        gap = current.start - previous.end
        if gap < 8:
            continue
        if is_non_material_text(current.text):
            continue
        if has_material_title(current.text):
            continue
        if not looks_like_question_context(previous.text):
            continue
        starts.append(max(0.0, current.start))
    return starts


def looks_like_question_context(text: str) -> bool:
    normalized = normalize_transcript_text(text)
    if QUESTION_LINE_RE.match(normalized) or QUESTION_PROMPT_RE.search(normalized):
        return True
    words = normalized.split()
    if len(words) <= 20 and re.search(r"\b(?:what|why|how|where|when|which|who|conversation|passage|news\s+report)\b", normalized):
        return True
    return False


def is_non_material_text(text: str) -> bool:
    normalized = normalize_transcript_text(text)
    if not normalized:
        return True
    if LISTENING_END_RE.search(normalized):
        return True
    if is_material_prompt(normalized):
        return True
    if QUESTION_PROMPT_RE.search(normalized):
        return True
    if DIRECTIONS_RE.search(normalized):
        return True
    if QUESTION_LINE_RE.match(normalized):
        return True
    words = normalized.split()
    if len(words) <= 3 and QUESTION_PROMPT_RE.search(normalized):
        return True
    return False


def normalize_transcript_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("’", "'")).strip().lower()


def build_transcript_text(segments: Iterable[TranscriptSegment]) -> str:
    lines = []
    for segment in segments:
        text = segment.text.strip()
        if text:
            lines.append(f"[{format_seconds(segment.start)}] {text}")
    return "\n".join(lines)


def format_seconds(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    minutes, second = divmod(total_seconds, 60)
    hour, minute = divmod(minutes, 60)
    if hour:
        return f"{hour:02d}:{minute:02d}:{second:02d}"
    return f"{minute:02d}:{second:02d}"


def parse_timestamped_transcript(transcript_text: str) -> list[tuple[float, str]]:
    entries: list[tuple[float, str]] = []
    for line in transcript_text.splitlines():
        match = re.match(r"^\[(?:(\d{2}):)?(\d{2}):(\d{2})\]\s*(.*)$", line.strip())
        if not match:
            continue
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        entries.append((hours * 3600 + minutes * 60 + seconds, match.group(4).strip()))
    return entries


def format_gpu_status(analysis: ListeningAnalysis) -> str:
    if analysis.from_cache:
        return "缓存：已读取"
    if analysis.requested_device == "gpu":
        if analysis.runtime_device == GPU_DEVICE:
            return "GPU：已启用"
        if "cublas64_12.dll" in analysis.fallback_reason:
            return "GPU：缺少 cublas64_12.dll（已回退CPU）"
        return "GPU：已回退CPU"
    return "CPU：稳定模式"


def format_analysis_summary(analysis: ListeningAnalysis) -> str:
    status = format_gpu_status(analysis)
    device = "GPU" if analysis.runtime_device == GPU_DEVICE else "CPU"
    return (
        f"{status}；实际设备：{device}；模型：{analysis.model or DEFAULT_WHISPER_MODEL}；"
        f"耗时：{analysis.elapsed_seconds:.2f}s；文章：{len(analysis.articles)}；"
        f"segment：{analysis.segment_count}"
    )


def default_listening_export_path(audio_path: Path) -> Path:
    return audio_path.with_name(f"{audio_path.stem}_listening_articles.txt")


def build_article_export_text(analysis: ListeningAnalysis) -> str:
    header = [
        f"音频：{analysis.audio}",
        f"模型：{analysis.model or DEFAULT_WHISPER_MODEL}",
        f"设备：{format_gpu_status(analysis)}",
        f"耗时：{analysis.elapsed_seconds:.2f}s",
        f"Whisper segment：{analysis.segment_count}",
        "",
    ]
    if not analysis.articles:
        return "\n".join(header + ["原始转写", analysis.transcript_text.strip(), ""]).strip() + "\n"

    entries = parse_timestamped_transcript(analysis.transcript_text)
    lines = header[:]
    article_starts = [article.start for article in analysis.articles]
    for index, article in enumerate(analysis.articles):
        next_start = article_starts[index + 1] if index + 1 < len(article_starts) else None
        lines.append(f"{article.title} {format_seconds(article.start)}")
        lower_bound = max(0, int(article.start) - 1)
        upper_bound = (int(next_start) - 1) if next_start is not None else None
        selected = [
            f"[{format_seconds(timestamp)}] {text}"
            for timestamp, text in entries
            if timestamp >= lower_bound and (upper_bound is None or timestamp < upper_bound)
        ]
        if selected:
            lines.extend(selected)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def normalize_word(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def normalize_words(words: Iterable[str]) -> list[str]:
    return [word for word in (normalize_word(item) for item in words) if word]


def find_subsequence(haystack: list[str], needle: list[str]) -> int | None:
    if not haystack or not needle or len(needle) > len(haystack):
        return None
    for index in range(0, len(haystack) - len(needle) + 1):
        if haystack[index : index + len(needle)] == needle:
            return index
    return None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def analysis_to_jsonable(analysis: ListeningAnalysis) -> dict[str, Any]:
    return {
        "audio": analysis.audio,
        "audio_path": analysis.audio_path,
        "articles": [{"title": item.title, "start": item.start} for item in analysis.articles],
        "companion_files": analysis.companion_files,
        "model": analysis.model,
        "model_cache": analysis.model_cache,
        "requested_device": analysis.requested_device,
        "runtime_device": analysis.runtime_device,
        "compute_type": analysis.compute_type,
        "fallback_reason": analysis.fallback_reason,
        "transcript_text": analysis.transcript_text,
        "segment_count": analysis.segment_count,
        "duration_seconds": analysis.duration_seconds,
        "cache_path": analysis.cache_path,
        "elapsed_seconds": analysis.elapsed_seconds,
        "from_cache": analysis.from_cache,
    }
