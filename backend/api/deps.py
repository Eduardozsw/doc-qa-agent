import logging
import os
from dataclasses import dataclass
from fastapi import Header, HTTPException
from supabase import create_client, Client
import threading

logger = logging.getLogger(__name__)

_admin: Client | None = None
_admin_lock = threading.Lock()


def _get_admin() -> Client:
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


@dataclass
class UserContext:
    id: str
    email: str


async def get_current_user(authorization: str = Header(...)) -> UserContext:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")

    token = authorization.removeprefix("Bearer ").strip()

    if not token or len(token.split(".")) != 3:
        raise HTTPException(status_code=401, detail="Token inválido")

    try:
        response = _get_admin().auth.get_user(token)
        user = response.user
        if not user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        return UserContext(id=user.id, email=user.email or "")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado na autenticação: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno de autenticação")
