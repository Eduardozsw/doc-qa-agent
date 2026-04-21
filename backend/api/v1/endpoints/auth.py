from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# Rotas futuras — autenticação por email/senha (alternativa ao OAuth Supabase)
# ---------------------------------------------------------------------------

# @router.post("/register")
# async def register(body: RegisterRequest) -> TokenResponse:
#     """Cria conta com email e senha."""
#     ...

# @router.post("/login")
# async def login(body: LoginRequest) -> TokenResponse:
#     """Autentica com email e senha, retorna JWT."""
#     ...

# @router.post("/logout")
# async def logout(user: UserContext = Depends(get_current_user)) -> None:
#     """Invalida sessão."""
#     ...

# @router.post("/refresh")
# async def refresh(refresh_token: str) -> TokenResponse:
#     """Renova access token usando refresh token."""
#     ...
