from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from core.exceptions import AppError, app_error_handler, generic_error_handler
from core.limiter import limiter
from middleware.cors import register_cors
from api.v1.router import router
from fastapi import FastAPI

app = FastAPI(title="doc-qa-agent", version="1.0.0")
app.state.limiter = limiter

register_cors(app)

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

app.include_router(router)
