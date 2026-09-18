import json
from typing import Generator

from agent.answerer import answer, answer_stream
from agent.query_rewriter import rewrite_query
from agent.retriever import retrieve
from core import tracing
from core.limits import get_limit
from guardrails.validator import validate

_SEM_INFO = "Não encontrei informação suficiente nos documentos para responder essa pergunta"


def orchestrator(
    query: str,
    namespaces: list[str] | None = None,
    historico: list[dict] = [],
    plan: str = "free",
    summary: str = "",
    user_id: str | None = None,
    session_id: str | None = None,
) -> dict:
    if not namespaces:
        namespaces = [""]

    include_page = get_limit(plan, "page_number")

    # Tudo síncrono aqui (sem yield no meio), então dá pra usar os helpers "current"
    # normais: user_session cobre a árvore inteira de spans/generations criados dentro.
    with tracing.span("doc-qa", input={"query": query, "plan": plan, "namespaces": namespaces}) as trace, \
            tracing.user_session(user_id, session_id):

        with tracing.span("rewrite") as s:
            retrieval_query = rewrite_query(query, historico, summary)
            s.update(output=retrieval_query)

        with tracing.span("retrieve") as s:
            chunks_with_sources = retrieve(retrieval_query, namespaces=namespaces)
            s.update(output={
                "chunks_count": len(chunks_with_sources),
                "fontes": [c[1] for c in chunks_with_sources],
            })

        if not chunks_with_sources:
            tracing.update_trace(tags=["blocked"])
            result = {"resposta": _SEM_INFO, "fontes": []}
            trace.update(output=result)
            return result

        top = chunks_with_sources[0]
        if include_page and top[3]:
            fontes = [f"{top[1]} (p. {top[3]})"]
        else:
            fontes = [top[1]]

        chunks = [text for _, _, text, _ in chunks_with_sources]

        with tracing.span("answer") as s:
            resposta, answer_usage = answer(query, chunks, historico=historico, summary=summary)
            s.update(output=resposta)

        with tracing.span("validate") as s:
            valido, validator_usage = validate(query, chunks, resposta, historico=historico, summary=summary)
            s.update(output={"valido": valido})

        if not valido:
            tracing.update_trace(tags=["blocked"])
            result = {"resposta": _SEM_INFO, "fontes": []}
            trace.update(output=result)
            return result

        result = {"resposta": resposta, "fontes": fontes}
        trace.update(output=result)
        return result


def orchestrator_stream(
    query: str,
    namespaces: list[str] | None = None,
    historico: list[dict] = [],
    plan: str = "free",
    summary: str = "",
    user_id: str | None = None,
    session_id: str | None = None,
) -> Generator[str, None, None]:
    if not namespaces:
        namespaces = [""]

    include_page = get_limit(plan, "page_number")

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
    try:
        with tracing.active(root, user_id=user_id, session_id=session_id):
            with tracing.span("rewrite") as s:
                retrieval_query = rewrite_query(query, historico, summary)
                s.update(output=retrieval_query)

            with tracing.span("retrieve") as s:
                chunks_with_sources = retrieve(retrieval_query, namespaces=namespaces)
                s.update(output={
                    "chunks_count": len(chunks_with_sources),
                    "fontes": [c[1] for c in chunks_with_sources],
                })

            if not chunks_with_sources:
                tracing.update_trace(tags=["blocked"])
                root.update(output={"blocked": True})

        if not chunks_with_sources:
            yield f"data: {json.dumps({'type': 'blocked'})}\n\n"
            yield "data: [DONE]\n\n"
            return

        chunks = [text for _, _, text, _ in chunks_with_sources]

        with tracing.active(root, user_id=user_id, session_id=session_id):
            answer_span = tracing.root_span("answer")

        full_response = ""
        try:
            iterator = answer_stream(query, chunks, historico=historico, summary=summary)
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
            yield f"data: {json.dumps({'type': 'error'})}\n\n"
            yield "data: [DONE]\n\n"
            return
        finally:
            with tracing.active(answer_span):
                answer_span.update(output=full_response)
            tracing.end_span(answer_span)

        valido = True
        try:
            with tracing.active(root, user_id=user_id, session_id=session_id), tracing.span("validate") as s:
                valido, _ = validate(query, chunks, full_response, historico=historico, summary=summary)
                s.update(output={"valido": valido})
        except Exception:
            valido = True

        with tracing.active(root):
            if valido:
                top = chunks_with_sources[0]
                if include_page and top[3]:
                    fontes = [f"{top[1]} (p. {top[3]})"]
                else:
                    fontes = [top[1]]
            else:
                fontes = []
                tracing.update_trace(tags=["blocked"])

            root.update(output={"resposta": full_response, "fontes": fontes, "blocked": not valido})

        yield f"data: {json.dumps({'type': 'done', 'fontes': fontes, 'blocked': not valido, 'resposta': full_response})}\n\n"
        yield "data: [DONE]\n\n"
    finally:
        # Cobre também o caso do cliente desconectar no meio do streaming: o
        # GeneratorExit lançado no ponto de yield atravessa os try/finally acima
        # normalmente e chega aqui, fechando o trace raiz.
        tracing.end_span(root)
