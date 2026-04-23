from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from typing import List

from api.deps import get_current_user, UserContext
from models.requests import DeleteRequest
from models.responses import IngestResponse, ListFilesResponse, DeleteResponse
from services import ingest as ingest_service
from db.usage import get_usage, increment
from core.limits import get_limit
from core.limiter import limiter

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.get("", response_model=ListFilesResponse)
async def list_files(user: UserContext = Depends(get_current_user)):
    files = await ingest_service.list_files(user.id)
    return ListFilesResponse(arquivos=files)


@router.post("", response_model=IngestResponse)
@limiter.limit("10/minute")
async def ingest_files(
    request: Request,
    files: List[UploadFile],
    user: UserContext = Depends(get_current_user),
):
    limit = get_limit(user.plan, "documents")
    if limit is not None:
        current = get_usage(user.id, "documents")
        available = limit - current
        if available <= 0:
            raise HTTPException(status_code=429, detail=f"Limite de {limit} documentos mensais atingido")
        if len(files) > available:
            raise HTTPException(
                status_code=429,
                detail=f"Você pode adicionar no máximo {available} documento(s) este mês",
            )

    added, total_chunks = await ingest_service.ingest_files(user.id, files)

    if limit is not None:
        for _ in added:
            increment(user.id, "documents")

    return IngestResponse(message=f"{total_chunks} chunks indexados", arquivos=added)


@router.delete("", response_model=DeleteResponse)
async def remove_files(
    body: DeleteRequest,
    user: UserContext = Depends(get_current_user),
):
    await ingest_service.remove_files(user.id, body.namespaces)
    return DeleteResponse(
        message=f"{len(body.namespaces)} arquivo(s) removido(s)",
        arquivos=body.namespaces,
    )
