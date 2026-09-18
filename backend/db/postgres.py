import logging
import threading

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pgvector.psycopg import register_vector

from core.config import get_settings
from core.security import hash_password

logger = logging.getLogger(__name__)

_pool: ConnectionPool | None = None
_pool_lock = threading.Lock()

_DDL = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email CITEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  name TEXT NOT NULL DEFAULT '',
  plan TEXT NOT NULL DEFAULT 'pro',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS namespaces (
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  namespace TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  filename TEXT NOT NULL,
  summary JSONB,
  summarized_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, namespace)
);
CREATE INDEX IF NOT EXISTS idx_namespaces_user_sha ON namespaces(user_id, sha256);

CREATE TABLE IF NOT EXISTS conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  summary TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
  id BIGSERIAL PRIMARY KEY,
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user','assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, id);

CREATE TABLE IF NOT EXISTS chunks (
  id TEXT PRIMARY KEY,
  namespace TEXT NOT NULL,
  chunk_index INT NOT NULL,
  page INT NOT NULL DEFAULT 0,
  text TEXT NOT NULL,
  embedding VECTOR(1536) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_namespace ON chunks(namespace);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops);

ALTER TABLE chunks ADD COLUMN IF NOT EXISTS tsv tsvector GENERATED ALWAYS AS (to_tsvector('portuguese', text)) STORED;
CREATE INDEX IF NOT EXISTS idx_chunks_tsv ON chunks USING gin (tsv);

-- Contextual retrieval (F4): frase(s) de contexto geradas por LLM, prefixadas ao texto
-- só na hora do embedding. `text` continua guardando o trecho original (citações/tsv).
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS context TEXT NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS temp_uploads (
  job_id TEXT PRIMARY KEY,
  content BYTEA NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- F5: feedback do usuário (👍/👎) por resposta, opcionalmente ligado a um trace do
-- Langfuse (trace_id fica NULL se o tracing estiver desligado).
CREATE TABLE IF NOT EXISTS feedback (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  trace_id TEXT,
  score SMALLINT NOT NULL CHECK (score IN (-1, 1)),
  comentario TEXT NOT NULL DEFAULT '',
  pergunta TEXT NOT NULL DEFAULT '',
  resposta TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- F5: cache semântico de respostas por conjunto de namespaces. Hit por similaridade
-- de cosseno (>= semantic_cache_min_score), com TTL e invalidação por namespace.
CREATE TABLE IF NOT EXISTS query_cache (
  id BIGSERIAL PRIMARY KEY,
  namespaces_key TEXT NOT NULL,
  namespaces TEXT[] NOT NULL,
  embedding VECTOR(1536) NOT NULL,
  query TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_query_cache_namespaces_key ON query_cache(namespaces_key);
"""


def _normalize_dsn(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


def _configure_connection(conn) -> None:
    # Garante a extensão antes de registrar o adapter: numa base nova (antes do primeiro
    # init_db()), o tipo `vector` ainda não existe e register_vector() falharia. Sob
    # concorrência (pool abrindo várias conexões de uma vez), duas conexões podem tentar
    # criar a extensão ao mesmo tempo; a que perder a corrida só precisa dar rollback.
    try:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.debug(f"CREATE EXTENSION vector: {e}")
    register_vector(conn)


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                settings = get_settings()
                dsn = _normalize_dsn(settings.database_url)
                _pool = ConnectionPool(
                    dsn,
                    open=True,
                    kwargs={"row_factory": dict_row},
                    configure=_configure_connection,
                )
    return _pool


def get_conn():
    return get_pool().connection()


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(_DDL)
        conn.commit()
    seed_demo_user()


def seed_demo_user() -> None:
    settings = get_settings()
    password_hash = hash_password(settings.demo_user_password)
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (email, password_hash, name, plan)
            VALUES (%s, %s, %s, 'pro')
            ON CONFLICT (email) DO NOTHING
            """,
            (settings.demo_user_email, password_hash, "Demo"),
        )
        conn.commit()
