import logging
from dataclasses import dataclass
from fastapi import Header, HTTPException
from db.supabase import get_admin, get_user_plan

logger = logging.getLogger(__name__)


@dataclass
class UserContext:
    id: str
    email: str
    plan: str
    name: str = ""


async def get_current_user(authorization: str = Header(...)) -> UserContext:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")

    token = authorization.removeprefix("Bearer ").strip()

    if not token or len(token.split(".")) != 3:
        raise HTTPException(status_code=401, detail="Token inválido")

    try:
        response = get_admin().auth.get_user(token)
        user = response.user
        if not user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        plan = get_user_plan(user.id)
        meta = user.user_metadata or {}
        name = meta.get("full_name") or meta.get("name") or ""
        return UserContext(id=user.id, email=user.email or "", plan=plan, name=name)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado na autenticação: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno de autenticação")
