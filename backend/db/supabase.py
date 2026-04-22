import os
import logging
import threading
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
