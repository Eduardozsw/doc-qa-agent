from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenAI
    openai_api_key: str
    openai_chat_model: str = "gpt-4o-mini"

    # Auth
    jwt_secret: str
    jwt_expire_days: int = 7

    # Postgres
    database_url: str = "postgresql://docqa:docqa@localhost:5432/docqa"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # CORS
    allowed_origins: str = "http://localhost:5173,http://localhost:8080"

    # Upload
    max_file_size_mb: int = 50

    # Retrieval
    hybrid_search: bool = True
    rerank_enabled: bool = True
    rerank_candidates: int = 20
    multi_query_enabled: bool = True

    # Ingestão
    # Desligado por padrão: medido no CAB 37 (doc único de 130 páginas), o prefixo de
    # contexto reduziu hit@5/MRR/citation_rate em vez de ajudar (ver evals de ablação).
    contextual_retrieval_enabled: bool = False
    ocr_enabled: bool = False

    # Cache semântico (F5): hit por similaridade de cosseno entre a pergunta e o
    # cache do mesmo conjunto de namespaces. Só é consultado sem histórico/resumo.
    semantic_cache_enabled: bool = True
    semantic_cache_min_score: float = 0.97
    semantic_cache_ttl_hours: int = 24

    # Demo user (seed no boot)
    demo_user_email: str = "demo@local"
    demo_user_password: str = "demo1234"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
