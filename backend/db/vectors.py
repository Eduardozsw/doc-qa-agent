import logging

from pgvector import Vector

from db.postgres import get_conn

logger = logging.getLogger(__name__)

UPSERT_BATCH_SIZE = 100


def upsert_vectors(namespace: str, rows: list[tuple[str, int, int, str, list[float]]]) -> None:
    """rows: (id, chunk_index, page, text, embedding)."""
    if not rows:
        return

    with get_conn() as conn:
        for i in range(0, len(rows), UPSERT_BATCH_SIZE):
            batch = rows[i:i + UPSERT_BATCH_SIZE]
            params = [
                (id_, namespace, chunk_index, page, text, Vector(embedding))
                for id_, chunk_index, page, text, embedding in batch
            ]
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO chunks (id, namespace, chunk_index, page, text, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                      namespace = EXCLUDED.namespace,
                      chunk_index = EXCLUDED.chunk_index,
                      page = EXCLUDED.page,
                      text = EXCLUDED.text,
                      embedding = EXCLUDED.embedding
                    """,
                    params,
                )
            conn.commit()


def query(namespace: str, embedding: list[float], top_k: int = 10) -> list[tuple[float, str, int]]:
    vec = Vector(embedding)
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT text, page, 1 - (embedding <=> %s) AS score
            FROM chunks
            WHERE namespace = %s
            ORDER BY embedding <=> %s
            LIMIT %s
            """,
            (vec, namespace, vec, top_k),
        ).fetchall()
    return [(row["score"], row["text"], row["page"]) for row in rows]


def delete_namespace(namespace: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM chunks WHERE namespace = %s", (namespace,))
        conn.commit()


def count(namespace: str) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT count(*) AS n FROM chunks WHERE namespace = %s", (namespace,)
        ).fetchone()
    return row["n"] if row else 0
