"""Funções puras de métrica usadas pelo benchmark (`run.py`) e testadas sem rede
em `tests/test_benchmark_metrics.py`. Nada aqui importa módulos de produção nem
faz chamadas de rede — todas as entradas já vêm computadas por quem chama
(instrumented.py, cost.py) como dicts/listas simples.
"""
import math
import statistics

# Preços em US$ por 1M tokens. Conferir em https://openai.com/api/pricing — valores
# registrados em 2026-09-18 (gpt-4o-mini entrada/saída, gpt-4o entrada/saída,
# text-embedding-3-small entrada; embeddings não têm tokens de "saída" cobrados).
PRICES_PER_1M_USD = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "text-embedding-3-small": {"input": 0.02, "output": 0.0},
}


def percentile(values: list[float], p: float) -> float:
    """Percentil `p` (0-100) por interpolação linear entre postos (método comum a
    numpy.percentile/Excel). Lista vazia devolve 0.0."""
    if not values:
        return 0.0
    ordenados = sorted(values)
    if len(ordenados) == 1:
        return ordenados[0]
    posicao = (len(ordenados) - 1) * (p / 100)
    piso, teto = math.floor(posicao), math.ceil(posicao)
    if piso == teto:
        return ordenados[int(posicao)]
    return ordenados[piso] + (ordenados[teto] - ordenados[piso]) * (posicao - piso)


def mean_std(values: list[float]) -> tuple[float, float]:
    """Média e desvio-padrão AMOSTRAL (ddof=1). Com 0 ou 1 valor, desvio = 0.0."""
    if not values:
        return 0.0, 0.0
    media = statistics.mean(values)
    desvio = statistics.stdev(values) if len(values) > 1 else 0.0
    return media, desvio


def latency_summary(timings_ms: dict[str, list[float]]) -> dict:
    """p50/p95 (ms) por etapa, agregando TODAS as chamadas recebidas (todas as
    repetições e casos de uma config) — não por repetição."""
    return {
        etapa: {"p50": percentile(valores, 50), "p95": percentile(valores, 95), "n": len(valores)}
        for etapa, valores in timings_ms.items()
    }


def reciprocal_rank(paginas_ranqueadas: list[int], paginas_relevantes: list[int]) -> float:
    for posicao, pagina in enumerate(paginas_ranqueadas, start=1):
        if pagina in paginas_relevantes:
            return 1 / posicao
    return 0.0


def hit_at_k(paginas_ranqueadas: list[int], paginas_relevantes: list[int], k: int) -> float:
    return 1.0 if any(p in paginas_relevantes for p in paginas_ranqueadas[:k]) else 0.0


_CORTES_HIT = (1, 3, 5)


def retrieval_metrics(cases: list[dict]) -> dict:
    """`cases`: lista de {"ranked_pages": [...], "relevant_pages": [...]}, já filtrada
    para só os casos que têm página relevante conhecida (factual/premissa_falsa).
    Devolve hit@1/3/5 e MRR médios, com `n` explícito."""
    n = len(cases)
    if n == 0:
        return {f"hit@{k}": 0.0 for k in _CORTES_HIT} | {"mrr": 0.0, "n": 0}

    hits = {k: [] for k in _CORTES_HIT}
    mrrs = []
    for caso in cases:
        ranqueadas, relevantes = caso["ranked_pages"], caso["relevant_pages"]
        for k in _CORTES_HIT:
            hits[k].append(hit_at_k(ranqueadas, relevantes, k))
        mrrs.append(reciprocal_rank(ranqueadas, relevantes))

    resultado = {f"hit@{k}": sum(v) / n for k, v in hits.items()}
    resultado["mrr"] = sum(mrrs) / n
    resultado["n"] = n
    return resultado


def quality_metrics(cases: list[dict]) -> dict:
    """`cases`: cada item tem `tipo` (factual/premissa_falsa/fora_do_documento),
    `score` (nota 0-1 do juiz, ou None se o caso falhou), `abstained` (bool — a
    resposta final foi a frase de "não encontrei"), `correcao` (bool) e `citacoes`
    (lista de {"verificada": bool}). Toda taxa vem com `_n`/`_total` explícitos."""
    julgados = [c for c in cases if c.get("score") is not None]
    n_julgados = len(julgados)
    media_nota = sum(c["score"] for c in julgados) / n_julgados if n_julgados else 0.0
    acertos = sum(1 for c in julgados if c["score"] >= 0.7)

    premissa = [c for c in cases if c.get("tipo") == "premissa_falsa"]
    correcoes = sum(1 for c in premissa if c.get("correcao"))

    fora = [c for c in cases if c.get("tipo") == "fora_do_documento"]
    abstencoes = sum(1 for c in fora if c.get("abstained"))
    alucinacoes = len(fora) - abstencoes

    factuais = [c for c in cases if c.get("tipo") == "factual"]
    falsas_abstencoes = sum(1 for c in factuais if c.get("abstained"))

    elegiveis = [c for c in cases if c.get("tipo") != "fora_do_documento" and not c.get("abstained")]
    com_citacao_verificada = sum(1 for c in elegiveis if any(cit.get("verificada") for cit in c.get("citacoes", [])))
    total_citacoes = sum(len(c.get("citacoes", [])) for c in elegiveis)
    citacoes_verificadas = sum(sum(1 for cit in c.get("citacoes", []) if cit.get("verificada")) for c in elegiveis)

    return {
        "avg_score": media_nota, "avg_score_n": n_julgados,
        "accuracy": acertos / n_julgados if n_julgados else 0.0, "accuracy_n": acertos, "accuracy_total": n_julgados,
        "correction_rate": correcoes / len(premissa) if premissa else 0.0,
        "correction_n": correcoes, "correction_total": len(premissa),
        "abstain_correct_rate": abstencoes / len(fora) if fora else 0.0,
        "abstain_correct_n": abstencoes, "abstain_correct_total": len(fora),
        "hallucination_rate": alucinacoes / len(fora) if fora else 0.0,
        "hallucination_n": alucinacoes, "hallucination_total": len(fora),
        "false_abstention_rate": falsas_abstencoes / len(factuais) if factuais else 0.0,
        "false_abstention_n": falsas_abstencoes, "false_abstention_total": len(factuais),
        "cited_rate": com_citacao_verificada / len(elegiveis) if elegiveis else 0.0,
        "cited_n": com_citacao_verificada, "cited_total": len(elegiveis),
        "citation_precision": citacoes_verificadas / total_citacoes if total_citacoes else 0.0,
        "citations_verified": citacoes_verificadas, "citations_total": total_citacoes,
    }


_RATE_KEYS = [
    "avg_score", "accuracy", "correction_rate", "abstain_correct_rate",
    "hallucination_rate", "false_abstention_rate", "cited_rate", "citation_precision",
]


def quality_variability(per_rep_cases: list[list[dict]]) -> dict:
    """Média ± desvio-padrão, ENTRE repetições, de cada taxa de `quality_metrics`.
    `per_rep_cases`: uma lista de casos por repetição."""
    por_rep = [quality_metrics(casos) for casos in per_rep_cases]
    return {chave: dict(zip(("mean", "std"), mean_std([r[chave] for r in por_rep]))) for chave in _RATE_KEYS}


def retrieval_variability(per_rep_cases: list[list[dict]]) -> dict:
    por_rep = [retrieval_metrics(casos) for casos in per_rep_cases]
    chaves = [f"hit@{k}" for k in _CORTES_HIT] + ["mrr"]
    return {chave: dict(zip(("mean", "std"), mean_std([r[chave] for r in por_rep]))) for chave in chaves}


def cost_usd(usage_by_model: dict[str, dict[str, int]], prices: dict = PRICES_PER_1M_USD) -> dict:
    """`usage_by_model`: {"gpt-4o-mini": {"input": N, "output": N}, ...} (tokens brutos).
    Devolve custo por modelo e total, em US$. Modelo desconhecido não é precificado
    (custo 0), mas os tokens continuam reportados."""
    por_modelo = {}
    total = 0.0
    for modelo, uso in usage_by_model.items():
        preco = prices.get(modelo, {"input": 0.0, "output": 0.0})
        entrada, saida = uso.get("input", 0), uso.get("output", 0)
        custo = entrada / 1_000_000 * preco["input"] + saida / 1_000_000 * preco["output"]
        por_modelo[modelo] = {"input_tokens": entrada, "output_tokens": saida, "cost_usd": custo}
        total += custo
    return {"per_model": por_modelo, "total_cost_usd": total}


def cost_per_question(total_cost_usd: float, n_questions: int) -> dict:
    por_pergunta = total_cost_usd / n_questions if n_questions else 0.0
    return {"usd_per_question": por_pergunta, "usd_per_1000": por_pergunta * 1000}


def diff_usage(before: dict[str, dict[str, int]], after: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
    """Delta de uso entre dois snapshots cumulativos de `CostTracker` (ver cost.py).
    Só inclui modelos com delta não-nulo."""
    resultado = {}
    for modelo in set(before) | set(after):
        b = before.get(modelo, {"input": 0, "output": 0})
        a = after.get(modelo, {"input": 0, "output": 0})
        d_in, d_out = a.get("input", 0) - b.get("input", 0), a.get("output", 0) - b.get("output", 0)
        if d_in or d_out:
            resultado[modelo] = {"input": d_in, "output": d_out}
    return resultado


def merge_usage(*usages: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
    """Soma vários dicts de uso por modelo (ex.: uso de todos os casos de uma config)."""
    total: dict[str, dict[str, int]] = {}
    for uso in usages:
        for modelo, valores in uso.items():
            acumulado = total.setdefault(modelo, {"input": 0, "output": 0})
            acumulado["input"] += valores.get("input", 0)
            acumulado["output"] += valores.get("output", 0)
    return total


def format_pct(rate: float, n: int, total: int) -> str:
    """Formata como "93% (28/30)", exigido no relatório para deixar o N explícito."""
    return f"{rate * 100:.0f}% ({n}/{total})"
