from fastapi import APIRouter, Depends, UploadFile
from typing import List

from api.deps import get_current_user, UserContext
from models.requests import DeleteRequest
from models.responses import IngestResponse, ListFilesResponse, DeleteResponse
from services import ingest as ingest_service

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.get("", response_model=ListFilesResponse)
async def list_files(user: UserContext = Depends(get_current_user)):
    files = await ingest_service.list_files(user.id)
    return ListFilesResponse(arquivos=files)


@router.post("", response_model=IngestResponse)
async def ingest_files(
    files: List[UploadFile],
    user: UserContext = Depends(get_current_user),
):
    added, total_chunks = await ingest_service.ingest_files(user.id, files)
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
