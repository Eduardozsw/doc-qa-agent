import json
from unittest.mock import MagicMock, patch

import pytest

from agent.context import _SEM_INFO
from agent.orchestrator import orchestrator, orchestrator_stream
from guardrails.validator import CitacaoVerificada, Verification


def _eventos(linhas: list[str]) -> list[dict]:
    return [json.loads(l[len("data: "):]) for l in linhas if l.startswith("data: {")]


@pytest.fixture(autouse=True)
def mock_cache(monkeypatch):
    """Cache semântico (F5) desligado por padrão nos testes existentes: sem histórico
    nem summary ele fica habilitado por padrão (settings), então sem este mock todo
    teste aqui chamaria embed_text/Postgres de verdade. `lookup` devolve None (miss)
    para não mudar o comportamento dos testes que já existiam antes da F5."""
    mock_embed = MagicMock(return_value=[0.1] * 1536)
    mock_lookup = MagicMock(return_value=None)
    mock_store = MagicMock()
    monkeypatch.setattr("agent.orchestrator.embed_text", mock_embed)
    monkeypatch.setattr("agent.orchestrator.query_cache_db.lookup", mock_lookup)
    monkeypatch.setattr("agent.orchestrator.query_cache_db.store", mock_store)
    return {"embed": mock_embed, "lookup": mock_lookup, "store": mock_store}


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
    assert resultado["trace_id"] is None  # sem Langfuse configurado nos testes


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


@patch("agent.orchestrator.choose_model")
@patch("agent.orchestrator.verify")
@patch("agent.orchestrator.answer")
@patch("agent.orchestrator.search")
@patch("agent.orchestrator.rewrite_query")
def test_conflito_ids_not_cited_keep_original_ids(mock_rewrite, mock_search, mock_answer, mock_verify, mock_choose_model):
    """Se a interseção com os ids citados `[n]` ficar vazia, o conflito mantém os
    ids como vieram do verificador em vez de sumir do payload."""
    mock_rewrite.return_value = "query reescrita"
    mock_search.return_value = [
        (0.9, "u1_aa_protocolo_a.pdf", "meta 130/80", None),
        (0.9, "u1_bb_protocolo_b.pdf", "meta 140/90", None),
    ]
    mock_answer.return_value = ("resposta que só cita o trecho 1 [1]", MagicMock())
    mock_choose_model.return_value = "gpt-4o-mini"
    mock_verify.return_value = Verification(
        fundamentada=True, correcao=False,
        citacoes=[CitacaoVerificada(id=1, trecho="meta 130/80", verificada=True)],
        conflitos=[{"ids": [2], "descricao": "Conflito envolvendo um trecho não citado."}],
    )

    resultado = orchestrator("pergunta", namespaces=["ns"], plan="pro")

    assert resultado["conflitos"] == [{"ids": [2], "descricao": "Conflito envolvendo um trecho não citado."}]


@patch("agent.orchestrator.choose_model")
@patch("agent.orchestrator.verify")
@patch("agent.orchestrator.answer")
@patch("agent.orchestrator.search")
@patch("agent.orchestrator.rewrite_query")
def test_payload_includes_modelo_and_conflitos(mock_rewrite, mock_search, mock_answer, mock_verify, mock_choose_model):
    mock_rewrite.return_value = "query reescrita"
    mock_search.return_value = [
        (0.9, "u1_aa_protocolo_a.pdf", "meta 130/80", 1),
        (0.9, "u1_bb_protocolo_b.pdf", "meta 140/90", 1),
    ]
    mock_answer.return_value = ("o documento A diz X [1]; o documento B diz Y [2]", MagicMock())
    mock_choose_model.return_value = "gpt-4o"
    mock_verify.return_value = Verification(
        fundamentada=True, correcao=False,
        citacoes=[
            CitacaoVerificada(id=1, trecho="meta 130/80", verificada=True),
            CitacaoVerificada(id=2, trecho="meta 140/90", verificada=True),
        ],
        conflitos=[{"ids": [1, 2], "descricao": "Os protocolos divergem sobre a meta pressórica."}],
    )

    resultado = orchestrator("pergunta", namespaces=["ns"], plan="pro")

    assert resultado["modelo"] == "gpt-4o"
    assert resultado["conflitos"] == [
        {"ids": [1, 2], "descricao": "Os protocolos divergem sobre a meta pressórica."}
    ]


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


@patch("agent.orchestrator.choose_model")
@patch("agent.orchestrator.verify")
@patch("agent.orchestrator.answer_stream")
@patch("agent.orchestrator.search")
@patch("agent.orchestrator.rewrite_query")
def test_stream_payload_includes_modelo_and_conflitos(
    mock_rewrite, mock_search, mock_answer_stream, mock_verify, mock_choose_model
):
    mock_rewrite.return_value = "query"
    mock_search.return_value = [
        (0.9, "u1_aa_protocolo_a.pdf", "meta 130/80", None),
        (0.9, "u1_bb_protocolo_b.pdf", "meta 140/90", None),
    ]
    mock_answer_stream.return_value = iter(["o documento A diz X [1]; ", "o documento B diz Y [2]"])
    mock_choose_model.return_value = "gpt-4o"
    mock_verify.return_value = Verification(
        fundamentada=True, correcao=False,
        citacoes=[
            CitacaoVerificada(id=1, trecho="meta 130/80", verificada=True),
            CitacaoVerificada(id=2, trecho="meta 140/90", verificada=True),
        ],
        conflitos=[{"ids": [1, 2], "descricao": "Os protocolos divergem sobre a meta pressórica."}],
    )

    linhas = list(orchestrator_stream("pergunta", namespaces=["ns"], plan="free"))
    eventos = _eventos(linhas)
    done = next(e for e in eventos if e["type"] == "done")

    assert done["modelo"] == "gpt-4o"
    assert done["conflitos"] == [
        {"ids": [1, 2], "descricao": "Os protocolos divergem sobre a meta pressórica."}
    ]


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


# --------------------------------------------------------------------------- #
# Cache semântico (F5): só é consultado sem histórico/summary.
# --------------------------------------------------------------------------- #

@patch("agent.orchestrator.verify")
@patch("agent.orchestrator.answer")
@patch("agent.orchestrator.search")
@patch("agent.orchestrator.rewrite_query")
def test_cache_hit_short_circuits_orchestrator(mock_rewrite, mock_search, mock_answer, mock_verify, mock_cache):
    cached_payload = {
        "resposta": "resposta em cache [1]",
        "fontes": ["doc.pdf"],
        "citacoes": [{
            "id": 1, "documento": "doc.pdf", "namespace": "u1_ab_doc.pdf",
            "pagina": None, "trecho": "texto1", "verificada": True,
        }],
        "correcao": False,
    }
    mock_cache["lookup"].return_value = cached_payload

    resultado = orchestrator("pergunta", namespaces=["ns"], plan="pro")

    assert resultado["cached"] is True
    assert resultado["resposta"] == "resposta em cache [1]"
    assert resultado["fontes"] == ["doc.pdf"]
    mock_rewrite.assert_not_called()
    mock_search.assert_not_called()
    mock_answer.assert_not_called()
    mock_verify.assert_not_called()
    mock_cache["embed"].assert_called_once_with("pergunta")
    mock_cache["lookup"].assert_called_once_with("ns", [0.1] * 1536, min_score=0.97)


@patch("agent.orchestrator.verify")
@patch("agent.orchestrator.answer")
@patch("agent.orchestrator.search")
@patch("agent.orchestrator.rewrite_query")
def test_cache_miss_stores_successful_result(mock_rewrite, mock_search, mock_answer, mock_verify, mock_cache):
    mock_rewrite.return_value = "query reescrita"
    mock_search.return_value = [(0.9, "u1_ab_doc.pdf", "texto1", None)]
    mock_answer.return_value = ("resposta com base [1]", MagicMock())
    mock_verify.return_value = Verification(
        fundamentada=True, correcao=False,
        citacoes=[CitacaoVerificada(id=1, trecho="texto1", verificada=True)],
    )

    resultado = orchestrator("pergunta", namespaces=["ns"], plan="pro")

    mock_cache["store"].assert_called_once()
    args, kwargs = mock_cache["store"].call_args
    namespaces_key, namespaces, embedding, query, payload = args[:5]
    assert namespaces_key == "ns"
    assert namespaces == ["ns"]
    assert query == "pergunta"
    assert payload["resposta"] == resultado["resposta"]
    assert "trace_id" not in payload
    assert "cached" not in payload
    assert kwargs["ttl_hours"] == 24


@patch("agent.orchestrator.verify")
@patch("agent.orchestrator.answer")
@patch("agent.orchestrator.search")
@patch("agent.orchestrator.rewrite_query")
def test_cache_skipped_when_historico_present(mock_rewrite, mock_search, mock_answer, mock_verify, mock_cache):
    mock_rewrite.return_value = "query reescrita"
    mock_search.return_value = [(0.9, "u1_ab_doc.pdf", "texto1", None)]
    mock_answer.return_value = ("resposta com base [1]", MagicMock())
    mock_verify.return_value = Verification(
        fundamentada=True, correcao=False,
        citacoes=[CitacaoVerificada(id=1, trecho="texto1", verificada=True)],
    )

    orchestrator(
        "pergunta", namespaces=["ns"], plan="pro",
        historico=[{"pergunta": "oi", "resposta": "tudo bem"}],
    )

    mock_cache["embed"].assert_not_called()
    mock_cache["lookup"].assert_not_called()
    mock_cache["store"].assert_not_called()


@patch("agent.orchestrator.verify")
@patch("agent.orchestrator.answer")
@patch("agent.orchestrator.search")
@patch("agent.orchestrator.rewrite_query")
def test_use_cache_false_skips_lookup_and_store(mock_rewrite, mock_search, mock_answer, mock_verify, mock_cache):
    """Evals passam use_cache=False: nem consulta nem grava, mesmo sem histórico/summary
    (senão a 2ª rodada de uma pergunta repetida viria do cache e não mediria nada)."""
    mock_rewrite.return_value = "query reescrita"
    mock_search.return_value = [(0.9, "u1_ab_doc.pdf", "texto1", None)]
    mock_answer.return_value = ("resposta com base [1]", MagicMock())
    mock_verify.return_value = Verification(
        fundamentada=True, correcao=False,
        citacoes=[CitacaoVerificada(id=1, trecho="texto1", verificada=True)],
    )

    orchestrator("pergunta", namespaces=["ns"], plan="pro", use_cache=False)

    mock_cache["embed"].assert_not_called()
    mock_cache["lookup"].assert_not_called()
    mock_cache["store"].assert_not_called()


@patch("agent.orchestrator.verify")
@patch("agent.orchestrator.answer_stream")
@patch("agent.orchestrator.search")
@patch("agent.orchestrator.rewrite_query")
def test_stream_cache_hit_short_circuits(mock_rewrite, mock_search, mock_answer_stream, mock_verify, mock_cache):
    cached_payload = {
        "resposta": "resposta em cache [1]",
        "fontes": ["doc.pdf"],
        "citacoes": [],
        "correcao": False,
    }
    mock_cache["lookup"].return_value = cached_payload

    linhas = list(orchestrator_stream("pergunta", namespaces=["ns"], plan="free"))
    eventos = _eventos(linhas)
    tipos = [e["type"] for e in eventos]

    assert tipos.count("chunk") == 1
    chunk = next(e for e in eventos if e["type"] == "chunk")
    assert chunk["text"] == "resposta em cache [1]"

    done = next(e for e in eventos if e["type"] == "done")
    assert done["cached"] is True
    assert done["blocked"] is False
    assert done["resposta"] == "resposta em cache [1]"

    mock_rewrite.assert_not_called()
    mock_search.assert_not_called()
    mock_answer_stream.assert_not_called()
    mock_verify.assert_not_called()


@patch("agent.orchestrator.verify")
@patch("agent.orchestrator.answer_stream")
@patch("agent.orchestrator.search")
@patch("agent.orchestrator.rewrite_query")
def test_stream_cache_miss_stores_result(mock_rewrite, mock_search, mock_answer_stream, mock_verify, mock_cache):
    mock_rewrite.return_value = "query"
    mock_search.return_value = [(0.9, "u1_ab_doc.pdf", "texto1", None)]
    mock_answer_stream.return_value = iter(["resposta ", "com [1]"])
    mock_verify.return_value = Verification(
        fundamentada=True, correcao=False,
        citacoes=[CitacaoVerificada(id=1, trecho="texto1", verificada=True)],
    )

    list(orchestrator_stream("pergunta", namespaces=["ns"], plan="free"))

    mock_cache["store"].assert_called_once()
    args, _kwargs = mock_cache["store"].call_args
    assert args[0] == "ns"
    assert args[3] == "pergunta"
