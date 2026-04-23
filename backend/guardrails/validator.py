from openai import OpenAI
from agent.answerer import Usage

client = OpenAI()

def validate(
    query: str,
    chunks: list[str],
    resposta: str,
    historico: list[dict] = [],
    summary: str = "",
) -> tuple[bool, Usage]:
    context = "\n\n".join(chunks)

    history_context = ""
    if summary:
        history_context += f"Resumo da conversa:\n{summary}\n\n"
    if historico:
        trocas = "\n".join(f"Usuário: {h['pergunta']}\nAssistente: {h['resposta']}" for h in historico)
        history_context += f"Histórico recente:\n{trocas}\n\n"

    user_content = ""
    if history_context:
        user_content += f"{history_context}"
    user_content += f"Trechos do documento:\n{context}\n\nPergunta:{query}\n\nResposta:{resposta}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=10,
        messages=[
            {
                "role": "system",
                "content": "Você é um validador de respostas de documentação. Avalie se a resposta está embasada nos trechos do documento ou no histórico da conversa fornecidos. Responda APENAS com sim ou não.",
            },
            {"role": "user", "content": user_content},
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