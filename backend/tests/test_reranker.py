import json
from unittest.mock import MagicMock, patch

from agent.reranker import _SYSTEM, rerank


def _candidatos(n: int) -> list[tuple]:
    return [(1.0 - i / 100, "ns", f"texto {i}", i) for i in range(n)]


def test_system_prompt_orienta_sobre_premissas():
    # Trechos que confirmam/contradizem uma premissa da pergunta (ex.: tabela de
    # valores de referência) precisam ser tratados como relevantes mesmo quando não
    # respondem diretamente à pergunta principal — regressão vista nas evals da F3.
    assert "premissa" in _SYSTEM.lower()


def _make_response(itens: list[dict]):
    choice = MagicMock()
    choice.message.content = json.dumps({"itens": itens})
    response = MagicMock()
    response.choices = [choice]
    return response


@patch("agent.reranker.client")
def test_reordena_por_relevancia_desc(mock_client):
    candidatos = _candidatos(3)
    # id 1 (texto 0) é o menos relevante; id 3 (texto 2) é o mais relevante
    mock_client.chat.completions.create.return_value = _make_response([
        {"id": 1, "relevancia": 0},
        {"id": 2, "relevancia": 2},
        {"id": 3, "relevancia": 3},
    ])

    resultado = rerank("pergunta", candidatos, top_k=2)

    assert [r[2] for r in resultado] == ["texto 2", "texto 1"]
    assert [r[0] for r in resultado] == [3, 2]  # score = relevância


@patch("agent.reranker.client")
def test_ids_ausentes_recebem_relevancia_zero(mock_client):
    candidatos = _candidatos(3)
    # só o id 2 aparece na resposta do LLM; ids 1 e 3 ficam com relevância 0
    mock_client.chat.completions.create.return_value = _make_response([
        {"id": 2, "relevancia": 1},
    ])

    resultado = rerank("pergunta", candidatos, top_k=3)

    assert resultado[0][2] == "texto 1"  # único com relevância > 0
    assert resultado[0][0] == 1
    # empate em relevância 0 entre id 1 e id 3: mantém ordem original
    assert [r[2] for r in resultado[1:]] == ["texto 0", "texto 2"]


@patch("agent.reranker.client")
def test_texto_truncado_em_1200_caracteres(mock_client):
    texto_longo = "a" * 2000
    candidatos = [(0.9, "ns", texto_longo, 1)]
    mock_client.chat.completions.create.return_value = _make_response([{"id": 1, "relevancia": 3}])

    rerank("pergunta", candidatos, top_k=1)

    mensagens = mock_client.chat.completions.create.call_args.kwargs["messages"]
    conteudo_usuario = mensagens[1]["content"]
    assert "a" * 1200 in conteudo_usuario
    assert "a" * 1201 not in conteudo_usuario


@patch("agent.reranker.client")
def test_excecao_faz_fail_open(mock_client):
    candidatos = _candidatos(5)
    mock_client.chat.completions.create.side_effect = Exception("timeout")

    resultado = rerank("pergunta", candidatos, top_k=3)

    assert resultado == candidatos[:3]


@patch("agent.reranker.client")
def test_json_invalido_faz_fail_open(mock_client):
    candidatos = _candidatos(4)
    choice = MagicMock()
    choice.message.content = "não é json"
    response = MagicMock()
    response.choices = [choice]
    mock_client.chat.completions.create.return_value = response

    resultado = rerank("pergunta", candidatos, top_k=2)

    assert resultado == candidatos[:2]
