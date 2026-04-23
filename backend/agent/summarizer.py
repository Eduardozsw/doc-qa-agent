from openai import OpenAI

client = OpenAI()


def summarize(existing_summary: str, pergunta: str, resposta: str) -> str:
    context = f"Resumo anterior:\n{existing_summary}\n\n" if existing_summary else ""
    prompt = (
        f"{context}"
        f"Nova troca a incorporar:\n"
        f"Usuário: {pergunta}\n"
        f"Assistente: {resposta}\n\n"
        "Atualize o resumo incorporando a nova troca. Seja conciso e mantenha apenas as informações relevantes para entender o contexto da conversa."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=300,
        temperature=0,
        messages=[
            {"role": "system", "content": "Você resume conversas de forma concisa, preservando o contexto relevante."},
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content or existing_summary
