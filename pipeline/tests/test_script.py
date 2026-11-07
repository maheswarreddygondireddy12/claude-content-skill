from pathlib import Path

from aligner.script import number_to_words, tokenize

ROOT = Path(__file__).resolve().parents[2]


def by_raw(words, raw):
    return next(w for w in words if w.raw == raw)


def test_ellipsis_without_space_splits_words():
    words = tokenize("A sample idea.....Another example")
    assert [w.raw for w in words] == ["A", "sample", "idea", "Another", "example"]
    assert words[2].punct_after == "....."
    assert "ellipsis_after" in words[2].markers
    assert words[3].sentence == words[2].sentence + 1


def test_unicode_ellipsis_and_question_marks():
    words = tokenize("andariki telusu… kani context engineering gurinchi miku telusaaa...????")
    assert by_raw(words, "telusu").punct_after == "..."
    last = words[-1]
    assert last.raw == "telusaaa"
    assert "question" in last.markers and "elongated" in last.markers
    assert last.align == "telusa"


def test_numbers_become_spoken_words():
    words = tokenize("everyday evening 7pm ki oka video. registration ki 3days matrame")
    seven = by_raw(words, "7pm")
    assert seven.display == "7 PM" and seven.align == "seven pee em" and seven.lang == "num"
    three = by_raw(words, "3days")
    assert three.display == "3 days" and three.align == "three days"
    assert "uncertain_spoken" in three.flags


def test_symbol_word():
    words = tokenize("learning + practice environment")
    plus = words[1]
    assert plus.raw == "+" and plus.align == "plus" and "symbol" in plus.markers


def test_spellfix_and_caps():
    words = tokenize("Full stack delevelopment nerchukolani. model ki EXACTLY em information")
    dev = by_raw(words, "delevelopment")
    assert dev.display == "development" and dev.align == "development" and "spellfixed" in dev.flags
    exactly = by_raw(words, "EXACTLY")
    assert "caps" in exactly.markers and exactly.align == "exactly"


def test_acronyms_spoken_as_letters():
    words = tokenize("AI world lo miku dm chestha")
    assert by_raw(words, "AI").align == "ay eye"
    assert by_raw(words, "dm").align == "dee em"


def test_signposts_start_new_phrase():
    words = tokenize("Practice cheyyali kani ikkade chala mandi students")
    kani = by_raw(words, "kani")
    assert kani.signpost and kani.phrase == words[1].phrase + 1


def test_number_to_words():
    assert number_to_words(7) == "seven"
    assert number_to_words(42) == "forty two"
    assert number_to_words(300) == "three hundred"
    assert number_to_words(2026) == "two thousand twenty six"


def test_generic_script_has_no_empty_align():
    text = "A clear example helps explain the idea. Show each step as it happens."
    words = tokenize(text)
    assert all(w.align for w in words)
    assert all(set(w.align) <= set("abcdefghijklmnopqrstuvwxyz' ") for w in words)
    assert len(words) >= 10
    assert words[-1].sentence >= 1


def test_spoken_alternatives_for_numbers_and_symbols():
    from aligner.script import spoken_alternatives
    words = tokenize("evening 7pm ki. 3days matrame. 2 days. learning + practice")
    seven = spoken_alternatives(by_raw(words, "7pm"))
    assert seven[0] == "seven pee em" and "edu pee em" in seven and "seven" in seven
    three = spoken_alternatives(by_raw(words, "3days"))
    assert "three days" in three and "moodu rojulu" in three
    assert spoken_alternatives(by_raw(words, "2")) == ["two", "rendu"]
    assert spoken_alternatives(by_raw(words, "+")) == ["plus", "and"]
    assert spoken_alternatives(by_raw(words, "learning")) == ["learning"]

