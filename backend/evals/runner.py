import json
from pathlib import Path

from agent.orchestrator import orchestrator
from db import vectors as vectors_db
from evals.judge import judge
from evals.retrieval import evaluate_retrieval
from ingestion.chunker import chunk_pages
from ingestion.embedder import upsert_chunks
from ingestion.loader import load_pages_from_bytes
from scripts.fetch_demo_pdf import DEMO_PDF_PATH, ensure_pdf

EVAL_NAMESPACE = "evals_cab37"

DATASET_PATH = Path(__file__).parent / "datasets" / "qa.json"

_ORDEM_METRICAS = ["answer_score", "hit@3", "hit@5", "hit@8", "mrr", "citation_rate", "correction_rate"]


def ensure_indexed() -> None:
    """Indexa o PDF de demonstração na namespace de evals, se ainda não indexado."""
    if vectors_db.count(EVAL_NAMESPACE) > 0:
        return

    if not DEMO_PDF_PATH.exists():
        ensure_pdf()

    contents = DEMO_PDF_PATH.read_bytes()
    pages = load_pages_from_bytes(contents)
    chunks = chunk_pages(pages)
    upsert_chunks(chunks, EVAL_NAMESPACE, EVAL_NAMESPACE)


def runner() -> dict:
    ensure_indexed()

    with open(DATASET_PATH, "r") as file:
        data = json.load(file)

    scores = []
    for caso in data:
        resultado = orchestrator(caso["query"], namespaces=[EVAL_NAMESPACE], plan="pro")
        score = judge(caso["query"], resultado["resposta"], caso["esperado"])
        print(f"[{score:.2f}] {caso['query'][:55]} → {resultado['resposta'][:70]}")
        scores.append(score)

    retrieval = evaluate_retrieval(data, EVAL_NAMESPACE)

    metricas = {
        "answer_score": sum(scores) / len(data),
        "hit@3": retrieval["hit@3"],
        "hit@5": retrieval["hit@5"],
        "hit@8": retrieval["hit@8"],
        "mrr": retrieval["mrr"],
        # placeholders da Fase 1 (citação e correção de premissa ainda não existem)
        "citation_rate": 0.0,
        "correction_rate": 0.0,
    }

    _print_metricas(metricas)
    return metricas


def _print_metricas(metricas: dict) -> None:
    print("\nmétrica          | valor")
    print("------------------|------")
    for nome in _ORDEM_METRICAS:
        print(f"{nome:<17} | {metricas[nome]:.2f}")
