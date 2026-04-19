import anthropic
from typing import cast
from anthropic.types import TextBlock
client = anthropic.Anthropic()
def validate(query: str, chunks: list[str], resposta: str) -> bool:
    context = "\n\n".join(chunks)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=20,
        messages=[{"role": "user", "content": f"Trechos:\n{context}\n\nPergunta:{query}\n\nResposta:{resposta}"}],
        system="Você é um validador de respostas. Dado um conjunto de trechos de documentação e uma resposta gerada, avalie se a resposta é razoavelmente suportada pelas informações presentes nos trechos, mesmo que de forma parcial ou indireta. Responda APENAS com sim ou não."
    )
    resultado = cast(TextBlock, message.content[0]).text
    return "sim" in resultado.lower()