import pytest

from db.uploads import delete_temp_file, download_temp_file, upload_temp_file


@pytest.mark.db
def test_upload_and_download_roundtrip(db):
    upload_temp_file("job-1", b"%PDF-conteudo-fake")
    result = download_temp_file("job-1")
    assert result == b"%PDF-conteudo-fake"


@pytest.mark.db
def test_upload_overwrites_existing_job_id(db):
    upload_temp_file("job-2", b"conteudo-antigo")
    upload_temp_file("job-2", b"conteudo-novo")
    assert download_temp_file("job-2") == b"conteudo-novo"


@pytest.mark.db
def test_download_missing_job_raises(db):
    with pytest.raises(FileNotFoundError):
        download_temp_file("job-inexistente")


@pytest.mark.db
def test_delete_temp_file_removes_it(db):
    upload_temp_file("job-3", b"dados")
    delete_temp_file("job-3")
    with pytest.raises(FileNotFoundError):
        download_temp_file("job-3")


@pytest.mark.db
def test_delete_temp_file_idempotent(db):
    delete_temp_file("job-nao-existe")
    delete_temp_file("job-nao-existe")
