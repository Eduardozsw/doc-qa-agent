import base64
import json
from fastapi import Request
from slowapi import Limiter


def _extract_user_id_from_jwt(auth_header: str) -> str | None:
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.removeprefix("Bearer ").strip()
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        sub = payload.get("sub")
        return str(sub) if sub else None
    except Exception:
        return None


def _key_by_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    user_id = _extract_user_id_from_jwt(auth)
    if user_id:
        return f"user:{user_id}"
    ip = request.client.host if request.client else "unknown"
    return f"ip:{ip}"


limiter = Limiter(key_func=_key_by_token)
