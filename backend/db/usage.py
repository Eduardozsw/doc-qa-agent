from datetime import datetime
from db.redis import get_client
from core.limits import get_limit

_TTL = 40 * 86400  # 40 dias


def _key(user_id: str, metric: str) -> str:
    month = datetime.now().strftime("%Y-%m")
    return f"user:{user_id}:usage:{month}:{metric}"


def atomic_increment_and_check(user_id: str, plan: str, metric: str) -> bool:
    """Incrementa atomicamente e retorna True se o limite foi excedido."""
    limit = get_limit(plan, metric)
    if limit is None:
        return False

    key = _key(user_id, metric)
    client = get_client()
    new_value = client.incr(key)
    client.expire(key, _TTL)

    if new_value > limit:
        client.decr(key)
        return True
    return False


def increment(user_id: str, metric: str) -> None:
    key = _key(user_id, metric)
    client = get_client()
    client.incr(key)
    client.expire(key, _TTL)


def get_usage(user_id: str, metric: str) -> int:
    val = get_client().get(_key(user_id, metric))
    return int(val) if val else 0
