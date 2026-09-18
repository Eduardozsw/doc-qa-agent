import logging
import re
import statistics
from pathlib import Path

import fitz

from core.config import get_settings

logger = logging.getLogger(__name__)

# Bit 4 dos `flags` de um span do PyMuPDF = negrito (ver `get_text("dict")`).
_BOLD_FLAG = 1 << 4
_RAZAO_TITULO = 1.15
_MAX_PALAVRAS_TITULO = 12
_TAMANHO_FONTE_PADRAO = 10.0

_CABECALHO_PADRAO = re.compile(
    r"^Minist[ée]rio da Sa[uú]de\s*\|\s*Secretaria de Aten[cç][aã]o [àa] Sa[uú]de\s*\|\s*"
    r"Departamento de Aten[cç][aã]o B[aá]sica$",
    re.IGNORECASE,
)
_NUMERO_PAGINA_ISOLADO = re.compile(r"^\d{1,4}$")


def load_document(file_path: str) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    suffix = path.suffix.lower()

    if suffix in [".txt", ".md"]:
        return path.read_text(encoding="utf-8")
    elif suffix == ".pdf":
        doc = fitz.open(str(path))
        try:
            return "\n".join(page.get_text() for page in doc)
        finally:
            doc.close()
    else:
        raise ValueError(f"Formato não suportado: {suffix}")


def load_document_from_bytes(contents: bytes) -> str:
    doc = fitz.open(stream=contents, filetype="pdf")
    try:
        return "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()


def load_pages_from_bytes(contents: bytes) -> list[tuple[int, str]]:
    """Extrai texto por página com tabelas viradas markdown, títulos marcados com `## `
    e cabeçalho/rodapé repetido removido. Cai para `page.get_text()` (ou OCR, se
    habilitado) quando a extração estruturada falha ou a página não tem texto."""
    doc = fitz.open(stream=contents, filetype="pdf")
    try:
        paginas = []
        for i, page in enumerate(doc):
            texto = _extrair_pagina(page, i + 1)
            paginas.append((i + 1, texto))
        return paginas
    finally:
        doc.close()


def _extrair_pagina(page, numero: int) -> str:
    if get_settings().ocr_enabled and not page.get_text().strip():
        try:
            return _ocr_pagina(page)
        except Exception as e:
            logger.warning(f"OCR falhou na página {numero}: {e}")
            return ""

    try:
        return _extrair_pagina_estruturada(page)
    except Exception as e:
        logger.warning(f"Extração estruturada falhou na página {numero}: {e}; usando fallback")
        return page.get_text()


def _extrair_pagina_estruturada(page) -> str:
    tabelas = _tabelas_da_pagina(page)
    dados = page.get_text("dict")
    mediana = _mediana_tamanho_fonte(dados)

    partes: list[str] = []
    tabelas_emitidas: set[int] = set()

    for bloco in dados.get("blocks", []):
        if bloco.get("type") != 0:
            continue

        idx_tabela = _tabela_sobreposta(bloco.get("bbox"), tabelas)
        if idx_tabela is not None:
            if idx_tabela not in tabelas_emitidas:
                tabelas_emitidas.add(idx_tabela)
                if not tabelas[idx_tabela]["trivial"]:
                    partes.append(tabelas[idx_tabela]["markdown"])
            continue

        for texto_linha, e_titulo in _linhas_do_bloco(bloco, mediana):
            if _e_ruido_cabecalho_rodape(texto_linha):
                continue
            partes.append(f"## {texto_linha}" if e_titulo else texto_linha)

    # Tabelas que não ficaram sob nenhum bloco de texto (raro) vão ao final da página.
    for idx, tabela in enumerate(tabelas):
        if idx not in tabelas_emitidas and not tabela["trivial"]:
            partes.append(tabela["markdown"])

    return "\n".join(partes)


def _tabelas_da_pagina(page) -> list[dict]:
    try:
        encontradas = page.find_tables()
    except Exception as e:
        logger.debug(f"find_tables falhou: {e}")
        return []

    tabelas = []
    for tabela in encontradas.tables:
        matriz = tabela.extract()
        trivial = _tabela_trivial(matriz)
        tabelas.append({
            "bbox": tabela.bbox,
            "trivial": trivial,
            "markdown": "" if trivial else tabela.to_markdown(),
        })
    return tabelas


def _tabela_trivial(matriz: list[list]) -> bool:
    """Tabelas com no máximo 1 célula preenchida costumam ser falsos positivos do
    detector (ex.: o número da página isolado na margem) — descartadas."""
    celulas = [c for linha in matriz for c in linha if c and str(c).strip()]
    return len(celulas) <= 1


def _tabela_sobreposta(bbox_bloco, tabelas: list[dict]) -> int | None:
    if not bbox_bloco:
        return None
    cx = (bbox_bloco[0] + bbox_bloco[2]) / 2
    cy = (bbox_bloco[1] + bbox_bloco[3]) / 2
    for idx, tabela in enumerate(tabelas):
        x0, y0, x1, y1 = tabela["bbox"]
        if x0 - 2 <= cx <= x1 + 2 and y0 - 2 <= cy <= y1 + 2:
            return idx
    return None


def _mediana_tamanho_fonte(dados: dict) -> float:
    tamanhos = [
        span["size"]
        for bloco in dados.get("blocks", [])
        if bloco.get("type") == 0
        for linha in bloco.get("lines", [])
        for span in linha.get("spans", [])
        if span["text"].strip()
    ]
    return statistics.median(tamanhos) if tamanhos else _TAMANHO_FONTE_PADRAO


def _linhas_do_bloco(bloco: dict, mediana: float) -> list[tuple[str, bool]]:
    """Devolve (texto_da_linha, é_título) para cada linha do bloco. Título = fonte
    >= 1.15x a mediana da página, ou negrito com poucas palavras numa linha isolada."""
    resultado = []
    for linha in bloco.get("lines", []):
        spans = linha.get("spans", [])
        texto = "".join(s["text"] for s in spans).strip()
        if not texto:
            continue
        maior_fonte = max((s["size"] for s in spans), default=0)
        negrito = any(s["flags"] & _BOLD_FLAG for s in spans)
        n_palavras = len(texto.split())
        e_titulo = maior_fonte >= mediana * _RAZAO_TITULO or (negrito and n_palavras <= _MAX_PALAVRAS_TITULO)
        resultado.append((texto, e_titulo))
    return resultado


def _e_ruido_cabecalho_rodape(texto: str) -> bool:
    texto = texto.strip()
    return bool(_CABECALHO_PADRAO.match(texto)) or bool(_NUMERO_PAGINA_ISOLADO.match(texto))


def _ocr_pagina(page) -> str:
    """OCR via tesseract (extra opcional `ocr`, ver pyproject.toml). Import lazy: só é
    exercitado quando `OCR_ENABLED=true` e a lib está instalada."""
    import pytesseract
    from PIL import Image

    pixmap = page.get_pixmap(dpi=200)
    imagem = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    return pytesseract.image_to_string(imagem, lang="por")
