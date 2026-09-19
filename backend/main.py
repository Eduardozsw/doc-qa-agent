import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from core.config import get_settings
from core.exceptions import AppError, app_error_handler, generic_error_handler
from core.limiter import limiter
from middleware.cors import register_cors
from api.v1.router import router

get_settings()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from db.postgres import init_db
    init_db()
    yield
    from core.tracing import flush
    flush()


app = FastAPI(title="doc-qa-agent", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter

register_cors(app)

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

app.include_router(router)


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


@app.get("/health/db")
async def health_db():
    from db.postgres import get_conn
    from db.redis import get_client

    try:
        with get_conn() as conn:
            row = conn.execute("SELECT count(*) AS n FROM namespaces").fetchone()
        namespaces_total = row["n"] if row else 0
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)

    try:
        get_client().ping()
        redis_status = "ok"
    except Exception as e:
        logger.warning(f"health/db: Redis indisponível: {e}")
        redis_status = "error"

    return JSONResponse({"status": "ok", "namespaces_total": namespaces_total, "redis": redis_status})
