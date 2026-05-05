from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.deps import UserContext, get_current_user
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
    filename: str
    summary: dict | None


class SummarizeListResponse(BaseModel):
    summaries: list[SummaryListItem]
    used_this_month: int
    limit: int


@router.post("", response_model=SummaryData)
async def summarize_document(
    body: SummarizeRequest,
    user: UserContext = Depends(get_current_user),
):
    result = await summarize_service.summarize_document(user.id, user.plan, body.namespace)
    return SummaryData(**result)


@router.get("", response_model=SummarizeListResponse)
async def list_summaries(
    user: UserContext = Depends(get_current_user),
):
    result = await summarize_service.list_summaries(user.id, user.plan)
    return SummarizeListResponse(**result)
