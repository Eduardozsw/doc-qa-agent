import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logging.getLogger("apscheduler").setLevel(logging.INFO)
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import timezone

from core.config import get_settings
from core.exceptions import AppError, app_error_handler, generic_error_handler
from core.limiter import limiter
from middleware.cors import register_cors
from api.v1.router import router
from db.supabase import expire_pix_plans

get_settings()

_scheduler = BackgroundScheduler(timezone=timezone.utc)
_scheduler.add_job(
    expire_pix_plans,
    CronTrigger(hour=6, minute=0, timezone="America/Sao_Paulo"),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _scheduler.start()
    yield
    _scheduler.shutdown(wait=False)


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
    from db.supabase import get_admin
    try:
        result = get_admin().table("namespaces").select("namespace", count="exact").limit(1).execute()
        return JSONResponse({"status": "ok", "namespaces_total": result.count})
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)
