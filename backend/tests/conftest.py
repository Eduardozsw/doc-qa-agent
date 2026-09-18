import os

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("DATABASE_URL", "postgresql://docqa:docqa@localhost:5432/docqa_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:1")

# Garante que o .env local do dev (que pode ter chaves reais do Langfuse) nunca
# ligue tracing durante os testes.
for _var in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST", "LANGFUSE_BASE_URL"):
    os.environ.pop(_var, None)


@pytest.fixture(autouse=True)
def _no_langfuse_env(monkeypatch):
    for _var in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST", "LANGFUSE_BASE_URL"):
        monkeypatch.delenv(_var, raising=False)


@pytest.fixture
def db():
    from db.postgres import get_pool, init_db, seed_demo_user

    try:
        with get_pool().connection() as conn:
            conn.execute("SELECT 1")
    except Exception:
        pytest.skip("Postgres indisponível")

    init_db()

    with get_pool().connection() as conn:
        conn.execute(
            "TRUNCATE users, namespaces, conversations, messages, chunks, temp_uploads, "
            "feedback, query_cache, documents "
            "RESTART IDENTITY CASCADE"
        )
        conn.commit()

    seed_demo_user()

    yield


@pytest.fixture
def demo_user(db):
    from core.config import get_settings
    from db.users import get_user_by_email

    settings = get_settings()
    user = get_user_by_email(settings.demo_user_email)
    assert user is not None
    return user
