"""Unit tests for word_count helpers."""

from joblab_api.word_count import count_words, is_within_limit


def test_empty_text_is_zero_words() -> None:
    assert count_words("") == 0
    assert count_words("   ") == 0


def test_basic_word_counting() -> None:
    assert count_words("hello world") == 2
    assert count_words("one two three four five") == 5


def test_whitespace_collapses() -> None:
    assert count_words("one\ttwo\n  three\r\nfour") == 4


def test_punctuation_does_not_split_words() -> None:
    assert count_words("don't, it's fine.") == 3


def test_is_within_limit() -> None:
    assert is_within_limit("one two three", 3) is True
    assert is_within_limit("one two three", 2) is False
    assert is_within_limit("", 0) is True
