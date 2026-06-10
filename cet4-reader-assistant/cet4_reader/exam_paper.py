from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


class ExamPaperParseError(RuntimeError):
    """Raised when a CET-4 paper cannot be split into reading passages."""


@dataclass(frozen=True)
class ExamPaperPassage:
    title: str
    section: str
    question_range: str
    article_text: str
    question_text: str
    source_path: Path | None = None


PART_READING_RE = re.compile(r"\bPart\s+III\s+Reading\s+Comprehension\b", re.IGNORECASE)
PART_AFTER_RE = re.compile(r"\bPart\s+IV\b|\bTranslation\b", re.IGNORECASE)
SECTION_RE = re.compile(r"^\s*Section\s+([A-C])\s*$", re.IGNORECASE | re.MULTILINE)
PASSAGE_ONE_RE = re.compile(r"^\s*Passage\s+One\s*$", re.IGNORECASE | re.MULTILINE)
PASSAGE_TWO_RE = re.compile(r"^\s*Passage\s+Two\s*$", re.IGNORECASE | re.MULTILINE)
QUESTION_LINE_TEMPLATE = r"^\s*{number}[\.\)]\s*"
QUESTION_RANGE_RE = re.compile(
    r"^\s*Questions?\s+\d{1,3}\s*(?:[-\u2013\u2014]|to|and)\s*\d{1,3}.*$",
    re.IGNORECASE | re.MULTILINE,
)
QUESTION_START_RE = re.compile(r"^\s*\d{1,3}[\.\)]\s*")
OPTION_START_RE = re.compile(r"^\s*[A-D][\.\)]\s*")
INLINE_OPTION_RE = re.compile(r"\s+([A-D][\.\)])\s*")
SPACE_RE = re.compile(r"[ \t]+")
APOSTROPHE_SPACE_RE = re.compile(r"\s+([’'])\s*")
SPLIT_WORD_SUFFIX_RE = re.compile(
    r"\b([A-Za-z]{3,})\s+(s|es|ed|er|ers|ing|ingly|ure|uring|ion|ions|al|ally|ive|ives|ment|ments|ity|ities)\b"
)
PARAGRAPH_START_RE = re.compile(
    r"^(?:I\s+am\b|One\s+\w+\b|A\s+\w+\b|An\s+\w+\b|Women\b|Men\b|But\b|However\b)",
    re.IGNORECASE,
)
SHORT_PARAGRAPH_END_LENGTH = 95


def parse_exam_pdf(path: Path) -> list[ExamPaperPassage]:
    text = extract_pdf_text(path)
    passages = parse_exam_text(text)
    return [
        ExamPaperPassage(
            title=item.title,
            section=item.section,
            question_range=item.question_range,
            article_text=item.article_text,
            question_text=item.question_text,
            source_path=path,
        )
        for item in passages
    ]


def extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ExamPaperParseError("缺少 pypdf，请先安装依赖后再导入 PDF。") from exc

    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise ExamPaperParseError(f"无法读取 PDF：{exc}") from exc

    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    text = "\n".join(pages)
    if not text.strip():
        raise ExamPaperParseError("这个 PDF 没有可复制文本，暂不支持扫描版整卷解析。")
    return text


def parse_exam_text(text: str) -> list[ExamPaperPassage]:
    normalized = _normalize_text(text)
    reading = _reading_part(normalized)
    sections = _split_sections(reading)
    passages: list[ExamPaperPassage] = []

    section_a = sections.get("A", "").strip()
    if section_a:
        article, questions = _split_at_question(section_a, 26)
        passages.append(
            ExamPaperPassage(
                title="选词填空 26-35",
                section="Section A",
                question_range="26-35",
                article_text=_format_article_text(article or section_a),
                question_text=_format_question_text(questions),
            )
        )

    section_b = sections.get("B", "").strip()
    if section_b:
        article, questions = _split_at_question(section_b, 36)
        passages.append(
            ExamPaperPassage(
                title="长篇阅读 36-45",
                section="Section B",
                question_range="36-45",
                article_text=_format_article_text(article or section_b),
                question_text=_format_question_text(questions),
            )
        )

    section_c = sections.get("C", "").strip()
    if section_c:
        passages.extend(_split_section_c(section_c))

    if not passages:
        raise ExamPaperParseError("未识别到阅读理解篇章。")
    if not any(item.section == "Section C" for item in passages):
        raise ExamPaperParseError("未识别到短篇阅读 Section C。")
    return passages


def _normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"([A-Za-z])-\s*\n\s*([A-Za-z])", r"\1\2", normalized)
    lines: list[str] = []
    raw_lines = normalized.splitlines()
    for index, raw_line in enumerate(raw_lines):
        line = _clean_pdf_line(raw_line)
        next_line = _clean_pdf_line(raw_lines[index + 1]) if index + 1 < len(raw_lines) else ""
        has_paragraph_break = _has_pdf_paragraph_break(raw_line, line, next_line)
        if line:
            lines.append(line)
        if has_paragraph_break and lines and lines[-1] != "":
            lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def _clean_pdf_line(line: str) -> str:
    cleaned = SPACE_RE.sub(" ", line).strip()
    cleaned = APOSTROPHE_SPACE_RE.sub(r"\1", cleaned)
    cleaned = SPLIT_WORD_SUFFIX_RE.sub(r"\1\2", cleaned)
    return cleaned


def _has_pdf_paragraph_break(raw_line: str, line: str, next_line: str) -> bool:
    if not raw_line.endswith("  ") or not line or not next_line:
        return False
    if len(line) <= SHORT_PARAGRAPH_END_LENGTH:
        return True
    return bool(PARAGRAPH_START_RE.match(next_line))


def _reading_part(text: str) -> str:
    start = PART_READING_RE.search(text)
    if start is None:
        raise ExamPaperParseError("未找到 Part III Reading Comprehension。")
    tail = text[start.end() :]
    end = PART_AFTER_RE.search(tail)
    return tail[: end.start()] if end else tail


def _split_sections(text: str) -> dict[str, str]:
    matches = list(SECTION_RE.finditer(text))
    if not matches:
        raise ExamPaperParseError("未找到阅读理解 Section A/B/C。")

    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        section_name = match.group(1).upper()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[section_name] = text[start:end].strip()
    return sections


def _split_section_c(section_text: str) -> list[ExamPaperPassage]:
    one = PASSAGE_ONE_RE.search(section_text)
    two = PASSAGE_TWO_RE.search(section_text)
    if one is None or two is None:
        raise ExamPaperParseError("未识别到 Passage One 和 Passage Two。")

    first_chunk = section_text[one.end() : two.start()].strip()
    second_chunk = section_text[two.end() :].strip()
    first_article, first_questions = _split_short_passage(first_chunk, 46)
    second_article, second_questions = _split_short_passage(second_chunk, 51)
    if not first_article or not first_questions or not second_article or not second_questions:
        raise ExamPaperParseError("短篇阅读正文或题目识别不完整。")

    return [
        ExamPaperPassage(
            title="第一篇短篇阅读 46-50",
            section="Section C",
            question_range="46-50",
            article_text=_format_article_text(first_article),
            question_text=_format_question_text(first_questions),
        ),
        ExamPaperPassage(
            title="第二篇短篇阅读 51-55",
            section="Section C",
            question_range="51-55",
            article_text=_format_article_text(second_article),
            question_text=_format_question_text(second_questions),
        ),
    ]


def _split_short_passage(chunk: str, first_question: int) -> tuple[str, str]:
    chunk = QUESTION_RANGE_RE.sub("", chunk, count=1).strip()
    return _split_at_question(chunk, first_question)


def _split_at_question(text: str, first_question: int) -> tuple[str, str]:
    pattern = re.compile(QUESTION_LINE_TEMPLATE.format(number=first_question), re.MULTILINE)
    match = pattern.search(text)
    if match is None:
        return text.strip(), ""
    return text[: match.start()].strip(), text[match.start() :].strip()


def _format_question_text(text: str) -> str:
    if not text.strip():
        return ""

    expanded_lines: list[str] = []
    for raw_line in text.splitlines():
        line = SPACE_RE.sub(" ", raw_line).strip()
        if not line:
            continue
        line = INLINE_OPTION_RE.sub(r"\n\1 ", line)
        for part in line.splitlines():
            part = SPACE_RE.sub(" ", part).strip()
            if not part:
                continue
            part = QUESTION_START_RE.sub(lambda match: f"{match.group(0).strip()} ", part, count=1)
            part = OPTION_START_RE.sub(lambda match: f"{match.group(0).strip()} ", part, count=1)
            expanded_lines.append(part)

    formatted: list[str] = []
    for line in expanded_lines:
        if QUESTION_START_RE.match(line) and formatted and formatted[-1] != "":
            formatted.append("")
        formatted.append(line)

    while formatted and formatted[-1] == "":
        formatted.pop()
    return "\n".join(formatted)


def _format_article_text(text: str) -> str:
    paragraphs: list[str] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = SPACE_RE.sub(" ", raw_line).strip()
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs).strip()
