import os
import redis
from dotenv import load_dotenv

load_dotenv()

_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)

NAMESPACE_KEY = "namespaces"

def get_namespaces() -> list[str]:
    return list(_client.smembers(NAMESPACE_KEY))

def add_namespace(name: str) -> None:
    _client.sadd(NAMESPACE_KEY, name)

def remove_namespace(name: str) -> None:
    _client.srem(NAMESPACE_KEY, name)

def get_cached_namespace(sha256: str) -> str | None:
    return _client.get(f"pdf_hash:{sha256}")

def set_cached_namespace(sha256: str, namespace: str, ttl_days: int = 30) -> None:
    _client.set(f"pdf_hash:{sha256}", namespace, ex=ttl_days * 86400)
