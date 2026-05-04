import os
import logging
import threading
from datetime import datetime
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


def get_customer_id(user_id: str) -> str | None:
    try:
        result = get_admin().table("profiles").select("customer_id").eq("id", user_id).single().execute()
        return result.data.get("customer_id") if result.data else None
    except Exception as e:
        logger.warning(f"Falha ao buscar customer_id para {user_id}: {e}")
        return None


def set_customer_id(user_id: str, customer_id: str) -> None:
    try:
        get_admin().table("profiles").update({"customer_id": customer_id}).eq("id", user_id).execute()
    except Exception as e:
        logger.error(f"Falha ao salvar customer_id para {user_id}: {e}")
        raise


def update_plan_and_status(
    user_id: str,
    plan: str,
    status: str,
    subscription_id: str | None = None,
    period_end: datetime | None = None,
) -> None:
    try:
        data: dict = {"plan": plan, "subscription_status": status}
        if subscription_id is not None:
            data["subscription_id"] = subscription_id
        if period_end is not None:
            data["current_period_end"] = period_end.isoformat()
        get_admin().table("profiles").update(data).eq("id", user_id).execute()
    except Exception as e:
        logger.error(f"Falha ao atualizar plano para {user_id}: {e}")
        raise


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


def expire_pix_plans() -> None:
    try:
        now = datetime.utcnow().isoformat()
        result = (
            get_admin()
            .table("profiles")
            .select("id")
            .neq("plan", "free")
            .is_("subscription_id", "null")
            .lt("current_period_end", now)
            .execute()
        )
        if not result.data:
            return
        ids = [r["id"] for r in result.data]
        get_admin().table("profiles").update(
            {"plan": "free", "subscription_status": "expired"}
        ).in_("id", ids).execute()
        logger.info(f"expire_pix_plans: {len(ids)} plano(s) expirado(s)")
    except Exception as e:
        logger.error(f"Falha ao expirar planos PIX: {e}")
