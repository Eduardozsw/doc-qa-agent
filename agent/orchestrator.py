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
            span.update(output={
                "chunks_count": len(chunks_with_sources),
                "top_score": round(chunks_with_sources[0][0], 3) if chunks_with_sources else 0,
                "min_score": round(chunks_with_sources[-1][0], 3) if chunks_with_sources else 0,
            })

        if not chunks_with_sources:
            langfuse.flush()
            return {"resposta": "Não encontrei informação suficiente nos documentos para responder essa pergunta", "fontes": []}

        fontes = [chunks_with_sources[0][1]]
        chunks = [text for _, _, text in chunks_with_sources]

        with langfuse.start_as_current_observation(as_type="generation", name="answerer") as span:
            resposta, answer_usage = answer(query, chunks, historico=historico)
            span.update(
                model="claude-haiku-4-5-20251001",
                usage={"input": answer_usage.input_tokens, "output": answer_usage.output_tokens},
                output=resposta,
            )

        with langfuse.start_as_current_observation(as_type="generation", name="validator") as span:
            valido, validator_usage = validate(query, chunks, resposta)
            span.update(
                model="claude-haiku-4-5-20251001",
                usage={"input": validator_usage.input_tokens, "output": validator_usage.output_tokens},
                output={"valido": valido},
            )

        if not valido:
            trace.update(output="sem base nos documentos")
            langfuse.flush()
            return {"resposta": "Não encontrei informação suficiente nos documentos para responder essa pergunta", "fontes": []}

        trace.update(output=resposta)
        langfuse.flush()
        return {"resposta": resposta, "fontes": fontes}