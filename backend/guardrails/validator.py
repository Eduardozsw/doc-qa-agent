from openai import OpenAI
from agent.answerer import Usage

client = OpenAI()

def validate(query: str, chunks: list[str], resposta: str) -> tuple[bool, Usage]:
    context = "\n\n".join(chunks)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=10,
        messages=[
            {
                "role": "system",
                "content": "Você é um validador de respostas de documentação. Dado um conjunto de trechos e uma resposta gerada, avalie se a resposta: (1) está diretamente baseada nas informações dos trechos, e (2) responde à pergunta feita ou indica corretamente que a informação não está nos documentos. Responda APENAS com sim ou não.",
            },
            {"role": "user", "content": f"Trechos:\n{context}\n\nPergunta:{query}\n\nResposta:{resposta}"},
        ],
    )

    usage = Usage(
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
    )
    content = response.choices[0].message.content if response.choices else None
    if not content:
        return False, usage

    return content.strip().lower().startswith("sim"), usage