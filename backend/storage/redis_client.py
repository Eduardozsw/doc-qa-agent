import hashlib
import os
import redis
from dotenv import load_dotenv

load_dotenv()

_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)

NAMESPACE_KEY = "namespaces"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def get_namespaces() -> list[str]:
    return list(_client.smembers(NAMESPACE_KEY))


def add_namespace(name: str) -> None:
    _client.sadd(NAMESPACE_KEY, name)


def remove_namespace(name: str) -> None:
    _client.srem(NAMESPACE_KEY, name)


def get_cached_namespace(sha256: str, user_id: str) -> str | None:
    cache_key = _sha256(f"{user_id}:{sha256}")
    return _client.get(f"pdf_hash:{cache_key}")


def set_cached_namespace(sha256: str, user_id: str, namespace: str, ttl_days: int = 30) -> None:
    cache_key = _sha256(f"{user_id}:{sha256}")
    _client.set(f"pdf_hash:{cache_key}", namespace, ex=ttl_days * 86400)
