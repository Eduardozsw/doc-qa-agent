from fastapi.testclient import TestClient

from core.security import create_token
from db.documents import save_document
from db.users import create_user
from main import app


def _client():
    return TestClient(app)


def _token(user) -> str:
    return create_token(user["id"], user["email"])


def test_get_pdf_returns_200_with_content_for_owner(db, demo_user):
    save_document("ns1", demo_user["id"], "protocolo.pdf", b"%PDF-1.4 conteudo")

    with _client() as c:
        resp = c.get("/api/files/ns1/pdf", headers={"Authorization": f"Bearer {_token(demo_user)}"})

    assert resp.status_code == 200
    assert resp.content == b"%PDF-1.4 conteudo"
    assert resp.headers["content-type"] == "application/pdf"
    assert 'filename="protocolo.pdf"' in resp.headers["content-disposition"]


def test_get_pdf_returns_404_for_other_users_namespace(db, demo_user):
    save_document("ns1", demo_user["id"], "protocolo.pdf", b"conteudo")
    outro = create_user("outro-pdf@teste.com", "senha1234")

    with _client() as c:
        resp = c.get("/api/files/ns1/pdf", headers={"Authorization": f"Bearer {_token(outro)}"})

    assert resp.status_code == 404


def test_get_pdf_returns_404_for_nonexistent_namespace(db, demo_user):
    with _client() as c:
        resp = c.get("/api/files/inexistente/pdf", headers={"Authorization": f"Bearer {_token(demo_user)}"})

    assert resp.status_code == 404


def test_get_pdf_requires_auth(db, demo_user):
    save_document("ns1", demo_user["id"], "protocolo.pdf", b"conteudo")

    with _client() as c:
        resp = c.get("/api/files/ns1/pdf")

    assert resp.status_code in (401, 422)
