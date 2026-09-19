import pytest
from ingestion.chunker import CHUNKER_VERSION, _contar_tokens, chunk_text


def test_version_is_v3():
    assert CHUNKER_VERSION == "v3"


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


def test_titulo_nao_fica_orfao_quando_seguido_de_tabela():
    intro = "Este e um paragrafo introdutorio que antecede a tabela de referencia."
    titulo = "## Tabela de referência"
    tabela = "|Classificação|Valor|\n|---|---|\n|Alto|180|"
    texto = f"{intro}\n{titulo}\n{tabela}"

    tokens_sem_tabela = _contar_tokens(intro) + _contar_tokens(titulo)
    result = chunk_text(texto, chunk_size=tokens_sem_tabela + 2, overlap=0)

    assert len(result) == 2
    assert not result[0].strip().endswith(titulo)
    assert result[1].startswith(titulo)
    assert "Classificação" in result[1]


def test_titulo_no_ultimo_chunk_nao_precisa_migrar():
    texto = "Frase final antes do título.\n## Último título da página"
    result = chunk_text(texto, chunk_size=350, overlap=0)

    assert len(result) == 1
    assert result[0].endswith("## Último título da página")


def test_tabela_pequena_nao_e_quebrada():
    tabela = (
        "|Classificação|Pressão sistólica (mmHg)|Pressão diastólica (mmHg)|\n"
        "|---|---|---|\n"
        "|Hipertensão estágio 2|160 – 179|100 – 109|"
    )
    result = chunk_text(tabela, chunk_size=350, overlap=60)

    assert len(result) == 1
    assert result[0] == tabela


def test_tabela_grande_e_fatiada_com_cabecalho_repetido():
    cabecalho = "|Classificação|Valor|\n|---|---|"
    linhas = [f"|Categoria {i}|{i * 10}|" for i in range(40)]
    tabela = cabecalho + "\n" + "\n".join(linhas)

    result = chunk_text(tabela, chunk_size=30, overlap=0)

    assert len(result) > 1
    for chunk in result:
        assert chunk.startswith("|Classificação|Valor|")
        assert "|---|" in chunk


def test_tabela_nao_e_dividida_por_sentenca_mesmo_com_muitos_numeros():
    tabela = (
        "|Faixa|Sistólica|Diastólica|\n"
        "|---|---|---|\n"
        "|Estágio 1|140 – 159|90 – 99|\n"
        "|Estágio 2|160 – 179|100 – 109|"
    )
    texto = f"Introdução ao tema.\n{tabela}\nTexto depois da tabela."

    result = chunk_text(texto, chunk_size=350, overlap=0)

    assert any(tabela in chunk for chunk in result)
