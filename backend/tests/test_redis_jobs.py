import json
from unittest.mock import MagicMock, patch


def _make_redis(store: dict):
    """Fake Redis client backed by a dict."""
    r = MagicMock()
    r.lpush = MagicMock(side_effect=lambda key, val: store.setdefault(key, []).append(val))
    r.setex = MagicMock(side_effect=lambda key, ttl, val: store.update({key: val}))
    r.mget = MagicMock(side_effect=lambda *keys: [store.get(k) for k in keys])
    return r


def test_enqueue_job_pushes_to_queue():
    store = {}
    with patch("db.redis.get_client", return_value=_make_redis(store)):
        from db.redis import enqueue_job
        enqueue_job({"job_id": "abc", "filename": "doc.pdf"})
    assert len(store.get("ingest_queue", [])) == 1
    payload = json.loads(store["ingest_queue"][0])
    assert payload["job_id"] == "abc"


def test_set_job_status_stores_with_ttl():
    store = {}
    r = _make_redis(store)
    with patch("db.redis.get_client", return_value=r):
        from db.redis import set_job_status
        set_job_status("abc", "processing", filename="doc.pdf")
    r.setex.assert_called_once()
    key, ttl, val = r.setex.call_args[0]
    assert key == "ingest_job:abc"
    assert ttl == 86400
    data = json.loads(val)
    assert data["status"] == "processing"
    assert data["filename"] == "doc.pdf"


def test_get_jobs_status_returns_dict():
    store = {
        "ingest_job:id1": json.dumps({"status": "done", "filename": "a.pdf"}),
        "ingest_job:id2": json.dumps({"status": "error", "filename": "b.pdf", "error": "falhou"}),
    }
    with patch("db.redis.get_client", return_value=_make_redis(store)):
        from db.redis import get_jobs_status
        result = get_jobs_status(["id1", "id2", "id3"])
    assert result["id1"]["status"] == "done"
    assert result["id2"]["error"] == "falhou"
    assert result["id3"] is None


def test_get_jobs_status_empty_list():
    with patch("db.redis.get_client"):
        from db.redis import get_jobs_status
        result = get_jobs_status([])
    assert result == {}
