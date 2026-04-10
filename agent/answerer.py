import anthropic
from typing import cast
from anthropic.types import TextBlock

client = anthropic.Anthropic()

def answer(query: str, chunks: list[str]) -> str:
    context = "\n\n".join(chunks)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": f"Trechos:\n{context}\n\nPergunta:{query}"}],
        system="Você é um assistente de documentação. Responda apenas com base nos trechos fornecidos. Se a resposta não estiver nos trechos, diga que não encontrou nos documentos."
    )
    return cast(TextBlock, message.content[0]).text