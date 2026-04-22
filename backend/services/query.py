from models.requests import QueryRequest
from agent.orchestrator import orchestrator
from core.exceptions import ForbiddenError
from db import redis as redis_db


async def handle_query(user_id: str, body: QueryRequest) -> dict:
    if body.namespaces:
        user_namespaces = set(redis_db.get_namespaces(user_id))
        unauthorized = [n for n in body.namespaces if n not in user_namespaces]
        if unauthorized:
            raise ForbiddenError("Namespaces não pertencem ao usuário")

    namespaces = body.namespaces if body.namespaces else None
    historico = [h.model_dump() for h in body.historico]
    return orchestrator(body.query, namespaces=namespaces, historico=historico)
