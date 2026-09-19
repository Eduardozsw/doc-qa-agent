import json
import logging

from agent.retriever import retrieve
from core.tracing import openai_client

logger = logging.getLogger(__name__)
client = openai_client()

_SUMMARY_QUERY = "Principais tópicos, seções, argumentos e conclusões do documento"
_TOP_K = 20

_SYSTEM_PROMPT = """Você é um assistente especializado em resumir documentos.
Responda APENAS com JSON válido no seguinte formato:
{
  "topicos_abordados": ["frase curta descritiva 1", "frase curta descritiva 2"],
  "resumo": "resumo organizado pelas seções do documento"
}
Regras:
- Baseie-se EXCLUSIVAMENTE no conteúdo fornecido. Nunca invente informações.
- topicos_abordados: lista de 3 a 8 frases curtas que descrevem os assuntos abordados.
- resumo: texto organizado seguindo as seções do documento; se não houver seções claras, organize por tema.
- Responda em português."""


def generate_summary(namespace: str) -> dict:
    chunks_data = retrieve(_SUMMARY_QUERY, top_k=_TOP_K, namespaces=[namespace])
    if not chunks_data:
        raise ValueError(f"Nenhum chunk encontrado no namespace '{namespace}'")

    context = "\n\n---\n\n".join(text for _, _, text, _ in chunks_data)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Resuma o seguinte documento:\n\n{context}"},
        ],
        temperature=0.3,
    )

    raw = response.choices[0].message.content
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"PDF summarizer retornou JSON inválido: {raw}")
        raise ValueError("Resposta inválida do modelo") from e

    if "topicos_abordados" not in data or "resumo" not in data:
        logger.error(f"PDF summarizer retornou estrutura inesperada: {data}")
        raise ValueError("Estrutura de resposta inválida do modelo")

    return data
