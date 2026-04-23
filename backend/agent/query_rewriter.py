from openai import OpenAI

client = OpenAI()


def rewrite_query(query: str, historico: list[dict], summary: str) -> str:
    if not historico and not summary:
        return query

    history_text = ""
    if summary:
        history_text += f"Resumo: {summary}\n"
    if historico:
        history_text += "\n".join(
            f"Usuário: {h['pergunta']}\nAssistente: {h['resposta']}" for h in historico[-3:]
        )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=100,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Reescreva a pergunta do usuário como uma pergunta autônoma e completa, "
                        "incorporando o contexto necessário da conversa para que ela faça sentido sozinha. "
                        "Se a pergunta já for autônoma e clara, retorne-a sem alterações. "
                        "Retorne APENAS a pergunta reescrita, sem explicações."
                    ),
                },
                {"role": "user", "content": f"Histórico:\n{history_text}\n\nPergunta: {query}"},
            ],
        )
        return response.choices[0].message.content.strip() or query
    except Exception:
        return query
