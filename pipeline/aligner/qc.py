"""Basic QC for an alignment: structural checks, per-word anomalies, suspected VO/script mismatches."""
from __future__ import annotations

import numpy as np

SQUEEZED_MIN_S = 0.06          # a word with >= 3 letters spoken in under 60 ms is not real
STRETCH_BASE_S = 1.2           # longer than this (plus per-letter allowance) is suspicious
STRETCH_PER_LETTER_S = 0.12
ELONGATED_MAX_S = 2.5
LOW_CONF_RZ = -3.5             # robust z-score of the word score
SPOKEN_FORM_RZ = -2.0          # looser threshold for words whose spoken form is a guess (numbers, symbols)
UNSCRIPTED_MIN_S = 0.35
UNSCRIPTED_RMS_BELOW_SPEECH_DB = 15.0
CLUSTER_WINDOW = 4             # words
CLUSTER_MIN_FLAGS = 2


def _robust_z(values: np.ndarray) -> np.ndarray:
    med = np.median(values)
    mad = np.median(np.abs(values - med)) * 1.4826 or 1e-6
    return (values - med) / mad


def run_qc(timing: dict, duration: float, n_script_words: int) -> dict:
    words = timing["words"]
    structural = []
    if len(words) != n_script_words:
        structural.append(f"word count {len(words)} != script words {n_script_words}")
    for a, b in zip(words, words[1:]):
        if b["start"] < a["end"] - 1e-6:
            structural.append(f"overlap: word {a['i']} ends {a['end']} after word {b['i']} starts {b['start']}")
    for w in words:
        if not (0 <= w["start"] < w["end"] <= duration + 0.05):
            structural.append(f"word {w['i']} '{w['display']}' has invalid span {w['start']}-{w['end']}")

    scores = np.array([w["score"] for w in words])
    rz = _robust_z(scores)
    speech_rms = float(np.median([w["rms_db"] for w in words]))
    for w, z in zip(words, rz):
        w["score_rz"] = round(float(z), 2)
        dur = w["end"] - w["start"]
        letters = len(w["align"].replace(" ", ""))
        new: list[str] = []
        if letters >= 3 and dur < SQUEEZED_MIN_S:
            new.append("squeezed")
        limit = ELONGATED_MAX_S if "elongated" in w["markers"] else STRETCH_BASE_S + STRETCH_PER_LETTER_S * letters
        if dur > limit:
            new.append("stretched")
        if z < LOW_CONF_RZ:
            new.append("low_conf")
        if "uncertain_spoken" in w["flags"] and z < SPOKEN_FORM_RZ:
            new.append("check_spoken_form")
        w["flags"] = sorted(set(w["flags"]) | set(new))

    unscripted = [
        u for u in timing["unscripted"]
        if u["dur"] >= UNSCRIPTED_MIN_S and u["rms_db"] > speech_rms - UNSCRIPTED_RMS_BELOW_SPEECH_DB
    ]

    anomaly = {"squeezed", "stretched", "low_conf", "check_spoken_form"}
    flagged = [w for w in words if anomaly & set(w["flags"])]
    regions = _mismatch_regions(words, anomaly, unscripted)

    flagged_frac = len(flagged) / max(len(words), 1)
    if structural:
        status = "FAIL"
    elif regions or flagged_frac > 0.02:
        status = "WARN"
    else:
        status = "PASS"

    return {
        "status": status,
        "structural_errors": structural,
        "n_words": len(words),
        "duration_s": round(duration, 3),
        "flagged_words": [
            {"i": w["i"], "display": w["display"], "start": w["start"], "end": w["end"],
             "flags": [f for f in w["flags"] if f in anomaly], "score_rz": w["score_rz"]}
            for w in flagged
        ],
        "flagged_fraction": round(flagged_frac, 4),
        "unscripted_speech": unscripted,
        "mismatch_regions": regions,
        "stats": {
            "score_median": round(float(np.median(scores)), 4),
            "conf_median": round(float(np.median([w["conf"] for w in words])), 4),
            "words_per_min": round(len(words) / duration * 60, 1),
            "speech_rms_db_median": round(speech_rms, 2),
            "word_dur_median_s": round(float(np.median([w["end"] - w["start"] for w in words])), 3),
        },
    }


def _mismatch_regions(words: list[dict], anomaly: set, unscripted: list[dict]) -> list[dict]:
    is_flag = np.array([bool(anomaly & set(w["flags"])) for w in words])
    hot = np.zeros(len(words), dtype=bool)
    for i in range(len(words)):
        window = slice(i, min(i + CLUSTER_WINDOW, len(words)))
        if is_flag[window].sum() >= CLUSTER_MIN_FLAGS:
            idx = np.nonzero(is_flag[window])[0] + i
            hot[idx[0]:idx[-1] + 1] = True
    # a single squeezed/stretched word is already a likely skip or ad-lib on its own
    for i, w in enumerate(words):
        if {"squeezed", "stretched"} & set(w["flags"]):
            hot[i] = True

    regions = []
    i = 0
    while i < len(words):
        if hot[i]:
            j = i
            while j + 1 < len(words) and hot[j + 1]:
                j += 1
            regions.append(_region(words, i, j, "flag_cluster"))
            i = j + 1
        else:
            i += 1
    for u in unscripted:
        k = u["before_word"]
        a = max(k - 1, 0) if k >= 0 else len(words) - 1
        b = k if k >= 0 else len(words) - 1
        r = _region(words, a, b, "unscripted_speech")
        r["start"], r["end"] = min(r["start"], u["start"]), max(r["end"], u["end"])
        regions.append(r)
    return sorted(regions, key=lambda r: r["start"])


def _region(words: list[dict], a: int, b: int, kind: str) -> dict:
    return {
        "kind": kind,
        "word_start": a,
        "word_end": b,
        "start": words[a]["start"],
        "end": words[b]["end"],
        "sentences": sorted({words[k]["sentence"] for k in range(a, b + 1)}),
        "text": " ".join(words[k]["display"] for k in range(a, b + 1)),
    }


def report_markdown(slug: str, model: dict, qc: dict) -> str:
    s = qc["stats"]
    lines = [
        f"# Alignment QC — {slug}",
        "",
        f"**Status: {qc['status']}**  ·  model `{model['id']}` ({model['license']})",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Words | {qc['n_words']} |",
        f"| Duration | {qc['duration_s']} s |",
        f"| Speech rate | {s['words_per_min']} words/min |",
        f"| Median word confidence | {s['conf_median']} |",
        f"| Median word duration | {s['word_dur_median_s']} s |",
        f"| Flagged words | {len(qc['flagged_words'])} ({qc['flagged_fraction'] * 100:.1f}%) |",
        f"| Suspected mismatch regions | {len(qc['mismatch_regions'])} |",
        "",
    ]
    if qc["structural_errors"]:
        lines += ["## Structural errors", ""] + [f"- {e}" for e in qc["structural_errors"]] + [""]
    if qc["mismatch_regions"]:
        lines += ["## Suspected VO/script mismatches", "", "| Time | Kind | Words | Text |", "|---|---|---|---|"]
        for r in qc["mismatch_regions"]:
            lines.append(f"| {r['start']:.2f}–{r['end']:.2f} s | {r['kind']} | {r['word_start']}–{r['word_end']} | {r['text']} |")
        lines.append("")
    if qc["flagged_words"]:
        lines += ["## Flagged words", "", "| # | Word | Time | Flags | score z |", "|---|---|---|---|---|"]
        for w in qc["flagged_words"]:
            lines.append(f"| {w['i']} | {w['display']} | {w['start']:.2f}–{w['end']:.2f} | {', '.join(w['flags'])} | {w['score_rz']} |")
        lines.append("")
    return "\n".join(lines)
