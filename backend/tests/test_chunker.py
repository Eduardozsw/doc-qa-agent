import pytest
from ingestion.chunker import CHUNKER_VERSION, _contar_tokens, chunk_text


def test_version_is_v2():
    assert CHUNKER_VERSION == "v2"


def test_empty_string_returns_empty_list():
    assert chunk_text("") == []


def test_whitespace_only_returns_empty_list():
    assert chunk_text("   \n\t  ") == []


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


def test_text_smaller_than_chunk_size_is_a_single_chunk():
    texto = "Esta é uma frase única e curta."
    result = chunk_text(texto, chunk_size=350, overlap=60)
    assert result == [texto]


def test_chunks_respect_token_budget():
    frases = [f"Esta é a frase número {i} do texto de teste." for i in range(60)]
    texto = " ".join(frases)

    result = chunk_text(texto, chunk_size=30, overlap=5)

    assert len(result) > 1
    for chunk in result:
        assert _contar_tokens(chunk) <= 30 + _contar_tokens(frases[0])


def test_sentence_is_not_split_mid_sentence():
    frases = [f"Frase numero {i} termina aqui." for i in range(40)]
    texto = " ".join(frases)

    result = chunk_text(texto, chunk_size=20, overlap=0)

    for chunk in result:
        assert chunk.strip().endswith(".")
        for frase in frases:
            # nenhuma frase aparece pela metade (sem o ponto final) em outro chunk
            assert frase[:-1] not in chunk or frase in chunk


def test_overlap_repeats_last_sentences():
    frases = [f"Frase numero {i} sobre hipertensao." for i in range(40)]
    texto = " ".join(frases)

    result = chunk_text(texto, chunk_size=20, overlap=10)

    assert len(result) > 1
    ultima_frase_chunk0 = result[0].split(".")[-2].strip() + "."
    assert ultima_frase_chunk0 in result[1]


def test_overlap_zero_has_no_repeated_sentences():
    frases = [f"Frase numero {i} sobre hipertensao." for i in range(40)]
    texto = " ".join(frases)

    result = chunk_text(texto, chunk_size=20, overlap=0)

    ultima_frase_chunk0 = result[0].split(".")[-2].strip() + "."
    assert ultima_frase_chunk0 not in result[1]


def test_single_sentence_larger_than_chunk_size_is_sliced_by_tokens():
    texto = " ".join(["palavra"] * 500)  # uma "sentença" sem pontuação
    result = chunk_text(texto, chunk_size=50, overlap=0)

    assert len(result) > 1
    for chunk in result:
        assert _contar_tokens(chunk) <= 50


def test_default_params_produce_output():
    texto = " ".join([f"Esta é a frase número {i} do documento." for i in range(200)])
    result = chunk_text(texto)
    assert len(result) > 1
    assert all(isinstance(c, str) for c in result)
