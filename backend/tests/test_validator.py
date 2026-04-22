import pytest
from unittest.mock import MagicMock, patch
from anthropic.types import Usage


def _make_usage():
    return Usage(input_tokens=10, output_tokens=5)


def _make_message(text: str):
    from anthropic.types import TextBlock, Message
    block = MagicMock(spec=TextBlock)
    block.text = text
    msg = MagicMock()
    msg.content = [block]
    msg.usage = _make_usage()
    return msg


def _make_empty_message():
    msg = MagicMock()
    msg.content = []
    msg.usage = _make_usage()
    return msg


@patch("guardrails.validator.client")
def test_sim_returns_true(mock_client):
    mock_client.messages.create.return_value = _make_message("sim")
    from guardrails.validator import validate
    result, _ = validate("pergunta", ["chunk"], "resposta")
    assert result is True


@patch("guardrails.validator.client")
def test_nao_returns_false(mock_client):
    mock_client.messages.create.return_value = _make_message("não")
    from guardrails.validator import validate
    result, _ = validate("pergunta", ["chunk"], "resposta")
    assert result is False


@patch("guardrails.validator.client")
def test_sim_uppercase_returns_true(mock_client):
    mock_client.messages.create.return_value = _make_message("Sim")
    from guardrails.validator import validate
    result, _ = validate("pergunta", ["chunk"], "resposta")
    assert result is True


@patch("guardrails.validator.client")
def test_sim_with_period_returns_true(mock_client):
    mock_client.messages.create.return_value = _make_message("sim.")
    from guardrails.validator import validate
    result, _ = validate("pergunta", ["chunk"], "resposta")
    assert result is True


@patch("guardrails.validator.client")
def test_ambiguous_nao_sim_returns_false(mock_client):
    mock_client.messages.create.return_value = _make_message("não consigo responder sim ou não")
    from guardrails.validator import validate
    result, _ = validate("pergunta", ["chunk"], "resposta")
    assert result is False


@patch("guardrails.validator.client")
def test_empty_content_returns_false(mock_client):
    mock_client.messages.create.return_value = _make_empty_message()
    from guardrails.validator import validate
    result, _ = validate("pergunta", ["chunk"], "resposta")
    assert result is False


@patch("guardrails.validator.client")
def test_unexpected_response_returns_false(mock_client):
    mock_client.messages.create.return_value = _make_message("talvez")
    from guardrails.validator import validate
    result, _ = validate("pergunta", ["chunk"], "resposta")
    assert result is False


@patch("guardrails.validator.client")
def test_usage_returned(mock_client):
    mock_client.messages.create.return_value = _make_message("sim")
    from guardrails.validator import validate
    _, usage = validate("pergunta", ["chunk"], "resposta")
    assert usage is not None
