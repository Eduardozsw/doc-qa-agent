"""Roteamento de modelo (F6): decide se uma pergunta merece o modelo forte
(`openai_chat_model_strong`) em vez do padrão (`openai_chat_model`).

Critérios (qualquer um basta): os trechos recuperados vêm de mais de um documento
(namespace) — caso em que o risco de conflito entre fontes é maior; a pergunta é
longa (> 60 tokens `cl100k_base`); ou a pergunta contém um marcador de premissa
("já que", "considerando que"...) que costuma indicar uma afirmação a ser checada
contra o documento, cenário em que vale a pena um modelo melhor para a correção.
"""
import re

import tiktoken

from core.config import get_settings

_MAX_TOKENS_PADRAO = 60

_MARCADORES_PREMISSA = re.compile(
    r"\b(j[áa] que|considerando que|sabendo que|dado que|visto que)\b", re.IGNORECASE
)


def _encoder():
    return tiktoken.get_encoding("cl100k_base")


def _multiplos_documentos(chunks_with_sources: list[tuple]) -> bool:
    namespaces = {namespace for _, namespace, _, _ in chunks_with_sources}
    return len(namespaces) >= 2


def _pergunta_longa(query: str) -> bool:
    return len(_encoder().encode(query)) > _MAX_TOKENS_PADRAO


def _tem_marcador_premissa(query: str) -> bool:
    return bool(_MARCADORES_PREMISSA.search(query))


def choose_model(query: str, chunks_with_sources: list[tuple]) -> str:
    """Devolve `openai_chat_model_strong` quando o roteamento está ligado e a
    pergunta atende a pelo menos um critério de complexidade; senão devolve
    `openai_chat_model`."""
    settings = get_settings()
    if not settings.model_routing_enabled:
        return settings.openai_chat_model

    precisa_modelo_forte = (
        _multiplos_documentos(chunks_with_sources)
        or _pergunta_longa(query)
        or _tem_marcador_premissa(query)
    )
    return settings.openai_chat_model_strong if precisa_modelo_forte else settings.openai_chat_model
