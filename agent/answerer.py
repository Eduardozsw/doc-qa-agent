import anthropic
from typing import cast
from anthropic.types import TextBlock, Usage

client = anthropic.Anthropic()

def answer(query: str, chunks: list[str], historico: list[dict] = []) -> tuple[str, Usage]:
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
        system="Você é um assistente de documentação. Responda APENAS com base nos trechos fornecidos. Se os trechos não contiverem a informação necessária para responder à pergunta, diga claramente que não encontrou nos documentos. Não tente inferir ou especular além do que está escrito nos trechos."
    )
    return cast(TextBlock, message.content[0]).text, message.usage