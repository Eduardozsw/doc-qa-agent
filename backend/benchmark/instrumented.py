"""Réplica instrumentada do `agent.orchestrator.orchestrator()` não-streaming, usada
pelo benchmark para cronometrar cada etapa com `time.perf_counter()`.

Por que uma réplica em vez de chamar `orchestrator(..., use_cache=False)` direto:
o benchmark precisa do tempo de CADA etapa (retrieve puro, busca completa, geração,
verificação) além do total, e o orchestrator não expõe esses tempos — só spans de
tracing (Langfuse), que ficam no-op sem as chaves configuradas. Os casos do eval
não têm histórico/resumo, então `rewrite_query` e o cache semântico do orchestrator
não entram no caminho (equivalente ao que `evals/runner.py` já faz com `plan="pro",
use_cache=False`). A lógica de bloqueio (`_bloqueado`) e o ajuste da citação de
correção (`ajustar_citacao_da_correcao`) são replicados fielmente a partir de
`agent/orchestrator.py` — qualquer mudança de comportamento lá deve ser espelhada aqui.
"""
import time

from agent.answerer import answer
from agent.context import _SEM_INFO, ajustar_citacao_da_correcao, extract_citation_ids, is_sem_info
from agent.retriever import retrieve
from agent.routing import choose_model
from agent.search import search
from guardrails.validator import verify


def _montar_citacoes(chunks_with_sources: list[tuple], citation_ids: list[int], verification) -> list[dict]:
    """Versão mínima de `orchestrator._montar_citacoes`: só os campos usados pelas
    métricas do benchmark (id/trecho/verificada) — página vem à parte, de `ranked_pages`."""
    verificadas_por_id = {c.id: c for c in verification.citacoes}
    citacoes = []
    for cid in citation_ids:
        if cid > len(chunks_with_sources):
            continue
        verificada = verificadas_por_id.get(cid)
        citacoes.append({
            "id": cid,
            "trecho": verificada.trecho if verificada else "",
            "verificada": verificada.verificada if verificada else False,
        })
    return citacoes


def _bloqueado(fundamentada: bool, citation_ids: list[int]) -> bool:
    return not fundamentada or not citation_ids


def run_case(query: str, namespaces: list[str]) -> dict:
    """Roda um caso pelo pipeline real e devolve resposta final, citações, flag de
    correção, páginas ranqueadas (as que de fato foram para o LLM, via `search()`) e
    `timings_ms` (search/retrieve/answer/verify/total, em milissegundos).

    `retrieve()` é chamado UMA VEZ A MAIS, ANTES e FORA da janela do `total` — mede a
    busca híbrida/vetorial pura (sem multi-query/rerank) como métrica isolada; seu
    resultado não é usado pela resposta (quem alimenta `answer()` é sempre `search()`,
    igual ao orchestrator).
    """
    t0 = time.perf_counter()
    retrieve(query, namespaces=namespaces)
    tempo_retrieve = (time.perf_counter() - t0) * 1000

    t_inicio = time.perf_counter()

    t0 = time.perf_counter()
    chunks = search(query, namespaces=namespaces)
    tempo_search = (time.perf_counter() - t0) * 1000
    ranked_pages = [pagina for _, _, _, pagina in chunks]

    if not chunks:
        tempo_total = (time.perf_counter() - t_inicio) * 1000
        return _resultado(
            _SEM_INFO, [], False, ranked_pages, None,
            {"search": tempo_search, "retrieve": tempo_retrieve, "answer": 0.0, "verify": 0.0, "total": tempo_total},
        )

    modelo = choose_model(query, chunks)
    t0 = time.perf_counter()
    resposta, _usage = answer(query, chunks, model=modelo)
    tempo_answer = (time.perf_counter() - t0) * 1000

    if is_sem_info(resposta):
        tempo_total = (time.perf_counter() - t_inicio) * 1000
        return _resultado(
            _SEM_INFO, [], False, ranked_pages, modelo,
            {"search": tempo_search, "retrieve": tempo_retrieve, "answer": tempo_answer, "verify": 0.0, "total": tempo_total},
        )

    t0 = time.perf_counter()
    verification = verify(query, chunks, resposta)
    tempo_verify = (time.perf_counter() - t0) * 1000
    timings_base = {"search": tempo_search, "retrieve": tempo_retrieve, "answer": tempo_answer, "verify": tempo_verify}

    citation_ids = extract_citation_ids(resposta, max_id=len(chunks))
    if _bloqueado(verification.fundamentada, citation_ids):
        tempo_total = (time.perf_counter() - t_inicio) * 1000
        return _resultado(_SEM_INFO, [], False, ranked_pages, modelo, {**timings_base, "total": tempo_total})

    citacoes = _montar_citacoes(chunks, citation_ids, verification)
    correcao = verification.correcao
    if correcao:
        resposta = ajustar_citacao_da_correcao(resposta, citacoes)

    tempo_total = (time.perf_counter() - t_inicio) * 1000
    return _resultado(resposta, citacoes, correcao, ranked_pages, modelo, {**timings_base, "total": tempo_total})


def _resultado(resposta, citacoes, correcao, ranked_pages, modelo, timings_ms) -> dict:
    return {
        "resposta": resposta,
        "citacoes": citacoes,
        "correcao": correcao,
        "abstained": is_sem_info(resposta),
        "ranked_pages": ranked_pages,
        "modelo": modelo,
        "timings_ms": timings_ms,
    }
