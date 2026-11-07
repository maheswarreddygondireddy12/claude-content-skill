"""JSON Schema for timing.json (schema_version 1) — the contract later stages consume."""
from __future__ import annotations

SCHEMA_VERSION = 1

_num = {"type": "number"}
_int = {"type": "integer"}
_str = {"type": "string"}
_bool = {"type": "boolean"}
_strs = {"type": "array", "items": _str}

WORD = {
    "type": "object",
    "required": ["i", "raw", "display", "align", "start", "end", "score", "conf", "lang", "markers",
                 "punct_after", "sentence", "phrase", "signpost", "rms_db", "dur_z", "flags"],
    "properties": {
        "i": _int, "raw": _str, "display": _str, "align": _str,
        "start": _num, "end": _num, "score": _num, "conf": _num, "score_rz": _num,
        "lang": {"enum": ["en", "te", "num", "other"]},
        "markers": _strs, "punct_after": _str, "sentence": _int, "phrase": _int,
        "signpost": _bool, "rms_db": _num, "dur_z": _num, "flags": _strs,
        "chars": {"type": "array", "items": {"type": "array", "items": _num, "minItems": 2, "maxItems": 2}},
    },
}

GROUP = {
    "type": "object",
    "required": ["i", "word_start", "word_end", "start", "end", "text"],
    "properties": {"i": _int, "word_start": _int, "word_end": _int, "start": _num, "end": _num, "text": _str},
}

TIMING_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Video Editing Workflow timing.json",
    "type": "object",
    "required": ["schema_version", "meta", "words", "boundaries", "sentences", "phrases", "rate", "unscripted"],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "meta": {
            "type": "object",
            "required": ["slug", "script_sha256", "audio_sha256", "audio_file", "duration_s", "model", "frame_s"],
        },
        "words": {"type": "array", "items": WORD, "minItems": 1},
        "boundaries": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["after", "gap_ms", "punct", "punct_score", "signpost_next", "lang_switch",
                             "sentence_break", "strength"],
            },
        },
        "sentences": {"type": "array", "items": GROUP},
        "phrases": {"type": "array", "items": GROUP},
        "rate": {"type": "object", "required": ["window_s", "hop_s", "values"]},
        "unscripted": {"type": "array"},
    },
}


def validate(timing: dict) -> None:
    import jsonschema
    jsonschema.validate(timing, TIMING_SCHEMA)
