import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.exceptions import AppError, ForbiddenError, NotFoundError
from ingestion.drive_client import download_drive_file

SMALL_PDF = b"%PDF-1.4 fake content"


def _make_mock_client(status_code: int, content: bytes = b"") -> AsyncMock:
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.content = content
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


@pytest.mark.asyncio
async def test_download_drive_file_success():
    mock_client = _make_mock_client(200, SMALL_PDF)

    with patch("ingestion.drive_client.httpx.AsyncClient", return_value=mock_client):
        result = await download_drive_file("file123", "token_abc")

    assert result == SMALL_PDF
    mock_client.get.assert_called_once_with(
        "https://www.googleapis.com/drive/v3/files/file123?alt=media",
        headers={"Authorization": "Bearer token_abc"},
        follow_redirects=True,
        timeout=30.0,
    )


@pytest.mark.asyncio
async def test_download_drive_file_raises_401():
    mock_client = _make_mock_client(401)

    with patch("ingestion.drive_client.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(AppError) as exc_info:
            await download_drive_file("file123", "bad_token")

    assert exc_info.value.status_code == 401
    assert "expirado" in exc_info.value.detail


@pytest.mark.asyncio
async def test_download_drive_file_raises_403():
    mock_client = _make_mock_client(403)

    with patch("ingestion.drive_client.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(ForbiddenError) as exc_info:
            await download_drive_file("file123", "token_abc")

    assert exc_info.value.status_code == 403
    assert "permissão" in exc_info.value.detail


@pytest.mark.asyncio
async def test_download_drive_file_raises_404():
    mock_client = _make_mock_client(404)

    with patch("ingestion.drive_client.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(NotFoundError) as exc_info:
            await download_drive_file("file123", "token_abc")

    assert exc_info.value.status_code == 404
    assert "encontrado" in exc_info.value.detail
