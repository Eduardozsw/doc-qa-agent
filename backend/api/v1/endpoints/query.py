from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from api.deps import UserContext, get_current_user
from core import tracing
from core.limiter import limiter
from core.limits import get_limit
from db import feedback as feedback_db
from db.conversations import reset_conversation
from db.usage import atomic_increment_and_check
from models.requests import FeedbackRequest, QueryRequest
from models.responses import QueryResponse
from services import query as query_service

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
    return QueryResponse(
        resposta=result["resposta"],
        fontes=result.get("fontes", []),
        citacoes=result.get("citacoes", []),
        correcao=result.get("correcao", False),
        conflitos=result.get("conflitos", []),
        trace_id=result.get("trace_id"),
        cached=result.get("cached", False),
        modelo=result.get("modelo"),
    )


@router.post("/stream")
@limiter.limit("5/minute")
async def query_stream(
    request: Request,
    body: QueryRequest,
    user: UserContext = Depends(get_current_user),
):
    if atomic_increment_and_check(user.id, user.plan, "queries"):
        limit = get_limit(user.plan, "queries")
        raise HTTPException(status_code=429, detail=f"Limite de {limit} perguntas mensais atingido")

    return StreamingResponse(
        query_service.handle_query_stream(user.id, user.plan, body),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.delete("/history", status_code=204)
async def clear_history(user: UserContext = Depends(get_current_user)):
    reset_conversation(user.id)


@router.post("/feedback")
@limiter.limit("5/minute")
async def feedback(
    request: Request,
    body: FeedbackRequest,
    user: UserContext = Depends(get_current_user),
):
    feedback_db.save_feedback(
        user.id, body.trace_id, body.score, body.comentario, body.pergunta, body.resposta
    )
    if body.trace_id:
        tracing.score(body.trace_id, "user_feedback", body.score, body.comentario or None)
    return {"ok": True}
