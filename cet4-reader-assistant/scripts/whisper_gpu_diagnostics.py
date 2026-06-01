from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
import subprocess
import threading
import time
from pathlib import Path


def package_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not installed"


def cuda_summary() -> dict[str, object]:
    summary: dict[str, object] = {
        "nvidia_smi": run_text(["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.used", "--format=csv,noheader"]),
        "torch": {"installed": package_version("torch") != "not installed"},
        "ctranslate2_cuda_device_count": None,
        "ctranslate2_cuda_error": "",
    }
    try:
        import torch

        summary["torch"] = {
            "installed": True,
            "version": getattr(torch, "__version__", ""),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_version": getattr(torch.version, "cuda", None),
            "device_count": int(torch.cuda.device_count()),
            "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "",
        }
    except Exception as exc:
        summary["torch_error"] = str(exc)

    try:
        import ctranslate2

        summary["ctranslate2_cuda_device_count"] = int(ctranslate2.get_cuda_device_count())
        summary["ctranslate2_cuda_compute_types"] = sorted(ctranslate2.get_supported_compute_types("cuda"))
    except Exception as exc:
        summary["ctranslate2_cuda_error"] = str(exc)
    return summary


def run_text(args: list[str]) -> str:
    try:
        completed = subprocess.run(args, capture_output=True, text=True, timeout=15, check=False)
    except Exception as exc:
        return str(exc)
    return (completed.stdout or completed.stderr).strip()


class GpuMemorySampler:
    def __init__(self) -> None:
        self.samples: list[int] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def __enter__(self) -> "GpuMemorySampler":
        self._thread.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self._stop.set()
        self._thread.join(timeout=2)

    @property
    def peak_mib(self) -> int | None:
        return max(self.samples) if self.samples else None

    def _run(self) -> None:
        while not self._stop.is_set():
            text = run_text(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"])
            try:
                self.samples.append(int(text.splitlines()[0].strip()))
            except (IndexError, ValueError):
                pass
            self._stop.wait(0.5)


def benchmark(audio_path: Path, model_name: str, device: str, compute_type: str, local_files_only: bool) -> dict[str, object]:
    from faster_whisper import WhisperModel

    started = time.perf_counter()
    with GpuMemorySampler() as sampler:
        try:
            model = WhisperModel(
                model_name,
                device=device,
                compute_type=compute_type,
                local_files_only=local_files_only,
            )
            raw_segments, info = model.transcribe(
                str(audio_path),
                language="en",
                beam_size=5,
                vad_filter=True,
                word_timestamps=True,
            )
            segments = list(raw_segments)
        except Exception as exc:
            return {
                "model": model_name,
                "device": device,
                "compute_type": compute_type,
                "ok": False,
                "elapsed_seconds": round(time.perf_counter() - started, 2),
                "peak_gpu_memory_mib": sampler.peak_mib,
                "error": str(exc),
            }
    return {
        "model": model_name,
        "device": device,
        "compute_type": compute_type,
        "ok": True,
        "elapsed_seconds": round(time.perf_counter() - started, 2),
        "peak_gpu_memory_mib": sampler.peak_mib,
        "audio_duration_seconds": round(float(getattr(info, "duration", 0.0)), 2),
        "segments": len(segments),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check faster-whisper CPU/GPU runtime and benchmark local audio.")
    parser.add_argument("audio", type=Path)
    parser.add_argument("--models", nargs="+", default=["small", "medium", "large-v3"])
    parser.add_argument("--local-files-only", action="store_true", default=True)
    args = parser.parse_args()

    results: dict[str, object] = {
        "audio": str(args.audio),
        "packages": {
            "faster-whisper": package_version("faster-whisper"),
            "ctranslate2": package_version("ctranslate2"),
            "torch": package_version("torch"),
        },
        "cuda": cuda_summary(),
        "benchmarks": [],
    }
    for model_name in args.models:
        for device, compute_type in (("cpu", "int8"), ("cuda", "float16")):
            results["benchmarks"].append(
                benchmark(args.audio, model_name, device, compute_type, args.local_files_only)
            )

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
