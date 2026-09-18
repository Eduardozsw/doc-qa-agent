import logging
from datetime import datetime, timezone

from psycopg.types.json import Jsonb

from db.postgres import get_conn

logger = logging.getLogger(__name__)


def count_namespaces(user_id: str) -> int:
    try:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT count(*) AS n FROM namespaces WHERE user_id = %s", (user_id,)
            ).fetchone()
        return row["n"] if row else 0
    except Exception as e:
        logger.error(f"Falha ao contar namespaces para {user_id}: {e}")
        return 0


def get_namespaces(user_id: str) -> list[str]:
    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT namespace FROM namespaces WHERE user_id = %s", (user_id,)
            ).fetchall()
        return [r["namespace"] for r in rows]
    except Exception as e:
        logger.error(f"Falha ao buscar namespaces para {user_id}: {e}")
        return []


def get_namespace_by_sha256(user_id: str, sha256: str) -> str | None:
    try:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT namespace FROM namespaces WHERE user_id = %s AND sha256 = %s",
                (user_id, sha256),
            ).fetchone()
        return row["namespace"] if row else None
    except Exception:
        return None


def add_namespace(user_id: str, namespace: str, sha256: str, filename: str) -> None:
    try:
        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO namespaces (user_id, namespace, sha256, filename)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, namespace) DO UPDATE
                SET sha256 = EXCLUDED.sha256, filename = EXCLUDED.filename
                """,
                (user_id, namespace, sha256, filename),
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Falha ao salvar namespace para {user_id}: {e}")
        raise


def get_sha256_for_namespace(user_id: str, namespace: str) -> str | None:
    try:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT sha256 FROM namespaces WHERE user_id = %s AND namespace = %s",
                (user_id, namespace),
            ).fetchone()
        return row["sha256"] if row else None
    except Exception:
        return None


def remove_namespace(user_id: str, namespace: str) -> None:
    try:
        with get_conn() as conn:
            conn.execute(
                "DELETE FROM namespaces WHERE user_id = %s AND namespace = %s",
                (user_id, namespace),
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Falha ao remover namespace para {user_id}: {e}")
        raise


def get_summary(user_id: str, namespace: str) -> dict | None:
    try:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT summary FROM namespaces WHERE user_id = %s AND namespace = %s",
                (user_id, namespace),
            ).fetchone()
        return row["summary"] if row else None
    except Exception:
        return None


def save_summary(user_id: str, namespace: str, summary: dict) -> None:
    try:
        with get_conn() as conn:
            conn.execute(
                """
                UPDATE namespaces
                SET summary = %s, summarized_at = %s
                WHERE user_id = %s AND namespace = %s
                """,
                (Jsonb(summary), datetime.now(timezone.utc), user_id, namespace),
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Falha ao salvar summary para {user_id}/{namespace}: {e}")
        raise


def count_summaries_this_month(user_id: str) -> int:
    try:
        now = datetime.now(timezone.utc)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        with get_conn() as conn:
            row = conn.execute(
                """
                SELECT count(*) AS n FROM namespaces
                WHERE user_id = %s AND summarized_at >= %s
                """,
                (user_id, start_of_month),
            ).fetchone()
        return row["n"] if row else 0
    except Exception as e:
        logger.warning(f"Falha ao contar summaries para {user_id}: {e}")
        return 0


def get_namespaces_with_summaries(user_id: str) -> list[dict]:
    try:
        with get_conn() as conn:
            rows = conn.execute(
                """
                SELECT namespace, filename, summary FROM namespaces
                WHERE user_id = %s AND summary IS NOT NULL
                """,
                (user_id,),
            ).fetchall()
        return rows
    except Exception as e:
        logger.error(f"Falha ao buscar summaries para {user_id}: {e}")
        return []
