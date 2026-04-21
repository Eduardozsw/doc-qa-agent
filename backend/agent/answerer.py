import anthropic
from typing import cast
from anthropic.types import TextBlock, Usage

client = anthropic.Anthropic()

def answer(query: str, chunks: list[str], historico: list[dict] = []) -> tuple[str, Usage]:
    context = "\n\n".join(chunks)
    messages = []

    for h in historico[:10]:
        if not isinstance(h, dict):
            continue
        pergunta = str(h.get("pergunta", "")).strip()
        resposta = str(h.get("resposta", "")).strip()
        if not pergunta or not resposta:
            continue
        if len(pergunta) > 2000 or len(resposta) > 5000:
            continue
        messages.append({"role": "user", "content": pergunta})
        messages.append({"role": "assistant", "content": resposta})

    messages.append({"role": "user", "content": f"Trechos:\n{context}\n\nPergunta: {query}"})
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        temperature=0,
        messages=messages,
        system="Você é um assistente de documentação. Responda APENAS com base nos trechos fornecidos. Se os trechos não contiverem a informação necessária para responder à pergunta, diga claramente que não encontrou nos documentos. Não tente inferir ou especular além do que está escrito nos trechos."
    )

    if not message.content or not isinstance(message.content[0], TextBlock):
        raise ValueError("Resposta inesperada da API Anthropic")

    return message.content[0].text, message.usage