import logging

from db.postgres import get_conn

logger = logging.getLogger(__name__)


def upload_temp_file(job_id: str, contents: bytes) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO temp_uploads (job_id, content)
            VALUES (%s, %s)
            ON CONFLICT (job_id) DO UPDATE SET content = EXCLUDED.content
            """,
            (job_id, contents),
        )
        conn.commit()


def download_temp_file(job_id: str) -> bytes:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT content FROM temp_uploads WHERE job_id = %s", (job_id,)
        ).fetchone()
    if not row:
        raise FileNotFoundError(f"Upload temporário não encontrado: {job_id}")
    return bytes(row["content"])


def delete_temp_file(job_id: str) -> None:
    try:
        with get_conn() as conn:
            conn.execute("DELETE FROM temp_uploads WHERE job_id = %s", (job_id,))
            conn.commit()
    except Exception as e:
        logger.warning(f"Falha ao deletar temp file {job_id}: {e}")
