from agent.context import _SEM_INFO, display_name, extract_citation_ids, format_context, is_sem_info


def test_display_name_strips_prefix():
    assert display_name("u1234567_ab3d9f21_protocolo.pdf") == "protocolo.pdf"


def test_display_name_keeps_underscores_in_filename():
    assert display_name("u1234567_ab3d9f21_manual_de_boas_praticas.pdf") == "manual_de_boas_praticas.pdf"


def test_display_name_without_prefix_returns_unchanged():
    assert display_name("protocolo.pdf") == "protocolo.pdf"


def test_format_context_includes_id_documento_pagina():
    chunks = [(0.9, "u1_ab_protocolo.pdf", "texto do trecho", 12)]
    resultado = format_context(chunks)
    assert '<trecho id="1" documento="protocolo.pdf" pagina="12">' in resultado
    assert "texto do trecho" in resultado
    assert "</trecho>" in resultado


def test_format_context_omits_pagina_when_zero_or_none():
    chunks = [
        (0.9, "u1_ab_a.pdf", "texto a", 0),
        (0.8, "u1_ab_b.pdf", "texto b", None),
    ]
    resultado = format_context(chunks)
    assert 'pagina=' not in resultado


def test_format_context_ids_start_at_one_in_order():
    chunks = [
        (0.9, "u1_ab_a.pdf", "primeiro", 1),
        (0.8, "u1_ab_b.pdf", "segundo", 2),
    ]
    resultado = format_context(chunks)
    assert 'id="1"' in resultado
    assert 'id="2"' in resultado
    assert resultado.index('id="1"') < resultado.index('id="2"')


def test_extract_citation_ids_unique_in_order():
    assert extract_citation_ids("afirma [2] e também [1][2] e [3]") == [2, 1, 3]


def test_extract_citation_ids_no_citations_returns_empty():
    assert extract_citation_ids("resposta sem citações") == []


def test_extract_citation_ids_ignores_out_of_range():
    assert extract_citation_ids("cita [1] e [9]", max_id=3) == [1]


def test_extract_citation_ids_ignores_zero():
    assert extract_citation_ids("cita [0] e [1]") == [1]


def test_is_sem_info_true_for_exact_match():
    assert is_sem_info(_SEM_INFO) is True


def test_is_sem_info_tolerates_trailing_period():
    assert is_sem_info(_SEM_INFO + ".") is True


def test_is_sem_info_tolerates_surrounding_quotes():
    assert is_sem_info(f'"{_SEM_INFO}"') is True


def test_is_sem_info_false_for_different_text():
    assert is_sem_info("resposta qualquer com base nos trechos [1]") is False
