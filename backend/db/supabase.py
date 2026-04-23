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


def get_stripe_customer_id(user_id: str) -> str | None:
    try:
        result = get_admin().table("profiles").select("stripe_customer_id").eq("id", user_id).single().execute()
        return result.data.get("stripe_customer_id") if result.data else None
    except Exception as e:
        logger.warning(f"Falha ao buscar stripe_customer_id para {user_id}: {e}")
        return None


def set_stripe_customer_id(user_id: str, customer_id: str) -> None:
    try:
        get_admin().table("profiles").update({"stripe_customer_id": customer_id}).eq("id", user_id).execute()
    except Exception as e:
        logger.error(f"Falha ao salvar stripe_customer_id para {user_id}: {e}")
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
            data["stripe_subscription_id"] = subscription_id
        if period_end is not None:
            data["current_period_end"] = period_end.isoformat()
        get_admin().table("profiles").update(data).eq("id", user_id).execute()
    except Exception as e:
        logger.error(f"Falha ao atualizar plano para {user_id}: {e}")
        raise
