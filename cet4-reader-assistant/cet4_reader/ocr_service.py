from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Iterable


class OcrService:
    PASSAGE_MARKER_RE = re.compile(
        r"^\s*passage\s+(?:one|two|three|[1-3])\s*$", re.IGNORECASE
    )

    def __init__(self) -> None:
        self._engine: Any | None = None
        base_dir = Path(__file__).resolve().parents[1]
        os.environ["PADDLE_PDX_CACHE_HOME"] = str(base_dir / "data" / "paddlex_cache")

    def recognize(self, image_array: Any) -> str:
        engine = self._get_engine()
        image_array = self._prepare_image(image_array)
        if hasattr(engine, "predict"):
            try:
                return self._extract_text(engine.predict(image_array))
            except TypeError:
                pass
        return self._extract_text(engine.ocr(image_array, cls=True))

    def _get_engine(self) -> Any:
        if self._engine is None:
            try:
                from paddleocr import PaddleOCR
            except ImportError as exc:
                raise RuntimeError("PaddleOCR 尚未安装，请先运行 install.ps1。") from exc

            self._engine = PaddleOCR(
                text_detection_model_name="PP-OCRv5_mobile_det",
                text_recognition_model_name="en_PP-OCRv5_mobile_rec",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                enable_mkldnn=False,
            )
        return self._engine

    @staticmethod
    def _prepare_image(image_array: Any, max_side: int = 1800) -> Any:
        try:
            height, width = image_array.shape[:2]
        except AttributeError:
            return image_array

        longest_side = max(height, width)
        if longest_side <= max_side:
            return image_array

        import cv2

        scale = max_side / longest_side
        new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        return cv2.resize(image_array, new_size, interpolation=cv2.INTER_AREA)

    def _extract_text(self, result: Any) -> str:
        texts: list[str] = []
        self._collect_texts(result, texts)
        return "\n".join(text for text in texts if text.strip())

    def _collect_texts(self, value: Any, texts: list[str]) -> None:
        if value is None:
            return

        if isinstance(value, dict):
            rec_texts = value.get("rec_texts")
            if isinstance(rec_texts, Iterable) and not isinstance(rec_texts, (str, bytes)):
                rec_boxes = value.get("rec_boxes")
                selected = self._select_primary_column(rec_texts, rec_boxes)
                texts.extend(str(item) for item in selected)
                return
            for child in value.values():
                self._collect_texts(child, texts)
            return

        json_payload = getattr(value, "json", None)
        if callable(json_payload):
            json_payload = json_payload()
        if isinstance(json_payload, dict):
            self._collect_texts(json_payload, texts)
            return

        res_payload = getattr(value, "res", None)
        if isinstance(res_payload, dict):
            self._collect_texts(res_payload, texts)
            return

        rec_texts = getattr(value, "rec_texts", None)
        if isinstance(rec_texts, Iterable) and not isinstance(rec_texts, (str, bytes)):
            texts.extend(str(item) for item in rec_texts)
            return

        if isinstance(value, (list, tuple)):
            if len(value) >= 2 and isinstance(value[1], (list, tuple)) and value[1]:
                possible_text = value[1][0]
                if isinstance(possible_text, str):
                    texts.append(possible_text)
                    return
            for child in value:
                self._collect_texts(child, texts)

    @classmethod
    def _select_primary_column(cls, rec_texts: Iterable[Any], rec_boxes: Any) -> list[Any]:
        collected_texts = list(rec_texts)
        if not isinstance(rec_boxes, Iterable):
            return collected_texts

        collected_boxes = list(rec_boxes)
        if len(collected_boxes) != len(collected_texts):
            return collected_texts

        marker_index = next(
            (
                index
                for index, text in enumerate(collected_texts)
                if cls.PASSAGE_MARKER_RE.match(str(text).strip())
            ),
            None,
        )
        if marker_index is None:
            return collected_texts

        marker_box = collected_boxes[marker_index]
        if not isinstance(marker_box, Iterable):
            return collected_texts
        marker_values = list(marker_box)
        if len(marker_values) < 4:
            return collected_texts

        marker_left = float(marker_values[0])
        lower_bound = marker_left - 180
        upper_bound = marker_left + 500

        selected: list[Any] = []
        for text, box in zip(collected_texts, collected_boxes):
            if not isinstance(box, Iterable):
                selected.append(text)
                continue
            values = list(box)
            if len(values) < 4:
                selected.append(text)
                continue
            left = float(values[0])
            if lower_bound <= left <= upper_bound:
                selected.append(text)
        return selected
