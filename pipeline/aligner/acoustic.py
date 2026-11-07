"""Acoustic models: audio -> per-frame CTC log-probabilities over characters.

Both providers are wav2vec2-style CTC models with a 20 ms frame (stride 320 @ 16 kHz), so the
aligner, features and QC are model-agnostic.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .audio import SAMPLE_RATE

FRAME_STRIDE = 320
FRAME_SEC = FRAME_STRIDE / SAMPLE_RATE  # 0.02
CACHE_DIR = Path.home() / ".video-editing-workflow" / "cache" / "emissions"


@dataclass(frozen=True)
class ModelSpec:
    key: str
    model_id: str
    license: str
    note: str


MODELS = {
    "wav2vec2": ModelSpec(
        "wav2vec2", "facebook/wav2vec2-large-960h-lv60-self", "Apache-2.0",
        "English character CTC model; permissive licence",
    ),
    "mms": ModelSpec(
        "mms", "MahmoudAshraf/mms-300m-1130-forced-aligner", "CC-BY-NC-4.0",
        "Multilingual MMS forced-alignment model; NON-COMMERCIAL licence",
    ),
}


class AcousticModel:
    def __init__(self, key: str, threads: int = 4):
        import torch
        from transformers import AutoFeatureExtractor, AutoTokenizer, Wav2Vec2ForCTC

        torch.set_num_threads(threads)
        self.spec = MODELS[key]

        def load(cls, **kw):
            # Cached copy first, so production never depends on the Hugging Face Hub being reachable.
            try:
                return cls.from_pretrained(self.spec.model_id, local_files_only=True, **kw)
            except OSError:
                return cls.from_pretrained(self.spec.model_id, **kw)

        self.feature_extractor = load(AutoFeatureExtractor)
        self.tokenizer = load(AutoTokenizer)
        self.model = load(Wav2Vec2ForCTC).eval()
        self.vocab: dict[str, int] = self.tokenizer.get_vocab()
        self.blank = self._blank_id()
        self.delimiter = self.vocab.get("|")
        self.uppercase = "A" in self.vocab and "a" not in self.vocab

    def _blank_id(self) -> int:
        for name in ("<blank>", "<pad>"):
            if name in self.vocab:
                return self.vocab[name]
        return int(self.model.config.pad_token_id)

    # ---- text -> tokens -------------------------------------------------
    def tokens_for(self, align_text: str) -> tuple[list[int], list[str]]:
        """Token ids for one word's spoken form ("seven pee em" -> parts joined by the delimiter if any)."""
        ids: list[int] = []
        dropped: list[str] = []
        for pi, part in enumerate(align_text.split()):
            if pi > 0 and self.delimiter is not None:
                ids.append(self.delimiter)
            for ch in part:
                key = ch.upper() if self.uppercase else ch
                if key in self.vocab:
                    ids.append(self.vocab[key])
                else:
                    dropped.append(ch)
        return ids, dropped

    # ---- audio -> emissions ---------------------------------------------
    def emissions(self, audio: np.ndarray, window_s: float = 30.0, context_s: float = 2.0,
                  cache_key: str | None = None) -> np.ndarray:
        cache_path = None
        if cache_key:
            digest = hashlib.sha256(f"{self.spec.model_id}|{cache_key}|{window_s}|{context_s}".encode()).hexdigest()[:24]
            cache_path = CACHE_DIR / f"{self.spec.key}_{digest}.npy"
            if cache_path.exists():
                return np.load(cache_path)

        import torch

        n = len(audio)
        n_frames = int(np.ceil(n / FRAME_STRIDE))
        vocab_size = self.model.config.vocab_size
        out = np.full((n_frames, vocab_size), -30.0, dtype=np.float32)
        out[:, self.blank] = 0.0  # frames the model never covers count as silence
        win, ctx = int(window_s * SAMPLE_RATE), int(context_s * SAMPLE_RATE)

        for c0 in range(0, n, win):
            c1 = min(n, c0 + win)
            s0, s1 = max(0, c0 - ctx), min(n, c1 + ctx)
            inputs = self.feature_extractor(audio[s0:s1], sampling_rate=SAMPLE_RATE, return_tensors="pt")
            with torch.inference_mode():
                logits = self.model(inputs.input_values).logits[0]
            lp = torch.log_softmax(logits.float(), dim=-1).numpy()
            f0 = (c0 - s0) // FRAME_STRIDE
            f_count = int(np.ceil((c1 - c0) / FRAME_STRIDE))
            seg = lp[f0:f0 + f_count]
            t0 = c0 // FRAME_STRIDE
            m = min(len(seg), n_frames - t0)
            out[t0:t0 + m] = seg[:m]

        if cache_path is not None:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            np.save(cache_path, out)
        return out
