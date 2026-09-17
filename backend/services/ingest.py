import logging

from core.exceptions import ForbiddenError
from db import redis as redis_db
from db import supabase as supabase_db
from ingestion.loader import load_pages_from_bytes
from ingestion.chunker import chunk_pages
from ingestion.embedder import upsert_chunks

logger = logging.getLogger(__name__)


async def list_files(user_id: str) -> list[str]:
    return supabase_db.get_namespaces(user_id)


async def remove_files(user_id: str, namespaces: list[str]) -> None:
    user_namespaces = supabase_db.get_namespaces(user_id)
    not_owned = [n for n in namespaces if n not in user_namespaces]
    if not_owned:
        logger.warning(
            f"403 delete user={user_id} requested={namespaces} owned={user_namespaces} not_owned={not_owned}"
        )
        raise ForbiddenError("Arquivo não encontrado")

    for ns in namespaces:
        sha256 = supabase_db.get_sha256_for_namespace(user_id, ns)
        supabase_db.remove_namespace(user_id, ns)
        if sha256:
            redis_db.delete_cached_namespace(sha256, user_id)


def process_file_job(job: dict) -> None:
    job_id = job["job_id"]
    try:
        contents = supabase_db.download_temp_file(job_id)

        try:
            pages = load_pages_from_bytes(contents)
        except Exception as e:
            logger.error(f"Job {job_id} — falha ao ler PDF: {e}")
            raise RuntimeError("Não foi possível ler o PDF. O arquivo pode estar corrompido.")

        if not pages or not any(t.strip() for _, t in pages):
            raise ValueError("PDF não contém texto extraível. Pode ser um arquivo escaneado.")

        chunks = chunk_pages(pages)
        if not chunks:
            raise ValueError("Não foi possível extrair conteúdo do documento.")

        try:
            upsert_chunks(chunks, job["namespace"], job["namespace"])
        except Exception as e:
            logger.error(f"Job {job_id} — falha ao indexar chunks: {e}")
            raise RuntimeError("Erro ao salvar o documento. Tente novamente em alguns instantes.")

        supabase_db.add_namespace(job["user_id"], job["namespace"], job["sha256"], job["filename"])
        redis_db.set_cached_namespace(job["sha256"], job["user_id"], job["namespace"])
        logger.info(f"Job {job_id} concluído: {len(chunks)} chunks")
    except (ValueError, RuntimeError):
        raise
    except Exception as e:
        logger.error(f"Job {job_id} — erro inesperado: {e}")
        raise RuntimeError("Erro inesperado ao processar o arquivo.")
    finally:
        supabase_db.delete_temp_file(job_id)
