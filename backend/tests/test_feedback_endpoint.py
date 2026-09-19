from unittest.mock import patch

from fastapi.testclient import TestClient

from core.security import create_token
from main import app


def _client():
    return TestClient(app)


def _token(demo_user) -> str:
    return create_token(demo_user["id"], demo_user["email"])


def test_feedback_saves_and_scores_trace(db, demo_user):
    with _client() as c:
        with patch("api.v1.endpoints.query.tracing.score") as mock_score:
            resp = c.post(
                "/api/query/feedback",
                json={"trace_id": "trace-123", "score": 1, "comentario": "ótimo", "pergunta": "q", "resposta": "a"},
                headers={"Authorization": f"Bearer {_token(demo_user)}"},
            )

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    mock_score.assert_called_once_with("trace-123", "user_feedback", 1, "ótimo")


def test_feedback_without_trace_id_does_not_score(db, demo_user):
    with _client() as c:
        with patch("api.v1.endpoints.query.tracing.score") as mock_score:
            resp = c.post(
                "/api/query/feedback",
                json={"score": -1},
                headers={"Authorization": f"Bearer {_token(demo_user)}"},
            )

    assert resp.status_code == 200
    mock_score.assert_not_called()


def test_feedback_persists_row(db, demo_user):
    with _client() as c:
        with patch("api.v1.endpoints.query.tracing.score"):
            c.post(
                "/api/query/feedback",
                json={"score": 1, "pergunta": "qual o prazo?", "resposta": "30 dias"},
                headers={"Authorization": f"Bearer {_token(demo_user)}"},
            )

    from db.postgres import get_conn

    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM feedback WHERE user_id = %s", (demo_user["id"],)
        ).fetchone()

    assert row is not None
    assert row["score"] == 1
    assert row["pergunta"] == "qual o prazo?"


def test_feedback_invalid_score_rejected(db, demo_user):
    with _client() as c:
        resp = c.post(
            "/api/query/feedback",
            json={"score": 0},
            headers={"Authorization": f"Bearer {_token(demo_user)}"},
        )

    assert resp.status_code == 422


def test_feedback_requires_auth(db):
    with _client() as c:
        resp = c.post("/api/query/feedback", json={"score": 1})

    assert resp.status_code in (401, 422)
