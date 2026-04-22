from fastapi import Request
from slowapi import Limiter


def _key_by_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    return auth if auth else (request.client.host if request.client else "unknown")


limiter = Limiter(key_func=_key_by_token)
