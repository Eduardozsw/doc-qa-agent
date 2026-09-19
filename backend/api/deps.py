import logging
from dataclasses import dataclass
from fastapi import Header, HTTPException

from core.security import decode_token
from db.users import get_user_by_id

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
        payload = decode_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Token inválido ou expirado")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")

        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Não autenticado")

        return UserContext(id=user["id"], email=user["email"] or "", plan=user["plan"], name=user["name"] or "")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado na autenticação: {type(e).__name__}: {e}")
        raise HTTPException(status_code=401, detail="Não autenticado")
