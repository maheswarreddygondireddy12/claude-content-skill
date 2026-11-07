"""Align one reel folder end to end: script + VO -> timing.json, qc.json, qc_report.md."""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import audio as audio_mod
from .acoustic import FRAME_SEC, MODELS, AcousticModel
from .features import build_timing
from .qc import report_markdown, run_qc
from .schema import SCHEMA_VERSION, validate
from .script import spoken_alternatives, tokenize
from .viterbi import add_star_column, build_graph, star_regions, viterbi, word_spans

DEFAULT_STAR_PENALTY = -2.0
_MODEL_CACHE: dict[str, AcousticModel] = {}


def get_model(key: str) -> AcousticModel:
    if key not in _MODEL_CACHE:
        _MODEL_CACHE[key] = AcousticModel(key)
    return _MODEL_CACHE[key]


def align_reel(reel_dir: Path, model_key: str = "wav2vec2", star_penalty: float | None = DEFAULT_STAR_PENALTY,
               with_chars: bool = True, out_dir: Path | None = None, full: bool = False) -> dict:
    """full=True also measures loudness (slower); production runs skip it."""
    t_start = time.perf_counter()
    reel_dir = Path(reel_dir)
    slug = reel_dir.name
    script_path = reel_dir / "script.txt"
    vo_path = audio_mod.find_vo(reel_dir)
    out_dir = out_dir or reel_dir / "align" / model_key
    out_dir.mkdir(parents=True, exist_ok=True)

    words = tokenize(script_path.read_text(encoding="utf-8"))
    pcm = audio_mod.load_audio(vo_path)
    duration = len(pcm) / audio_mod.SAMPLE_RATE
    audio_sha = audio_mod.sha256(vo_path)

    model = get_model(model_key)
    t_em = time.perf_counter()
    emissions = model.emissions(pcm, cache_key=audio_sha)
    t_em = time.perf_counter() - t_em

    word_tokens = []
    for w in words:
        ids, dropped = model.tokens_for(w.align)
        if dropped:
            w.flags.append("dropped_chars:" + "".join(sorted(set(dropped))))
        if not ids:
            raise ValueError(f"Word {w.i} '{w.raw}' has no alignable characters for model {model_key}")
        word_tokens.append(ids)

    star_col = None
    star_before: set[int] = set()
    if star_penalty is not None:
        emissions, star_col = add_star_column(emissions, model.blank, star_penalty)
        star_before = {0, len(words)} | {w.i for w in words if w.i > 0 and w.sentence != words[w.i - 1].sentence}

    graph = build_graph(word_tokens, model.blank, star_col, star_before, model.delimiter)
    t_vit = time.perf_counter()
    path, frame_lp = viterbi(emissions, graph)
    spans = word_spans(path, frame_lp, graph, len(words))
    if _choose_spoken_forms(words, word_tokens, spans, emissions, model):
        graph = build_graph(word_tokens, model.blank, star_col, star_before, model.delimiter)
        path, frame_lp = viterbi(emissions, graph)
        spans = word_spans(path, frame_lp, graph, len(words))
    t_vit = time.perf_counter() - t_vit
    stars = star_regions(path, graph) if star_col is not None else []

    timing = {
        "schema_version": SCHEMA_VERSION,
        "meta": {
            "slug": slug,
            "script_sha256": audio_mod.sha256(script_path),
            "audio_sha256": audio_sha,
            "audio_file": vo_path.name,
            "duration_s": round(duration, 3),
            "loudness": audio_mod.loudness(vo_path) if full else None,
            "model": {"key": model_key, "id": model.spec.model_id, "license": model.spec.license},
            "frame_s": FRAME_SEC,
            "star_penalty": star_penalty,
        },
    }
    timing.update(build_timing(words, spans, pcm, duration, stars, with_chars))
    qc = run_qc(timing, duration, len(words))
    timing["meta"]["qc_status"] = qc["status"]
    validate(timing)

    runtime = {
        "emissions_s": round(t_em, 2),
        "viterbi_s": round(t_vit, 2),
        "total_s": round(time.perf_counter() - t_start, 2),
    }
    qc["runtime"] = runtime  # kept out of timing.json so reruns stay byte-identical

    (out_dir / "timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "qc.json").write_text(json.dumps(qc, ensure_ascii=False, indent=1), encoding="utf-8")
    model_info = {"id": model.spec.model_id, "license": model.spec.license}
    (out_dir / "qc_report.md").write_text(report_markdown(slug, model_info, qc), encoding="utf-8")
    return {"timing": timing, "qc": qc, "out_dir": out_dir}


def model_keys() -> list[str]:
    return list(MODELS)


def _choose_spoken_forms(words, word_tokens, spans, emissions, model) -> bool:
    """For numbers/symbols, try each plausible spoken form on the local audio window and keep
    the best-scoring one. Returns True if any word changed (caller re-aligns)."""
    changed = False
    for w in words:
        alts = spoken_alternatives(w)
        if len(alts) < 2:
            continue
        i = w.i
        lo = spans[i - 1].start_frame if i > 0 else max(0, spans[i].start_frame - 10)
        hi = spans[i + 1].end_frame if i + 1 < len(words) else min(len(emissions), spans[i].end_frame + 10)
        window = emissions[lo:hi]
        best, best_score = None, float("-inf")
        for cand in alts:
            ids, _ = model.tokens_for(cand)
            if not ids:
                continue
            ctx = ([word_tokens[i - 1]] if i > 0 else []) + [ids] + ([word_tokens[i + 1]] if i + 1 < len(words) else [])
            g = build_graph(ctx, model.blank, delimiter=model.delimiter)
            try:
                _, lp = viterbi(window, g)
            except ValueError:
                continue
            score = float(lp.sum())
            if score > best_score:
                best, best_score = (cand, ids), score
        if best and best[0] != w.align:
            w.align = best[0]
            word_tokens[i] = best[1]
            changed = True
        if best:
            w.flags = [f for f in w.flags if f != "uncertain_spoken"] + [f"spoken_form:{best[0]}"]
    return changed
