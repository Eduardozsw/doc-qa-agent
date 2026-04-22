import pytest
from unittest.mock import patch, AsyncMock
from core.exceptions import ForbiddenError
from models.requests import QueryRequest
from services.query import handle_query


USER_ID = "user-123"


def _make_request(namespaces=None, query="qual o prazo?", historico=None):
    return QueryRequest(
        query=query,
        namespaces=namespaces or [],
        historico=historico or [],
    )


@pytest.mark.asyncio
async def test_query_with_owned_namespaces_succeeds():
    req = _make_request(namespaces=["contrato.pdf"])
    with patch("services.query.redis_db.get_namespaces", return_value=["contrato.pdf"]):
        with patch("services.query.orchestrator", return_value={"resposta": "30 dias", "fontes": ["contrato.pdf"]}):
            result = await handle_query(USER_ID, req)
    assert result["resposta"] == "30 dias"


@pytest.mark.asyncio
async def test_query_with_unauthorized_namespace_raises():
    req = _make_request(namespaces=["outro-user.pdf"])
    with patch("services.query.redis_db.get_namespaces", return_value=["meu-doc.pdf"]):
        with pytest.raises(ForbiddenError):
            await handle_query(USER_ID, req)


@pytest.mark.asyncio
async def test_query_with_empty_namespaces_skips_check():
    req = _make_request(namespaces=[])
    with patch("services.query.redis_db.get_namespaces") as mock_redis:
        with patch("services.query.orchestrator", return_value={"resposta": "ok", "fontes": []}):
            await handle_query(USER_ID, req)
    mock_redis.assert_not_called()


@pytest.mark.asyncio
async def test_query_passes_none_namespaces_to_orchestrator():
    req = _make_request(namespaces=[])
    with patch("services.query.orchestrator") as mock_orch:
        mock_orch.return_value = {"resposta": "ok", "fontes": []}
        await handle_query(USER_ID, req)
    assert mock_orch.call_args.kwargs["namespaces"] is None


@pytest.mark.asyncio
async def test_query_passes_historico_as_dicts():
    req = _make_request(historico=[{"pergunta": "antes?", "resposta": "sim"}])
    with patch("services.query.orchestrator") as mock_orch:
        mock_orch.return_value = {"resposta": "ok", "fontes": []}
        await handle_query(USER_ID, req)
    historico = mock_orch.call_args.kwargs["historico"]
    assert isinstance(historico[0], dict)
    assert historico[0]["pergunta"] == "antes?"


@pytest.mark.asyncio
async def test_query_partial_unauthorized_namespaces_raises():
    req = _make_request(namespaces=["meu.pdf", "alheio.pdf"])
    with patch("services.query.redis_db.get_namespaces", return_value=["meu.pdf"]):
        with pytest.raises(ForbiddenError):
            await handle_query(USER_ID, req)
