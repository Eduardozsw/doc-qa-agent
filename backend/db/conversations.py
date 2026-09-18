import logging

from db.postgres import get_conn

logger = logging.getLogger(__name__)

_WINDOW = 5


def get_or_create_conversation(user_id: str) -> str:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id FROM conversations
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        if row:
            return str(row["id"])

        created = conn.execute(
            "INSERT INTO conversations (user_id, summary) VALUES (%s, '') RETURNING id",
            (user_id,),
        ).fetchone()
        conn.commit()
    return str(created["id"])


def get_history(conversation_id: str, user_id: str) -> tuple[str, list[dict]]:
    with get_conn() as conn:
        conv = conn.execute(
            "SELECT summary FROM conversations WHERE id = %s AND user_id = %s",
            (conversation_id, user_id),
        ).fetchone()
        summary = conv["summary"] if conv else ""

        msgs = conn.execute(
            """
            SELECT role, content FROM messages
            WHERE conversation_id = %s
            ORDER BY id ASC
            """,
            (conversation_id,),
        ).fetchall()

    messages = msgs or []
    pairs = _to_pairs(messages)
    recent = pairs[-_WINDOW:]

    historico = [{"pergunta": p, "resposta": r} for p, r in recent]
    return summary, historico


def save_message(conversation_id: str, role: str, content: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (%s, %s, %s)
            """,
            (conversation_id, role, content),
        )
        conn.commit()


def count_pairs(conversation_id: str) -> int:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT count(*) AS n FROM messages
            WHERE conversation_id = %s AND role = 'user'
            """,
            (conversation_id,),
        ).fetchone()
    return row["n"] if row else 0


def pop_oldest_pair(conversation_id: str) -> tuple[str, str] | None:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, role, content FROM messages
            WHERE conversation_id = %s
            ORDER BY id ASC
            LIMIT 2
            """,
            (conversation_id,),
        ).fetchall()

        rows = rows or []
        if len(rows) < 2:
            return None

        pergunta = next((r["content"] for r in rows if r["role"] == "user"), None)
        resposta = next((r["content"] for r in rows if r["role"] == "assistant"), None)
        if not pergunta or not resposta:
            return None

        ids = [r["id"] for r in rows]
        conn.execute("DELETE FROM messages WHERE id = ANY(%s)", (ids,))
        conn.commit()
    return pergunta, resposta


def update_summary(conversation_id: str, summary: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE conversations SET summary = %s WHERE id = %s",
            (summary, conversation_id),
        )
        conn.commit()


def reset_conversation(user_id: str) -> str:
    with get_conn() as conn:
        created = conn.execute(
            "INSERT INTO conversations (user_id, summary) VALUES (%s, '') RETURNING id",
            (user_id,),
        ).fetchone()
        conn.commit()
    return str(created["id"])


def _to_pairs(messages: list[dict]) -> list[tuple[str, str]]:
    pairs = []
    i = 0
    while i < len(messages) - 1:
        if messages[i]["role"] == "user" and messages[i + 1]["role"] == "assistant":
            pairs.append((messages[i]["content"], messages[i + 1]["content"]))
            i += 2
        else:
            i += 1
    return pairs
