import pytest
from pydantic import ValidationError
from models.requests import HistoricoItem, QueryRequest, DeleteRequest


# --- HistoricoItem ---

def test_historico_item_valid():
    item = HistoricoItem(pergunta="qual o prazo?", resposta="30 dias")
    assert item.pergunta == "qual o prazo?"
    assert item.resposta == "30 dias"


def test_historico_item_empty_pergunta_raises():
    with pytest.raises(ValidationError):
        HistoricoItem(pergunta="", resposta="resposta")


def test_historico_item_whitespace_pergunta_raises():
    with pytest.raises(ValidationError):
        HistoricoItem(pergunta="   ", resposta="resposta")


def test_historico_item_empty_resposta_raises():
    with pytest.raises(ValidationError):
        HistoricoItem(pergunta="pergunta", resposta="")


def test_historico_item_pergunta_at_limit():
    item = HistoricoItem(pergunta="a" * 2000, resposta="ok")
    assert len(item.pergunta) == 2000


def test_historico_item_pergunta_over_limit_raises():
    with pytest.raises(ValidationError):
        HistoricoItem(pergunta="a" * 2001, resposta="ok")


def test_historico_item_resposta_at_limit():
    item = HistoricoItem(pergunta="ok", resposta="a" * 5000)
    assert len(item.resposta) == 5000


def test_historico_item_resposta_over_limit_raises():
    with pytest.raises(ValidationError):
        HistoricoItem(pergunta="ok", resposta="a" * 5001)


# --- QueryRequest ---

def test_query_request_valid():
    req = QueryRequest(query="o que diz o contrato?")
    assert req.query == "o que diz o contrato?"
    assert req.namespaces == []


def test_query_request_strips_whitespace():
    req = QueryRequest(query="  pergunta  ")
    assert req.query == "pergunta"


def test_query_request_empty_query_raises():
    with pytest.raises(ValidationError):
        QueryRequest(query="")


def test_query_request_whitespace_only_raises():
    with pytest.raises(ValidationError):
        QueryRequest(query="   ")


def test_query_request_at_limit():
    req = QueryRequest(query="a" * 5000)
    assert len(req.query) == 5000


def test_query_request_over_limit_raises():
    with pytest.raises(ValidationError):
        QueryRequest(query="a" * 5001)


# --- DeleteRequest ---

def test_delete_request_valid():
    req = DeleteRequest(namespaces=["doc1.pdf", "doc2.pdf"])
    assert req.namespaces == ["doc1.pdf", "doc2.pdf"]


def test_delete_request_empty_list_raises():
    with pytest.raises(ValidationError):
        DeleteRequest(namespaces=[])
