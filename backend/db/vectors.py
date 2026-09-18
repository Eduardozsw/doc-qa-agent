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


def query_keyword(namespace: str, query_text: str, top_k: int = 10) -> list[tuple[float, str, int]]:
    with get_conn() as conn:
        lexemes = conn.execute(
            "SELECT tsvector_to_array(to_tsvector('portuguese', %s)) AS lexemes", (query_text,)
        ).fetchone()["lexemes"]
        if not lexemes:
            return []

        # OR (não AND): perguntas em linguagem natural raramente casam todos os termos;
        # com OR o ranking (ts_rank_cd) ainda favorece quem casa mais lexemas. Usamos a
        # config 'simple' no to_tsquery externo porque os lexemas já vieram stemizados
        # pelo 'portuguese' acima — re-stemizá-los (com 'portuguese' de novo) distorce
        # palavras já reduzidas (ex.: 'sódi' vira 'sód') e quebra o match.
        rows = conn.execute(
            """
            SELECT text, page, ts_rank_cd(tsv, q) AS score
            FROM chunks, to_tsquery('simple', array_to_string(%s::text[], ' | ')) AS q
            WHERE namespace = %s AND tsv @@ q
            ORDER BY score DESC
            LIMIT %s
            """,
            (lexemes, namespace, top_k),
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
