"""Valida o dataset de evals (`evals/datasets/qa.json`) contra o PDF de origem.

Para cada caso com `termo_chave`, confere que o termo aparece (normalizado) em pelo
menos uma das `paginas_relevantes`. Para casos `fora_do_documento` com o campo
opcional `termos_ausentes`, confere que nenhum desses termos aparece em nenhuma
página do PDF.

Uso: `uv run python -m evals.validate_dataset`
"""

import json
import re
import sys
from pathlib import Path

import fitz

DATASET_PATH = Path(__file__).parent / "datasets" / "qa.json"
PDF_PATH = Path(__file__).parent.parent / "docs" / "examples" / "cab37_hipertensao.pdf"


def _normalize(text: str) -> str:
    """Casefold, remove hífen de quebra de linha e colapsa espaços/quebras de linha."""
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().casefold()


def _load_pages(pdf_path: Path) -> dict[int, str]:
    """Carrega o texto normalizado de cada página do PDF, 1-based (índice + 1)."""
    doc = fitz.open(pdf_path)
    try:
        return {i + 1: _normalize(doc[i].get_text()) for i in range(doc.page_count)}
    finally:
        doc.close()


def validate() -> bool:
    if not PDF_PATH.exists():
        print(f"PDF não encontrado em {PDF_PATH}")
        return False

    dataset = json.loads(DATASET_PATH.read_text())
    pages = _load_pages(PDF_PATH)
    full_text = " ".join(pages.values())

    ok_count = 0
    fail_count = 0
    skip_count = 0
    falhas: list[str] = []

    for i, caso in enumerate(dataset):
        query_preview = caso.get("query", "")[:60]
        termo_chave = caso.get("termo_chave")
        termos_ausentes = caso.get("termos_ausentes")
        paginas_relevantes = caso.get("paginas_relevantes") or []

        if termo_chave:
            termo_norm = _normalize(termo_chave)
            achou = any(termo_norm in pages.get(p, "") for p in paginas_relevantes)
            if achou:
                ok_count += 1
            else:
                fail_count += 1
                falhas.append(
                    f"[{i}] termo_chave ausente nas páginas {paginas_relevantes}: "
                    f"'{termo_chave}' — query: {query_preview!r}"
                )

        if termos_ausentes:
            for termo in termos_ausentes:
                termo_norm = _normalize(termo)
                if termo_norm in full_text:
                    fail_count += 1
                    falhas.append(
                        f"[{i}] termo_ausente encontrado no PDF (não deveria): "
                        f"'{termo}' — query: {query_preview!r}"
                    )
                else:
                    ok_count += 1

        if not termo_chave and not termos_ausentes:
            skip_count += 1

    print(f"Total de casos: {len(dataset)}")
    por_tipo: dict[str, int] = {}
    for caso in dataset:
        por_tipo[caso.get("tipo", "?")] = por_tipo.get(caso.get("tipo", "?"), 0) + 1
    for tipo, n in sorted(por_tipo.items()):
        print(f"  {tipo}: {n}")
    print(f"\nVerificações OK: {ok_count}")
    print(f"Verificações com falha: {fail_count}")
    print(f"Casos sem termo_chave/termos_ausentes (não verificados): {skip_count}")

    if falhas:
        print("\nFalhas:")
        for f in falhas:
            print(f"  - {f}")

    return fail_count == 0


if __name__ == "__main__":
    sucesso = validate()
    sys.exit(0 if sucesso else 1)
