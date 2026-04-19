import anthropic
from typing import cast
from anthropic.types import TextBlock

client = anthropic.Anthropic()
def judge(query: str, resposta: str, esperado: str) -> float:
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        temperature=0,
        messages=[{"role": "user", "content": f"Query:\n{query}\n\n Resposta:\n{resposta} \n\n esperado:\n{esperado}"}],
        system="Você é um avaliador de qualidade de respostas. Dado uma pergunta, uma resposta gerada e um critério esperado, avalie a qualidade da resposta de 0 a 1. Responda APENAS com um número decimal entre 0 e 1, sem nenhum texto adicional, sem explicação, sem pontuação. Exemplo de resposta válida: 0.8"
    )
    resultado = cast(TextBlock, message.content[0]).text
    numero = resultado.strip().split()[0]
    return float(numero)