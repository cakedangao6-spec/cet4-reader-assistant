import json
import re
from datetime import datetime, timezone
from pathlib import Path

from faster_whisper import WhisperModel


PLAYER_ROOT = Path(__file__).resolve().parents[1]
AUDIO = PLAYER_ROOT / "materials" / "listening" / "25-6-1" / "cet4_2025_06_1.mp3"
MODELS = PLAYER_ROOT / "runtime" / "models"
MODEL_CACHE = MODELS / "models--Systran--faster-whisper-base.en" / "snapshots"
OUT_JSON = PLAYER_ROOT / "data" / "cet4_2025_06_1_timeline.json"
OUT_JS = PLAYER_ROOT / "data" / "cet4_2025_06_1_timeline.js"
DATA_JS = PLAYER_ROOT / "data" / "cet4_2025_06_1.js"


def load_questions():
    text = DATA_JS.read_text(encoding="utf-8")
    starts = {}
    current_id = None
    for line in text.splitlines():
      id_match = re.search(r"\bid:\s*(\d+),", line)
      if id_match:
          current_id = int(id_match.group(1))
      start_match = re.search(r"\bstart:\s*([0-9.]+),", line)
      if current_id and start_match:
          starts[current_id] = float(start_match.group(1))

    questions = []
    ids = sorted(starts)
    for index, qid in enumerate(ids):
        start = starts[qid]
        end = starts[ids[index + 1]] if index + 1 < len(ids) else 1416.0
        questions.append({"id": qid, "start": start, "end": end})
    return questions


def question_for_time(questions, start):
    for question in questions:
        if question["start"] <= start < question["end"]:
            return question["id"]
    return None


def model_path():
    snapshots = sorted(MODEL_CACHE.glob("*"))
    if not snapshots:
        raise FileNotFoundError(f"没有找到 base.en 模型缓存：{MODEL_CACHE}")
    return snapshots[-1]


def main():
    questions = load_questions()
    model_dir = model_path()
    print(f"Loading model: {model_dir}")
    model = WhisperModel(str(model_dir), device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        str(AUDIO),
        language="en",
        beam_size=3,
        vad_filter=False,
        condition_on_previous_text=False,
    )

    timeline = []
    for index, segment in enumerate(segments, start=1):
        text = " ".join(segment.text.strip().split())
        if not text:
            continue
        start = round(segment.start, 2)
        end = round(segment.end, 2)
        timeline.append(
            {
                "id": index,
                "start": start,
                "end": end,
                "questionId": question_for_time(questions, start),
                "text": text,
            }
        )

    payload = {
        "version": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "model": "Systran/faster-whisper-base.en",
        "audioFile": "materials/listening/25-6-1/cet4_2025_06_1.mp3",
        "language": info.language,
        "languageProbability": round(info.language_probability, 4),
        "duration": round(info.duration, 2),
        "segments": timeline,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_JS.write_text(
        "window.CET4_TIMELINE = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )
    print(f"Generated {len(timeline)} timeline segments")
    print(OUT_JS)


if __name__ == "__main__":
    main()
