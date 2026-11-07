"""Viterbi on synthetic emissions where the right answer is known."""
import numpy as np

from aligner.viterbi import STAR, add_star_column, build_graph, star_regions, viterbi, word_spans

BLANK = 0
V = 6  # blank + tokens 1..5


def make_emissions(frames: list[int], noise: float = 0.0, seed: int = 0) -> np.ndarray:
    """Each frame strongly predicts the given token id (or 'speech' = -1: a random non-blank)."""
    rng = np.random.default_rng(seed)
    em = np.full((len(frames), V), -8.0, dtype=np.float32)
    for t, tok in enumerate(frames):
        if tok == -1:
            em[t, rng.integers(1, V)] = -0.1
        else:
            em[t, tok] = -0.05
    em += rng.normal(0, noise, em.shape).astype(np.float32)
    return em


def test_simple_alignment_recovers_word_boundaries():
    # word0 = [1, 2], word1 = [3]; timeline: blank x3, 1 1, 2, blank x2, 3 3 3, blank
    frames = [0, 0, 0, 1, 1, 2, 0, 0, 3, 3, 3, 0]
    em = make_emissions(frames)
    g = build_graph([[1, 2], [3]], BLANK)
    path, lp = viterbi(em, g)
    spans = word_spans(path, lp, g, 2)
    assert (spans[0].start_frame, spans[0].end_frame) == (3, 6)
    assert (spans[1].start_frame, spans[1].end_frame) == (8, 11)


def test_repeated_token_needs_blank_between():
    frames = [0, 4, 0, 4, 0]
    g = build_graph([[4, 4]], BLANK)
    path, lp = viterbi(make_emissions(frames), g)
    spans = word_spans(path, lp, g, 1)
    assert spans[0].char_frames == [(1, 2), (3, 4)]


def test_delimiter_is_not_part_of_words():
    frames = [0, 1, 5, 2, 0]
    g = build_graph([[1], [2]], BLANK, delimiter=5)
    path, lp = viterbi(make_emissions(frames), g)
    spans = word_spans(path, lp, g, 2)
    assert (spans[0].start_frame, spans[0].end_frame) == (1, 2)
    assert (spans[1].start_frame, spans[1].end_frame) == (3, 4)


def test_star_absorbs_unscripted_speech_and_keeps_neighbours():
    # script: w0=[1], w1=[2]; audio: 1, then 8 frames of unscripted speech, then 2
    frames = [0, 1, 1, 0] + [-1] * 8 + [0, 2, 2, 0]
    em, star_col = add_star_column(make_emissions(frames, seed=3), BLANK, penalty=-1.0)
    g = build_graph([[1], [2]], BLANK, star_col=star_col, star_before={1})
    path, lp = viterbi(em, g)
    spans = word_spans(path, lp, g, 2)
    assert (spans[0].start_frame, spans[0].end_frame) == (1, 3)
    assert (spans[1].start_frame, spans[1].end_frame) == (13, 15)
    regions = star_regions(path, g)
    assert len(regions) == 1 and regions[0][2] == 1
    assert regions[0][1] - regions[0][0] >= 6


def test_star_is_skipped_when_audio_matches_script():
    frames = [0, 1, 1, 0, 2, 2, 0]
    em, star_col = add_star_column(make_emissions(frames), BLANK, penalty=-2.0)
    g = build_graph([[1], [2]], BLANK, star_col=star_col, star_before={0, 1, 2})
    path, _ = viterbi(em, g)
    assert not (g.kind[path] == STAR).any()


def test_adjacent_words_without_blank():
    frames = [1, 1, 2, 2]
    g = build_graph([[1], [2]], BLANK)
    path, lp = viterbi(make_emissions(frames), g)
    spans = word_spans(path, lp, g, 2)
    assert spans[0].end_frame == spans[1].start_frame == 2

