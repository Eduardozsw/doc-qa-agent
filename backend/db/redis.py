import logging
import time
import redis
from redis.exceptions import ConnectionError as RedisConnectionError
from core.config import get_settings

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None


def get_client() -> redis.Redis:
    global _client
    if _client is None:
        settings = get_settings()
        r = redis.from_url(settings.redis_url, decode_responses=True)
        for attempt in range(5):
            try:
                r.ping()
                _client = r
                return _client
            except Exception as e:
                if attempt < 4:
                    logger.warning(f"Redis não disponível, tentativa {attempt + 1}/5: {e}")
                    time.sleep(2)
                else:
                    raise RuntimeError(f"Falha ao conectar ao Redis após 5 tentativas: {e}") from e
    return _client


def _namespace_key(user_id: str) -> str:
    return f"user:{user_id}:namespaces"


def get_namespaces(user_id: str) -> list[str]:
    try:
        return list(get_client().smembers(_namespace_key(user_id)))
    except Exception as e:
        logger.error(f"Redis get_namespaces falhou para user {user_id}: {e}")
        return []


def add_namespace(user_id: str, name: str) -> None:
    try:
        get_client().sadd(_namespace_key(user_id), name)
    except Exception as e:
        logger.error(f"Redis add_namespace falhou: {e}")
        raise


def remove_namespace(user_id: str, name: str) -> None:
    try:
        get_client().srem(_namespace_key(user_id), name)
    except Exception as e:
        logger.error(f"Redis remove_namespace falhou: {e}")
        raise


def get_cached_namespace(sha256: str, user_id: str) -> str | None:
    try:
        return get_client().get(f"pdf_hash:{sha256}:{user_id}")
    except Exception as e:
        logger.error(f"Redis get_cached_namespace falhou: {e}")
        return None


def set_cached_namespace(sha256: str, user_id: str, namespace: str, ttl_days: int = 30) -> None:
    try:
        get_client().set(f"pdf_hash:{sha256}:{user_id}", namespace, ex=ttl_days * 86400)
    except Exception as e:
        logger.error(f"Redis set_cached_namespace falhou: {e}")
