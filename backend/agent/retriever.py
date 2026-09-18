from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from core.config import get_settings
from db import vectors as vectors_db
from ingestion.embedder import embed_text

_RRF_K = 60
_SUB_TOP_K = 20


def retrieve(
    query: str, top_k: int = 12, namespaces: list[str] = [""], embedding: list[float] | None = None
) -> list[tuple[float, str, str, int]]:
    """`embedding`, se informado (cache semântico já o calculou para a pergunta
    original), evita recalcular o embedding de `query` aqui."""
    xq = embedding if embedding is not None else embed_text(query)
    hybrid = get_settings().hybrid_search

    def busca(namespace: str) -> tuple[str, list[tuple[str, int]], list[tuple[str, int]]]:
        vetorial, keyword = _busca_namespace(namespace, xq, query, hybrid)
        return namespace, vetorial, keyword

    with ThreadPoolExecutor() as executor:
        buscas = list(executor.map(busca, namespaces))

    return _fundir_rrf(buscas)[:top_k]


def _busca_namespace(
    namespace: str, xq: list[float], query: str, hybrid: bool
) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    """Roda a busca vetorial e, se habilitada, a busca por palavra-chave em paralelo.
    Retorna (vetorial, keyword) como listas de (texto, pagina) ordenadas por relevância."""
    if not hybrid:
        vetorial = vectors_db.query(namespace, xq, _SUB_TOP_K)
        return [(text, page) for _score, text, page in vetorial], []

    with ThreadPoolExecutor(max_workers=2) as executor:
        vetorial_future = executor.submit(vectors_db.query, namespace, xq, _SUB_TOP_K)
        keyword_future = executor.submit(vectors_db.query_keyword, namespace, query, _SUB_TOP_K)
        vetorial = vetorial_future.result()
        keyword = keyword_future.result()

    return (
        [(text, page) for _score, text, page in vetorial],
        [(text, page) for _score, text, page in keyword],
    )


def _fundir_rrf(
    buscas: list[tuple[str, list[tuple[str, int]], list[tuple[str, int]]]],
) -> list[tuple[float, str, str, int]]:
    """Reciprocal Rank Fusion: soma 1/(k + rank + 1) de cada lista em que o chunk aparece.
    Chave de identidade (namespace, texto) deduplica o mesmo chunk vindo das duas buscas."""
    scores: dict[tuple[str, str], float] = defaultdict(float)
    paginas: dict[tuple[str, str], int] = {}

    for namespace, vetorial, keyword in buscas:
        for rank, (text, page) in enumerate(vetorial):
            chave = (namespace, text)
            scores[chave] += 1 / (_RRF_K + rank + 1)
            paginas[chave] = page
        for rank, (text, page) in enumerate(keyword):
            chave = (namespace, text)
            scores[chave] += 1 / (_RRF_K + rank + 1)
            paginas[chave] = page

    fundido = [
        (score, namespace, text, paginas[(namespace, text)])
        for (namespace, text), score in scores.items()
    ]
    fundido.sort(key=lambda x: x[0], reverse=True)
    return fundido
