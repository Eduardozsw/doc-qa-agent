def test_save_and_get_document(db, demo_user):
    from db.documents import get_document, save_document

    save_document("ns1", demo_user["id"], "protocolo.pdf", b"%PDF-1.4 conteudo")

    assert get_document("ns1", demo_user["id"]) == ("protocolo.pdf", b"%PDF-1.4 conteudo")


def test_get_document_returns_none_for_missing_namespace(db, demo_user):
    from db.documents import get_document

    assert get_document("inexistente", demo_user["id"]) is None


def test_get_document_returns_none_for_other_user(db, demo_user):
    from db.documents import get_document, save_document
    from db.users import create_user

    save_document("ns1", demo_user["id"], "protocolo.pdf", b"conteudo")
    outro = create_user("outro-documents@teste.com", "senha1234")

    assert get_document("ns1", outro["id"]) is None


def test_save_document_upserts_by_namespace(db, demo_user):
    from db.documents import get_document, save_document

    save_document("ns1", demo_user["id"], "v1.pdf", b"conteudo-v1")
    save_document("ns1", demo_user["id"], "v2.pdf", b"conteudo-v2")

    assert get_document("ns1", demo_user["id"]) == ("v2.pdf", b"conteudo-v2")


def test_delete_document_removes_row(db, demo_user):
    from db.documents import delete_document, get_document, save_document

    save_document("ns1", demo_user["id"], "protocolo.pdf", b"conteudo")
    delete_document("ns1")

    assert get_document("ns1", demo_user["id"]) is None


def test_delete_document_does_not_raise_for_missing_namespace(db):
    from db.documents import delete_document

    delete_document("nao-existe")
