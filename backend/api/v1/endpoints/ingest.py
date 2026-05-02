from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from typing import List

from api.deps import get_current_user, UserContext
from models.requests import DeleteRequest
from models.responses import IngestResponse, ListFilesResponse, DeleteResponse
from services import ingest as ingest_service
from db import supabase as supabase_db
from db.redis import get_cached_namespace
from core.limits import get_limit
from core.limiter import limiter
from utils.hashing import sha256_bytes

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

    file_bytes: list[tuple[UploadFile, bytes]] = []
    for f in files:
        contents = await f.read()
        file_bytes.append((f, contents))

    skipped_names: list[str] = []

    if limit is not None:
        current = supabase_db.count_namespaces(user.id)
        available = limit - current

        cached: list[tuple[UploadFile, bytes]] = []
        new: list[tuple[UploadFile, bytes]] = []
        for f, contents in file_bytes:
            if get_cached_namespace(sha256_bytes(contents), user.id):
                cached.append((f, contents))
            else:
                new.append((f, contents))

        allowed_new = new[:max(available, 0)]
        skipped = new[max(available, 0):]
        skipped_names = [f.filename or "arquivo" for f, _ in skipped]
        file_bytes = cached + allowed_new

    for f, _ in file_bytes:
        await f.seek(0)

    allowed_files = [f for f, _ in file_bytes]
    added, total_chunks, new_namespaces = await ingest_service.ingest_files(user.id, allowed_files)

    if skipped_names:
        nomes = ", ".join(f'"{n}"' for n in skipped_names)
        verb = "foi" if len(skipped_names) == 1 else "foram"
        message = (
            f"O arquivo {nomes} não {verb} adicionado(s) pois você atingiu o limite de "
            f"{limit} documentos simultâneos do plano {user.plan}."
        )
    else:
        message = f"{total_chunks} chunks indexados"

    return IngestResponse(message=message, arquivos=added)


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
