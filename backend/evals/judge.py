from openai import OpenAI

client = OpenAI()


def judge(query: str, resposta: str, esperado: str) -> float:
    message = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=16,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "Você é um avaliador de qualidade de respostas. Dado uma pergunta, uma resposta gerada e um critério esperado, avalie a qualidade da resposta de 0 a 1. Responda APENAS com um número decimal entre 0 e 1, sem nenhum texto adicional, sem explicação, sem pontuação. Exemplo de resposta válida: 0.8",
            },
            {
                "role": "user",
                "content": f"Query:\n{query}\n\n Resposta:\n{resposta} \n\n esperado:\n{esperado}",
            },
        ],
    )
    resultado = message.choices[0].message.content
    numero = resultado.strip().split()[0]
    return float(numero)
