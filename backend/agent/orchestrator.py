import json
import logging
import queue
from concurrent.futures import ThreadPoolExecutor
from typing import Generator

from agent.answerer import answer, answer_stream
from agent.context import _SEM_INFO, ajustar_citacao_da_correcao, display_name, extract_citation_ids, is_sem_info
from agent.query_rewriter import rewrite_query
from agent.routing import choose_model
from agent.search import search
from core import tracing
from core.config import get_settings
from core.limits import get_limit
from db import query_cache as query_cache_db
from guardrails.validator import Verification, verify
from ingestion.embedder import embed_text

logger = logging.getLogger(__name__)

_STATUS_LENTO = "Verificando o embasamento — está demorando mais que o normal"
_ERRO_CONSULTA = "Não foi possível consultar os documentos agora. Tente novamente em instantes."


def _cache_habilitado(historico: list[dict], summary: str, use_cache: bool) -> bool:
    """Cache semântico só é consultado sem histórico/resumo (com eles, `rewrite_query`
    reescreve a pergunta e o embedding calculado aqui deixaria de corresponder ao que
    de fato é buscado) e quando `use_cache` é True — evals passam `use_cache=False`
    para medir o pipeline de verdade a cada rodada, em vez de respostas cacheadas."""
    return use_cache and get_settings().semantic_cache_enabled and not historico and not summary


def _namespaces_key(namespaces: list[str]) -> str:
    return ",".join(sorted(namespaces))


def _montar_citacoes(
    chunks_with_sources: list[tuple], citation_ids: list[int], verification: Verification, include_page: bool
) -> list[dict]:
    """Monta a lista `citacoes` do contrato: só os ids citados em `[n]`, na ordem
    da 1ª ocorrência, com o trecho e o veredito do verificador."""
    verificadas_por_id = {c.id: c for c in verification.citacoes}

    citacoes = []
    for cid in citation_ids:
        if cid > len(chunks_with_sources):
            continue
        _, namespace, _, pagina = chunks_with_sources[cid - 1]
        verificada = verificadas_por_id.get(cid)
        citacoes.append({
            "id": cid,
            "documento": display_name(namespace),
            "namespace": namespace,
            "pagina": pagina if (include_page and pagina) else None,
            "trecho": verificada.trecho if verificada else "",
            "verificada": verificada.verificada if verificada else False,
        })
    return citacoes


def _montar_fontes(citacoes: list[dict]) -> list[str]:
    """`fontes` = documentos únicos das citações usadas na resposta, na mesma ordem."""
    vistos = set()
    fontes = []
    for c in citacoes:
        chave = (c["documento"], c["pagina"])
        if chave in vistos:
            continue
        vistos.add(chave)
        fontes.append(f"{c['documento']} (p. {c['pagina']})" if c["pagina"] else c["documento"])
    return fontes


def _montar_conflitos(conflitos_llm: list[dict], citation_ids: list[int], max_id: int) -> list[dict]:
    """Mantém, em cada conflito, só os ids que também aparecem citados `[n]` na
    resposta; se a interseção ficar vazia (ids válidos mas nenhum citado), mantém
    os ids como vieram do verificador em vez de descartar o conflito."""
    resultado = []
    for item in conflitos_llm:
        ids_validos = [i for i in item.get("ids", []) if 1 <= i <= max_id]
        if not ids_validos:
            continue
        ids_citados = [i for i in ids_validos if i in citation_ids]
        resultado.append({
            "ids": ids_citados if ids_citados else ids_validos,
            "descricao": item.get("descricao", ""),
        })
    return resultado


def _bloqueado(fundamentada: bool, citation_ids: list[int]) -> bool:
    """Só é chamado para respostas que não são `_SEM_INFO` (ver `is_sem_info`)."""
    return not fundamentada or not citation_ids


def orchestrator(
    query: str,
    namespaces: list[str] | None = None,
    historico: list[dict] = [],
    plan: str = "free",
    summary: str = "",
    user_id: str | None = None,
    session_id: str | None = None,
    use_cache: bool = True,
) -> dict:
    if not namespaces:
        namespaces = [""]

    include_page = get_limit(plan, "page_number")
    settings = get_settings()
    cache_habilitado = _cache_habilitado(historico, summary, use_cache)
    namespaces_key = _namespaces_key(namespaces)

    # Tudo síncrono aqui (sem yield no meio), então dá pra usar os helpers "current"
    # normais: user_session cobre a árvore inteira de spans/generations criados dentro.
    with tracing.span("doc-qa", input={"query": query, "plan": plan, "namespaces": namespaces}) as trace, \
            tracing.user_session(user_id, session_id):
        trace_id = tracing.trace_id_of(trace)

        embedding = None
        if cache_habilitado:
            embedding = embed_text(query)
            with tracing.span("cache") as s:
                cached = query_cache_db.lookup(namespaces_key, embedding, min_score=settings.semantic_cache_min_score)
                s.update(output={"hit": cached is not None})
            if cached is not None:
                result = {**cached, "cached": True, "trace_id": trace_id}
                trace.update(output=result)
                return result

        with tracing.span("rewrite") as s:
            retrieval_query = rewrite_query(query, historico, summary)
            s.update(output=retrieval_query)

        with tracing.span("retrieve") as s:
            chunks_with_sources = search(retrieval_query, namespaces=namespaces, embedding=embedding)
            s.update(output={
                "chunks_count": len(chunks_with_sources),
                "fontes": [c[1] for c in chunks_with_sources],
            })

        if not chunks_with_sources:
            tracing.update_trace(tags=["blocked"])
            result = {
                "resposta": _SEM_INFO, "fontes": [], "citacoes": [], "correcao": False, "conflitos": [],
                "trace_id": trace_id,
            }
            trace.update(output=result)
            return result

        with tracing.span("answer") as s:
            model = choose_model(query, chunks_with_sources)
            resposta, answer_usage = answer(query, chunks_with_sources, historico=historico, summary=summary, model=model)
            s.update(output=resposta, metadata={"model": model})

        def _log_retry(tentativa: int) -> None:
            logger.info(f"Verificador: tentativa {tentativa} após falha")

        with tracing.span("validate") as s:
            verification = verify(
                query, chunks_with_sources, resposta, historico=historico, summary=summary, on_retry=_log_retry
            )
            s.update(output={"fundamentada": verification.fundamentada, "correcao": verification.correcao})

        if is_sem_info(resposta):
            result = {
                "resposta": _SEM_INFO, "fontes": [], "citacoes": [], "correcao": False, "conflitos": [],
                "modelo": model, "trace_id": trace_id,
            }
            trace.update(output=result)
            return result

        citation_ids = extract_citation_ids(resposta, max_id=len(chunks_with_sources))

        if _bloqueado(verification.fundamentada, citation_ids):
            tracing.update_trace(tags=["blocked"])
            result = {
                "resposta": _SEM_INFO, "fontes": [], "citacoes": [], "correcao": False, "conflitos": [],
                "modelo": model, "trace_id": trace_id,
            }
            trace.update(output=result)
            return result

        citacoes = _montar_citacoes(chunks_with_sources, citation_ids, verification, include_page)
        conflitos = _montar_conflitos(verification.conflitos, citation_ids, len(chunks_with_sources))
        if verification.correcao:
            resposta = ajustar_citacao_da_correcao(resposta, citacoes)
        result = {
            "resposta": resposta,
            "fontes": _montar_fontes(citacoes),
            "citacoes": citacoes,
            "correcao": verification.correcao,
            "conflitos": conflitos,
            "modelo": model,
            "trace_id": trace_id,
        }
        trace.update(output=result)

        if cache_habilitado:
            cache_payload = {k: v for k, v in result.items() if k != "trace_id"}
            query_cache_db.store(
                namespaces_key, namespaces, embedding, query, cache_payload, ttl_hours=settings.semantic_cache_ttl_hours
            )

        return result


def orchestrator_stream(
    query: str,
    namespaces: list[str] | None = None,
    historico: list[dict] = [],
    plan: str = "free",
    summary: str = "",
    user_id: str | None = None,
    session_id: str | None = None,
    use_cache: bool = True,
) -> Generator[str, None, None]:
    if not namespaces:
        namespaces = [""]

    include_page = get_limit(plan, "page_number")
    settings = get_settings()
    cache_habilitado = _cache_habilitado(historico, summary, use_cache)
    namespaces_key = _namespaces_key(namespaces)
    embedding: list[float] | None = None

    # ATENÇÃO: este generator é consumido via starlette.concurrency.iterate_in_threadpool
    # (StreamingResponse com generator síncrono), e cada `next()` roda numa cópia NOVA
    # do contexto — contextvars setados antes de um `yield` não sobrevivem depois dele.
    # Por isso nenhum span "current" (attach) pode atravessar um `yield`: usamos
    # tracing.root_span()/tracing.active() (sem attach) para o span raiz e para o span
    # "answer" (que engloba o loop de streaming), e reaplicamos user_id/session_id a
    # cada trecho reativado. "rewrite"/"retrieve"/"validate" não têm yield no meio do
    # seu próprio bloco, então usam o tracing.span() normal, desde que dentro de um
    # tracing.active(root, ...) daquele trecho.
    root = tracing.root_span("doc-qa-stream", input={"query": query, "plan": plan, "namespaces": namespaces})
    trace_id = tracing.trace_id_of(root)
    try:
        cached = None
        try:
            with tracing.active(root, user_id=user_id, session_id=session_id):
                if cache_habilitado:
                    embedding = embed_text(query)
                    with tracing.span("cache") as s:
                        cached = query_cache_db.lookup(namespaces_key, embedding, min_score=settings.semantic_cache_min_score)
                        s.update(output={"hit": cached is not None})

                if cached is None:
                    with tracing.span("rewrite") as s:
                        retrieval_query = rewrite_query(query, historico, summary)
                        s.update(output=retrieval_query)

                    with tracing.span("retrieve") as s:
                        chunks_with_sources = search(retrieval_query, namespaces=namespaces, embedding=embedding)
                        s.update(output={
                            "chunks_count": len(chunks_with_sources),
                            "fontes": [c[1] for c in chunks_with_sources],
                        })

                    if not chunks_with_sources:
                        tracing.update_trace(tags=["blocked"])
                        root.update(output={"blocked": True})
        except Exception:
            logger.exception("Falha antes do primeiro yield do stream (cache/rewrite/search)")
            yield f"data: {json.dumps({'type': 'error', 'text': _ERRO_CONSULTA})}\n\n"
            yield "data: [DONE]\n\n"
            return

        if cached is not None:
            resposta_cache = cached.get("resposta", "")
            yield f"data: {json.dumps({'type': 'chunk', 'text': resposta_cache})}\n\n"
            done_cache = {**cached, "type": "done", "blocked": False, "cached": True, "trace_id": trace_id}
            yield f"data: {json.dumps(done_cache)}\n\n"
            yield "data: [DONE]\n\n"
            return

        if not chunks_with_sources:
            yield f"data: {json.dumps({'type': 'blocked'})}\n\n"
            yield "data: [DONE]\n\n"
            return

        model = choose_model(query, chunks_with_sources)
        with tracing.active(root, user_id=user_id, session_id=session_id):
            answer_span = tracing.root_span("answer")

        full_response = ""
        try:
            iterator = answer_stream(query, chunks_with_sources, historico=historico, summary=summary, model=model)
            while True:
                try:
                    with tracing.active(answer_span, user_id=user_id, session_id=session_id):
                        text_chunk = next(iterator)
                except StopIteration:
                    break
                full_response += text_chunk
                yield f"data: {json.dumps({'type': 'chunk', 'text': text_chunk})}\n\n"
        except Exception:
            with tracing.active(root):
                root.update(output={"error": True})
            yield f"data: {json.dumps({'type': 'error', 'text': _ERRO_CONSULTA})}\n\n"
            yield "data: [DONE]\n\n"
            return
        finally:
            with tracing.active(answer_span):
                answer_span.update(output=full_response, metadata={"model": model})
            tracing.end_span(answer_span)

        # `verify` é síncrono e pode retentar com backoff (até ~2s). Roda numa thread
        # separada para poder, enquanto ela não termina, dar polling numa fila
        # alimentada por `on_retry` e emitir o evento "status" a cada nova tentativa —
        # sem isso, o generator ficaria bloqueado sem poder yield nada até o fim.
        status_queue: queue.Queue[int] = queue.Queue()

        def _run_verify() -> Verification:
            def _on_retry(tentativa: int) -> None:
                status_queue.put(tentativa)

            # A thread não herda contextvars: reabre o span raiz e cria "validate"
            # dentro dela, igual ao padrão usado no resto deste generator.
            with tracing.active(root, user_id=user_id, session_id=session_id), tracing.span("validate") as s:
                verification = verify(
                    query, chunks_with_sources, full_response, historico=historico, summary=summary,
                    on_retry=_on_retry,
                )
                s.update(output={"fundamentada": verification.fundamentada, "correcao": verification.correcao})
                return verification

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_run_verify)
                while not future.done():
                    try:
                        status_queue.get(timeout=0.2)
                    except queue.Empty:
                        continue
                    yield f"data: {json.dumps({'type': 'status', 'text': _STATUS_LENTO})}\n\n"
                while not status_queue.empty():
                    status_queue.get_nowait()
                    yield f"data: {json.dumps({'type': 'status', 'text': _STATUS_LENTO})}\n\n"
                verification = future.result()
        except Exception:
            # Fail-closed: qualquer falha inesperada na orquestração do verificador
            # bloqueia a resposta, igual ao caso de esgotar as tentativas internas.
            verification = Verification(fundamentada=False, correcao=False)

        sem_info = is_sem_info(full_response)
        citation_ids = [] if sem_info else extract_citation_ids(full_response, max_id=len(chunks_with_sources))
        bloqueado = False if sem_info else _bloqueado(verification.fundamentada, citation_ids)

        with tracing.active(root):
            if sem_info:
                resposta_final = _SEM_INFO
                fontes, citacoes, correcao, conflitos = [], [], False, []
            elif bloqueado:
                resposta_final = full_response
                fontes, citacoes, correcao, conflitos = [], [], False, []
                tracing.update_trace(tags=["blocked"])
            else:
                resposta_final = full_response
                citacoes = _montar_citacoes(chunks_with_sources, citation_ids, verification, include_page)
                fontes = _montar_fontes(citacoes)
                correcao = verification.correcao
                conflitos = _montar_conflitos(verification.conflitos, citation_ids, len(chunks_with_sources))
                if correcao:
                    resposta_final = ajustar_citacao_da_correcao(resposta_final, citacoes)

            root.update(output={
                "resposta": resposta_final, "fontes": fontes, "blocked": bloqueado,
                "citacoes": citacoes, "correcao": correcao, "conflitos": conflitos, "modelo": model,
            })

        if cache_habilitado and not bloqueado and not sem_info:
            cache_payload = {
                "resposta": resposta_final, "fontes": fontes, "citacoes": citacoes, "correcao": correcao,
                "conflitos": conflitos, "modelo": model,
            }
            query_cache_db.store(
                namespaces_key, namespaces, embedding, query, cache_payload, ttl_hours=settings.semantic_cache_ttl_hours
            )

        yield (
            f"data: {json.dumps({'type': 'done', 'fontes': fontes, 'blocked': bloqueado, 'resposta': resposta_final, 'citacoes': citacoes, 'correcao': correcao, 'conflitos': conflitos, 'modelo': model, 'trace_id': trace_id})}\n\n"
        )
        yield "data: [DONE]\n\n"
    finally:
        # Cobre também o caso do cliente desconectar no meio do streaming: o
        # GeneratorExit lançado no ponto de yield atravessa os try/finally acima
        # normalmente e chega aqui, fechando o trace raiz.
        tracing.end_span(root)
