from datetime import datetime
from db.redis import get_client
from core.limits import get_limit

_TTL = 40 * 86400  # 40 dias

_INCR_EXPIRE_LUA = """
local v = redis.call('INCR', KEYS[1])
redis.call('EXPIRE', KEYS[1], ARGV[1])
return v
"""

_CHECK_AND_INCR_LUA = """
local current = tonumber(redis.call('GET', KEYS[1]) or '0')
if current >= tonumber(ARGV[2]) then
  return -1
end
local v = redis.call('INCR', KEYS[1])
redis.call('EXPIRE', KEYS[1], ARGV[1])
return v
"""


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
    result = client.eval(_CHECK_AND_INCR_LUA, 1, key, _TTL, limit)
    return int(result) == -1


def increment(user_id: str, metric: str) -> None:
    key = _key(user_id, metric)
    client = get_client()
    client.eval(_INCR_EXPIRE_LUA, 1, key, _TTL)


def get_usage(user_id: str, metric: str) -> int:
    val = get_client().get(_key(user_id, metric))
    return int(val) if val else 0
