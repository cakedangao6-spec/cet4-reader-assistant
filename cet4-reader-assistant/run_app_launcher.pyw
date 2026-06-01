from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path


CREATE_NO_WINDOW = 0x08000000


def main() -> int:
    project_dir = Path(__file__).resolve().parent
    runtime_dir = project_dir / "runtime"
    runtime_dir.mkdir(exist_ok=True)
    log_path = runtime_dir / "launcher.log"
    python = project_dir / ".venv" / "Scripts" / "python.exe"

    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Starting CET-4 Reader\n")
        log.flush()

        if not python.exists():
            installer = project_dir / "install.ps1"
            result = subprocess.run(
                [
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(installer),
                ],
                cwd=project_dir,
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=CREATE_NO_WINDOW,
                check=False,
            )
            if result.returncode != 0:
                log.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Install failed: {result.returncode}\n")
                return result.returncode

        subprocess.Popen(
            [str(python), "-m", "cet4_reader.main"],
            cwd=project_dir,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=CREATE_NO_WINDOW,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
