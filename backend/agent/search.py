"""Pipeline completo de recuperação, usado pelo orchestrator (streaming e não) e
pelas evals — para medir o pipeline real, e não só o retrieve() cru.

Duas otimizações opcionais em cima do retrieve() híbrido (RRF vetorial + keyword):
- multi-query: perguntas curtas são ambíguas; gera até 3 reformulações e busca todas.
- rerank: um LLM listwise reordena os candidatos por relevância antes do corte final.
"""
from concurrent.futures import ThreadPoolExecutor

from agent.query_rewriter import expand_query
from agent.reranker import rerank
from agent.retriever import retrieve
from core import tracing
from core.config import Settings, get_settings

_MULTI_QUERY_MAX_PALAVRAS = 8


def search(query: str, namespaces: list[str], top_k: int = 12) -> list[tuple[float, str, str, int]]:
    settings = get_settings()
    candidatos = _buscar_candidatos(query, namespaces, settings)

    if settings.rerank_enabled and len(candidatos) > top_k:
        with tracing.span("rerank") as s:
            candidatos = rerank(query, candidatos, top_k)
            s.update(output=[
                {"id": i, "relevancia": relevancia}
                for i, (relevancia, *_resto) in enumerate(candidatos, start=1)
            ])
        return candidatos

    return candidatos[:top_k]


def _buscar_candidatos(
    query: str, namespaces: list[str], settings: Settings
) -> list[tuple[float, str, str, int]]:
    """Busca os candidatos a serem (opcionalmente) reranqueados: a pergunta original
    sozinha, ou ela + até 3 reformulações unidas por soma de score RRF."""
    palavras = len(query.split())
    if not (settings.multi_query_enabled and palavras < _MULTI_QUERY_MAX_PALAVRAS):
        return retrieve(query, top_k=settings.rerank_candidates, namespaces=namespaces)

    with tracing.span("expand") as s:
        variantes = expand_query(query)
        s.update(output=variantes)

    queries = [query] + variantes
    with ThreadPoolExecutor() as executor:
        resultados = list(executor.map(
            lambda q: retrieve(q, top_k=settings.rerank_candidates, namespaces=namespaces), queries
        ))

    return _unir_por_chave(resultados)


def _unir_por_chave(
    resultados: list[list[tuple[float, str, str, int]]],
) -> list[tuple[float, str, str, int]]:
    """Une os resultados das várias buscas por (namespace, texto), somando os scores
    RRF de cada reformulação em que o chunk aparece."""
    scores: dict[tuple[str, str], float] = {}
    paginas: dict[tuple[str, str], int] = {}

    for lista in resultados:
        for score, namespace, texto, pagina in lista:
            chave = (namespace, texto)
            scores[chave] = scores.get(chave, 0.0) + score
            paginas[chave] = pagina

    fundido = [(score, ns, texto, paginas[(ns, texto)]) for (ns, texto), score in scores.items()]
    fundido.sort(key=lambda x: x[0], reverse=True)
    return fundido
