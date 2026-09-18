import os
import sys
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("DATABASE_URL", "postgresql://docqa:docqa@localhost:5432/docqa_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:1")
os.environ.setdefault("PINECONE_API_KEY", "test-key")
os.environ.setdefault("PINECONE_INDEX", "test-index")

# Mock ingestion.embedder before it's imported (Pinecone sai só na F2)
sys.modules["ingestion.embedder"] = MagicMock()


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
            "TRUNCATE users, namespaces, conversations, messages, chunks, temp_uploads "
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
