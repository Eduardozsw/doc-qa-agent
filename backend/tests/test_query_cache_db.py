from datetime import datetime, timedelta, timezone

from pgvector import Vector
from psycopg.types.json import Jsonb

from db.postgres import get_conn
from db.query_cache import invalidate_namespace, lookup, store

_DIM = 1536


def _vetor(base: float) -> list[float]:
    """Vetor quase idêntico entre chamadas com o mesmo `base` (cosseno ~1), e bem
    diferente entre `base`s distintos (cosseno baixo)."""
    return [base] * _DIM


def test_lookup_hit_above_min_score(db):
    embedding = _vetor(1.0)
    store("ns_a", ["ns_a"], embedding, "pergunta", {"resposta": "ok"}, ttl_hours=24)

    resultado = lookup("ns_a", embedding, min_score=0.97)

    assert resultado == {"resposta": "ok"}


def test_lookup_miss_below_min_score(db):
    store("ns_a", ["ns_a"], _vetor(1.0), "pergunta", {"resposta": "ok"}, ttl_hours=24)

    # Vetor ortogonal-ish: cosseno baixo com o armazenado.
    outro = [1.0] * (_DIM // 2) + [-1.0] * (_DIM // 2)
    resultado = lookup("ns_a", outro, min_score=0.97)

    assert resultado is None


def test_lookup_ignores_expired_entries(db):
    embedding = _vetor(1.0)
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO query_cache (namespaces_key, namespaces, embedding, query, payload, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                "ns_a", ["ns_a"], Vector(embedding), "pergunta",
                Jsonb({"resposta": "velho"}),
                datetime.now(timezone.utc) - timedelta(hours=1),
            ),
        )
        conn.commit()

    resultado = lookup("ns_a", embedding, min_score=0.97)

    assert resultado is None


def test_invalidate_namespace_removes_matching_entries(db):
    embedding = _vetor(1.0)
    store("ns_a,ns_b", ["ns_a", "ns_b"], embedding, "pergunta", {"resposta": "x"}, ttl_hours=24)
    store("ns_c", ["ns_c"], embedding, "outra pergunta", {"resposta": "y"}, ttl_hours=24)

    invalidate_namespace("ns_a")

    with get_conn() as conn:
        rows = conn.execute("SELECT namespaces_key FROM query_cache").fetchall()

    chaves = {r["namespaces_key"] for r in rows}
    assert chaves == {"ns_c"}
