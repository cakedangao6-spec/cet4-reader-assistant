from __future__ import annotations

import json
import re
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "qwen3:8b"
OLLAMA_TIMEOUT_SECONDS = 60
MAX_ARTICLE_CHARS = 6000
MAX_QUESTION_CHARS = 2600

THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)


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
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": build_tutor_prompt(question, context),
            }
        ],
        "options": {
            "temperature": 0.2,
        },
    }
    endpoint = base_url.rstrip("/") + "/api/chat"
    request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raise AITutorError(f"Ollama 请求失败：HTTP {exc.code}") from exc
    except URLError as exc:
        raise AITutorError("连接不到 Ollama，请确认 Ollama 正在运行。") from exc
    except TimeoutError as exc:
        raise AITutorError("Ollama 响应超时，请稍后重试。") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AITutorError("Ollama 返回了无法解析的内容。") from exc

    message = data.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise AITutorError("Ollama 没有返回有效讲解。")
    return strip_thinking(content)


def strip_thinking(text: str) -> str:
    return THINK_BLOCK_RE.sub("", text).strip()


def _truncate_middle(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    head = max_chars // 2
    tail = max_chars - head
    return text[:head].rstrip() + "\n...\n" + text[-tail:].lstrip()
