from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from cet4_reader.ai_tutor import AITutorContext, ask_ollama, build_tutor_prompt, strip_thinking


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")


class AITutorTests(unittest.TestCase):
    def test_build_tutor_prompt_includes_reading_context(self) -> None:
        prompt = build_tutor_prompt(
            "为什么选 B？",
            AITutorContext(
                article_text="Chocolate can calm people down.",
                question_text="51. What can chocolate do?\nA) Harm people.\nB) Calm people down.",
                selected_text="51. What can chocolate do?",
            ),
        )

        self.assertIn("Chocolate can calm people down.", prompt)
        self.assertIn("51. What can chocolate do?", prompt)
        self.assertIn("用户当前选中的内容", prompt)
        self.assertIn("为什么选 B？", prompt)
        self.assertIn("不要输出思考过程", prompt)

    def test_strip_thinking_removes_qwen_think_block(self) -> None:
        self.assertEqual(strip_thinking("<think>hidden</think>\n定位：原文第二句。"), "定位：原文第二句。")

    def test_ask_ollama_parses_chat_response(self) -> None:
        captured: dict[str, object] = {}

        def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
            captured["timeout"] = timeout
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse({"message": {"content": "<think>x</think>\n结论：选 B。"}})

        with patch("cet4_reader.ai_tutor.urlopen", fake_urlopen):
            answer = ask_ollama(
                "讲一下",
                AITutorContext(article_text="Body", question_text="Question"),
                base_url="http://127.0.0.1:11434",
                model="qwen3:8b",
            )

        self.assertEqual(answer, "结论：选 B。")
        body = captured["body"]
        self.assertIsInstance(body, dict)
        self.assertEqual(body["model"], "qwen3:8b")
        self.assertFalse(body["stream"])


if __name__ == "__main__":
    unittest.main()
