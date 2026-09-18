"""Utilitários compartilhados por answerer, validator e orchestrator para montar o
contexto enviado ao LLM e interpretar citações `[n]` na resposta.

Fica aqui (em vez de em orchestrator.py) para evitar import circular: validator
precisa de `_SEM_INFO` e `format_context`, e orchestrator importa answerer e
validator — se `_SEM_INFO` continuasse em orchestrator.py, validator teria que
importar de lá e o ciclo se fecharia.
"""
import re

_SEM_INFO = "Não encontrei informação suficiente nos documentos para responder essa pergunta"

_CITATION_RE = re.compile(r"\[(\d+)\]")

_PONTUACAO_BORDA = ".!\"'"


def _normalizar_sem_info(texto: str) -> str:
    return texto.strip().strip(_PONTUACAO_BORDA).strip().casefold()


_SEM_INFO_NORMALIZADO = _normalizar_sem_info(_SEM_INFO)


def is_sem_info(resposta: str) -> bool:
    """Compara com `_SEM_INFO` tolerando variações comuns do LLM (ponto final,
    aspas envolvendo a frase, maiúsculas/minúsculas)."""
    return _normalizar_sem_info(resposta) == _SEM_INFO_NORMALIZADO


def display_name(namespace: str) -> str:
    """Extrai o nome do arquivo original da namespace `{user_id[:8]}_{sha[:8]}_{filename}`.
    Mesma regra do frontend (`AnswerSection.tsx`)."""
    partes = namespace.split("_")
    return "_".join(partes[2:]) if len(partes) > 2 else namespace


def format_context(chunks_with_sources: list[tuple]) -> str:
    """Monta o bloco `<trecho id="n" documento="..." pagina="...">` enviado ao LLM.
    `chunks_with_sources` é a saída de `retrieve()`: (score, namespace, texto, pagina).
    Ids começam em 1, na ordem recebida. `pagina` é omitida se 0/None."""
    trechos = []
    for i, (_, namespace, texto, pagina) in enumerate(chunks_with_sources, start=1):
        atributos = f'id="{i}" documento="{display_name(namespace)}"'
        if pagina:
            atributos += f' pagina="{pagina}"'
        trechos.append(f"<trecho {atributos}>\n{texto}\n</trecho>")
    return "\n\n".join(trechos)


def extract_citation_ids(resposta: str, max_id: int | None = None) -> list[int]:
    """Extrai os ids `[n]` citados na resposta, únicos e na ordem da 1ª ocorrência.
    Ignora ids fora do intervalo válido (< 1, ou > `max_id` quando informado)."""
    vistos: list[int] = []
    for match in _CITATION_RE.finditer(resposta):
        n = int(match.group(1))
        if n < 1:
            continue
        if max_id is not None and n > max_id:
            continue
        if n not in vistos:
            vistos.append(n)
    return vistos
