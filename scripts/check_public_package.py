"""Basic hygiene check for accidental private paths, markers, and media outputs."""
from __future__ import annotations

import sys
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", "node_modules", ".venv"}
FORBIDDEN_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".mp3", ".m4a", ".flac", ".jpg", ".jpeg", ".png"}
PRIVATE_PATH = re.compile(r"(?i)\b[a-z]:\\users\\[^\\\s]+")


def main() -> int:
    problems: list[str] = []
    for current, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            path = Path(current) / name
            if path == Path(__file__).resolve():
                continue  # This file contains the markers it scans for.
            if path.suffix.lower() in FORBIDDEN_EXTENSIONS:
                problems.append(f"media/output file: {path.relative_to(ROOT)}")
                continue
            if path.name == ".env":
                problems.append(f"private config: {path.relative_to(ROOT)}")
                continue
            if path.suffix.lower() in {".md", ".json", ".py", ".ts", ".tsx", ".txt", ".ps1", ".mjs", ".toml"}:
                try:
                    content = path.read_text(encoding="utf-8").lower()
                except (UnicodeDecodeError, OSError):
                    continue
                if PRIVATE_PATH.search(content):
                    problems.append(f"possible personal Windows user path: {path.relative_to(ROOT)}")
    if problems:
        print("Public package check found possible issues:")
        print("\n".join(f"- {p}" for p in problems))
        return 1
    print("Public package check passed (basic marker and extension scan).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
