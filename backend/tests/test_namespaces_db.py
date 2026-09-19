import pytest

from db.namespaces import (
    add_namespace,
    count_namespaces,
    count_summaries_this_month,
    get_namespace_by_sha256,
    get_namespaces,
    get_namespaces_with_summaries,
    get_summary,
    remove_namespace,
    save_summary,
)
from db.users import create_user


@pytest.fixture
def user_id(db):
    user = create_user("namespaces@teste.com", "senha1234", "Fulano")
    return user["id"]


@pytest.mark.db
def test_add_and_get_namespaces(user_id):
    add_namespace(user_id, "ns1", "sha1", "doc1.pdf")
    add_namespace(user_id, "ns2", "sha2", "doc2.pdf")

    namespaces = get_namespaces(user_id)
    assert set(namespaces) == {"ns1", "ns2"}


@pytest.mark.db
def test_count_namespaces(user_id):
    assert count_namespaces(user_id) == 0
    add_namespace(user_id, "ns1", "sha1", "doc1.pdf")
    assert count_namespaces(user_id) == 1


@pytest.mark.db
def test_get_namespace_by_sha256(user_id):
    add_namespace(user_id, "ns1", "sha-abc", "doc1.pdf")
    assert get_namespace_by_sha256(user_id, "sha-abc") == "ns1"
    assert get_namespace_by_sha256(user_id, "sha-inexistente") is None


@pytest.mark.db
def test_remove_namespace(user_id):
    add_namespace(user_id, "ns1", "sha1", "doc1.pdf")
    remove_namespace(user_id, "ns1")
    assert get_namespaces(user_id) == []


@pytest.mark.db
def test_save_and_get_summary(user_id):
    add_namespace(user_id, "ns1", "sha1", "doc1.pdf")
    assert get_summary(user_id, "ns1") is None

    summary = {"topicos_abordados": ["a", "b"], "resumo": "texto do resumo"}
    save_summary(user_id, "ns1", summary)

    result = get_summary(user_id, "ns1")
    assert result == summary


@pytest.mark.db
def test_count_summaries_this_month(user_id):
    add_namespace(user_id, "ns1", "sha1", "doc1.pdf")
    add_namespace(user_id, "ns2", "sha2", "doc2.pdf")

    assert count_summaries_this_month(user_id) == 0

    save_summary(user_id, "ns1", {"topicos_abordados": [], "resumo": "x"})
    assert count_summaries_this_month(user_id) == 1

    save_summary(user_id, "ns2", {"topicos_abordados": [], "resumo": "y"})
    assert count_summaries_this_month(user_id) == 2


@pytest.mark.db
def test_get_namespaces_with_summaries(user_id):
    add_namespace(user_id, "ns1", "sha1", "doc1.pdf")
    add_namespace(user_id, "ns2", "sha2", "doc2.pdf")
    save_summary(user_id, "ns1", {"topicos_abordados": ["x"], "resumo": "y"})

    result = get_namespaces_with_summaries(user_id)
    assert len(result) == 1
    assert result[0]["namespace"] == "ns1"
    assert result[0]["summary"] == {"topicos_abordados": ["x"], "resumo": "y"}
