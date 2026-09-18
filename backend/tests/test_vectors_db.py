import pytest

from db.vectors import count, delete_namespace, query, query_keyword, upsert_vectors


def _vec(seed: float) -> list[float]:
    return [seed] * 1536


@pytest.mark.db
def test_upsert_and_query_returns_score_in_range_and_best_first(db):
    rows = [
        ("ns1_chunk_0", 0, 1, "texto idêntico à query", _vec(0.1)),
        ("ns1_chunk_1", 1, 2, "texto bem diferente", _vec(0.9)),
        ("ns2_chunk_0", 0, 1, "texto de outro namespace", _vec(0.1)),
    ]
    upsert_vectors("ns1", rows[:2])
    upsert_vectors("ns2", rows[2:])

    results = query("ns1", _vec(0.1), top_k=10)

    assert len(results) == 2
    for score, _text, _page in results:
        assert 0.0 <= score <= 1.0 + 1e-6

    best_score, best_text, best_page = results[0]
    assert best_text == "texto idêntico à query"
    assert best_page == 1
    assert best_score == pytest.approx(1.0, abs=1e-6)


@pytest.mark.db
def test_query_respects_top_k(db):
    rows = [(f"ns1_chunk_{i}", i, i, f"texto {i}", _vec(i / 10)) for i in range(5)]
    upsert_vectors("ns1", rows)

    results = query("ns1", _vec(0.0), top_k=2)

    assert len(results) == 2


@pytest.mark.db
def test_query_unknown_namespace_returns_empty(db):
    assert query("namespace-que-nao-existe", _vec(0.1), top_k=5) == []


@pytest.mark.db
def test_delete_namespace_is_idempotent_and_count_zero(db):
    rows = [("ns1_chunk_0", 0, 1, "texto", _vec(0.1))]
    upsert_vectors("ns1", rows)
    assert count("ns1") == 1

    delete_namespace("ns1")
    assert count("ns1") == 0

    # idempotente: chamar de novo não deve levantar erro
    delete_namespace("ns1")
    assert count("ns1") == 0


@pytest.mark.db
def test_query_keyword_finds_relevant_chunk(db):
    rows = [
        ("ns1_chunk_0", 0, 1, "o paciente recebeu nitroprussiato de sódio na emergência", _vec(0.1)),
        ("ns1_chunk_1", 1, 1, "a dieta recomendada reduz o consumo de sódio", _vec(0.2)),
        ("ns1_chunk_2", 2, 2, "texto totalmente não relacionado sobre outro assunto", _vec(0.3)),
    ]
    upsert_vectors("ns1", rows)

    results = query_keyword("ns1", "nitroprussiato", top_k=10)

    assert len(results) == 1
    _score, text, page = results[0]
    assert "nitroprussiato" in text
    assert page == 1


@pytest.mark.db
def test_query_keyword_stopwords_only_returns_empty(db):
    rows = [("ns1_chunk_0", 0, 1, "texto de exemplo qualquer", _vec(0.1))]
    upsert_vectors("ns1", rows)

    assert query_keyword("ns1", "de o a", top_k=10) == []


@pytest.mark.db
def test_query_keyword_natural_language_question_matches_partial_chunk(db):
    rows = [
        ("ns1_chunk_0", 0, 1, "o sódio em excesso agrava o quadro de hipertensos", _vec(0.1)),
        ("ns1_chunk_1", 1, 2, "texto totalmente não relacionado sobre outro assunto", _vec(0.2)),
    ]
    upsert_vectors("ns1", rows)

    # pergunta em linguagem natural: só "sódio" e "hipertensos" casam com o chunk acima,
    # mas com OR (em vez de AND) isso já basta para encontrá-lo.
    results = query_keyword("ns1", "Qual o limite de sódio na dieta para hipertensos?", top_k=10)

    assert len(results) == 1
    _score, text, page = results[0]
    assert "sódio" in text
    assert page == 1


@pytest.mark.db
def test_query_keyword_ranks_more_matched_terms_first(db):
    rows = [
        ("ns1_chunk_0", 0, 1, "o sódio é um mineral", _vec(0.1)),
        ("ns1_chunk_1", 1, 2, "o sódio na dieta de hipertensos deve ser controlado", _vec(0.2)),
    ]
    upsert_vectors("ns1", rows)

    results = query_keyword("ns1", "sódio dieta hipertensos", top_k=10)

    assert len(results) == 2
    assert results[0][1] == "o sódio na dieta de hipertensos deve ser controlado"
