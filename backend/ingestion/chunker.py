import re
from functools import lru_cache

import tiktoken

CHUNKER_VERSION = "v2"

_QUEBRA_SENTENCA = re.compile(r"(?<=[.!?;:])\s+|\n\s*\n")


@lru_cache
def _enc():
    return tiktoken.get_encoding("cl100k_base")


def _contar_tokens(texto: str) -> int:
    return len(_enc().encode(texto))


def chunk_pages(pages: list[tuple[int, str]], chunk_size: int = 350, overlap: int = 60) -> list[tuple[str, int]]:
    result = []
    for page_num, text in pages:
        for chunk in chunk_text(text, chunk_size, overlap):
            result.append((chunk, page_num))
    return result


def chunk_text(text: str, chunk_size: int = 350, overlap: int = 60) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size deve ser > 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap deve ser >= 0 e < chunk_size")
    if not text or not text.strip():
        return []

    sentencas = _sentencas_dentro_do_limite(text, chunk_size)
    if not sentencas:
        return []

    chunks = []
    atual: list[str] = []
    tokens_atual = 0

    for sentenca in sentencas:
        tokens_sentenca = _contar_tokens(sentenca)
        if atual and tokens_atual + tokens_sentenca > chunk_size:
            chunks.append(" ".join(atual))
            atual = _sentencas_de_overlap(atual, overlap)
            tokens_atual = sum(_contar_tokens(s) for s in atual)
        atual.append(sentenca)
        tokens_atual += tokens_sentenca

    if atual:
        chunks.append(" ".join(atual))

    return chunks


def _sentencas_dentro_do_limite(text: str, chunk_size: int) -> list[str]:
    """Divide em sentenças; uma sentença isolada maior que chunk_size é fatiada por tokens."""
    sentencas = []
    for sentenca in _QUEBRA_SENTENCA.split(text):
        sentenca = sentenca.strip()
        if not sentenca:
            continue
        if _contar_tokens(sentenca) > chunk_size:
            sentencas.extend(_fatiar_por_tokens(sentenca, chunk_size))
        else:
            sentencas.append(sentenca)
    return sentencas


def _fatiar_por_tokens(sentenca: str, chunk_size: int) -> list[str]:
    tokens = _enc().encode(sentenca)
    return [_enc().decode(tokens[i:i + chunk_size]) for i in range(0, len(tokens), chunk_size)]


def _sentencas_de_overlap(sentencas: list[str], overlap: int) -> list[str]:
    """Últimas sentenças de `sentencas` cuja soma de tokens chega perto de `overlap`."""
    if overlap == 0:
        return []
    selecionadas: list[str] = []
    tokens = 0
    for sentenca in reversed(sentencas):
        tokens_sentenca = _contar_tokens(sentenca)
        if selecionadas and tokens + tokens_sentenca > overlap:
            break
        selecionadas.insert(0, sentenca)
        tokens += tokens_sentenca
    return selecionadas
