import logging
from datetime import UTC, datetime, timedelta

from pgvector import Vector
from psycopg.types.json import Jsonb

from db.postgres import get_conn

logger = logging.getLogger(__name__)


def lookup(namespaces_key: str, embedding: list[float], min_score: float = 0.97) -> dict | None:
    """Melhor hit (maior similaridade de cosseno) para `namespaces_key`, entre as
    entradas ainda não expiradas. Retorna None se não houver nenhum hit >= min_score."""
    vec = Vector(embedding)
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT payload, 1 - (embedding <=> %s) AS score
            FROM query_cache
            WHERE namespaces_key = %s AND expires_at > now()
            ORDER BY embedding <=> %s
            LIMIT 1
            """,
            (vec, namespaces_key, vec),
        ).fetchone()

    if not row or row["score"] < min_score:
        return None
    return row["payload"]


def store(
    namespaces_key: str,
    namespaces: list[str],
    embedding: list[float],
    query: str,
    payload: dict,
    ttl_hours: int = 24,
) -> None:
    expires_at = datetime.now(UTC) + timedelta(hours=ttl_hours)
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO query_cache (namespaces_key, namespaces, embedding, query, payload, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (namespaces_key, namespaces, Vector(embedding), query, Jsonb(payload), expires_at),
        )
        conn.commit()


def invalidate_namespace(namespace: str) -> None:
    """Apaga todas as entradas de cache que incluem `namespace` (chamado quando o
    documento é removido/reingerido, para não servir respostas com fontes obsoletas)."""
    with get_conn() as conn:
        conn.execute("DELETE FROM query_cache WHERE %s = ANY(namespaces)", (namespace,))
        conn.commit()


def purge_expired() -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM query_cache WHERE expires_at <= now()")
        conn.commit()
