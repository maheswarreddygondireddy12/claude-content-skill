"""Script tokenisation.

Turns a project's script into a list of words. The default lexicon supports Romanized Telugu-English.
Each word has three text forms:
  raw      exactly as written (letters/digits/symbol only)
  display  cleaned for on-screen use (typos fixed, numbers formatted); the Director may restyle it
  align    what is actually spoken, lowercase a-z/' with spaces between spoken parts
plus markers (caps, elongated, question, ...), sentence/phrase ids and signpost hints.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

LEXICON_DIR = Path(__file__).resolve().parent.parent / "lexicon"

TOKEN_RE = re.compile(r"\n+|[A-Za-z0-9']+|[^\sA-Za-z0-9']+")
SPOKEN_SYMBOLS = {"+": "plus", "&": "and", "=": "equals", "%": "percent", "@": "at"}
DISPLAY_SUFFIX_UPPER = {"pm", "am", "k", "gb", "mb"}
SPOKEN_SUFFIX = {"pm": "pee em", "am": "ay em", "k": "kay", "gb": "jee bee", "mb": "em bee",
                 "st": "", "nd": "", "rd": "", "th": ""}

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


@dataclass
class Word:
    i: int
    raw: str
    display: str
    align: str
    punct_after: str = ""
    newline_after: bool = False
    markers: list[str] = field(default_factory=list)
    lang: str = "other"
    sentence: int = 0
    phrase: int = 0
    signpost: bool = False
    flags: list[str] = field(default_factory=list)


def number_to_words(n: int) -> str:
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    if n < 1000:
        rest = n % 100
        return ONES[n // 100] + " hundred" + ("" if rest == 0 else " " + number_to_words(rest))
    if n < 1_000_000:
        rest = n % 1000
        return number_to_words(n // 1000) + " thousand" + ("" if rest == 0 else " " + number_to_words(rest))
    return " ".join(ONES[int(d)] for d in str(n))


def _load_json(name: str) -> dict:
    data = json.loads((LEXICON_DIR / name).read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


@dataclass(frozen=True)
class Lexicon:
    spellfix: dict
    acronyms: dict
    signposts: tuple
    telugu_common: frozenset


@lru_cache(maxsize=1)
def default_lexicon() -> Lexicon:
    telugu = {
        line.strip().lower()
        for line in (LEXICON_DIR / "telugu_common.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    signposts = sorted(
        (tuple(s.lower().split()) for s in _load_json("signposts.json")["signposts"]),
        key=len, reverse=True,
    )
    return Lexicon(
        spellfix={k.lower(): v for k, v in _load_json("spellfix.json").items()},
        acronyms={k.lower(): v for k, v in _load_json("acronyms.json").items()},
        signposts=tuple(signposts),
        telugu_common=frozenset(telugu),
    )


def normalise_text(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = unicodedata.normalize("NFKC", text)  # "…" -> "..."
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _align_letters(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z' ]+", " ", s)
    s = re.sub(r"([a-z])\1{2,}", r"\1", s)  # "telusaaa" -> "telusa": one long vowel, not three
    s = re.sub(r"(^|\s)'+|'+(\s|$)", " ", s)
    return " ".join(s.split())


def _english_zipf(word: str) -> float:
    from wordfreq import zipf_frequency
    return zipf_frequency(word, "en")


def _forms(raw: str, lex: Lexicon) -> tuple[str, str, list[str], list[str]]:
    """Return (display, align, markers, flags) for one raw token."""
    markers: list[str] = []
    flags: list[str] = []
    low = raw.lower().strip("'")

    if raw in SPOKEN_SYMBOLS:
        return raw, SPOKEN_SYMBOLS[raw], ["symbol"], ["uncertain_spoken"]

    m = re.fullmatch(r"(\d+)([a-z]*)", low)
    if m:
        num, suffix = int(m.group(1)), m.group(2)
        spoken_suffix = SPOKEN_SUFFIX.get(suffix, suffix)
        align = " ".join(p for p in (number_to_words(num), spoken_suffix) if p)
        disp_suffix = suffix.upper() if suffix in DISPLAY_SUFFIX_UPPER else suffix
        display = f"{num} {disp_suffix}".strip() if suffix not in ("st", "nd", "rd", "th") else f"{num}{suffix}"
        # Telugu speakers may say numbers in Telugu; QC checks the score of these words.
        return display, _align_letters(align), ["number"], ["uncertain_spoken"]

    if low in lex.acronyms:
        markers.append("acronym")
        return raw.upper() if raw.isupper() or len(low) <= 4 else raw, _align_letters(lex.acronyms[low]), markers, flags

    if raw.isupper() and len(raw) >= 2:
        if len(raw) <= 3:  # unknown short all-caps -> probably an acronym spoken letter by letter
            markers.append("acronym")
            flags.append("uncertain_spoken")
            return raw, _align_letters(" ".join(lex.acronyms.get(c.lower(), c.lower()) for c in raw)), markers, flags
        markers.append("caps")

    if re.search(r"([a-z])\1{2,}", low):
        markers.append("elongated")

    fixed = lex.spellfix.get(low)
    if fixed:
        flags.append("spellfixed")
        display = fixed if raw.islower() else fixed.capitalize() if raw[:1].isupper() and not raw.isupper() else fixed.upper()
        return display, _align_letters(fixed), markers, flags

    return raw.strip("'"), _align_letters(low), markers, flags


def _lang(word: Word, lex: Lexicon) -> str:
    if "number" in word.markers:
        return "num"
    if "symbol" in word.markers:
        return "other"
    if "acronym" in word.markers:
        return "en"
    low = word.align.replace(" ", "")
    if low in lex.telugu_common:
        return "te"
    if not _has_wordfreq():
        return "other"
    return "en" if _english_zipf(low) >= 3.3 else "te"


@lru_cache(maxsize=1)
def _has_wordfreq() -> bool:
    try:
        import wordfreq  # noqa: F401
        return True
    except ImportError:
        return False


SENTENCE_PUNCT = re.compile(r"[.?!]")
PHRASE_PUNCT = re.compile(r"[,;:\-]")


def tokenize(text: str, lex: Lexicon | None = None) -> list[Word]:
    lex = lex or default_lexicon()
    text = normalise_text(text)
    words: list[Word] = []
    for tok in TOKEN_RE.findall(text):
        if tok.startswith("\n"):
            if words:
                words[-1].newline_after = True
            continue
        is_wordlike = bool(re.search(r"[A-Za-z0-9]", tok))
        if not is_wordlike and tok.strip() not in SPOKEN_SYMBOLS:
            if words:
                words[-1].punct_after += tok
            continue
        display, align, markers, flags = _forms(tok.strip(), lex)
        if not align:
            if words:
                words[-1].punct_after += tok
            continue
        words.append(Word(i=len(words), raw=tok.strip(), display=display, align=align, markers=markers, flags=flags))

    _mark_signposts(words, lex)
    _assign_structure(words, lex)
    return words


def _mark_signposts(words: list[Word], lex: Lexicon) -> None:
    aligned = [w.align for w in words]
    for i in range(len(words)):
        for sp in lex.signposts:
            if tuple(aligned[i:i + len(sp)]) == sp:
                words[i].signpost = True
                break


def _assign_structure(words: list[Word], lex: Lexicon) -> None:
    sentence = phrase = 0
    for idx, w in enumerate(words):
        if idx > 0:
            prev = words[idx - 1]
            if prev.newline_after or SENTENCE_PUNCT.search(prev.punct_after):
                sentence += 1
                phrase += 1
            elif PHRASE_PUNCT.search(prev.punct_after) or w.signpost:
                phrase += 1
        w.sentence, w.phrase = sentence, phrase
        p = w.punct_after
        if "?" in p:
            w.markers.append("question")
        if "!" in p:
            w.markers.append("exclaim")
        if re.search(r"\.{2,}", p):
            w.markers.append("ellipsis_after")
        w.lang = _lang(w, lex)


TELUGU_NUMBERS = {1: "okati", 2: "rendu", 3: "moodu", 4: "naalugu", 5: "aidu", 6: "aaru", 7: "edu", 8: "enimidi",
                  9: "tommidi", 10: "padi", 100: "vanda"}
SYMBOL_ALTERNATIVES = {"+": ["plus", "and"], "&": ["and"], "=": ["equals", "equal to"], "%": ["percent", "percentage"]}


def spoken_alternatives(w: Word) -> list[str]:
    """Plausible spoken forms for words whose pronunciation the script cannot tell us
    (numbers may be said in English or Telugu, symbols may be read differently).
    The aligner scores each against the audio and keeps the best. First entry = default."""
    if "symbol" in w.markers:
        return [_align_letters(a) for a in SYMBOL_ALTERNATIVES.get(w.raw, [w.align])]
    if "number" not in w.markers:
        return [w.align]
    m = re.fullmatch(r"(\d+)([a-z]*)", w.raw.lower())
    if not m:
        return [w.align]
    num, suffix = int(m.group(1)), m.group(2)
    suffixes = {"pm": ["pee em", "pm", ""], "am": ["ay em", "am", ""], "days": ["days", "rojulu"],
                "day": ["day", "roju"]}.get(suffix, [SPOKEN_SUFFIX.get(suffix, suffix)])
    numbers = [number_to_words(num)] + ([TELUGU_NUMBERS[num]] if num in TELUGU_NUMBERS else [])
    out: list[str] = []
    for n in numbers:
        for s in suffixes:
            cand = _align_letters(f"{n} {s}")
            if cand and cand not in out:
                out.append(cand)
    return out or [w.align]


def boundary_punct_score(w: Word) -> float:
    """Strength of the written break after word w (0..1)."""
    p = w.punct_after
    if w.newline_after or "?" in p or "!" in p:
        return 1.0
    if re.search(r"\.{2,}", p):
        return 0.8
    if "." in p:
        return 0.9
    if PHRASE_PUNCT.search(p):
        return 0.5
    return 0.0
