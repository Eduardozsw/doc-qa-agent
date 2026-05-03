import httpx

from core.exceptions import AppError, ForbiddenError, NotFoundError

_DOWNLOAD_URL = "https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"


async def download_drive_file(file_id: str, access_token: str) -> bytes:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _DOWNLOAD_URL.format(file_id=file_id),
            headers={"Authorization": f"Bearer {access_token}"},
            follow_redirects=True,
            timeout=30.0,
        )
        if response.status_code == 401:
            raise AppError(401, "Token do Google Drive inválido ou expirado.")
        if response.status_code == 403:
            raise ForbiddenError("Sem permissão para acessar este arquivo do Drive.")
        if response.status_code == 404:
            raise NotFoundError("Arquivo não encontrado no Drive.")
        response.raise_for_status()
        return response.content
