import anthropic
from typing import cast
from anthropic.types import TextBlock

client = anthropic.Anthropic()

def answer(query: str, chunks: list[str], historico: list[dict] = []) -> str:
    context = "\n\n".join(chunks)
    messages = []
    for h in historico:
        messages.append({"role": "user", "content": h["pergunta"]})
        messages.append({"role": "assistant", "content": h["resposta"]})
    messages.append({"role": "user", "content": f"Trechos:\n{context}\n\nPergunta: {query}"})
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        temperature=0,
        messages=messages,
        system="Você é um assistente de documentação. Responda com base nos trechos fornecidos. Se a informação estiver parcialmente disponível, sintetize o que foi encontrado e indique o que não foi coberto. Só diga que não encontrou se os trechos não tiverem nenhuma relação com a pergunta."
    )
    return cast(TextBlock, message.content[0]).text