"""CTC forced alignment (Viterbi) over a token graph.

The graph is the usual CTC chain  blank, t1, blank, t2, ..., tN, blank  extended with optional
<star> states. A star state matches "any speech" at a fixed penalty, so audio that is not in the
script is absorbed there instead of being forced onto neighbouring words. Stars can be skipped.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

BLANK, TOKEN, STAR = 0, 1, 2
MAX_OFFSET = 4
NEG = np.float32(-1e30)


@dataclass
class Graph:
    kind: np.ndarray    # (S,) int8: BLANK / TOKEN / STAR
    col: np.ndarray     # (S,) emission column for each state
    word: np.ndarray    # (S,) word index for word tokens, -1 otherwise
    char: np.ndarray    # (S,) character index inside the word's token list, -1 otherwise
    preds: np.ndarray   # (S, MAX_OFFSET + 1) bool: may come from state s - k
    start_ok: np.ndarray
    end_ok: np.ndarray

    @property
    def n_required(self) -> int:
        return int((self.kind == TOKEN).sum())


def build_graph(
    word_tokens: list[list[int]],
    blank: int,
    star_col: int | None = None,
    star_before: set[int] | frozenset = frozenset(),
    delimiter: int | None = None,
) -> Graph:
    """word_tokens[w] = token ids of word w (a delimiter id may appear inside multi-part words).

    star_before: word indices that get an optional star group in front of them;
    len(word_tokens) in this set adds a trailing star.
    delimiter: word-separator token (e.g. "|" for wav2vec2 English), inserted between words.
    """
    kind: list[int] = [BLANK]
    col: list[int] = [blank]
    word: list[int] = [-1]
    char: list[int] = [-1]

    def add(k: int, c: int, w: int = -1, ch: int = -1) -> None:
        kind.extend([k, BLANK])
        col.extend([c, blank])
        word.extend([w, -1])
        char.extend([ch, -1])

    use_star = star_col is not None
    for w, toks in enumerate(word_tokens):
        if delimiter is not None and w > 0:
            add(TOKEN, delimiter)
        if use_star and w in star_before:
            add(STAR, star_col)
        for ci, t in enumerate(toks):
            add(TOKEN, t, w if t != delimiter else -1, ci)
    if use_star and len(word_tokens) in star_before:
        add(STAR, star_col)

    kind_a = np.array(kind, dtype=np.int8)
    col_a = np.array(col, dtype=np.int64)
    S = len(kind_a)
    preds = np.zeros((S, MAX_OFFSET + 1), dtype=bool)
    preds[:, 0] = True
    preds[1:, 1] = True
    for s in range(S):
        k = kind_a[s]
        if k != BLANK:
            # skip the blank between two different symbols
            if s >= 2 and kind_a[s - 1] == BLANK and kind_a[s - 2] != BLANK and col_a[s - 2] != col_a[s]:
                preds[s, 2] = True
            # skip an optional star group: blank, STAR, blank -> s
            if s >= 3 and kind_a[s - 1] == BLANK and kind_a[s - 2] == STAR and kind_a[s - 3] == BLANK:
                preds[s, 3] = True
                if s >= 4 and kind_a[s - 4] != BLANK and col_a[s - 4] != col_a[s]:
                    preds[s, 4] = True
        elif s >= 2 and kind_a[s - 1] == STAR and kind_a[s - 2] == BLANK:
            preds[s, 2] = True  # blank -> (skip star) -> blank

    optional = kind_a != TOKEN
    start_ok = np.zeros(S, dtype=bool)
    end_ok = np.zeros(S, dtype=bool)
    for s in range(S):
        start_ok[s] = True
        if not optional[s]:
            break
    for s in range(S - 1, -1, -1):
        end_ok[s] = True
        if not optional[s]:
            break

    return Graph(kind_a, col_a, np.array(word, dtype=np.int64), np.array(char, dtype=np.int64),
                 preds, start_ok, end_ok)


def add_star_column(emissions: np.ndarray, blank: int, penalty: float) -> tuple[np.ndarray, int]:
    """Append a <star> column: best non-blank log-prob at each frame plus a (negative) penalty."""
    non_blank = np.delete(emissions, blank, axis=1)
    star = non_blank.max(axis=1, keepdims=True) + np.float32(penalty)
    return np.concatenate([emissions, star.astype(emissions.dtype)], axis=1), emissions.shape[1]


def viterbi(emissions: np.ndarray, graph: Graph) -> tuple[np.ndarray, np.ndarray]:
    """Best state path. Returns (state index per frame, per-frame log-prob on that path)."""
    T = emissions.shape[0]
    S = len(graph.kind)
    if graph.n_required > T:
        raise ValueError(f"Audio too short for script: {graph.n_required} tokens need >= that many frames, got {T}")

    em = emissions[:, graph.col].astype(np.float32)  # (T, S)
    pred_masks = [None] + [~graph.preds[:, k] for k in range(1, MAX_OFFSET + 1)]

    delta = np.full(S, NEG, dtype=np.float32)
    delta[graph.start_ok] = em[0, graph.start_ok]
    back = np.zeros((T, S), dtype=np.int8)
    cand = np.empty(S, dtype=np.float32)
    for t in range(1, T):
        best = delta.copy()
        arg = np.zeros(S, dtype=np.int8)
        for k in range(1, MAX_OFFSET + 1):
            cand[:k] = NEG
            cand[k:] = delta[:-k]
            cand[pred_masks[k]] = NEG
            better = cand > best
            best[better] = cand[better]
            arg[better] = k
        delta = best + em[t]
        back[t] = arg

    final = np.where(graph.end_ok, delta, NEG)
    s = int(np.argmax(final))
    if final[s] <= NEG / 2:
        raise RuntimeError("No valid alignment path found")
    path = np.empty(T, dtype=np.int64)
    for t in range(T - 1, -1, -1):
        path[t] = s
        s -= int(back[t, s])
    frame_lp = em[np.arange(T), path]
    return path, frame_lp


@dataclass
class WordSpan:
    word: int
    start_frame: int
    end_frame: int         # exclusive
    score: float           # mean log-prob over the word's token frames
    char_frames: list[tuple[int, int]]  # (first frame, last frame + 1) per token of the word


def word_spans(path: np.ndarray, frame_lp: np.ndarray, graph: Graph, n_words: int) -> list[WordSpan]:
    spans: list[WordSpan] = []
    state_word = graph.word[path]
    state_char = graph.char[path]
    is_tok = (graph.kind[path] == TOKEN) & (state_word >= 0)
    for w in range(n_words):
        frames = np.nonzero(is_tok & (state_word == w))[0]
        if len(frames) == 0:  # cannot happen for a valid path; keep the record honest anyway
            spans.append(WordSpan(w, -1, -1, float("-inf"), []))
            continue
        chars: list[tuple[int, int]] = []
        for ci in np.unique(state_char[frames]):
            cf = frames[state_char[frames] == ci]
            chars.append((int(cf[0]), int(cf[-1]) + 1))
        spans.append(WordSpan(w, int(frames[0]), int(frames[-1]) + 1, float(frame_lp[frames].mean()), chars))
    return spans


def star_regions(path: np.ndarray, graph: Graph) -> list[tuple[int, int, int]]:
    """Contiguous runs of star frames as (start_frame, end_frame_exclusive, next_word_index)."""
    is_star = graph.kind[path] == STAR
    regions: list[tuple[int, int, int]] = []
    t, T = 0, len(path)
    while t < T:
        if is_star[t]:
            t0 = t
            while t < T and is_star[t]:
                t += 1
            nxt = next((int(graph.word[path[u]]) for u in range(t, T)
                        if graph.kind[path[u]] == TOKEN and graph.word[path[u]] >= 0), -1)
            regions.append((t0, t, nxt))
        else:
            t += 1
    return regions
