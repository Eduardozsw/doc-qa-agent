from fastapi import APIRouter, Depends, HTTPException, Request

from api.deps import get_current_user, UserContext
from models.requests import QueryRequest
from models.responses import QueryResponse
from services import query as query_service
from db.usage import atomic_increment_and_check
from db.conversations import reset_conversation
from core.limits import get_limit
from core.limiter import limiter

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
@limiter.limit("5/minute")
async def query(
    request: Request,
    body: QueryRequest,
    user: UserContext = Depends(get_current_user),
):
    if atomic_increment_and_check(user.id, user.plan, "queries"):
        limit = get_limit(user.plan, "queries")
        raise HTTPException(status_code=429, detail=f"Limite de {limit} perguntas mensais atingido")

    result = await query_service.handle_query(user.id, user.plan, body)
    return QueryResponse(resposta=result["resposta"], fontes=result.get("fontes", []))


@router.delete("/history", status_code=204)
async def clear_history(user: UserContext = Depends(get_current_user)):
    reset_conversation(user.id)
