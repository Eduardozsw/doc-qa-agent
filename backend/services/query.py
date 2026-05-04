import logging
from models.requests import QueryRequest
from agent.orchestrator import orchestrator
from agent.summarizer import summarize
from core.exceptions import ForbiddenError
from core.limits import get_limit
from db import supabase as supabase_db
from db.conversations import (
    get_or_create_conversation,
    get_history,
    save_message,
    count_pairs,
    pop_oldest_pair,
    update_summary,
)

logger = logging.getLogger(__name__)

_WINDOW = 5


async def handle_query(user_id: str, plan: str, body: QueryRequest) -> dict:
    if body.namespaces:
        user_namespaces = set(supabase_db.get_namespaces(user_id))
        unauthorized = [n for n in body.namespaces if n not in user_namespaces]
        if unauthorized:
            logger.warning(
                f"403 query user={user_id} requested={body.namespaces} owned={list(user_namespaces)} unauthorized={unauthorized}"
            )
            raise ForbiddenError("Namespaces não pertencem ao usuário")

    namespaces = body.namespaces if body.namespaces else None
    has_history = get_limit(plan, "history")

    if not has_history:
        return orchestrator(body.query, namespaces=namespaces, historico=[], plan=plan)

    conversation_id = get_or_create_conversation(user_id)
    summary, historico = get_history(conversation_id, user_id)

    result = orchestrator(body.query, namespaces=namespaces, historico=historico, plan=plan, summary=summary)

    save_message(conversation_id, "user", body.query)
    save_message(conversation_id, "assistant", result["resposta"])

    if count_pairs(conversation_id) > _WINDOW:
        pair = pop_oldest_pair(conversation_id)
        if pair:
            try:
                new_summary = summarize(summary, pair[0], pair[1])
                update_summary(conversation_id, new_summary)
            except Exception as e:
                logger.warning(f"Sumarização falhou para conversa {conversation_id}: {e}")

    return result
