"""Testes sem rede das funções puras de métrica do benchmark (`benchmark/metrics.py`)
e da geração do markdown (`benchmark/report.py`) a partir de um JSON sintético."""
from benchmark import report
from benchmark.metrics import (
    cost_per_question,
    cost_usd,
    diff_usage,
    format_pct,
    latency_summary,
    mean_std,
    merge_usage,
    percentile,
    quality_metrics,
    quality_variability,
    retrieval_metrics,
    retrieval_variability,
)


def test_percentile_p50_e_p95():
    valores = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    assert percentile(valores, 50) == 55
    assert abs(percentile(valores, 95) - 95.5) < 1e-9


def test_percentile_lista_vazia_e_valor_unico():
    assert percentile([], 50) == 0.0
    assert percentile([42], 95) == 42


def test_mean_std_amostral():
    media, desvio = mean_std([2, 4, 4, 4, 5, 5, 7, 9])
    assert media == 5.0
    assert round(desvio, 4) == 2.1381


def test_mean_std_com_um_valor_desvio_zero():
    assert mean_std([7]) == (7.0, 0.0)
    assert mean_std([]) == (0.0, 0.0)


def test_hit_at_k_e_mrr():
    cases = [
        {"ranked_pages": [1, 5, 2], "relevant_pages": [5, 6]},  # acerta na posição 2 -> RR=0.5
        {"ranked_pages": [1, 2, 3, 4, 10], "relevant_pages": [10]},  # posição 5 -> RR=0.2
    ]
    metricas = retrieval_metrics(cases)
    assert metricas["n"] == 2
    assert metricas["hit@1"] == 0.0
    assert metricas["hit@3"] == 0.5
    assert metricas["hit@5"] == 1.0
    assert metricas["mrr"] == (0.5 + 0.2) / 2


def test_retrieval_metrics_lista_vazia():
    metricas = retrieval_metrics([])
    assert metricas == {"hit@1": 0.0, "hit@3": 0.0, "hit@5": 0.0, "mrr": 0.0, "n": 0}


def test_retrieval_variability_media_e_desvio_entre_repeticoes():
    rep1 = [{"ranked_pages": [1], "relevant_pages": [1]}]  # hit@1 = 1.0
    rep2 = [{"ranked_pages": [2], "relevant_pages": [1]}]  # hit@1 = 0.0
    variabilidade = retrieval_variability([rep1, rep2])
    assert variabilidade["hit@1"]["mean"] == 0.5
    assert variabilidade["hit@1"]["std"] > 0


def test_quality_metrics_classifica_abstencao_alucinacao_e_correcao():
    cases = [
        {"tipo": "factual", "score": 0.9, "abstained": False, "citacoes": [{"verificada": True}]},
        {"tipo": "factual", "score": 0.5, "abstained": False, "citacoes": [{"verificada": False}]},
        {"tipo": "factual", "score": 0.2, "abstained": True},  # falsa abstenção
        {"tipo": "premissa_falsa", "score": 1.0, "abstained": False, "correcao": True, "citacoes": [{"verificada": True}]},
        {"tipo": "premissa_falsa", "score": 0.3, "abstained": False, "correcao": False, "citacoes": []},
        {"tipo": "fora_do_documento", "score": 1.0, "abstained": True},  # abstenção correta
        {"tipo": "fora_do_documento", "score": 0.0, "abstained": False},  # alucinação
    ]
    m = quality_metrics(cases)

    assert m["avg_score_n"] == 7
    assert m["accuracy_n"] == 3  # notas >= 0.7: 0.9, 1.0, 1.0
    assert m["accuracy_total"] == 7
    assert format_pct(m["accuracy"], m["accuracy_n"], m["accuracy_total"]) == "43% (3/7)"

    assert m["correction_n"] == 1 and m["correction_total"] == 2
    assert m["abstain_correct_n"] == 1 and m["abstain_correct_total"] == 2
    assert m["hallucination_n"] == 1 and m["hallucination_total"] == 2
    assert m["false_abstention_n"] == 1 and m["false_abstention_total"] == 3

    # elegíveis p/ citação: factual/premissa_falsa não abstidos = 4 casos
    assert m["cited_total"] == 4
    assert m["cited_n"] == 2  # 2 dos 4 têm ao menos 1 citação verificada
    assert m["citations_total"] == 3
    assert m["citations_verified"] == 2


def test_quality_metrics_sem_casos_de_um_tipo_nao_quebra():
    cases = [{"tipo": "factual", "score": 0.8, "abstained": False, "citacoes": []}]
    m = quality_metrics(cases)
    assert m["correction_rate"] == 0.0 and m["correction_total"] == 0
    assert m["abstain_correct_rate"] == 0.0 and m["abstain_correct_total"] == 0


def test_quality_variability_media_desvio_entre_repeticoes():
    rep1 = [{"tipo": "factual", "score": 1.0, "abstained": False, "citacoes": []}]
    rep2 = [{"tipo": "factual", "score": 0.0, "abstained": False, "citacoes": []}]
    variabilidade = quality_variability([rep1, rep2])
    assert variabilidade["avg_score"]["mean"] == 0.5
    assert variabilidade["avg_score"]["std"] > 0


def test_cost_usd_calcula_por_modelo_e_total():
    uso = {
        "gpt-4o-mini": {"input": 1_000_000, "output": 1_000_000},
        "text-embedding-3-small": {"input": 1_000_000, "output": 0},
    }
    resultado = cost_usd(uso)
    assert round(resultado["per_model"]["gpt-4o-mini"]["cost_usd"], 4) == round(0.15 + 0.60, 4)
    assert round(resultado["per_model"]["text-embedding-3-small"]["cost_usd"], 4) == 0.02
    assert round(resultado["total_cost_usd"], 4) == round(0.15 + 0.60 + 0.02, 4)


def test_cost_usd_modelo_desconhecido_tem_custo_zero_mas_reporta_tokens():
    resultado = cost_usd({"modelo-novo": {"input": 500, "output": 500}})
    assert resultado["per_model"]["modelo-novo"]["cost_usd"] == 0.0
    assert resultado["per_model"]["modelo-novo"]["input_tokens"] == 500


def test_cost_per_question():
    resultado = cost_per_question(1.0, 1000)
    assert resultado["usd_per_question"] == 0.001
    assert resultado["usd_per_1000"] == 1.0
    assert cost_per_question(1.0, 0) == {"usd_per_question": 0.0, "usd_per_1000": 0.0}


def test_diff_usage_e_merge_usage():
    antes = {"gpt-4o-mini": {"input": 100, "output": 50}}
    depois = {"gpt-4o-mini": {"input": 150, "output": 80}, "gpt-4o": {"input": 10, "output": 5}}
    delta = diff_usage(antes, depois)
    assert delta == {"gpt-4o-mini": {"input": 50, "output": 30}, "gpt-4o": {"input": 10, "output": 5}}

    somado = merge_usage({"a": {"input": 1, "output": 1}}, {"a": {"input": 2, "output": 3}}, {"b": {"input": 5, "output": 0}})
    assert somado == {"a": {"input": 3, "output": 4}, "b": {"input": 5, "output": 0}}


def test_latency_summary_pooled():
    resumo = latency_summary({"search": [100, 200, 300], "answer": []})
    assert resumo["search"]["n"] == 3
    assert resumo["search"]["p50"] == 200
    assert resumo["answer"] == {"p50": 0.0, "p95": 0.0, "n": 0}


def test_format_pct():
    assert format_pct(0.9333, 28, 30) == "93% (28/30)"
    assert format_pct(0.0, 0, 10) == "0% (0/10)"


def _json_sintetico() -> dict:
    quality = quality_metrics([
        {"tipo": "factual", "score": 0.9, "abstained": False, "citacoes": [{"verificada": True}]},
        {"tipo": "fora_do_documento", "score": 1.0, "abstained": True},
    ])
    retrieval = retrieval_metrics([{"ranked_pages": [1, 2], "relevant_pages": [2]}])
    aggregated_full = {
        "quality": quality, "quality_variability": {}, "retrieval": retrieval, "retrieval_variability": {},
        "latency_ms": latency_summary({"search": [100, 150], "retrieve": [50], "answer": [300], "verify": [200], "total": [700]}),
        "cost": {**cost_usd({"gpt-4o-mini": {"input": 1000, "output": 500}}),
                 **cost_per_question(0.001, 2), "n_questions": 2,
                 "usd_per_question_variability": {"mean": 0.0005, "std": 0.0001}},
        "judge_cost_usd": 0.0001, "n_failed": 0, "n_total_attempts": 2,
    }
    aggregated_naive = {**aggregated_full, "retrieval": retrieval_metrics([{"ranked_pages": [9, 9], "relevant_pages": [2]}])}
    return {
        "generated_at": "2026-09-18T00:00:00",
        "environment": {
            "date": "2026-09-18", "commit": "abc1234", "cpu": "Intel Alder Lake", "ram_gb": 7.5,
            "models": {"chat": "gpt-4o-mini", "chat_strong": "gpt-4o", "embedding": "text-embedding-3-small"},
            "dataset_counts": {"factual": 1, "fora_do_documento": 1, "total": 2},
            "dataset_limit": None, "repeats": 1, "configs_run": ["naive", "full"],
        },
        "configs": {
            "naive": {"env": {}, "n_cases": 2, "reps": [], "aggregated": aggregated_naive},
            "full": {"env": {}, "n_cases": 2, "reps": [], "aggregated": aggregated_full},
        },
        "ingestion": None, "cache": None, "http": None,
    }


def test_generate_markdown_contem_secoes_e_numeros_com_n_explicito():
    markdown = report.generate_markdown(_json_sintetico())

    for titulo in ["# Benchmark", "## Metodologia", "## Ambiente", "## Qualidade", "## Recuperação",
                   "## Latência", "## Custo", "## Ingestão", "## Cache semântico", "## HTTP ponta a ponta",
                   "## Limitações", "## Como reproduzir"]:
        assert titulo in markdown

    quality = _json_sintetico()["configs"]["full"]["aggregated"]["quality"]
    esperado = format_pct(quality["accuracy"], quality["accuracy_n"], quality["accuracy_total"])
    assert esperado in markdown
    assert "naive" in markdown and "full" in markdown
    assert "Pulada nesta rodada" in markdown or "Pulado" in markdown or "Não medido" in markdown


def test_generate_markdown_sem_config_full_nao_quebra():
    dados = _json_sintetico()
    dados["configs"] = {}
    markdown = report.generate_markdown(dados)
    assert "Sem a config `full`" in markdown
