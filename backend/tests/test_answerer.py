import pytest
from unittest.mock import MagicMock, patch


def _chunk(texto: str, namespace: str = "u1_ab_contrato.pdf", pagina: int | None = None, score: float = 0.9):
    return (score, namespace, texto, pagina)


def _make_response(text="resposta gerada"):
    choice = MagicMock()
    choice.message.content = text
    response = MagicMock()
    response.choices = [choice]
    response.usage = MagicMock(prompt_tokens=100, completion_tokens=50)
    return response


def _make_empty_response():
    response = MagicMock()
    response.choices = []
    response.usage = MagicMock(prompt_tokens=10, completion_tokens=0)
    return response


@patch("agent.answerer.client")
def test_basic_answer(mock_client):
    mock_client.chat.completions.create.return_value = _make_response("prazo é 30 dias [1]")
    from agent.answerer import answer
    result, _ = answer("qual o prazo?", [_chunk("O prazo é 30 dias conforme cláusula 3.")])
    assert result == "prazo é 30 dias [1]"


@patch("agent.answerer.client")
def test_uses_configured_chat_model(mock_client):
    mock_client.chat.completions.create.return_value = _make_response()
    from agent.answerer import answer
    from core.config import get_settings
    answer("query", [_chunk("chunk")])
    assert mock_client.chat.completions.create.call_args.kwargs["model"] == get_settings().openai_chat_model


@patch("agent.answerer.client")
def test_max_tokens_is_1500(mock_client):
    mock_client.chat.completions.create.return_value = _make_response()
    from agent.answerer import answer
    answer("query", [_chunk("chunk")])
    assert mock_client.chat.completions.create.call_args.kwargs["max_tokens"] == 1500


@patch("agent.answerer.client")
def test_historico_truncated_to_last_10(mock_client):
    mock_client.chat.completions.create.return_value = _make_response()
    from agent.answerer import answer
    historico = [{"pergunta": f"p{i}", "resposta": f"r{i}"} for i in range(15)]
    answer("nova pergunta", [_chunk("chunk")], historico=historico)
    messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
    history_messages = [m for m in messages if m["role"] in ("user", "assistant")][:-1]
    assert len(history_messages) <= 20  # 10 turnos × 2 mensagens


@patch("agent.answerer.client")
def test_historico_keeps_last_not_first(mock_client):
    mock_client.chat.completions.create.return_value = _make_response()
    from agent.answerer import answer
    historico = [{"pergunta": f"p{i}", "resposta": f"r{i}"} for i in range(15)]
    answer("nova pergunta", [_chunk("chunk")], historico=historico)
    messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
    user_msgs = [m["content"] for m in messages if m["role"] == "user"]
    assert "p14" in user_msgs  # último turno, não "p0"
    assert "p0" not in user_msgs


@patch("agent.answerer.client")
def test_historico_empty_items_skipped(mock_client):
    mock_client.chat.completions.create.return_value = _make_response()
    from agent.answerer import answer
    historico = [
        {"pergunta": "", "resposta": "ok"},
        {"pergunta": "valida", "resposta": ""},
        {"pergunta": "boa", "resposta": "resposta"},
    ]
    answer("query", [_chunk("chunk")], historico=historico)
    messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
    user_msgs = [m["content"] for m in messages if m["role"] == "user"]
    assert "boa" in user_msgs


@patch("agent.answerer.client")
def test_historico_over_limit_chars_skipped(mock_client):
    mock_client.chat.completions.create.return_value = _make_response()
    from agent.answerer import answer
    historico = [
        {"pergunta": "a" * 2001, "resposta": "ok"},
        {"pergunta": "normal", "resposta": "ok"},
    ]
    answer("query", [_chunk("chunk")], historico=historico)
    messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
    user_msgs = [m["content"] for m in messages if m["role"] == "user"]
    assert not any(len(m) > 2000 for m in user_msgs[:-1])


@patch("agent.answerer.client")
def test_non_dict_historico_items_skipped(mock_client):
    mock_client.chat.completions.create.return_value = _make_response()
    from agent.answerer import answer
    historico = ["string invalida", 42, None, {"pergunta": "valida", "resposta": "ok"}]
    answer("query", [_chunk("chunk")], historico=historico)
    messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
    user_msgs = [m["content"] for m in messages if m["role"] == "user"]
    assert "valida" in user_msgs


@patch("agent.answerer.client")
def test_empty_content_raises(mock_client):
    mock_client.chat.completions.create.return_value = _make_empty_response()
    from agent.answerer import answer
    with pytest.raises(ValueError, match="inesperada"):
        answer("query", [_chunk("chunk")])


@patch("agent.answerer.client")
def test_multiple_chunks_joined_in_context(mock_client):
    mock_client.chat.completions.create.return_value = _make_response()
    from agent.answerer import answer
    answer("query", [_chunk("chunk1"), _chunk("chunk2"), _chunk("chunk3")])
    messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
    content = messages[-1]["content"]
    assert "chunk1" in content
    assert "chunk2" in content
    assert "chunk3" in content


@patch("agent.answerer.client")
def test_context_includes_documento_e_pagina(mock_client):
    mock_client.chat.completions.create.return_value = _make_response()
    from agent.answerer import answer
    answer("query", [_chunk("texto", namespace="u1_ab_protocolo.pdf", pagina=12)])
    messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
    content = messages[-1]["content"]
    assert 'documento="protocolo.pdf"' in content
    assert 'pagina="12"' in content
