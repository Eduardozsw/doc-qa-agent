import logging

from db.postgres import get_conn

logger = logging.getLogger(__name__)


def save_document(namespace: str, user_id: str, filename: str, content: bytes) -> None:
    """Grava (ou substitui) o PDF original de um namespace, usado pelo visualizador
    do frontend. Upsert por namespace."""
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO documents (namespace, user_id, filename, content)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (namespace) DO UPDATE
            SET user_id = EXCLUDED.user_id, filename = EXCLUDED.filename, content = EXCLUDED.content
            """,
            (namespace, user_id, filename, content),
        )
        conn.commit()


def get_document(namespace: str, user_id: str) -> tuple[str, bytes] | None:
    """Devolve `(filename, content)` do documento se ele existir e pertencer a
    `user_id`; `None` caso contrário (namespace inexistente ou de outro usuário)."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT filename, content FROM documents WHERE namespace = %s AND user_id = %s",
            (namespace, user_id),
        ).fetchone()
    if not row:
        return None
    return row["filename"], bytes(row["content"])


def delete_document(namespace: str) -> None:
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM documents WHERE namespace = %s", (namespace,))
            conn.commit()
    except Exception as e:
        logger.warning(f"Falha ao deletar documento do namespace {namespace}: {e}")
