import pytest

from db.vectors import count, delete_namespace, query, upsert_vectors


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
