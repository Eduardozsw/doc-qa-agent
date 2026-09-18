import importlib.util
import re

from pydantic import BaseModel, field_validator, model_validator

_HAS_EMAIL_VALIDATOR = importlib.util.find_spec("email_validator") is not None

if _HAS_EMAIL_VALIDATOR:
    from pydantic import EmailStr

    EmailField = EmailStr
else:
    EmailField = str

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+$")


def _validate_email_fallback(v: str) -> str:
    if not _HAS_EMAIL_VALIDATOR:
        v = v.strip()
        if not _EMAIL_RE.match(v):
            raise ValueError("email inválido")
    return v


def _validate_password_bytes(v: str) -> str:
    length = len(v.encode("utf-8"))
    if length < 8:
        raise ValueError("senha deve ter no mínimo 8 caracteres")
    if length > 72:
        raise ValueError("senha deve ter no máximo 72 bytes")
    return v


class RegisterRequest(BaseModel):
    email: EmailField
    password: str
    name: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        return _validate_email_fallback(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_bytes(v)


class LoginRequest(BaseModel):
    email: EmailField
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        return _validate_email_fallback(v)


class UpdateMeRequest(BaseModel):
    name: str | None = None
    password: str | None = None
    current_password: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _validate_password_bytes(v)

    @model_validator(mode="after")
    def validate_current_password_required(self):
        if self.password is not None and not self.current_password:
            raise ValueError("current_password é obrigatório para alterar a senha")
        return self


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    plan: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
