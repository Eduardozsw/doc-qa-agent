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


def _normalizar(texto: str) -> str:
    """Normaliza texto para comparação tolerante a diferenças de pontuação/espaço.
    Vive aqui (em vez de em guardrails/validator.py) porque `ajustar_citacao_da_correcao`
    também precisa dela e validator já importa deste módulo — importar na direção
    contrária fecharia um ciclo. `guardrails.validator` importa esta função daqui."""
    texto = texto.casefold()
    texto = re.sub(r"(?<=\w)-\s+(?=\w)", "", texto)  # hífen de quebra de palavra (extração de PDF)
    texto = re.sub(r"[^\w\s]", "", texto, flags=re.UNICODE)  # pontuação, bullets (\x07) etc.
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


_ASPAS_COM_CITACAO_RE = re.compile(r'["“]([^"”]*)["”](\s*)((?:\[\d+\]\s*)+)')
_PRIMEIRO_COLCHETE_RE = re.compile(r"\[(\d+)\]")
_MAX_PALAVRAS_TRECHO = 40


def ajustar_citacao_da_correcao(resposta: str, citacoes: list[dict]) -> str:
    """Corrige a citação literal entre aspas na 1ª linha do blockquote `> **Correção:**
    ...`, que o LLM às vezes preenche com uma paráfrase em vez do texto literal do
    documento. Só mexe nessa 1ª linha; o resto da resposta fica intacto.

    Para o primeiro `[n]` após cada trecho entre aspas: se `citacoes` tem um item
    daquele id com `verificada=True` e o texto entre aspas (normalizado) não está
    contido no `trecho` verificado (normalizado), substitui o texto entre aspas pelo
    `trecho` verificado (truncado a `_MAX_PALAVRAS_TRECHO` palavras + "…" se maior).
    Se não há citação verificada para aquele id, remove as aspas (mantém a paráfrase
    como texto solto) e mantém o(s) `[n]`.
    """
    texto_sem_espacos = resposta.lstrip()
    if not texto_sem_espacos.startswith(">"):
        return resposta

    fim_primeira_linha = texto_sem_espacos.find("\n")
    primeira_linha = texto_sem_espacos if fim_primeira_linha == -1 else texto_sem_espacos[:fim_primeira_linha]
    if "**Correção:**" not in primeira_linha:
        return resposta

    citacoes_por_id = {c["id"]: c for c in citacoes}

    def _substituir(match: re.Match) -> str:
        texto_aspas, espacos, colchetes = match.group(1), match.group(2), match.group(3)
        m_id = _PRIMEIRO_COLCHETE_RE.search(colchetes)
        if not m_id:
            return match.group(0)

        citacao = citacoes_por_id.get(int(m_id.group(1)))
        if not citacao or not citacao.get("verificada"):
            return f"{texto_aspas}{espacos}{colchetes}"

        trecho = citacao.get("trecho", "")
        if _normalizar(texto_aspas) in _normalizar(trecho):
            return match.group(0)

        palavras = trecho.split()
        trecho_final = " ".join(palavras[:_MAX_PALAVRAS_TRECHO]) + "…" if len(palavras) > _MAX_PALAVRAS_TRECHO else trecho
        return f'"{trecho_final}"{espacos}{colchetes}'

    nova_primeira_linha = _ASPAS_COM_CITACAO_RE.sub(_substituir, primeira_linha)
    if nova_primeira_linha == primeira_linha:
        return resposta

    prefixo_removido = resposta[: len(resposta) - len(texto_sem_espacos)]
    resto = texto_sem_espacos[len(primeira_linha):]
    return f"{prefixo_removido}{nova_primeira_linha}{resto}"
