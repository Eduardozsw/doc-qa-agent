from models.requests import QueryRequest
from agent.orchestrator import orchestrator


async def handle_query(user_id: str, body: QueryRequest) -> dict:
    namespaces = body.namespaces if body.namespaces else None
    historico = [h.model_dump() for h in body.historico]
    return orchestrator(body.query, namespaces=namespaces, historico=historico)
