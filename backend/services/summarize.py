import logging
from agent.pdf_summarizer import generate_summary
from core.exceptions import ForbiddenError
from core.limits import get_limit
from db import supabase as supabase_db

logger = logging.getLogger(__name__)


async def summarize_document(user_id: str, plan: str, namespace: str) -> dict:
    user_namespaces = set(supabase_db.get_namespaces(user_id))
    if namespace not in user_namespaces:
        logger.warning(f"403 summarize user={user_id} namespace={namespace} not owned")
        raise ForbiddenError("Namespace não pertence ao usuário")

    cached = supabase_db.get_summary(user_id, namespace)
    if cached:
        return {**cached, "cached": True}

    used = supabase_db.count_summaries_this_month(user_id)
    limit = get_limit(plan, "summaries")
    if used >= limit:
        raise ForbiddenError(f"Limite de {limit} resumos por mês atingido")

    summary = generate_summary(namespace)
    supabase_db.save_summary(user_id, namespace, summary)

    return {**summary, "cached": False}


async def list_summaries(user_id: str, plan: str) -> dict:
    summaries = supabase_db.get_namespaces_with_summaries(user_id)
    used = supabase_db.count_summaries_this_month(user_id)
    limit = get_limit(plan, "summaries")
    return {
        "summaries": summaries,
        "used_this_month": used,
        "limit": limit,
    }
