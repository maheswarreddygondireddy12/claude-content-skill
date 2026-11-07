"""One command to make a Reel folder render-ready.

    python pipeline/prepare_reel.py reels/<slug>              align (if needed) + QC + stage
    python pipeline/prepare_reel.py reels/<slug> --stage-only re-stage after editing edl.json / assets
    python pipeline/prepare_reel.py --brand-only              refresh staged brand assets

Steps
  1. Align script.txt to the VO (wav2vec2 by default; emissions cached) -> reels/<slug>/align/<model>/
    2. Stage into the renderer's public dir (~/.video-editing-workflow/studio_public/reels/<slug>/):
       vo.<ext> (untouched copy), timing.json, manifest.json, edl.json (if present), assets/**, icons.json
  3. Stage shared assets into ~/.video-editing-workflow/studio_public/brand/: sfx, lottie, icon pack
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aligner.audio import find_vo  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STUDIO = ROOT / "studio"
PUBLIC = Path.home() / ".video-editing-workflow" / "studio_public"  # must match studio/remotion.config.ts setPublicDir
DEFAULT_MODEL = "wav2vec2"


def _copy_tree(src: Path, dst: Path) -> int:
    n = 0
    if not src.exists():
        return 0
    for p in src.rglob("*"):
        if p.is_file():
            out = dst / p.relative_to(src)
            out.parent.mkdir(parents=True, exist_ok=True)
            if not out.exists() or out.stat().st_mtime < p.stat().st_mtime or out.stat().st_size != p.stat().st_size:
                shutil.copy2(p, out)
            n += 1
    return n


def build_icon_pack(out: Path, names: list[str] | None = None, edl: Path | None = None) -> None:
    cmd = ["node", str(STUDIO / "scripts" / "icons.mjs")]
    cmd += ["pack-edl", str(edl), str(out)] if edl else ["pack", str(out), *(names or [])]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=STUDIO, shell=False)
    print("  icons:", (res.stdout + res.stderr).strip())
    if res.returncode != 0:
        raise SystemExit("icon pack has missing icons (fix names with: node studio/scripts/icons.mjs search <query>)")


def stage_brand() -> None:
    dst = PUBLIC / "brand"
    dst.mkdir(parents=True, exist_ok=True)
    n = _copy_tree(ROOT / "brand" / "sfx", dst / "sfx")
    n += _copy_tree(ROOT / "library" / "lottie", dst / "lottie")
    names = [
        "lucide:server", "tabler:database", "mdi:api", "logos:react", "devicon:python",
        "fluent-emoji-flat:health-worker", "fluent-emoji:thermometer", "lucide:monitor", "tabler:server-2",
    ]
    build_icon_pack(dst / "icons.json", names=names)
    print(f"  brand: {n} files staged -> {dst}")


def stage_reel(reel_dir: Path, model: str) -> Path:
    slug = reel_dir.name
    dst = PUBLIC / "reels" / slug
    dst.mkdir(parents=True, exist_ok=True)
    vo = find_vo(reel_dir)
    shutil.copy2(vo, dst / vo.name)
    timing_src = reel_dir / "align" / model / "timing.json"
    if not timing_src.exists():
        raise SystemExit(f"No timing for model {model}: run without --stage-only first")
    shutil.copy2(timing_src, dst / "timing.json")
    (dst / "manifest.json").write_text(json.dumps({"slug": slug, "vo": vo.name, "model": model}), encoding="utf-8")
    edl = reel_dir / "edl.json"
    if edl.exists():
        shutil.copy2(edl, dst / "edl.json")
        build_icon_pack(dst / "icons.json", edl=edl)
    elif not (dst / "icons.json").exists():
        (dst / "icons.json").write_text('{"icons":{}}', encoding="utf-8")
    n = _copy_tree(reel_dir / "assets", dst / "assets")
    print(f"  staged {slug}: vo={vo.name}, timing, {'edl, ' if edl.exists() else ''}{n} asset file(s) -> {dst}")
    return dst


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reel_dir", type=Path, nargs="?")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--stage-only", action="store_true")
    ap.add_argument("--brand-only", action="store_true")
    ap.add_argument("--realign", action="store_true", help="force alignment even if timing exists")
    args = ap.parse_args()

    stage_brand()
    if args.brand_only:
        return
    if not args.reel_dir:
        ap.error("reel_dir is required unless --brand-only")
    reel_dir = args.reel_dir.resolve()

    timing = reel_dir / "align" / args.model / "timing.json"
    if not args.stage_only and (args.realign or not timing.exists() or
                                timing.stat().st_mtime < max((reel_dir / "script.txt").stat().st_mtime,
                                                             find_vo(reel_dir).stat().st_mtime)):
        from aligner.run import align_reel
        res = align_reel(reel_dir, args.model)
        qc = res["qc"]
        print(f"  align [{args.model}] {qc['status']}: {qc['n_words']} words, {len(qc['flagged_words'])} flagged, "
              f"{len(qc['mismatch_regions'])} mismatch region(s), {qc['runtime']['total_s']} s")
        for r in qc["mismatch_regions"]:
            print(f"    ! {r['start']:.2f}-{r['end']:.2f}s {r['kind']}: {r['text']}")
        if qc["status"] == "FAIL":
            raise SystemExit("alignment QC FAILED; see qc_report.md")
    stage_reel(reel_dir, args.model)


if __name__ == "__main__":
    main()

