from dataclasses import dataclass
from openai import OpenAI

client = OpenAI()

@dataclass
class Usage:
    input_tokens: int
    output_tokens: int

def answer(query: str, chunks: list[str], historico: list[dict] = []) -> tuple[str, Usage]:
    context = "\n\n".join(chunks)
    messages = [
        {
            "role": "system",
            "content": "Você é um assistente de documentação. Responda APENAS com base nos trechos fornecidos. Se os trechos não contiverem a informação necessária para responder à pergunta, diga claramente que não encontrou nos documentos. Não tente inferir ou especular além do que está escrito nos trechos.",
        }
    ]

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

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1024,
        temperature=0,
        messages=messages,
    )

    content = response.choices[0].message.content if response.choices else None
    if not content:
        raise ValueError("Resposta inesperada da API OpenAI")

    usage = Usage(
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
    )
    return content, usage