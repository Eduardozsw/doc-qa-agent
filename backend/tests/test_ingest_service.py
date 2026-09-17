import pytest
from unittest.mock import patch
from core.exceptions import ForbiddenError

# Pre-import process_file_job at module level to avoid reload issues
from services.ingest import process_file_job

USER_ID = "user-abc"


@pytest.mark.asyncio
async def test_list_files_returns_user_namespaces():
    with patch("services.ingest.supabase_db.get_namespaces", return_value=["doc1.pdf"]):
        from services.ingest import list_files
        result = await list_files(USER_ID)
    assert result == ["doc1.pdf"]


@pytest.mark.asyncio
async def test_remove_files_owned_succeeds():
    with patch("services.ingest.supabase_db.get_namespaces", return_value=["doc.pdf"]):
        with patch("services.ingest.supabase_db.get_sha256_for_namespace", return_value="abc123"):
            with patch("services.ingest.supabase_db.remove_namespace") as mock_remove:
                with patch("services.ingest.redis_db.delete_cached_namespace") as mock_del_cache:
                    from services.ingest import remove_files
                    await remove_files(USER_ID, ["doc.pdf"])
    mock_remove.assert_called_once_with(USER_ID, "doc.pdf")
    mock_del_cache.assert_called_once_with("abc123", USER_ID)


@pytest.mark.asyncio
async def test_remove_files_not_owned_raises():
    with patch("services.ingest.supabase_db.get_namespaces", return_value=["meu.pdf"]):
        from services.ingest import remove_files
        with pytest.raises(ForbiddenError):
            await remove_files(USER_ID, ["alheio.pdf"])


def test_process_file_job_success():
    job = {
        "job_id": "test-id",
        "user_id": USER_ID,
        "filename": "doc.pdf",
        "namespace": "user_sha_doc",
        "sha256": "abc123",
        "plan": "free",
    }
    with patch("services.ingest.supabase_db.download_temp_file", return_value=b"%PDF-fake"):
        with patch("services.ingest.supabase_db.delete_temp_file"):
            with patch("services.ingest.load_pages_from_bytes", return_value=[(1, "texto")]):
                with patch("services.ingest.chunk_pages", return_value=[("chunk1", 1)]):
                    with patch("services.ingest.upsert_chunks"):
                        with patch("services.ingest.supabase_db.add_namespace") as mock_add:
                            with patch("services.ingest.redis_db.set_cached_namespace"):
                                process_file_job(job)
    mock_add.assert_called_once_with(USER_ID, "user_sha_doc", "abc123", "doc.pdf")


def test_process_file_job_deletes_temp_on_error():
    job = {
        "job_id": "test-id",
        "user_id": USER_ID,
        "filename": "bad.pdf",
        "namespace": "user_sha_bad",
        "sha256": "abc123",
        "plan": "free",
    }
    with patch("services.ingest.supabase_db.download_temp_file", return_value=b"%PDF-fake"):
        with patch("services.ingest.supabase_db.delete_temp_file") as mock_delete:
            with patch("services.ingest.load_pages_from_bytes", side_effect=Exception("erro")):
                with pytest.raises(RuntimeError):
                    process_file_job(job)
    mock_delete.assert_called_once_with("test-id")


def test_process_file_job_wraps_pdf_read_error_as_runtime():
    job = {
        "job_id": "test-id",
        "user_id": USER_ID,
        "filename": "corrupto.pdf",
        "namespace": "user_sha_x",
        "sha256": "abc123",
        "plan": "free",
    }
    with patch("services.ingest.supabase_db.download_temp_file", return_value=b"%PDF-fake"):
        with patch("services.ingest.supabase_db.delete_temp_file"):
            with patch("services.ingest.load_pages_from_bytes", side_effect=Exception("fitz error")):
                with pytest.raises(RuntimeError, match="corrompido"):
                    process_file_job(job)


def test_process_file_job_wraps_upsert_error_as_runtime():
    job = {
        "job_id": "test-id",
        "user_id": USER_ID,
        "filename": "doc.pdf",
        "namespace": "user_sha_doc",
        "sha256": "abc123",
        "plan": "free",
    }
    with patch("services.ingest.supabase_db.download_temp_file", return_value=b"%PDF-fake"):
        with patch("services.ingest.supabase_db.delete_temp_file"):
            with patch("services.ingest.load_pages_from_bytes", return_value=[(1, "texto")]):
                with patch("services.ingest.chunk_pages", return_value=[("chunk1", 1)]):
                    with patch("services.ingest.upsert_chunks", side_effect=Exception("pinecone error")):
                        with pytest.raises(RuntimeError, match="salvar"):
                            process_file_job(job)
