import hashlib
import json
import logging
import time
import redis
from redis.exceptions import ConnectionError as RedisConnectionError
from core.config import get_settings

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def get_client() -> redis.Redis:
    global _client
    if _client is None:
        settings = get_settings()
        r = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_timeout=None,
            socket_connect_timeout=10,
            retry_on_timeout=True,
            health_check_interval=10,
        )
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


def get_cached_namespace(sha256: str, user_id: str) -> str | None:
    try:
        cache_key = _sha256(f"{user_id}:{sha256}")
        return get_client().get(f"pdf_hash:{cache_key}")
    except Exception as e:
        logger.error(f"Redis get_cached_namespace falhou: {e}")
        return None


def delete_cached_namespace(sha256: str, user_id: str) -> None:
    try:
        cache_key = _sha256(f"{user_id}:{sha256}")
        get_client().delete(f"pdf_hash:{cache_key}")
    except Exception as e:
        logger.error(f"Redis delete_cached_namespace falhou: {e}")


def set_cached_namespace(sha256: str, user_id: str, namespace: str, ttl_days: int = 30) -> None:
    try:
        cache_key = _sha256(f"{user_id}:{sha256}")
        get_client().set(f"pdf_hash:{cache_key}", namespace, ex=ttl_days * 86400)
    except Exception as e:
        logger.error(f"Redis set_cached_namespace falhou: {e}")


def enqueue_job(payload: dict) -> None:
    try:
        get_client().lpush("ingest_queue", json.dumps(payload))
    except Exception as e:
        logger.error(f"Redis enqueue_job falhou: {e}")
        raise


def set_job_status(job_id: str, status: str, **kwargs) -> None:
    data = {"status": status, **kwargs}
    try:
        get_client().setex(f"ingest_job:{job_id}", 86400, json.dumps(data))
    except Exception as e:
        logger.error(f"Redis set_job_status falhou: {e}")
        raise


def get_jobs_status(job_ids: list[str]) -> dict[str, dict | None]:
    if not job_ids:
        return {}
    try:
        keys = [f"ingest_job:{jid}" for jid in job_ids]
        values = get_client().mget(*keys)
        return {
            jid: json.loads(val) if val else None
            for jid, val in zip(job_ids, values)
        }
    except Exception as e:
        logger.error(f"Redis get_jobs_status falhou: {e}")
        return {jid: None for jid in job_ids}
