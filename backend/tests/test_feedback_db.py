import pytest

from db.feedback import save_feedback
from db.postgres import get_conn


def test_save_feedback_persists_row(db, demo_user):
    save_feedback(
        demo_user["id"], "trace-abc", 1, comentario="ótima resposta", pergunta="qual o prazo?", resposta="30 dias",
    )

    with get_conn() as conn:
        row = conn.execute("SELECT * FROM feedback WHERE user_id = %s", (demo_user["id"],)).fetchone()

    assert row is not None
    assert row["trace_id"] == "trace-abc"
    assert row["score"] == 1
    assert row["comentario"] == "ótima resposta"
    assert row["pergunta"] == "qual o prazo?"
    assert row["resposta"] == "30 dias"


def test_save_feedback_allows_null_trace_id(db, demo_user):
    save_feedback(demo_user["id"], None, -1)

    with get_conn() as conn:
        row = conn.execute("SELECT * FROM feedback WHERE user_id = %s", (demo_user["id"],)).fetchone()

    assert row is not None
    assert row["trace_id"] is None
    assert row["score"] == -1
    assert row["comentario"] == ""
    assert row["pergunta"] == ""
    assert row["resposta"] == ""


def test_save_feedback_rejects_invalid_score(db, demo_user):
    with pytest.raises(Exception):
        save_feedback(demo_user["id"], None, 0)
