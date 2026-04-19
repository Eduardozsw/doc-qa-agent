from fastapi import Header, HTTPException
from supabase import create_client, Client
import os

_admin: Client | None = None

def _get_admin() -> Client:
    global _admin
    if _admin is None:
        _admin = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        )
    return _admin

async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    token = authorization.removeprefix("Bearer ")
    try:
        user = _get_admin().auth.get_user(token).user
        if not user:
            raise HTTPException(status_code=401, detail="Não autenticado")
        return {"id": user.id, "email": user.email}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Não autenticado")
