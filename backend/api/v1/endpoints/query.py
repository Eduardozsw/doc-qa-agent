from fastapi import APIRouter, Depends

from api.deps import get_current_user, UserContext
from models.requests import QueryRequest
from models.responses import QueryResponse
from services import query as query_service

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query(
    body: QueryRequest,
    user: UserContext = Depends(get_current_user),
):
    result = await query_service.handle_query(user.id, body)
    return QueryResponse(resposta=result["resposta"], fontes=result.get("fontes", []))
