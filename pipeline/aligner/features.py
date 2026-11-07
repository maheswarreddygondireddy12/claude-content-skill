"""Turn raw word spans into the timing foundation: words, boundaries, sentences, phrases, rate.

Nothing here decides a caption style. Boundaries carry ingredients (gap, punctuation, signpost,
language switch) and a blended strength so the Director can chunk differently per Reel.
"""
from __future__ import annotations

import numpy as np

from .acoustic import FRAME_SEC
from .audio import rms_db
from .script import Word, boundary_punct_score
from .viterbi import WordSpan


def _t(frame: int) -> float:
    return round(frame * FRAME_SEC, 3)


def build_words(words: list[Word], spans: list[WordSpan], audio: np.ndarray, with_chars: bool) -> list[dict]:
    durations = np.array([max(s.end_frame - s.start_frame, 1) * FRAME_SEC for s in spans])
    letters = np.array([max(len(w.align.replace(" ", "")), 1) for w in words])
    per_char = np.log(durations / letters)
    mu, sd = per_char.mean(), per_char.std() or 1.0

    out = []
    for w, s, pc in zip(words, spans, per_char):
        start, end = _t(s.start_frame), _t(s.end_frame)
        rec = {
            "i": w.i,
            "raw": w.raw,
            "display": w.display,
            "align": w.align,
            "start": start,
            "end": end,
            "score": round(s.score, 4),
            "conf": round(float(np.exp(s.score)), 4),
            "lang": w.lang,
            "markers": list(w.markers),
            "punct_after": w.punct_after,
            "sentence": w.sentence,
            "phrase": w.phrase,
            "signpost": w.signpost,
            "rms_db": round(rms_db(audio, start, end), 2),
            "dur_z": round(float((pc - mu) / sd), 3),
            "flags": list(w.flags),
        }
        if with_chars:
            rec["chars"] = [[_t(a), _t(b)] for a, b in s.char_frames]
        out.append(rec)
    return out


def build_boundaries(words: list[Word], wrecs: list[dict]) -> list[dict]:
    out = []
    for a, b, w in zip(wrecs, wrecs[1:], words):
        gap_ms = max(0.0, (b["start"] - a["end"]) * 1000)
        punct = boundary_punct_score(w)
        lang_switch = a["lang"] in ("en", "te") and b["lang"] in ("en", "te") and a["lang"] != b["lang"]
        strength = 0.55 * punct + 0.25 * min(gap_ms / 250.0, 1.0) + 0.12 * b["signpost"] + 0.08 * lang_switch
        out.append({
            "after": a["i"],
            "gap_ms": round(gap_ms, 1),
            "punct": w.punct_after,
            "punct_score": punct,
            "signpost_next": b["signpost"],
            "lang_switch": bool(lang_switch),
            "sentence_break": a["sentence"] != b["sentence"],
            "strength": round(min(strength, 1.0), 3),
        })
    return out


def _groups(wrecs: list[dict], key: str) -> list[dict]:
    groups: list[dict] = []
    for w in wrecs:
        if not groups or groups[-1]["i"] != w[key]:
            groups.append({"i": w[key], "word_start": w["i"], "word_end": w["i"], "start": w["start"], "end": w["end"], "words": []})
        g = groups[-1]
        g["word_end"], g["end"] = w["i"], w["end"]
        g["words"].append(w["display"])
    for g in groups:
        g["text"] = " ".join(g.pop("words"))
    return groups


def speech_rate(wrecs: list[dict], duration: float, window: float = 3.0, hop: float = 0.5) -> dict:
    starts = np.array([w["start"] for w in wrecs])
    values = []
    t = 0.0
    while t + window <= duration + 1e-6:
        n = int(((starts >= t) & (starts < t + window)).sum())
        values.append([round(t + window / 2, 2), round(n / window, 2)])
        t += hop
    return {"window_s": window, "hop_s": hop, "unit": "words_per_s", "values": values}


def build_timing(words: list[Word], spans: list[WordSpan], audio: np.ndarray, duration: float,
                 stars: list[tuple[int, int, int]], with_chars: bool = False) -> dict:
    wrecs = build_words(words, spans, audio, with_chars)
    return {
        "words": wrecs,
        "boundaries": build_boundaries(words, wrecs),
        "sentences": _groups(wrecs, "sentence"),
        "phrases": _groups(wrecs, "phrase"),
        "rate": speech_rate(wrecs, duration),
        "unscripted": [
            {"start": _t(a), "end": _t(b), "before_word": nxt, "dur": round((b - a) * FRAME_SEC, 3),
             "rms_db": round(rms_db(audio, _t(a), _t(b)), 2)}
            for a, b, nxt in stars
        ],
    }
