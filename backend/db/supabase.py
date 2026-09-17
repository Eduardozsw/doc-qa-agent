import os
import logging
import threading
from datetime import datetime, timezone
from supabase import create_client, Client

logger = logging.getLogger(__name__)

_admin: Client | None = None
_admin_lock = threading.Lock()


def get_admin() -> Client:
    global _admin
    if _admin is None:
        with _admin_lock:
            if _admin is None:
                url = os.environ.get("SUPABASE_URL")
                key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
                if not url or not key:
                    raise RuntimeError("SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são obrigatórias")
                _admin = create_client(url, key)
    return _admin


def get_user_plan(user_id: str) -> str:
    try:
        result = get_admin().table("profiles").select("plan").eq("id", user_id).single().execute()
        return result.data.get("plan", "free") if result.data else "free"
    except Exception as e:
        logger.warning(f"Falha ao buscar plano do usuário {user_id}: {e}")
        return "free"


def count_namespaces(user_id: str) -> int:
    try:
        result = get_admin().table("namespaces").select("*", count="exact").eq("user_id", user_id).execute()
        return result.count or 0
    except Exception as e:
        logger.error(f"Falha ao contar namespaces para {user_id}: {e}")
        return 0


def get_namespaces(user_id: str) -> list[str]:
    try:
        result = get_admin().table("namespaces").select("namespace").eq("user_id", user_id).execute()
        return [r["namespace"] for r in result.data] if result.data else []
    except Exception as e:
        logger.error(f"Falha ao buscar namespaces para {user_id}: {e}")
        return []


def get_namespace_by_sha256(user_id: str, sha256: str) -> str | None:
    try:
        result = (
            get_admin()
            .table("namespaces")
            .select("namespace")
            .eq("user_id", user_id)
            .eq("sha256", sha256)
            .single()
            .execute()
        )
        return result.data["namespace"] if result.data else None
    except Exception:
        return None


def add_namespace(user_id: str, namespace: str, sha256: str, filename: str) -> None:
    try:
        get_admin().table("namespaces").upsert(
            {"user_id": user_id, "namespace": namespace, "sha256": sha256, "filename": filename}
        ).execute()
    except Exception as e:
        logger.error(f"Falha ao salvar namespace para {user_id}: {e}")
        raise


def get_sha256_for_namespace(user_id: str, namespace: str) -> str | None:
    try:
        result = (
            get_admin()
            .table("namespaces")
            .select("sha256")
            .eq("user_id", user_id)
            .eq("namespace", namespace)
            .single()
            .execute()
        )
        return result.data["sha256"] if result.data else None
    except Exception:
        return None


def remove_namespace(user_id: str, namespace: str) -> None:
    try:
        get_admin().table("namespaces").delete().eq("user_id", user_id).eq("namespace", namespace).execute()
    except Exception as e:
        logger.error(f"Falha ao remover namespace para {user_id}: {e}")
        raise


def get_user_info(user_id: str) -> tuple[str, str]:
    try:
        response = get_admin().auth.admin.get_user_by_id(user_id)
        user = response.user
        email = user.email or ""
        name = (user.user_metadata or {}).get("full_name", "")
        return email, name
    except Exception as e:
        logger.warning(f"Falha ao buscar info do usuário {user_id}: {e}")
        return "", ""


def upload_temp_file(job_id: str, contents: bytes) -> None:
    path = f"{job_id}.pdf"
    get_admin().storage.from_("temp-uploads").upload(
        path, contents, {"content-type": "application/pdf", "upsert": "true"}
    )


def download_temp_file(job_id: str) -> bytes:
    path = f"{job_id}.pdf"
    return bytes(get_admin().storage.from_("temp-uploads").download(path))


def delete_temp_file(job_id: str) -> None:
    try:
        get_admin().storage.from_("temp-uploads").remove([f"{job_id}.pdf"])
    except Exception as e:
        logger.warning(f"Falha ao deletar temp file {job_id}: {e}")


def get_summary(user_id: str, namespace: str) -> dict | None:
    try:
        result = (
            get_admin()
            .table("namespaces")
            .select("summary")
            .eq("user_id", user_id)
            .eq("namespace", namespace)
            .single()
            .execute()
        )
        return result.data.get("summary") if result.data else None
    except Exception:
        return None


def save_summary(user_id: str, namespace: str, summary: dict) -> None:
    try:
        get_admin().table("namespaces").update({
            "summary": summary,
            "summarized_at": datetime.now(timezone.utc).isoformat(),
        }).eq("user_id", user_id).eq("namespace", namespace).execute()
    except Exception as e:
        logger.error(f"Falha ao salvar summary para {user_id}/{namespace}: {e}")
        raise


def count_summaries_this_month(user_id: str) -> int:
    try:
        now = datetime.now(timezone.utc)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        result = (
            get_admin()
            .table("namespaces")
            .select("namespace", count="exact")
            .eq("user_id", user_id)
            .gte("summarized_at", start_of_month)
            .execute()
        )
        return result.count or 0
    except Exception as e:
        logger.warning(f"Falha ao contar summaries para {user_id}: {e}")
        return 0


def get_namespaces_with_summaries(user_id: str) -> list[dict]:
    try:
        result = (
            get_admin()
            .table("namespaces")
            .select("namespace, filename, summary")
            .eq("user_id", user_id)
            .not_.is_("summary", "null")
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error(f"Falha ao buscar summaries para {user_id}: {e}")
        return []
