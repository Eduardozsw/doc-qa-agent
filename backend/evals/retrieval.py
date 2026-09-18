from agent.retriever import retrieve

_CORTES = (3, 5, 8)


def evaluate_retrieval(cases: list[dict], namespace: str, top_k: int = 10) -> dict:
    """Calcula hit@3, hit@5, hit@8 e MRR médios sobre os casos com `paginas_relevantes`.

    Casos sem `paginas_relevantes` (fora do documento, sem resposta clara etc.) são ignorados.
    """
    hits = {corte: [] for corte in _CORTES}
    mrrs = []

    for caso in cases:
        paginas_relevantes = caso.get("paginas_relevantes")
        if not paginas_relevantes:
            continue

        resultados = retrieve(caso["query"], top_k=top_k, namespaces=[namespace])
        paginas_ranqueadas = [pagina for _, _, _, pagina in resultados]

        for corte in _CORTES:
            acertou = any(pagina in paginas_relevantes for pagina in paginas_ranqueadas[:corte])
            hits[corte].append(1.0 if acertou else 0.0)

        mrrs.append(_reciprocal_rank(paginas_ranqueadas, paginas_relevantes))

    if not mrrs:
        return {f"hit@{corte}": 0.0 for corte in _CORTES} | {"mrr": 0.0}

    metricas = {f"hit@{corte}": sum(valores) / len(valores) for corte, valores in hits.items()}
    metricas["mrr"] = sum(mrrs) / len(mrrs)
    return metricas


def _reciprocal_rank(paginas_ranqueadas: list[int], paginas_relevantes: list[int]) -> float:
    for posicao, pagina in enumerate(paginas_ranqueadas, start=1):
        if pagina in paginas_relevantes:
            return 1 / posicao
    return 0.0
