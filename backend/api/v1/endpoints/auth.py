import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from api.deps import get_current_user, UserContext
from core.exceptions import ConflictError
from core.limiter import limiter
from core.security import create_token, verify_password
from db import users as users_db
from models.auth import LoginRequest, RegisterRequest, TokenResponse, UpdateMeRequest, UserOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_user_out(user: dict) -> UserOut:
    return UserOut(id=user["id"], email=user["email"], name=user.get("name") or "", plan=user["plan"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest):
    existing = users_db.get_user_by_email(body.email)
    if existing:
        raise ConflictError("E-mail já cadastrado")

    user = users_db.create_user(body.email, body.password, body.name or "")
    token = create_token(user["id"], user["email"])
    return TokenResponse(access_token=token, user=_to_user_out(user))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest):
    user = users_db.get_user_by_email(body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    token = create_token(user["id"], user["email"])
    return TokenResponse(access_token=token, user=_to_user_out(user))


@router.get("/me", response_model=UserOut)
async def get_me(user: UserContext = Depends(get_current_user)):
    return UserOut(id=user.id, email=user.email, name=user.name, plan=user.plan)


@router.patch("/me", response_model=UserOut)
async def update_me(body: UpdateMeRequest, user: UserContext = Depends(get_current_user)):
    if body.password is not None:
        current = users_db.get_user_by_id(user.id)
        if not current or not verify_password(body.current_password or "", current["password_hash"]):
            raise HTTPException(status_code=401, detail="Senha atual incorreta")

    updated = users_db.update_user(user.id, name=body.name, password=body.password)
    return _to_user_out(updated)


@router.post("/logout", status_code=204)
async def logout(user: UserContext = Depends(get_current_user)) -> None:
    return None
