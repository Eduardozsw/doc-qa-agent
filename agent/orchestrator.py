from agent.retriever import retrieve
from agent.answerer import answer
from guardrails.validator import validate
def orchestrator(query: str) -> str:
    chunks = retrieve(query)
    resposta = answer(query, chunks)

    if not validate(query, chunks, resposta):
        return "Não encontrei informação suficiente nos documentos para responder essa pergunta."
    return resposta