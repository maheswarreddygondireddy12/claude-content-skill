"""Audio I/O via ffmpeg: decode to 16 kHz mono float32, loudness stats, hashing."""
from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

import numpy as np

SAMPLE_RATE = 16000
AUDIO_EXTS = (".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg")


def find_vo(reel_dir: Path) -> Path:
    for ext in AUDIO_EXTS:
        p = reel_dir / f"vo{ext}"
        if p.exists():
            return p
    raise FileNotFoundError(f"No vo.<{'|'.join(e[1:] for e in AUDIO_EXTS)}> in {reel_dir}")


def load_audio(path: Path, sr: int = SAMPLE_RATE) -> np.ndarray:
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def loudness(path: Path) -> dict:
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-nostdin", "-i", str(path), "-af", "ebur128=framelog=quiet", "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True).stderr
    summary = err[err.rfind("Summary:"):]

    def grab(label: str) -> float | None:
        m = re.search(label + r":\s+(-?[\d.]+)", summary)
        return float(m.group(1)) if m else None

    return {"integrated_lufs": grab("I"), "lra_lu": grab("LRA")}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def rms_db(audio: np.ndarray, start_s: float, end_s: float, sr: int = SAMPLE_RATE) -> float:
    seg = audio[int(start_s * sr):max(int(end_s * sr), int(start_s * sr) + 1)]
    return float(20 * np.log10(np.sqrt(np.mean(seg.astype(np.float64) ** 2)) + 1e-9))
