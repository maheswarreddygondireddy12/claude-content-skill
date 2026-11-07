"""Build the brand SFX palette: curated Kenney CC0 clips + locally synthesised sounds.

Each clip is trimmed of leading/trailing silence, peak-normalised to -3 dBFS and stored as
48 kHz stereo WAV in brand/sfx/<role>_<nn>.wav. library/sfx_index.json describes every clip so the
Director can pick sounds by role and character, per Reel.

    python pipeline/sfx_setup.py [--kenney <path-to-kenney-sounds>]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from assets import register

ROOT = Path(__file__).resolve().parents[1]
SFX_DIR = ROOT / "brand" / "sfx"
INDEX = ROOT / "library" / "sfx_index.json"
DEFAULT_KENNEY = Path.home() / ".video-editing-workflow" / "downloads" / "kenney"
PEAK_DB = -3.0

# role -> (pack, filename glob prefix, how many, character tags)
KENNEY_PICKS = [
    ("click", "kenney_interface-sounds", "click_00", 4, ["ui", "light", "tap"]),
    ("click", "kenney_ui-audio", "click", 3, ["ui", "soft", "tap"]),
    ("tick", "kenney_interface-sounds", "tick_00", 3, ["ui", "tiny", "counter"]),
    ("select", "kenney_interface-sounds", "select_00", 4, ["ui", "highlight"]),
    ("toggle", "kenney_interface-sounds", "toggle_00", 2, ["ui", "switch"]),
    ("pop", "kenney_interface-sounds", "drop_00", 4, ["appear", "bubble", "light"]),
    ("pop", "kenney_interface-sounds", "pluck_00", 2, ["appear", "pluck", "musical"]),
    ("open", "kenney_interface-sounds", "maximize_00", 3, ["reveal", "expand"]),
    ("close", "kenney_interface-sounds", "minimize_00", 3, ["hide", "collapse"]),
    ("confirm", "kenney_interface-sounds", "confirmation_00", 4, ["success", "positive", "musical"]),
    ("error", "kenney_interface-sounds", "error_00", 4, ["wrong", "negative", "buzz"]),
    ("question", "kenney_interface-sounds", "question_00", 3, ["curious", "hook", "musical"]),
    ("glitch", "kenney_interface-sounds", "glitch_00", 4, ["tech", "digital", "transition"]),
    ("scratch", "kenney_interface-sounds", "scratch_00", 2, ["stop", "rewind", "comedic"]),
    ("bong", "kenney_interface-sounds", "bong_00", 1, ["notification", "musical"]),
    ("impact_soft", "kenney_impact-sounds", "impactSoft_medium_00", 2, ["hit", "soft", "text-land"]),
    ("impact_soft", "kenney_impact-sounds", "impactSoft_heavy_00", 2, ["hit", "thud", "emphasis"]),
    ("impact_punch", "kenney_impact-sounds", "impactPunch_heavy_00", 2, ["hit", "strong", "emphasis"]),
    ("impact_metal", "kenney_impact-sounds", "impactMetal_light_00", 2, ["hit", "metallic", "tech"]),
    ("impact_bell", "kenney_impact-sounds", "impactBell_heavy_00", 1, ["hit", "bell", "big-reveal"]),
    ("zap", "kenney_digital-audio", "zap", 2, ["digital", "energy", "transition"]),
    ("rise_short", "kenney_digital-audio", "phaserUp", 3, ["digital", "up", "build"]),
    ("fall_short", "kenney_digital-audio", "phaserDown", 2, ["digital", "down"]),
    ("powerup", "kenney_digital-audio", "powerUp", 3, ["success", "level-up", "game"]),
    ("tone", "kenney_digital-audio", "twoTone", 2, ["digital", "notification"]),
]

# Synthesised with ffmpeg (our own work, licence "Generated"). role, name, filtergraph, tags
SYNTH = [
    ("whoosh", "whoosh_01", "anoisesrc=color=pink:duration=0.55:amplitude=0.9,bandpass=f=1400:width_type=o:w=1.6,"
     "afade=t=in:d=0.28:curve=exp,afade=t=out:st=0.28:d=0.27:curve=exp", ["transition", "fast", "air"]),
    ("whoosh", "whoosh_02", "anoisesrc=color=pink:duration=0.8:amplitude=0.9,lowpass=f=3000,highpass=f=300,"
     "afade=t=in:d=0.45:curve=qsin,afade=t=out:st=0.45:d=0.35:curve=qsin", ["transition", "smooth", "air"]),
    ("whoosh", "whoosh_03", "anoisesrc=color=brown:duration=0.45:amplitude=1,highpass=f=200,"
     "afade=t=in:d=0.15,afade=t=out:st=0.15:d=0.3:curve=exp", ["transition", "short", "deep"]),
    ("whoosh", "whoosh_04", "anoisesrc=color=white:duration=0.35:amplitude=0.6,bandpass=f=4000:width_type=o:w=1,"
     "afade=t=in:d=0.12,afade=t=out:st=0.12:d=0.23", ["transition", "swish", "bright"]),
    ("riser", "riser_01", "aevalsrc='0.35*sin(2*PI*(200+900*t*t/4)*t)':d=2:s=48000,"
     "afade=t=in:d=1.8:curve=exp,afade=t=out:st=1.9:d=0.1", ["build-up", "tension", "tonal"]),
    ("riser", "riser_02", "anoisesrc=color=pink:duration=1.6:amplitude=0.8,highpass=f=800,"
     "afade=t=in:d=1.5:curve=exp,afade=t=out:st=1.5:d=0.1", ["build-up", "noise", "airy"]),
    ("sub_hit", "sub_hit_01", "aevalsrc='0.9*sin(2*PI*(55+80*exp(-12*t))*t)*exp(-4*t)':d=1.0:s=48000",
     ["hit", "bass", "big-reveal"]),
    ("ding", "ding_01", "aevalsrc='0.4*(sin(2*PI*1318*t)+0.5*sin(2*PI*2637*t))*exp(-5*t)':d=0.9:s=48000",
     ["success", "bright", "musical"]),
    ("ding", "ding_02", "aevalsrc='0.4*(sin(2*PI*880*t)+0.4*sin(2*PI*1760*t))*exp(-6*t)':d=0.8:s=48000",
     ["notification", "soft", "musical"]),
    ("tick", "tick_soft_01", "aevalsrc='0.6*sin(2*PI*2200*t)*exp(-90*t)':d=0.08:s=48000", ["counter", "tiny", "clock"]),
]


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


def max_volume(path: Path) -> float:
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"max_volume:\s*(-?[\d.]+) dB", err)
    return float(m.group(1)) if m else 0.0


def duration(path: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]).stdout
    return round(float(out.strip()), 3)


def finalize(src_args: list[str], out: Path) -> None:
    """Trim silence, convert to 48 kHz stereo, then peak-normalise to PEAK_DB."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "t.wav"
        trim = ("silenceremove=start_periods=1:start_threshold=-55dB,areverse,"
                "silenceremove=start_periods=1:start_threshold=-55dB,areverse")
        run(["ffmpeg", "-y", "-v", "error", "-nostdin", *src_args, "-af", trim, "-ar", "48000", "-ac", "2", str(tmp)])
        gain = PEAK_DB - max_volume(tmp)
        run(["ffmpeg", "-y", "-v", "error", "-nostdin", "-i", str(tmp), "-af", f"volume={gain:.2f}dB",
             "-c:a", "pcm_s16le", str(out)])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kenney", type=Path, default=DEFAULT_KENNEY)
    args = ap.parse_args()

    if SFX_DIR.exists():
        shutil.rmtree(SFX_DIR)
    SFX_DIR.mkdir(parents=True)
    index, reg_entries, counters = [], [], {}

    def next_name(role: str) -> str:
        counters[role] = counters.get(role, 0) + 1
        return f"{role}_{counters[role]:02d}"

    for role, pack, prefix, count, tags in KENNEY_PICKS:
        files = sorted(p for p in (args.kenney / pack).rglob("*.ogg") if p.name.startswith(prefix))[:count]
        if len(files) < count:
            print(f"warning: {pack}/{prefix}* has only {len(files)} files")
        for src in files:
            name = next_name(role)
            out = SFX_DIR / f"{name}.wav"
            finalize(["-i", str(src)], out)
            rel = out.relative_to(ROOT).as_posix()
            index.append({"id": name, "file": rel, "role": role, "tags": tags, "duration_s": duration(out),
                          "origin": f"{pack}/{src.name}"})
            reg_entries.append({"id": f"sfx:{name}", "kind": "sfx", "path": rel, "licence": "CC0-1.0",
                                "source": f"Kenney ({pack.replace('kenney_', '')}) https://kenney.nl",
                                "origin_file": src.name})

    for role, name, graph, tags in SYNTH:
        out = SFX_DIR / f"{name}.wav"
        finalize(["-f", "lavfi", "-i", graph], out)
        rel = out.relative_to(ROOT).as_posix()
        index.append({"id": name, "file": rel, "role": role, "tags": tags + ["synth"], "duration_s": duration(out),
                      "origin": "synthesised with ffmpeg (pipeline/sfx_setup.py)"})
        reg_entries.append({"id": f"sfx:{name}", "kind": "sfx", "path": rel, "licence": "Generated",
                            "source": "Synthesised locally with FFmpeg"})

    # A typing loop assembled from short Kenney clicks with human-ish irregular spacing.
    clicks = [SFX_DIR / f"click_0{i}.wav" for i in (1, 2, 3, 4)]
    gaps = [0.09, 0.13, 0.07, 0.16, 0.1, 0.08, 0.14, 0.11, 0.07, 0.12, 0.09, 0.15]
    inputs, filters, t = [], [], 0.0
    for k, gap in enumerate(gaps):
        inputs += ["-i", str(clicks[k % 4])]
        delay = int(t * 1000)
        filters.append(f"[{k}:a]volume={0.55 + 0.1 * (k % 3):.2f},adelay={delay}|{delay}[c{k}]")
        t += gap
    mix = "".join(f"[c{k}]" for k in range(len(gaps))) + f"amix=inputs={len(gaps)}:normalize=0[a]"
    typing = SFX_DIR / "typing_01.wav"
    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / "typing.wav"
        run(["ffmpeg", "-y", "-v", "error", "-nostdin", *inputs, "-filter_complex", ";".join(filters) + ";" + mix,
             "-map", "[a]", str(raw)])
        finalize(["-i", str(raw)], typing)
    rel = typing.relative_to(ROOT).as_posix()
    index.append({"id": "typing_01", "file": rel, "role": "typing", "tags": ["keyboard", "code", "loopable"],
                  "duration_s": duration(typing), "origin": "assembled from Kenney CC0 clicks"})
    reg_entries.append({"id": "sfx:typing_01", "kind": "sfx", "path": rel, "licence": "CC0-1.0",
                        "source": "Kenney CC0 clicks, assembled locally"})

    INDEX.write_text(json.dumps({"peak_dbfs": PEAK_DB, "sample_rate": 48000, "clips": index}, indent=1),
                     encoding="utf-8")
    register(reg_entries)
    roles = sorted({c["role"] for c in index})
    print(f"{len(index)} clips, {len(roles)} roles: {', '.join(roles)}")


if __name__ == "__main__":
    main()
