import pytest
from unittest.mock import MagicMock, patch
from anthropic.types import TextBlock


def _make_response(text="resposta gerada"):
    block = MagicMock(spec=TextBlock)
    block.text = text
    msg = MagicMock()
    msg.content = [block]
    msg.usage = MagicMock(input_tokens=100, output_tokens=50)
    return msg


@patch("agent.answerer.client")
def test_basic_answer(mock_client):
    mock_client.messages.create.return_value = _make_response("prazo é 30 dias")
    from agent.answerer import answer
    result, _ = answer("qual o prazo?", ["O prazo é 30 dias conforme cláusula 3."])
    assert result == "prazo é 30 dias"


@patch("agent.answerer.client")
def test_historico_truncated_to_10(mock_client):
    mock_client.messages.create.return_value = _make_response()
    from agent.answerer import answer
    historico = [{"pergunta": f"p{i}", "resposta": f"r{i}"} for i in range(15)]
    answer("nova pergunta", ["chunk"], historico=historico)
    messages = mock_client.messages.create.call_args.kwargs["messages"]
    history_messages = [m for m in messages if m["role"] in ("user", "assistant")][:-1]
    assert len(history_messages) <= 20  # 10 turnos × 2 mensagens


@patch("agent.answerer.client")
def test_historico_empty_items_skipped(mock_client):
    mock_client.messages.create.return_value = _make_response()
    from agent.answerer import answer
    historico = [
        {"pergunta": "", "resposta": "ok"},
        {"pergunta": "valida", "resposta": ""},
        {"pergunta": "boa", "resposta": "resposta"},
    ]
    answer("query", ["chunk"], historico=historico)
    messages = mock_client.messages.create.call_args.kwargs["messages"]
    user_msgs = [m["content"] for m in messages if m["role"] == "user"]
    assert "boa" in user_msgs


@patch("agent.answerer.client")
def test_historico_over_limit_chars_skipped(mock_client):
    mock_client.messages.create.return_value = _make_response()
    from agent.answerer import answer
    historico = [
        {"pergunta": "a" * 2001, "resposta": "ok"},
        {"pergunta": "normal", "resposta": "ok"},
    ]
    answer("query", ["chunk"], historico=historico)
    messages = mock_client.messages.create.call_args.kwargs["messages"]
    user_msgs = [m["content"] for m in messages if m["role"] == "user"]
    assert not any(len(m) > 2000 for m in user_msgs[:-1])


@patch("agent.answerer.client")
def test_non_dict_historico_items_skipped(mock_client):
    mock_client.messages.create.return_value = _make_response()
    from agent.answerer import answer
    historico = ["string invalida", 42, None, {"pergunta": "valida", "resposta": "ok"}]
    answer("query", ["chunk"], historico=historico)
    messages = mock_client.messages.create.call_args.kwargs["messages"]
    user_msgs = [m["content"] for m in messages if m["role"] == "user"]
    assert "valida" in user_msgs


@patch("agent.answerer.client")
def test_empty_content_raises(mock_client):
    msg = MagicMock()
    msg.content = []
    msg.usage = MagicMock()
    mock_client.messages.create.return_value = msg
    from agent.answerer import answer
    with pytest.raises(ValueError, match="inesperada"):
        answer("query", ["chunk"])


@patch("agent.answerer.client")
def test_multiple_chunks_joined_in_context(mock_client):
    mock_client.messages.create.return_value = _make_response()
    from agent.answerer import answer
    answer("query", ["chunk1", "chunk2", "chunk3"])
    content = mock_client.messages.create.call_args.kwargs["messages"][-1]["content"]
    assert "chunk1" in content
    assert "chunk2" in content
    assert "chunk3" in content
