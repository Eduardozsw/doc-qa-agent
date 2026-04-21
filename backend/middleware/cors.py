from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import get_settings


def register_cors(app: FastAPI) -> None:
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
        allow_credentials=True,
    )
