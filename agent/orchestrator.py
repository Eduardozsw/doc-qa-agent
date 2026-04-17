from agent.retriever import retrieve
from agent.answerer import answer
from guardrails.validator import validate
from langfuse import get_client

langfuse = get_client()

def orchestrator(query: str) -> str:
    with langfuse.start_as_current_observation(
        as_type="span",
        name="doc-qa",
        input={"query": query}
    ) as trace:
        with langfuse.start_as_current_observation(as_type="span", name="retrieve") as span:
            chunks = retrieve(query)
            span.update(output={"chunks_count": len(chunks)})

        with langfuse.start_as_current_observation(as_type="span", name="answerer") as span:
            resposta = answer(query, chunks)
            span.update(output={"resposta": resposta})

        with langfuse.start_as_current_observation(as_type="span", name="validator") as span:
            valido = validate(query, chunks, resposta)
            span.update(output={"valido": valido})

        if not valido:
            trace.update(output="sem base nos documentos")
            langfuse.flush()
            return "Não encontrei informação suficiente nos documentos para responder essa pergunta"
        
        trace.update(output=resposta)
        langfuse.flush()
        return resposta