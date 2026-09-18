import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile

from api.deps import get_current_user, UserContext
from models.requests import DeleteRequest
from models.responses import AsyncIngestResponse, JobInfo, JobStatusResponse, JobStatus, ListFilesResponse, DeleteResponse
from services import ingest as ingest_service
from db import namespaces as namespaces_db
from db import uploads as uploads_db
from db import redis as redis_db
from core.limits import get_limit
from core.limiter import limiter
from core.config import get_settings
from utils.hashing import sha256_bytes
from utils.sanitize import sanitize_namespace

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])


async def _build_and_enqueue_jobs(
    file_entries: list[tuple[str, bytes]],
    user: UserContext,
    limit: int | None,
) -> AsyncIngestResponse:
    # Build sha→cached_ns map in one pass (avoids double DB lookups)
    file_data: list[tuple[str, bytes, str]] = []
    sha_to_cached_ns: dict[str, str | None] = {}
    for filename, contents in file_entries:
        sha = sha256_bytes(contents)
        sha_to_cached_ns[sha] = (
            redis_db.get_cached_namespace(sha, user.id)
            or namespaces_db.get_namespace_by_sha256(user.id, sha)
        )
        file_data.append((filename, contents, sha))

    skipped_names: list[str] = []

    # All-or-nothing: if any file fails validation before this point, no jobs are created.
    if limit is not None:
        current = namespaces_db.count_namespaces(user.id)
        available = limit - current

        cached_files = [(n, c, s) for n, c, s in file_data if sha_to_cached_ns[s]]
        new_files = [(n, c, s) for n, c, s in file_data if not sha_to_cached_ns[s]]

        allowed_new = new_files[:max(available, 0)]
        skipped = new_files[max(available, 0):]
        skipped_names = [n for n, _, _ in skipped]
        file_data = cached_files + allowed_new

    jobs: list[JobInfo] = []
    for filename, contents, sha in file_data:
        namespace = f"{user.id[:8]}_{sha[:8]}_{sanitize_namespace(filename)}"
        cached_ns = sha_to_cached_ns[sha]
        if cached_ns:
            # Already indexed — return immediately as done job
            job_id = str(uuid.uuid4())
            redis_db.set_job_status(job_id, "done", filename=filename, namespace=cached_ns, user_id=user.id)
            jobs.append(JobInfo(job_id=job_id, filename=filename))
            continue

        # Upload temporário (Postgres) e enqueue
        job_id = str(uuid.uuid4())
        uploads_db.upload_temp_file(job_id, contents)

        payload = {
            "job_id": job_id,
            "user_id": user.id,
            "filename": filename,
            "namespace": namespace,
            "sha256": sha,
            "plan": user.plan,
        }
        try:
            redis_db.set_job_status(job_id, "pending", filename=filename, user_id=user.id)
            redis_db.enqueue_job(payload)
        except Exception:
            uploads_db.delete_temp_file(job_id)
            raise
        jobs.append(JobInfo(job_id=job_id, filename=filename))

    return AsyncIngestResponse(jobs=jobs, skipped=skipped_names)


@router.get("", response_model=ListFilesResponse)
async def list_files(user: UserContext = Depends(get_current_user)):
    files = await ingest_service.list_files(user.id)
    return ListFilesResponse(arquivos=files)


@router.post("", response_model=AsyncIngestResponse, status_code=202)
@limiter.limit("10/minute")
async def ingest_files(
    request: Request,
    files: list[UploadFile],
    user: UserContext = Depends(get_current_user),
):
    settings = get_settings()

    file_entries: list[tuple[str, bytes]] = []
    for f in files:
        if f.content_type != "application/pdf":
            raise HTTPException(status_code=422, detail="Apenas arquivos PDF são aceitos.")
        contents = await f.read()
        if len(contents) > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(status_code=422, detail=f"Arquivo maior que {settings.max_file_size_mb}MB.")
        if not contents.startswith(b"%PDF-"):
            raise HTTPException(status_code=422, detail="Arquivo PDF inválido.")
        file_entries.append((f.filename or "unknown", contents))

    return await _build_and_enqueue_jobs(file_entries, user, get_limit(user.plan, "documents"))


@router.get("/status", response_model=JobStatusResponse)
async def get_jobs_status(
    jobs: str,
    user: UserContext = Depends(get_current_user),
):
    job_ids = [j.strip() for j in jobs.split(",") if j.strip()]
    if not job_ids:
        return JobStatusResponse(jobs={})
    if len(job_ids) > 100:
        raise HTTPException(status_code=422, detail="Máximo de 100 job_ids por consulta.")
    raw = redis_db.get_jobs_status(job_ids)
    result: dict[str, JobStatus | None] = {}
    for jid, data in raw.items():
        if data is None or data.get("user_id") != user.id:
            result[jid] = None
        else:
            result[jid] = JobStatus(**{k: v for k, v in data.items() if k != "user_id"})
    return JobStatusResponse(jobs=result)


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
