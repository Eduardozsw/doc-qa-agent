from unittest.mock import patch

from evals.retrieval import evaluate_retrieval


def _fake_retrieve(query, top_k, namespaces):
    if query == "q1":
        # página relevante (5) aparece na 2ª posição
        return [(0.9, "ns", "t1", 1), (0.8, "ns", "t2", 5), (0.7, "ns", "t3", 2)]
    if query == "q2":
        # página relevante (10) aparece na 5ª posição
        return [
            (0.95, "ns", "t1", 1),
            (0.90, "ns", "t2", 2),
            (0.85, "ns", "t3", 3),
            (0.80, "ns", "t4", 4),
            (0.75, "ns", "t5", 10),
            (0.70, "ns", "t6", 6),
        ]
    return []


@patch("evals.retrieval.retrieve")
def test_evaluate_retrieval_calcula_hit_at_k_e_mrr(mock_retrieve):
    mock_retrieve.side_effect = _fake_retrieve
    cases = [
        {"query": "q1", "paginas_relevantes": [5, 6]},
        {"query": "q2", "paginas_relevantes": [10]},
    ]

    metricas = evaluate_retrieval(cases, namespace="ns")

    # q1: acerto na posição 2 -> hit@3/5/8 = 1, RR = 1/2
    # q2: acerto na posição 5 -> hit@3 = 0, hit@5/8 = 1, RR = 1/5
    assert metricas["hit@3"] == 0.5
    assert metricas["hit@5"] == 1.0
    assert metricas["hit@8"] == 1.0
    assert metricas["mrr"] == (0.5 + 0.2) / 2


@patch("evals.retrieval.retrieve")
def test_evaluate_retrieval_ignora_casos_sem_paginas_relevantes(mock_retrieve):
    mock_retrieve.side_effect = _fake_retrieve
    cases = [
        {"query": "q1", "paginas_relevantes": [5]},
        {"query": "fora do documento"},
    ]

    metricas = evaluate_retrieval(cases, namespace="ns")

    assert mock_retrieve.call_count == 1
    mock_retrieve.assert_called_once_with("q1", top_k=10, namespaces=["ns"])
    assert metricas["hit@3"] == 1.0


@patch("evals.retrieval.retrieve")
def test_evaluate_retrieval_sem_nenhum_caso_valido_retorna_zeros(mock_retrieve):
    cases = [{"query": "fora do documento"}]

    metricas = evaluate_retrieval(cases, namespace="ns")

    mock_retrieve.assert_not_called()
    assert metricas == {"hit@3": 0.0, "hit@5": 0.0, "hit@8": 0.0, "mrr": 0.0}


@patch("evals.retrieval.retrieve")
def test_evaluate_retrieval_sem_acerto_no_top_k_da_mrr_zero(mock_retrieve):
    mock_retrieve.return_value = [(0.9, "ns", "t1", 1), (0.8, "ns", "t2", 2)]
    cases = [{"query": "q", "paginas_relevantes": [99]}]

    metricas = evaluate_retrieval(cases, namespace="ns")

    assert metricas["hit@3"] == 0.0
    assert metricas["mrr"] == 0.0
