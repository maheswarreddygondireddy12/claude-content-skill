"""Diagnostic sync-check videos from timing.json (NOT a caption design).

Renders three chunkings from the same timing data to prove it is treatment-agnostic:
  word     one word at a time
  phrase   chunks cut at strong boundaries (karaoke highlight inside the chunk)
  keyword  only English/technical/emphasis words
A small top line shows word index, time, confidence and QC flags for review.

    python pipeline/preview.py reels/<slug> [--model wav2vec2] [--modes word,phrase,keyword]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from aligner.audio import find_vo

W, H = 720, 1280
HI = r"{\c&H00D7FF&}"   # highlight colour (BGR)
FLAG = r"{\c&H5050FF&}"
RESET = r"{\r}"
KEYWORD_STOP = {"and", "the", "for", "just", "with", "this", "that", "from", "only", "already", "soo", "so"}
QC_FLAGS = {"squeezed", "stretched", "low_conf", "check_spoken_form"}

HEADER = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Arial,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,3,0,5,40,40,0,1
Style: Info,Consolas,22,&H00A0A0A0,&H00A0A0A0,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,7,24,24,24,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ts(sec: float) -> str:
    cs = int(round(max(sec, 0) * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def esc(text: str) -> str:
    return text.replace("\\", "/").replace("{", "(").replace("}", ")")


def event(start: float, end: float, text: str, style: str = "Main", layer: int = 0) -> str:
    return f"Dialogue: {layer},{ts(start)},{ts(end)},{style},,0,0,0,,{text}"


def word_ends(words: list[dict], duration: float) -> list[float]:
    """Display end of each word: until the next word starts (gap-free reading)."""
    return [words[k + 1]["start"] if k + 1 < len(words) else min(w["end"] + 0.4, duration)
            for k, w in enumerate(words)]


def info_events(timing: dict, ends: list[float]) -> list[str]:
    out = []
    for w, e in zip(timing["words"], ends):
        flags = [f for f in w["flags"] if f in QC_FLAGS]
        line = f"#{w['i']:<4} {w['start']:7.2f}s  conf {w['conf']:.2f}  {w['lang']}"
        if flags:
            line += f"  {FLAG}{' '.join(flags)}"
        out.append(event(w["start"], e, line, "Info", 1))
    for u in timing["unscripted"]:
        out.append(event(u["start"], u["end"], f"\\N{FLAG}[unscripted audio {u['dur']:.2f}s]", "Info", 2))
    return out


def mode_word(timing: dict, ends: list[float]) -> list[str]:
    return [event(w["start"], e, esc(w["display"])) for w, e in zip(timing["words"], ends)]


def mode_phrase(timing: dict, ends: list[float], max_words: int = 4, cut: float = 0.5) -> list[str]:
    words, bounds = timing["words"], timing["boundaries"]
    chunks, cur = [], [0]
    for k in range(1, len(words)):
        if bounds[k - 1]["strength"] >= cut or len(cur) >= max_words:
            chunks.append(cur)
            cur = []
        cur.append(k)
    chunks.append(cur)
    out = []
    for chunk in chunks:
        for k in chunk:
            text = " ".join(
                (HI + esc(words[j]["display"]) + RESET) if j == k else esc(words[j]["display"]) for j in chunk
            )
            out.append(event(words[k]["start"], ends[k], text))
    return out


def mode_keyword(timing: dict, ends: list[float], hold: float = 1.2) -> list[str]:
    words = timing["words"]
    keys = [
        w for w in words
        if {"caps", "acronym", "number"} & set(w["markers"])
        or (w["lang"] == "en" and len(w["align"]) >= 4 and w["align"] not in KEYWORD_STOP)
    ]
    out = []
    for k, w in enumerate(keys):
        nxt = keys[k + 1]["start"] if k + 1 < len(keys) else w["start"] + hold
        out.append(event(w["start"], min(nxt, w["start"] + hold), HI + esc(w["display"].upper())))
    return out


MODES = {"word": mode_word, "phrase": mode_phrase, "keyword": mode_keyword}


def render(reel_dir: Path, model: str, modes: list[str]) -> list[Path]:
    align_dir = reel_dir / "align" / model
    timing = json.loads((align_dir / "timing.json").read_text(encoding="utf-8"))
    duration = timing["meta"]["duration_s"]
    vo = find_vo(reel_dir).resolve()
    out_dir = align_dir / "preview"
    out_dir.mkdir(parents=True, exist_ok=True)
    ends = word_ends(timing["words"], duration)
    outputs = []
    for mode in modes:
        ass_name = f"sync_{mode}.ass"
        lines = MODES[mode](timing, ends) + info_events(timing, ends)
        (out_dir / ass_name).write_text(HEADER + "\n".join(lines) + "\n", encoding="utf-8")
        mp4 = f"sync_check_{mode}.mp4"
        cmd = [
            "ffmpeg", "-y", "-v", "error", "-nostdin",
            "-f", "lavfi", "-i", f"color=c=0x101418:s={W}x{H}:r=30",
            "-i", str(vo),
            "-filter_complex",
            f"[1:a]showwaves=s={W}x140:mode=cline:colors=0x5ad1ff:rate=30[wv];"
            f"[0:v][wv]overlay=0:{H - 300}:shortest=1,ass={ass_name}[v]",
            "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", mp4,
        ]
        subprocess.run(cmd, cwd=out_dir, check=True)
        outputs.append(out_dir / mp4)
    return outputs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reel_dir", type=Path)
    ap.add_argument("--model", default="wav2vec2")
    ap.add_argument("--modes", default="word,phrase,keyword")
    args = ap.parse_args()
    for p in render(args.reel_dir, args.model, args.modes.split(",")):
        print(p)


if __name__ == "__main__":
    main()

