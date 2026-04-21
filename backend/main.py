from fastapi import FastAPI
from core.exceptions import AppError, app_error_handler, generic_error_handler
from middleware.cors import register_cors
from api.v1.router import router

app = FastAPI(title="doc-qa-agent", version="1.0.0")

register_cors(app)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

app.include_router(router)
