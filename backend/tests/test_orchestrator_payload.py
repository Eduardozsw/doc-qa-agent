import json
from unittest.mock import MagicMock, patch

from agent.context import _SEM_INFO
from agent.orchestrator import orchestrator, orchestrator_stream
from guardrails.validator import CitacaoVerificada, Verification


def _eventos(linhas: list[str]) -> list[dict]:
    return [json.loads(l[len("data: "):]) for l in linhas if l.startswith("data: {")]


@patch("agent.orchestrator.verify")
@patch("agent.orchestrator.answer")
@patch("agent.orchestrator.search")
@patch("agent.orchestrator.rewrite_query")
def test_payload_with_page_number(mock_rewrite, mock_search, mock_answer, mock_verify):
    mock_rewrite.return_value = "query reescrita"
    mock_search.return_value = [(0.9, "u1_ab_protocolo.pdf", "texto1", 12)]
    mock_answer.return_value = ("resposta com base [1]", MagicMock())
    mock_verify.return_value = Verification(
        fundamentada=True, correcao=False,
        citacoes=[CitacaoVerificada(id=1, trecho="texto1", verificada=True)],
    )

    resultado = orchestrator("pergunta", namespaces=["ns"], plan="pro")

    assert resultado["resposta"] == "resposta com base [1]"
    assert resultado["fontes"] == ["protocolo.pdf (p. 12)"]
    assert resultado["citacoes"] == [{
        "id": 1, "documento": "protocolo.pdf", "namespace": "u1_ab_protocolo.pdf",
        "pagina": 12, "trecho": "texto1", "verificada": True,
    }]
    assert resultado["correcao"] is False


@patch("agent.orchestrator.verify")
@patch("agent.orchestrator.answer")
@patch("agent.orchestrator.search")
@patch("agent.orchestrator.rewrite_query")
def test_payload_without_page_number(mock_rewrite, mock_search, mock_answer, mock_verify):
    mock_rewrite.return_value = "query reescrita"
    mock_search.return_value = [(0.9, "u1_ab_protocolo.pdf", "texto1", 12)]
    mock_answer.return_value = ("resposta com base [1]", MagicMock())
    mock_verify.return_value = Verification(
        fundamentada=True, correcao=False,
        citacoes=[CitacaoVerificada(id=1, trecho="texto1", verificada=True)],
    )

    resultado = orchestrator("pergunta", namespaces=["ns"], plan="free")

    assert resultado["fontes"] == ["protocolo.pdf"]
    assert resultado["citacoes"][0]["pagina"] is None


@patch("agent.orchestrator.verify")
@patch("agent.orchestrator.answer")
@patch("agent.orchestrator.search")
@patch("agent.orchestrator.rewrite_query")
def test_blocks_when_response_has_no_citation_markers(mock_rewrite, mock_search, mock_answer, mock_verify):
    mock_rewrite.return_value = "query"
    mock_search.return_value = [(0.9, "u1_ab_doc.pdf", "texto1", None)]
    mock_answer.return_value = ("resposta sem nenhuma citação", MagicMock())
    mock_verify.return_value = Verification(fundamentada=True, correcao=False, citacoes=[])

    resultado = orchestrator("pergunta", namespaces=["ns"], plan="pro")

    assert resultado["resposta"] == _SEM_INFO
    assert resultado["fontes"] == []
    assert resultado["citacoes"] == []
    assert resultado["correcao"] is False


@patch("agent.orchestrator.verify")
@patch("agent.orchestrator.answer")
@patch("agent.orchestrator.search")
@patch("agent.orchestrator.rewrite_query")
def test_blocks_when_verification_not_fundamentada(mock_rewrite, mock_search, mock_answer, mock_verify):
    mock_rewrite.return_value = "query"
    mock_search.return_value = [(0.9, "u1_ab_doc.pdf", "texto1", None)]
    mock_answer.return_value = ("resposta com citação [1]", MagicMock())
    mock_verify.return_value = Verification(fundamentada=False, correcao=False, citacoes=[])

    resultado = orchestrator("pergunta", namespaces=["ns"], plan="pro")

    assert resultado["resposta"] == _SEM_INFO
    assert resultado["citacoes"] == []


@patch("agent.orchestrator.verify")
@patch("agent.orchestrator.answer")
@patch("agent.orchestrator.search")
@patch("agent.orchestrator.rewrite_query")
def test_sem_info_is_not_blocked_and_has_empty_citations(mock_rewrite, mock_search, mock_answer, mock_verify):
    mock_rewrite.return_value = "query"
    mock_search.return_value = [(0.9, "u1_ab_doc.pdf", "texto1", None)]
    mock_answer.return_value = (_SEM_INFO, MagicMock())
    mock_verify.return_value = Verification(fundamentada=True, correcao=False, citacoes=[])

    resultado = orchestrator("pergunta", namespaces=["ns"], plan="pro")

    assert resultado["resposta"] == _SEM_INFO
    assert resultado["fontes"] == []
    assert resultado["citacoes"] == []


@patch("agent.orchestrator.verify")
@patch("agent.orchestrator.answer_stream")
@patch("agent.orchestrator.search")
@patch("agent.orchestrator.rewrite_query")
def test_stream_payload_includes_citacoes_and_correcao(mock_rewrite, mock_search, mock_answer_stream, mock_verify):
    mock_rewrite.return_value = "query"
    mock_search.return_value = [(0.9, "u1_ab_doc.pdf", "texto1", None)]
    mock_answer_stream.return_value = iter(["resposta ", "com [1]"])
    mock_verify.return_value = Verification(
        fundamentada=True, correcao=True,
        citacoes=[CitacaoVerificada(id=1, trecho="texto1", verificada=True)],
    )

    linhas = list(orchestrator_stream("pergunta", namespaces=["ns"], plan="free"))
    eventos = _eventos(linhas)
    done = next(e for e in eventos if e["type"] == "done")

    assert done["resposta"] == "resposta com [1]"
    assert done["blocked"] is False
    assert done["correcao"] is True
    assert done["citacoes"] == [{
        "id": 1, "documento": "doc.pdf", "namespace": "u1_ab_doc.pdf",
        "pagina": None, "trecho": "texto1", "verificada": True,
    }]


@patch("agent.orchestrator.verify")
@patch("agent.orchestrator.answer_stream")
@patch("agent.orchestrator.search")
@patch("agent.orchestrator.rewrite_query")
def test_stream_blocks_without_citation_markers(mock_rewrite, mock_search, mock_answer_stream, mock_verify):
    mock_rewrite.return_value = "query"
    mock_search.return_value = [(0.9, "u1_ab_doc.pdf", "texto1", None)]
    mock_answer_stream.return_value = iter(["resposta sem citação"])
    mock_verify.return_value = Verification(fundamentada=True, correcao=False, citacoes=[])

    linhas = list(orchestrator_stream("pergunta", namespaces=["ns"], plan="free"))
    eventos = _eventos(linhas)
    done = next(e for e in eventos if e["type"] == "done")

    assert done["blocked"] is True
    assert done["fontes"] == []
    assert done["citacoes"] == []
    assert done["correcao"] is False


@patch("agent.orchestrator.verify")
@patch("agent.orchestrator.answer_stream")
@patch("agent.orchestrator.search")
@patch("agent.orchestrator.rewrite_query")
def test_stream_emits_status_event_on_retry(mock_rewrite, mock_search, mock_answer_stream, mock_verify):
    mock_rewrite.return_value = "query"
    mock_search.return_value = [(0.9, "u1_ab_doc.pdf", "texto1", None)]
    mock_answer_stream.return_value = iter(["resposta ", "com [1]"])

    def fake_verify(query, chunks, resposta, historico=None, summary="", on_retry=None):
        if on_retry:
            on_retry(2)
        return Verification(
            fundamentada=True, correcao=False,
            citacoes=[CitacaoVerificada(id=1, trecho="texto1", verificada=True)],
        )

    mock_verify.side_effect = fake_verify

    linhas = list(orchestrator_stream("pergunta", namespaces=["ns"], plan="free"))
    eventos = _eventos(linhas)
    tipos = [e["type"] for e in eventos]

    assert "status" in tipos
    status = next(e for e in eventos if e["type"] == "status")
    assert "demorando mais que o normal" in status["text"]
    assert tipos[-1] == "done"
