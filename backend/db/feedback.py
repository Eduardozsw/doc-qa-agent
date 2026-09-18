import logging

from db.postgres import get_conn

logger = logging.getLogger(__name__)


def save_feedback(
    user_id: str,
    trace_id: str | None,
    score: int,
    comentario: str = "",
    pergunta: str = "",
    resposta: str = "",
) -> None:
    """Grava um feedback (👍/👎) do usuário. `trace_id` fica NULL quando o tracing
    está desligado ou a resposta veio de fora do fluxo normal (ex.: cache)."""
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO feedback (user_id, trace_id, score, comentario, pergunta, resposta)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, trace_id, score, comentario, pergunta, resposta),
        )
        conn.commit()
