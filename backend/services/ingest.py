import asyncio
import logging
from fastapi import UploadFile

from core.config import get_settings
from core.exceptions import FileTooLargeError, UnsupportedFileTypeError, ForbiddenError
from db import redis as redis_db
from ingestion.loader import load_pages_from_bytes
from ingestion.chunker import chunk_pages
from ingestion.embedder import upsert_chunks
from utils.sanitize import sanitize_namespace
from utils.hashing import sha256_bytes

logger = logging.getLogger(__name__)

_INGEST_LOCK = asyncio.Lock()
_SEM = asyncio.Semaphore(3)


async def list_files(user_id: str) -> list[str]:
    return redis_db.get_namespaces(user_id)


async def remove_files(user_id: str, namespaces: list[str]) -> None:
    user_namespaces = redis_db.get_namespaces(user_id)
    not_owned = [n for n in namespaces if n not in user_namespaces]
    if not_owned:
        raise ForbiddenError("Arquivo não encontrado")

    for ns in namespaces:
        redis_db.remove_namespace(user_id, ns)


async def ingest_files(user_id: str, files: list[UploadFile]) -> tuple[list[str], int]:
    settings = get_settings()

    for file in files:
        if file.content_type != "application/pdf":
            raise UnsupportedFileTypeError()

    all_contents: list[tuple[UploadFile, bytes]] = []
    for file in files:
        contents = await file.read()
        if len(contents) > settings.max_file_size_mb * 1024 * 1024:
            raise FileTooLargeError(settings.max_file_size_mb)
        if not contents.startswith(b"%PDF-"):
            raise UnsupportedFileTypeError()
        all_contents.append((file, contents))

    results = await asyncio.gather(*[_process_file(user_id, f, c) for f, c in all_contents])

    added = [ns for ns, _ in results]
    total_chunks = sum(n for _, n in results)
    return added, total_chunks


async def _process_file(user_id: str, file: UploadFile, contents: bytes) -> tuple[str, int]:
    async with _SEM:
        sha256 = sha256_bytes(contents)
        namespace = f"{user_id[:8]}_{sha256[:8]}_{sanitize_namespace(file.filename or 'unknown')}"

        cached_ns = redis_db.get_cached_namespace(sha256, user_id)
        if cached_ns:
            redis_db.add_namespace(user_id, cached_ns)
            return cached_ns, 0

        loop = asyncio.get_event_loop()
        try:
            try:
                pages = await asyncio.wait_for(
                    loop.run_in_executor(None, load_pages_from_bytes, contents),
                    timeout=30,
                )
            except asyncio.TimeoutError:
                raise UnsupportedFileTypeError()
            except Exception:
                raise UnsupportedFileTypeError()

            if not pages or not any(t.strip() for _, t in pages):
                raise ValueError("Arquivo não contém texto extraível")

            chunks = chunk_pages(pages)
            if not chunks:
                raise ValueError("Arquivo resultou em 0 chunks")

            await loop.run_in_executor(None, upsert_chunks, chunks, namespace, namespace)
        except Exception as e:
            logger.error(f"Erro ao processar arquivo de user {user_id}: {type(e).__name__}")
            raise

        redis_db.set_cached_namespace(sha256, user_id, namespace)
        redis_db.add_namespace(user_id, namespace)
        logger.info(f"Arquivo indexado: {len(chunks)} chunks — user {user_id}")
        return namespace, len(chunks)
