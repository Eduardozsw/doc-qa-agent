import logging
from fastapi import APIRouter, Depends, Header

from api.deps import get_current_user, UserContext
from db.supabase import get_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/logout", status_code=204)
async def logout(
    authorization: str = Header(...),
    user: UserContext = Depends(get_current_user),
) -> None:
    token = authorization.removeprefix("Bearer ").strip()
    try:
        get_admin().auth.admin.sign_out(token)
    except Exception as e:
        logger.warning(f"Falha ao revogar sessão para user {user.id}: {e}")
    return None
