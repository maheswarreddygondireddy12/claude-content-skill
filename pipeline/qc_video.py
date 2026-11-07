"""Render QC and audio mastering for finished Reels.

    python pipeline/qc_video.py <video.mp4> [--sheet out.jpg] [--expect-duration 93.4]
    python pipeline/qc_video.py <video.mp4> --master <out.mp4>     loudness-normalise to -14 LUFS (video copied)

Checks: 1080x1920, 30 fps, H.264/yuv420p, audio present, duration, integrated loudness,
black frames, long frozen stretches. Writes a contact sheet (6x4 grid) for visual review.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TARGET_LUFS = -14.0
LUFS_TOLERANCE = 2.0
FREEZE_WARN_S = 3.0


def ffprobe(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def _ffmpeg_filter_log(path: Path, vf: str | None = None, af: str | None = None) -> str:
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-nostdin", "-i", str(path)]
    if vf:
        cmd += ["-vf", vf, "-an"]
    if af:
        cmd += ["-af", af, "-vn"]
    cmd += ["-f", "null", "-"]
    return subprocess.run(cmd, capture_output=True, text=True).stderr


def loudness(path: Path) -> dict:
    err = _ffmpeg_filter_log(path, af="ebur128=framelog=quiet:peak=true")
    s = err[err.rfind("Summary:"):]
    grab = lambda k: float(m.group(1)) if (m := re.search(k + r":\s+(-?[\d.]+)", s)) else None  # noqa: E731
    return {"integrated_lufs": grab("I"), "lra_lu": grab("LRA"), "true_peak_dbfs": grab("Peak")}


def black_segments(path: Path) -> list[dict]:
    err = _ffmpeg_filter_log(path, vf="blackdetect=d=0.4:pix_th=0.06")
    return [{"start": float(a), "end": float(b)} for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)]


def freeze_segments(path: Path) -> list[dict]:
    err = _ffmpeg_filter_log(path, vf=f"freezedetect=n=0.002:d={FREEZE_WARN_S}")
    starts = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", err)]
    return [{"start": a, "end": b} for a, b in zip(starts, ends + [None] * (len(starts) - len(ends)))]


def contact_sheet(path: Path, out: Path, duration: float, cols: int = 6, rows: int = 4) -> None:
    n = cols * rows
    fps = n / max(duration, 0.1)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-nostdin", "-i", str(path), "-vf",
                    f"fps={fps:.5f},scale=270:-1,tile={cols}x{rows}:padding=6:color=0x202020", "-frames:v", "1",
                    "-q:v", "3", str(out)], check=True)


def master(src: Path, dst: Path) -> dict:
    """Two-pass loudnorm to TARGET_LUFS / -1 dBTP; video stream copied untouched."""
    err = _ffmpeg_filter_log(src, af=f"loudnorm=I={TARGET_LUFS}:TP=-1:LRA=11:print_format=json")
    m = json.loads(err[err.rfind("{"):err.rfind("}") + 1])
    af = (f"loudnorm=I={TARGET_LUFS}:TP=-1:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-nostdin", "-i", str(src), "-c:v", "copy", "-af", af,
                    "-ar", "48000", "-c:a", "aac", "-b:a", "192k", str(dst)], check=True)
    return {"before_lufs": float(m["input_i"]), "after": loudness(dst)}


def run_qc(path: Path, sheet: Path | None, expect_duration: float | None) -> dict:
    info = ffprobe(path)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    duration = float(info["format"]["duration"])
    checks: dict[str, tuple[bool, str]] = {}
    if v:
        num, den = (int(x) for x in v["r_frame_rate"].split("/"))
        checks["resolution"] = (v["width"] == 1080 and v["height"] == 1920, f"{v['width']}x{v['height']}")
        checks["fps"] = (abs(num / den - 30) < 0.01, f"{num / den:.2f}")
        checks["codec"] = (v["codec_name"] == "h264" and v.get("pix_fmt") == "yuv420p", f"{v['codec_name']}/{v.get('pix_fmt')}")
    else:
        checks["video"] = (False, "no video stream")
    checks["audio"] = (a is not None, a["codec_name"] if a else "missing")
    if expect_duration:
        checks["duration"] = (abs(duration - expect_duration) < 1.5, f"{duration:.2f}s (expected ~{expect_duration:.2f}s)")
    loud = loudness(path) if a else {}
    loud_ok = True
    if a and loud.get("integrated_lufs") is not None:
        loud_ok = abs(loud["integrated_lufs"] - TARGET_LUFS) <= LUFS_TOLERANCE
    blacks = black_segments(path)
    checks["black_frames"] = (not blacks, f"{len(blacks)} segment(s)")
    freezes = freeze_segments(path)
    warnings = [f"frozen {f['start']:.1f}-{f['end'] if f['end'] is not None else 'end'}s" for f in freezes]
    if not loud_ok:  # unmastered renders sit at the raw VO level; mastering fixes this
        warnings.append(f"loudness {loud['integrated_lufs']} LUFS, target {TARGET_LUFS}±{LUFS_TOLERANCE}: run with --master")
    if sheet:
        contact_sheet(path, sheet, duration)
    status = "PASS" if all(ok for ok, _ in checks.values()) else "FAIL"
    if status == "PASS" and warnings:
        status = "WARN"
    return {"status": status, "duration_s": round(duration, 3), "checks": {k: {"ok": ok, "value": val} for k, (ok, val) in checks.items()},
            "loudness": loud, "black": blacks, "freeze": freezes, "warnings": warnings, "sheet": str(sheet) if sheet else None}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("--sheet", type=Path)
    ap.add_argument("--expect-duration", type=float)
    ap.add_argument("--master", type=Path, help="write a loudness-normalised copy here")
    args = ap.parse_args()
    if args.master:
        print(json.dumps(master(args.video, args.master), indent=1))
        return
    res = run_qc(args.video, args.sheet, args.expect_duration)
    for k, c in res["checks"].items():
        print(f"  {'OK ' if c['ok'] else 'BAD'} {k:13} {c['value']}")
    for w in res["warnings"]:
        print(f"  WARN {w}")
    print(f"QC {res['status']}" + (f" · contact sheet: {res['sheet']}" if res["sheet"] else ""))
    sys.exit(1 if res["status"] == "FAIL" else 0)


if __name__ == "__main__":
    main()
