from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


class NotFoundError(AppError):
    def __init__(self, detail: str = "Recurso não encontrado"):
        super().__init__(404, detail)


class ForbiddenError(AppError):
    def __init__(self, detail: str = "Sem permissão"):
        super().__init__(403, detail)


class FileTooLargeError(AppError):
    def __init__(self, max_mb: int):
        super().__init__(413, f"Arquivo excede o limite de {max_mb}MB")


class UnsupportedFileTypeError(AppError):
    def __init__(self, filename: str):
        super().__init__(415, f"'{filename}' não é um PDF")


class SlotLimitError(AppError):
    def __init__(self, available: int):
        super().__init__(400, f"Você pode adicionar no máximo {available} arquivo(s)")


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Erro interno: {type(exc).__name__}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor"})
