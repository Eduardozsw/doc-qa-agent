import pytest
from unittest.mock import MagicMock, patch


def _make_response(text: str):
    choice = MagicMock()
    choice.message.content = text
    response = MagicMock()
    response.choices = [choice]
    response.usage = MagicMock(prompt_tokens=10, completion_tokens=5)
    return response


def _make_empty_response():
    response = MagicMock()
    response.choices = []
    response.usage = MagicMock(prompt_tokens=10, completion_tokens=0)
    return response


@patch("guardrails.validator.client")
def test_sim_returns_true(mock_client):
    mock_client.chat.completions.create.return_value = _make_response("sim")
    from guardrails.validator import validate
    result, _ = validate("pergunta", ["chunk"], "resposta")
    assert result is True


@patch("guardrails.validator.client")
def test_nao_returns_false(mock_client):
    mock_client.chat.completions.create.return_value = _make_response("não")
    from guardrails.validator import validate
    result, _ = validate("pergunta", ["chunk"], "resposta")
    assert result is False


@patch("guardrails.validator.client")
def test_sim_uppercase_returns_true(mock_client):
    mock_client.chat.completions.create.return_value = _make_response("Sim")
    from guardrails.validator import validate
    result, _ = validate("pergunta", ["chunk"], "resposta")
    assert result is True


@patch("guardrails.validator.client")
def test_sim_with_period_returns_true(mock_client):
    mock_client.chat.completions.create.return_value = _make_response("sim.")
    from guardrails.validator import validate
    result, _ = validate("pergunta", ["chunk"], "resposta")
    assert result is True


@patch("guardrails.validator.client")
def test_ambiguous_nao_sim_returns_false(mock_client):
    mock_client.chat.completions.create.return_value = _make_response("não consigo responder sim ou não")
    from guardrails.validator import validate
    result, _ = validate("pergunta", ["chunk"], "resposta")
    assert result is False


@patch("guardrails.validator.client")
def test_empty_content_returns_false(mock_client):
    mock_client.chat.completions.create.return_value = _make_empty_response()
    from guardrails.validator import validate
    result, _ = validate("pergunta", ["chunk"], "resposta")
    assert result is False


@patch("guardrails.validator.client")
def test_unexpected_response_returns_false(mock_client):
    mock_client.chat.completions.create.return_value = _make_response("talvez")
    from guardrails.validator import validate
    result, _ = validate("pergunta", ["chunk"], "resposta")
    assert result is False


@patch("guardrails.validator.client")
def test_usage_returned(mock_client):
    mock_client.chat.completions.create.return_value = _make_response("sim")
    from guardrails.validator import validate
    _, usage = validate("pergunta", ["chunk"], "resposta")
    assert usage is not None
