import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_download_drive_file_success():
    pdf_bytes = b"%PDF-1.4 fake content"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = pdf_bytes
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("ingestion.drive_client.httpx.AsyncClient", return_value=mock_client):
        from ingestion.drive_client import download_drive_file
        result = await download_drive_file("file123", "token_abc")

    assert result == pdf_bytes
    mock_client.get.assert_called_once_with(
        "https://www.googleapis.com/drive/v3/files/file123?alt=media",
        headers={"Authorization": "Bearer token_abc"},
        follow_redirects=True,
        timeout=30.0,
    )


@pytest.mark.asyncio
async def test_download_drive_file_raises_401():
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("ingestion.drive_client.httpx.AsyncClient", return_value=mock_client):
        from ingestion.drive_client import download_drive_file
        with pytest.raises(HTTPException) as exc_info:
            await download_drive_file("file123", "bad_token")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_download_drive_file_raises_403():
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("ingestion.drive_client.httpx.AsyncClient", return_value=mock_client):
        from ingestion.drive_client import download_drive_file
        with pytest.raises(HTTPException) as exc_info:
            await download_drive_file("file123", "token_abc")

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_download_drive_file_raises_404():
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("ingestion.drive_client.httpx.AsyncClient", return_value=mock_client):
        from ingestion.drive_client import download_drive_file
        with pytest.raises(HTTPException) as exc_info:
            await download_drive_file("file123", "token_abc")

    assert exc_info.value.status_code == 404
