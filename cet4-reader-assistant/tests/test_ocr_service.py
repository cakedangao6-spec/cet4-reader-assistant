from __future__ import annotations

import unittest

import numpy as np

from cet4_reader.ocr_service import OcrService


class OcrServiceTests(unittest.TestCase):
    def test_prepare_image_resizes_large_inputs(self) -> None:
        image = np.zeros((3000, 4000, 3), dtype=np.uint8)
        resized = OcrService._prepare_image(image, max_side=1800)

        self.assertEqual(resized.shape[:2], (1350, 1800))

    def test_select_primary_column_uses_passage_marker_band(self) -> None:
        texts = [
            "Passage Two",
            "Questions 51 to 55 are based on the following passage.",
            "With the rise of pop music...",
            "They are essential",
        ]
        boxes = [
            [234, 187, 376, 219],
            [229, 219, 820, 275],
            [268, 295, 1305, 361],
            [1495, 394, 1712, 458],
        ]

        self.assertEqual(
            OcrService._select_primary_column(texts, boxes),
            texts[:3],
        )


if __name__ == "__main__":
    unittest.main()
