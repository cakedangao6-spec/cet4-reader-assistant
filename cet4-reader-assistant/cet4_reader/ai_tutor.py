from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "qwen3:8b"
DEFAULT_OLLAMA_MODELS_DIR = Path("E:/OllamaModels")
OLLAMA_TIMEOUT_SECONDS = 60
OLLAMA_FORMAT_TIMEOUT_SECONDS = 90
OLLAMA_STARTUP_TIMEOUT_SECONDS = 20
MAX_ARTICLE_CHARS = 6000
MAX_QUESTION_CHARS = 2600

THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)
THINK_START = "<think>"
THINK_END = "</think>"


class AITutorError(RuntimeError):
    """Raised when the local AI tutor cannot answer a request."""


@dataclass(frozen=True)
class AITutorContext:
    article_text: str
    question_text: str
    selected_text: str = ""


def build_tutor_prompt(question: str, context: AITutorContext) -> str:
    article = _truncate_middle(context.article_text.strip(), MAX_ARTICLE_CHARS)
    questions = _truncate_middle(context.question_text.strip(), MAX_QUESTION_CHARS)
    selected = context.selected_text.strip()
    focus = f"\n\n用户当前选中的内容：\n{selected}" if selected else ""
    user_question = question.strip() or "我不会这道题，请教我怎么分析。"

    return (
        "你是大学英语四级阅读题老师。请用中文讲解，语气耐心、清楚。\n"
        "可以输出给学生看的思考过程和解题步骤，但不要输出 <think> 标签或内部草稿。不要编造原文不存在的信息。\n"
        "优先教做题方法：定位原文依据、解释关键句、排除错误选项。\n"
        "如果题目没有明确答案，请先给提示，再说明还需要用户提供哪一题。\n\n"
        f"文章：\n{article or '（暂无文章）'}\n\n"
        f"题目区：\n{questions or '（暂无题目）'}"
        f"{focus}\n\n"
        f"用户问题：{user_question}\n\n"
        "请按「思考过程」「定位」「排除」「结论」四部分回答，结论可以给出答案但要说明原因。"
    )


def ask_ollama(
    question: str,
    context: AITutorContext,
    base_url: str = DEFAULT_OLLAMA_BASE_URL,
    model: str = DEFAULT_OLLAMA_MODEL,
    timeout: float = OLLAMA_TIMEOUT_SECONDS,
) -> str:
    return _chat_ollama(
        build_tutor_prompt(question, context),
        base_url=base_url,
        model=model,
        timeout=timeout,
        temperature=0.2,
        error_prefix="Ollama",
    )


def stream_ollama(
    question: str,
    context: AITutorContext,
    on_chunk: Callable[[str], None],
    base_url: str = DEFAULT_OLLAMA_BASE_URL,
    model: str = DEFAULT_OLLAMA_MODEL,
    timeout: float = OLLAMA_TIMEOUT_SECONDS,
) -> str:
    return _chat_ollama_stream(
        build_tutor_prompt(question, context),
        on_chunk=on_chunk,
        base_url=base_url,
        model=model,
        timeout=timeout,
        temperature=0.2,
        error_prefix="Ollama",
    )


def format_article_paragraphs_with_ollama(
    article_text: str,
    base_url: str = DEFAULT_OLLAMA_BASE_URL,
    model: str = DEFAULT_OLLAMA_MODEL,
    timeout: float = OLLAMA_FORMAT_TIMEOUT_SECONDS,
) -> str:
    source = article_text.strip()
    if not source:
        return ""
    prompt = (
        "你是英语试卷文本排版助手。请只修复下面英文阅读文章的自然段分段。\n"
        "严格要求：\n"
        "1. 不翻译，不总结，不讲解。\n"
        "2. 不改写单词、标点、数字和句子顺序。\n"
        "3. 只在需要的位置加入空行，把属于同一自然段的句子放在同一段。\n"
        "4. 不输出标题、说明、Markdown 代码块或 <think> 标签。\n\n"
        f"文章：\n{source}\n\n"
        "请直接输出修复分段后的文章正文："
    )
    formatted = _chat_ollama(
        prompt,
        base_url=base_url,
        model=model,
        timeout=timeout,
        temperature=0.0,
        error_prefix="Ollama 分段",
    )
    return _clean_formatted_article(formatted)


def _chat_ollama(
    prompt: str,
    base_url: str,
    model: str,
    timeout: float,
    temperature: float,
    error_prefix: str,
) -> str:
    payload = _build_chat_payload(prompt, model, stream=False, temperature=temperature)
    endpoint = base_url.rstrip("/") + "/api/chat"
    request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    raw = _open_ollama_request(request, base_url, timeout, error_prefix)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AITutorError(f"{error_prefix} 返回了无法解析的内容。") from exc

    message = data.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise AITutorError(f"{error_prefix} 没有返回有效内容。")
    return strip_thinking(content)


def _chat_ollama_stream(
    prompt: str,
    on_chunk: Callable[[str], None],
    base_url: str,
    model: str,
    timeout: float,
    temperature: float,
    error_prefix: str,
) -> str:
    payload = _build_chat_payload(prompt, model, stream=True, temperature=temperature)
    endpoint = base_url.rstrip("/") + "/api/chat"
    request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    chunks: list[str] = []
    filter_state = _ThinkStreamState()

    def consume_response() -> None:
        with urlopen(request, timeout=timeout) as response:
            for raw_line in response:
                if not raw_line.strip():
                    continue
                try:
                    data = json.loads(raw_line.decode("utf-8"))
                except json.JSONDecodeError:
                    continue
                message = data.get("message")
                content = message.get("content") if isinstance(message, dict) else None
                if isinstance(content, str) and content:
                    visible = filter_state.feed(content)
                    if visible:
                        chunks.append(visible)
                        on_chunk(visible)
                if data.get("done"):
                    tail = filter_state.flush()
                    if tail:
                        chunks.append(tail)
                        on_chunk(tail)
                    break

    try:
        consume_response()
    except HTTPError as exc:
        raise AITutorError(f"{error_prefix} 请求失败：HTTP {exc.code}") from exc
    except URLError as exc:
        if _maybe_start_local_ollama(base_url):
            try:
                consume_response()
            except HTTPError as retry_exc:
                raise AITutorError(f"{error_prefix} 请求失败：HTTP {retry_exc.code}") from retry_exc
            except URLError as retry_exc:
                raise AITutorError("连接不到 Ollama，请确认 Ollama 正在运行。") from retry_exc
        else:
            raise AITutorError("连接不到 Ollama，请确认 Ollama 正在运行。") from exc
    except TimeoutError as exc:
        raise AITutorError(f"{error_prefix} 响应超时，请稍后重试。") from exc

    result = "".join(chunks).strip()
    if not result:
        raise AITutorError(f"{error_prefix} 没有返回有效内容。")
    return result


def _build_chat_payload(prompt: str, model: str, stream: bool, temperature: float) -> dict[str, object]:
    return {
        "model": model,
        "stream": stream,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "options": {
            "temperature": temperature,
        },
    }


def _open_ollama_request(request: Request, base_url: str, timeout: float, error_prefix: str) -> str:
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except HTTPError as exc:
        raise AITutorError(f"{error_prefix} 请求失败：HTTP {exc.code}") from exc
    except URLError as exc:
        if _maybe_start_local_ollama(base_url):
            try:
                with urlopen(request, timeout=timeout) as response:
                    return response.read().decode("utf-8")
            except HTTPError as retry_exc:
                raise AITutorError(f"{error_prefix} 请求失败：HTTP {retry_exc.code}") from retry_exc
            except URLError as retry_exc:
                raise AITutorError("连接不到 Ollama，请确认 Ollama 正在运行。") from retry_exc
        else:
            raise AITutorError("连接不到 Ollama，请确认 Ollama 正在运行。") from exc
    except TimeoutError as exc:
        raise AITutorError(f"{error_prefix} 响应超时，请稍后重试。") from exc


def strip_thinking(text: str) -> str:
    return THINK_BLOCK_RE.sub("", text).strip()


class _ThinkStreamState:
    def __init__(self) -> None:
        self.in_think = False
        self.pending = ""

    def feed(self, chunk: str) -> str:
        text = self.pending + chunk
        self.pending = ""
        visible: list[str] = []

        while text:
            lower = text.lower()
            if self.in_think:
                end = lower.find(THINK_END)
                if end < 0:
                    return "".join(visible)
                text = text[end + len(THINK_END) :]
                self.in_think = False
                continue

            start = lower.find(THINK_START)
            if start < 0:
                keep = max(0, len(THINK_START) - 1)
                if len(text) <= keep:
                    self.pending = text
                    break
                visible.append(text[:-keep])
                self.pending = text[-keep:]
                break

            visible.append(text[:start])
            text = text[start + len(THINK_START) :]
            self.in_think = True

        return "".join(visible)

    def flush(self) -> str:
        if self.in_think:
            self.pending = ""
            return ""
        tail = self.pending
        self.pending = ""
        return tail


def _clean_formatted_article(text: str) -> str:
    cleaned = strip_thinking(text).strip()
    cleaned = re.sub(r"^```(?:text|markdown)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    cleaned = re.sub(r"^(?:修复分段后的文章正文|文章正文|正文)\s*[:：]\s*", "", cleaned, flags=re.IGNORECASE)
    lines = [line.rstrip() for line in cleaned.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines).strip()


def _maybe_start_local_ollama(base_url: str) -> bool:
    if not base_url.rstrip("/").startswith("http://127.0.0.1:11434"):
        return False
    executable = _find_ollama_executable()
    if executable is None:
        return False

    env = os.environ.copy()
    if "OLLAMA_MODELS" not in env and DEFAULT_OLLAMA_MODELS_DIR.exists():
        env["OLLAMA_MODELS"] = str(DEFAULT_OLLAMA_MODELS_DIR)
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        subprocess.Popen(
            [str(executable), "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            creationflags=creationflags,
        )
    except OSError:
        return False

    deadline = time.monotonic() + OLLAMA_STARTUP_TIMEOUT_SECONDS
    tags_url = base_url.rstrip("/") + "/api/tags"
    while time.monotonic() < deadline:
        try:
            with urlopen(tags_url, timeout=1):
                return True
        except Exception:
            time.sleep(0.4)
    return False


def _find_ollama_executable() -> Path | None:
    found = shutil.which("ollama")
    if found:
        return Path(found)
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidate = Path(local_app_data) / "Programs" / "Ollama" / "ollama.exe"
        if candidate.exists():
            return candidate
    return None


def _truncate_middle(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    head = max_chars // 2
    tail = max_chars - head
    return text[:head].rstrip() + "\n...\n" + text[-tail:].lstrip()
