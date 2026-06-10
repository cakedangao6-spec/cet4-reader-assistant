from __future__ import annotations

import unittest

from cet4_reader.exam_paper import ExamPaperParseError, parse_exam_text


SAMPLE_PAPER = """
Part III       Reading Comprehension      (40 minutes)
Section A
Directions: Choose words from the bank.
Language learning remains ___26___ throughout life.
A) active B) useful C) narrow
26. blank one
Section B
Directions: Match the statements.
A) Design can help students learn.
B) Teachers receive support.
36. Teachers get tutoring from designers.
37. Students learn about design.
Section C
Directions: There are 2 passages in this section.
Passage One
Questions 46 to 50 are based on the following passage.
New research suggests that pandas may be at risk of dying out.
Their chances of finding new mates have a lot to do with their habitat.
46. What do experts say about pandas?
A) They need new mates.
B) They should live alone.
47. What does the passage imply?
A) Habitat matters.
B) Food is enough.
Passage Two
Questions 51 to 55 are based on the following passage.
Engineering in the U.S. has long been a male-dominated profession.
Many women engineers reflected on the challenges they faced.
51. What does the passage mainly discuss?
A) Women in engineering.
B) New machines.
52. What did one engineer report?
A) She had to prove herself.
B) She disliked chemistry.
Part IV Translation
"""


class ExamPaperTests(unittest.TestCase):
    def test_parse_exam_text_splits_all_reading_sections(self) -> None:
        passages = parse_exam_text(SAMPLE_PAPER)

        self.assertEqual([item.title for item in passages], [
            "选词填空 26-35",
            "长篇阅读 36-45",
            "第一篇短篇阅读 46-50",
            "第二篇短篇阅读 51-55",
        ])
        self.assertIn("Language learning", passages[0].article_text)
        self.assertIn("36. Teachers", passages[1].question_text)

    def test_parse_exam_text_extracts_first_short_reading(self) -> None:
        first_short = parse_exam_text(SAMPLE_PAPER)[2]

        self.assertEqual(first_short.question_range, "46-50")
        self.assertIn("pandas may be at risk", first_short.article_text)
        self.assertNotIn("46.", first_short.article_text)
        self.assertIn("46. What do experts say", first_short.question_text)
        self.assertNotIn("Passage Two", first_short.question_text)

    def test_parse_exam_text_extracts_second_short_reading(self) -> None:
        second_short = parse_exam_text(SAMPLE_PAPER)[3]

        self.assertEqual(second_short.question_range, "51-55")
        self.assertIn("male-dominated profession", second_short.article_text)
        self.assertNotIn("51.", second_short.article_text)
        self.assertIn("51. What does the passage", second_short.question_text)

    def test_parse_exam_text_requires_part_three(self) -> None:
        with self.assertRaisesRegex(ExamPaperParseError, "Part III"):
            parse_exam_text("Section C\nPassage One\nText")

    def test_parse_exam_text_requires_section_c(self) -> None:
        with self.assertRaisesRegex(ExamPaperParseError, "Section C"):
            parse_exam_text("Part III Reading Comprehension\nSection A\nOnly section A")


if __name__ == "__main__":
    unittest.main()
