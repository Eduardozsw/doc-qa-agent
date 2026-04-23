import pytest
from ingestion.chunker import chunk_text


def test_basic_chunking():
    words = ["word"] * 10
    result = chunk_text(" ".join(words), chunk_size=5, overlap=0)
    assert len(result) == 2
    assert result[0] == "word word word word word"


def test_overlap_repeats_words():
    words = [f"w{i}" for i in range(10)]
    result = chunk_text(" ".join(words), chunk_size=5, overlap=2)
    last_words_first = result[0].split()[-2:]
    first_words_second = result[1].split()[:2]
    assert last_words_first == first_words_second


def test_text_smaller_than_chunk_size():
    result = chunk_text("apenas tres palavras", chunk_size=500, overlap=50)
    assert len(result) == 1
    assert result[0] == "apenas tres palavras"


def test_empty_string_returns_empty_list():
    assert chunk_text("") == []


def test_whitespace_only_returns_empty_list():
    assert chunk_text("   \n\t  ") == []


def test_single_word():
    result = chunk_text("palavra", chunk_size=5, overlap=0)
    assert result == ["palavra"]


def test_chunk_size_zero_raises():
    with pytest.raises(ValueError):
        chunk_text("texto qualquer", chunk_size=0)


def test_negative_chunk_size_raises():
    with pytest.raises(ValueError):
        chunk_text("texto qualquer", chunk_size=-1)


def test_overlap_equal_chunk_size_raises():
    with pytest.raises(ValueError):
        chunk_text("texto", chunk_size=5, overlap=5)


def test_overlap_greater_than_chunk_size_raises():
    with pytest.raises(ValueError):
        chunk_text("texto", chunk_size=5, overlap=10)


def test_overlap_zero_is_valid():
    result = chunk_text("a b c d e", chunk_size=3, overlap=0)
    assert len(result) == 2


def test_no_empty_chunks():
    result = chunk_text("palavra " * 100, chunk_size=10, overlap=3)
    assert all(chunk.strip() for chunk in result)


def test_default_params_produce_output():
    text = " ".join([f"word{i}" for i in range(1000)])
    result = chunk_text(text)
    assert len(result) > 1
    assert all(isinstance(c, str) for c in result)
