import json
from typing import Generator

from agent.retriever import retrieve
from agent.answerer import answer, answer_stream
from agent.query_rewriter import rewrite_query
from guardrails.validator import validate
from core.limits import get_limit


def orchestrator(
    query: str,
    namespaces: list[str] | None = None,
    historico: list[dict] = [],
    plan: str = "free",
    summary: str = "",
) -> dict:
    if not namespaces:
        namespaces = [""]

    include_page = get_limit(plan, "page_number")

    retrieval_query = rewrite_query(query, historico, summary)

    chunks_with_sources = retrieve(retrieval_query, namespaces=namespaces)

    if not chunks_with_sources:
        return {"resposta": "Não encontrei informação suficiente nos documentos para responder essa pergunta", "fontes": []}

    top = chunks_with_sources[0]
    if include_page and top[3]:
        fontes = [f"{top[1]} (p. {top[3]})"]
    else:
        fontes = [top[1]]

    chunks = [text for _, _, text, _ in chunks_with_sources]

    resposta, answer_usage = answer(query, chunks, historico=historico, summary=summary)

    valido, validator_usage = validate(query, chunks, resposta, historico=historico, summary=summary)

    if not valido:
        return {"resposta": "Não encontrei informação suficiente nos documentos para responder essa pergunta", "fontes": []}

    return {"resposta": resposta, "fontes": fontes}


def orchestrator_stream(
    query: str,
    namespaces: list[str] | None = None,
    historico: list[dict] = [],
    plan: str = "free",
    summary: str = "",
) -> Generator[str, None, None]:
    if not namespaces:
        namespaces = [""]

    include_page = get_limit(plan, "page_number")

    retrieval_query = rewrite_query(query, historico, summary)
    chunks_with_sources = retrieve(retrieval_query, namespaces=namespaces)

    if not chunks_with_sources:
        yield f"data: {json.dumps({'type': 'blocked'})}\n\n"
        yield "data: [DONE]\n\n"
        return

    chunks = [text for _, _, text, _ in chunks_with_sources]

    full_response = ""
    try:
        for text_chunk in answer_stream(query, chunks, historico=historico, summary=summary):
            full_response += text_chunk
            yield f"data: {json.dumps({'type': 'chunk', 'text': text_chunk})}\n\n"
    except Exception:
        yield f"data: {json.dumps({'type': 'error'})}\n\n"
        yield "data: [DONE]\n\n"
        return

    try:
        valido, _ = validate(query, chunks, full_response, historico=historico, summary=summary)
    except Exception:
        valido = True

    if valido:
        top = chunks_with_sources[0]
        if include_page and top[3]:
            fontes = [f"{top[1]} (p. {top[3]})"]
        else:
            fontes = [top[1]]
    else:
        fontes = []

    yield f"data: {json.dumps({'type': 'done', 'fontes': fontes, 'blocked': not valido, 'resposta': full_response})}\n\n"
    yield "data: [DONE]\n\n"
