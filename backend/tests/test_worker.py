import json
import pytest
from unittest.mock import MagicMock, patch, call


def _make_redis_client(jobs: list[dict]):
    """Redis fake que retorna jobs da lista e depois levanta KeyboardInterrupt."""
    r = MagicMock()
    calls = iter([(b"ingest_queue", json.dumps(job).encode()) for job in jobs])

    def blpop(key, timeout=0):
        try:
            return next(calls)
        except StopIteration:
            raise KeyboardInterrupt

    r.blpop = MagicMock(side_effect=blpop)
    return r


def test_worker_processes_job_and_sets_done():
    job = {"job_id": "j1", "user_id": "u1", "filename": "a.pdf",
           "tmp_path": "/tmp/j1.pdf", "namespace": "ns1", "sha256": "sha", "plan": "free"}

    with patch("worker.get_client", return_value=_make_redis_client([job])):
        with patch("worker.set_job_status") as mock_status:
            with patch("worker.process_file_job") as mock_process:
                try:
                    from worker import run_worker
                    run_worker()
                except KeyboardInterrupt:
                    pass

    assert mock_status.call_args_list[0] == call("j1", "processing", filename="a.pdf")
    mock_process.assert_called_once_with(job)
    assert mock_status.call_args_list[1] == call("j1", "done", filename="a.pdf", namespace="ns1")


def test_worker_sets_error_on_failure():
    job = {"job_id": "j2", "user_id": "u1", "filename": "b.pdf",
           "tmp_path": "/tmp/j2.pdf", "namespace": "ns2", "sha256": "sha", "plan": "free"}

    with patch("worker.get_client", return_value=_make_redis_client([job])):
        with patch("worker.set_job_status") as mock_status:
            with patch("worker.process_file_job", side_effect=ValueError("pdf ruim")):
                try:
                    from worker import run_worker
                    run_worker()
                except KeyboardInterrupt:
                    pass

    last_call = mock_status.call_args_list[-1]
    assert last_call[0][1] == "error"
    assert "pdf ruim" in last_call[1].get("error", "")
