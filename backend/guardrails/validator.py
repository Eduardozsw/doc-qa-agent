import anthropic
from typing import cast
from anthropic.types import TextBlock, Usage

client = anthropic.Anthropic()

def validate(query: str, chunks: list[str], resposta: str) -> tuple[bool, Usage]:
    context = "\n\n".join(chunks)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[{"role": "user", "content": f"Trechos:\n{context}\n\nPergunta:{query}\n\nResposta:{resposta}"}],
        system="Você é um validador de respostas de documentação. Dado um conjunto de trechos e uma resposta gerada, avalie se a resposta: (1) está diretamente baseada nas informações dos trechos, e (2) responde à pergunta feita ou indica corretamente que a informação não está nos documentos. Responda APENAS com sim ou não."
    )
    if not message.content or not isinstance(message.content[0], TextBlock):
        return False, message.usage

    resultado = message.content[0].text.strip().lower()
    return resultado.startswith("sim"), message.usage