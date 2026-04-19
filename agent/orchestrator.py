from agent.retriever import retrieve
from agent.answerer import answer
from guardrails.validator import validate
from langfuse import get_client

langfuse = get_client()

def orchestrator(query: str, namespaces: list[str] = [""], historico: list[dict] = []) -> dict:
    with langfuse.start_as_current_observation(
        as_type="span",
        name="doc-qa",
        input={"query": query}
    ) as trace:
        with langfuse.start_as_current_observation(as_type="span", name="retrieve") as span:
            chunks_with_sources = retrieve(query, namespaces=namespaces)
            span.update(output={"chunks_count": len(chunks_with_sources)})

        fontes = [chunks_with_sources[0][0]] if chunks_with_sources else []
        chunks = [text for _, text in chunks_with_sources]

        with langfuse.start_as_current_observation(as_type="span", name="answerer") as span:
            resposta = answer(query, chunks, historico=historico)
            span.update(output={"resposta": resposta})

        with langfuse.start_as_current_observation(as_type="span", name="validator") as span:
            valido = validate(query, chunks, resposta)
            span.update(output={"valido": valido})

        if not valido:
            trace.update(output="sem base nos documentos")
            langfuse.flush()
            return {"resposta": "Não encontrei informação suficiente nos documentos para responder essa pergunta", "fontes": []}

        trace.update(output=resposta)
        langfuse.flush()
        return {"resposta": resposta, "fontes": fontes}