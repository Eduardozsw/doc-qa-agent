from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from api.deps import UserContext, get_current_user
from core.limiter import limiter
from services import summarize as summarize_service

router = APIRouter(prefix="/summarize", tags=["summarize"])


class SummarizeRequest(BaseModel):
    namespace: str


class SummaryData(BaseModel):
    topicos_abordados: list[str]
    resumo: str
    cached: bool


class SummaryListItem(BaseModel):
    namespace: str
    filename: str | None = None
    summary: dict | None = None


class SummarizeListResponse(BaseModel):
    summaries: list[SummaryListItem]
    used_this_month: int
    limit: int


@router.post("", response_model=SummaryData)
@limiter.limit("5/minute")
async def summarize_document(
    request: Request,
    body: SummarizeRequest,
    user: UserContext = Depends(get_current_user),
):
    return await summarize_service.summarize_document(user.id, user.plan, body.namespace)


@router.get("", response_model=SummarizeListResponse)
async def list_summaries(
    user: UserContext = Depends(get_current_user),
):
    return await summarize_service.list_summaries(user.id, user.plan)
