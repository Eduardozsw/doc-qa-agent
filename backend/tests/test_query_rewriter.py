import json
from unittest.mock import MagicMock, patch

from agent.query_rewriter import expand_query


def _make_response(reformulacoes: list[str]):
    choice = MagicMock()
    choice.message.content = json.dumps({"reformulacoes": reformulacoes})
    response = MagicMock()
    response.choices = [choice]
    return response


@patch("agent.query_rewriter.client")
def test_expand_query_retorna_reformulacoes(mock_client):
    mock_client.chat.completions.create.return_value = _make_response(["variante 1", "variante 2"])

    resultado = expand_query("qual a PA alvo?")

    assert resultado == ["variante 1", "variante 2"]


@patch("agent.query_rewriter.client")
def test_expand_query_limita_a_tres(mock_client):
    mock_client.chat.completions.create.return_value = _make_response(["a", "b", "c", "d"])

    resultado = expand_query("pergunta")

    assert len(resultado) == 3


@patch("agent.query_rewriter.client")
def test_expand_query_excecao_retorna_lista_vazia(mock_client):
    mock_client.chat.completions.create.side_effect = Exception("timeout")

    assert expand_query("pergunta") == []
