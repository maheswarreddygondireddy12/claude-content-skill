"""CLI: align a reel folder.

    python pipeline/align_reel.py reels/<slug> [--model wav2vec2|mms|all] [--no-star]
"""
from __future__ import annotations

import argparse
from pathlib import Path

from aligner.run import align_reel, model_keys


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reel_dir", type=Path)
    ap.add_argument("--model", default="wav2vec2", choices=model_keys() + ["all"])
    ap.add_argument("--no-star", action="store_true", help="disable the <star> wildcard for unscripted speech")
    ap.add_argument("--star-penalty", type=float, default=-2.0)
    args = ap.parse_args()

    keys = model_keys() if args.model == "all" else [args.model]
    for key in keys:
        res = align_reel(args.reel_dir, key, None if args.no_star else args.star_penalty)
        qc = res["qc"]
        print(f"[{key}] {qc['status']}  words={qc['n_words']}  flagged={len(qc['flagged_words'])}  "
              f"regions={len(qc['mismatch_regions'])}  runtime={qc['runtime']}  -> {res['out_dir']}")


if __name__ == "__main__":
    main()

