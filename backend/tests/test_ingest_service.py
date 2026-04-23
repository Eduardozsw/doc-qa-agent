import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile
from core.exceptions import ForbiddenError, FileTooLargeError, UnsupportedFileTypeError


USER_ID = "user-abc"
SMALL_PDF = b"%PDF-1.4 fake content"


def _make_upload(filename="doc.pdf", content_type="application/pdf", data=SMALL_PDF):
    file = MagicMock(spec=UploadFile)
    file.filename = filename
    file.content_type = content_type
    file.read = AsyncMock(return_value=data)
    return file


@pytest.mark.asyncio
async def test_list_files_returns_user_namespaces():
    with patch("services.ingest.redis_db.get_namespaces", return_value=["doc1.pdf"]):
        from services.ingest import list_files
        result = await list_files(USER_ID)
    assert result == ["doc1.pdf"]


@pytest.mark.asyncio
async def test_remove_files_owned_succeeds():
    with patch("services.ingest.redis_db.get_namespaces", return_value=["doc.pdf"]):
        with patch("services.ingest.delete_namespace") as mock_del:
            with patch("services.ingest.redis_db.remove_namespace") as mock_rem:
                from services.ingest import remove_files
                await remove_files(USER_ID, ["doc.pdf"])
    mock_del.assert_called_once_with("doc.pdf")
    mock_rem.assert_called_once_with(USER_ID, "doc.pdf")


@pytest.mark.asyncio
async def test_remove_files_not_owned_raises():
    with patch("services.ingest.redis_db.get_namespaces", return_value=["meu.pdf"]):
        from services.ingest import remove_files
        with pytest.raises(ForbiddenError):
            await remove_files(USER_ID, ["alheio.pdf"])


@pytest.mark.asyncio
async def test_ingest_rejects_non_pdf():
    file = _make_upload(filename="doc.txt", content_type="text/plain")
    with patch("services.ingest.redis_db.get_namespaces", return_value=[]):
        from services.ingest import ingest_files
        with pytest.raises(UnsupportedFileTypeError):
            await ingest_files(USER_ID, [file])


@pytest.mark.asyncio
async def test_ingest_rejects_oversized_file():
    big_content = b"x" * (51 * 1024 * 1024)
    file = _make_upload(data=big_content)
    with patch("services.ingest.redis_db.get_namespaces", return_value=[]):
        from services.ingest import ingest_files
        with pytest.raises(FileTooLargeError):
            await ingest_files(USER_ID, [file])


@pytest.mark.asyncio
async def test_ingest_uses_cache_on_duplicate():
    file = _make_upload()
    with patch("services.ingest.redis_db.get_namespaces", return_value=[]):
        with patch("services.ingest.redis_db.get_cached_namespace", return_value="doc.pdf"):
            with patch("services.ingest.redis_db.add_namespace") as mock_add:
                with patch("services.ingest.load_pages_from_bytes") as mock_load:
                    from services.ingest import ingest_files
                    added, chunks = await ingest_files(USER_ID, [file])
    mock_load.assert_not_called()
    mock_add.assert_called_once()
    assert chunks == 0


@pytest.mark.asyncio
async def test_ingest_new_file_processes_and_caches():
    file = _make_upload()
    with patch("services.ingest.redis_db.get_namespaces", return_value=[]):
        with patch("services.ingest.redis_db.get_cached_namespace", return_value=None):
            with patch("services.ingest.load_pages_from_bytes", return_value=[(1, "texto do pdf")]):
                with patch("services.ingest.chunk_pages", return_value=[("chunk1", 1), ("chunk2", 1)]):
                    with patch("services.ingest.upsert_chunks"):
                        with patch("services.ingest.redis_db.set_cached_namespace") as mock_cache:
                            with patch("services.ingest.redis_db.add_namespace"):
                                from services.ingest import ingest_files
                                added, total = await ingest_files(USER_ID, [file])
    mock_cache.assert_called_once()
    assert total == 2


@pytest.mark.asyncio
async def test_ingest_raises_on_empty_text():
    file = _make_upload()
    with patch("services.ingest.redis_db.get_namespaces", return_value=[]):
        with patch("services.ingest.redis_db.get_cached_namespace", return_value=None):
            with patch("services.ingest.load_pages_from_bytes", return_value=[(1, "   ")]):
                from services.ingest import ingest_files
                with pytest.raises(Exception):
                    await ingest_files(USER_ID, [file])
