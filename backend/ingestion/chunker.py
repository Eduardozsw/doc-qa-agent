import re
from functools import lru_cache

import tiktoken

CHUNKER_VERSION = "v3"

_QUEBRA_SENTENCA = re.compile(r"(?<=[.!?;:])\s+|\n\s*\n")
_PREFIXO_TITULO = "## "


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

    blocos: list[list[str]] = []
    atual: list[str] = []
    tokens_atual = 0

    for sentenca in sentencas:
        tokens_sentenca = _contar_tokens(sentenca)
        if atual and tokens_atual + tokens_sentenca > chunk_size:
            blocos.append(atual)
            atual = _sentencas_de_overlap(atual, overlap)
            tokens_atual = sum(_contar_tokens(s) for s in atual)
        atual.append(sentenca)
        tokens_atual += tokens_sentenca

    if atual:
        blocos.append(atual)

    _evitar_titulo_orfao(blocos)
    return [" ".join(bloco) for bloco in blocos if bloco]


def _evitar_titulo_orfao(blocos: list[list[str]]) -> None:
    """Uma linha `## Título` nunca fica sozinha no fim de um chunk: se sobrar como
    última sentença de um bloco (e houver um próximo), ela migra para o começo do
    próximo — a menos que já esteja lá por causa do overlap."""
    for i in range(len(blocos) - 1):
        while blocos[i] and _e_titulo(blocos[i][-1]):
            titulo = blocos[i][-1]
            if blocos[i + 1] and blocos[i + 1][0] == titulo:
                blocos[i].pop()
            else:
                blocos[i + 1].insert(0, blocos[i].pop())


def _e_titulo(sentenca: str) -> bool:
    return sentenca.startswith(_PREFIXO_TITULO)


def _sentencas_dentro_do_limite(text: str, chunk_size: int) -> list[str]:
    """Divide em sentenças; uma sentença isolada maior que chunk_size é fatiada por
    tokens. Blocos de tabela markdown (linhas começando com `|`) são tratados à parte,
    como sentença(s) atômica(s) — nunca quebrados no meio de uma linha de dados."""
    sentencas = []
    for tipo, bloco in _dividir_blocos(text):
        if tipo == "tabela":
            sentencas.extend(_processar_tabela(bloco, chunk_size))
            continue
        for sentenca in _QUEBRA_SENTENCA.split(bloco):
            sentenca = sentenca.strip()
            if not sentenca:
                continue
            if _contar_tokens(sentenca) > chunk_size:
                sentencas.extend(_fatiar_por_tokens(sentenca, chunk_size))
            else:
                sentencas.append(sentenca)
    return sentencas


def _dividir_blocos(text: str) -> list[tuple[str, str]]:
    """Agrupa linhas consecutivas em blocos ("tabela" ou "texto")."""
    blocos: list[tuple[str, str]] = []
    linhas_atual: list[str] = []
    tipo_atual: str | None = None

    for linha in text.split("\n"):
        tipo = "tabela" if linha.strip().startswith("|") else "texto"
        if tipo_atual is not None and tipo != tipo_atual:
            blocos.append((tipo_atual, "\n".join(linhas_atual)))
            linhas_atual = []
        tipo_atual = tipo
        linhas_atual.append(linha)

    if linhas_atual:
        blocos.append((tipo_atual, "\n".join(linhas_atual)))

    return blocos


def _processar_tabela(bloco: str, chunk_size: int) -> list[str]:
    """Tabela markdown como sentença única; se exceder o orçamento, fatia por linhas
    repetindo o cabeçalho (2 primeiras linhas: título/colunas + separador) em cada fatia."""
    bloco = bloco.strip("\n")
    if _contar_tokens(bloco) <= chunk_size:
        return [bloco]

    linhas = bloco.split("\n")
    if len(linhas) <= 2:
        return [bloco]

    cabecalho = linhas[:2]
    dados = linhas[2:]

    fatias = []
    atual = list(cabecalho)
    tokens_atual = _contar_tokens("\n".join(atual))
    for linha in dados:
        tokens_linha = _contar_tokens(linha)
        if len(atual) > 2 and tokens_atual + tokens_linha > chunk_size:
            fatias.append("\n".join(atual))
            atual = list(cabecalho)
            tokens_atual = _contar_tokens("\n".join(atual))
        atual.append(linha)
        tokens_atual += tokens_linha
    if len(atual) > 2:
        fatias.append("\n".join(atual))

    return fatias


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
