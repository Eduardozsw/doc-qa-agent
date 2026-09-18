import json
from pathlib import Path

from agent.orchestrator import orchestrator
from db import vectors as vectors_db
from evals.judge import judge
from evals.retrieval import evaluate_retrieval
from ingestion import chunker
from ingestion.chunker import chunk_pages
from ingestion.contextualizer import build_preview, contextualize
from ingestion.embedder import upsert_chunks
from ingestion.loader import load_pages_from_bytes
from scripts.fetch_demo_pdf import DEMO_PDF_PATH, ensure_pdf

# Só existe `CHUNKER_VERSION` em ingestion/chunker.py a partir da F2 (chunker por
# sentença); até lá, "v1" identifica o chunker de 500 palavras atual.
CHUNKER_VERSION = getattr(chunker, "CHUNKER_VERSION", "v1")
EVAL_NAMESPACE = f"evals_cab37_{CHUNKER_VERSION}"

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
    preview = build_preview("\n".join(text for _, text in pages))
    contexts = contextualize(chunks, preview)
    upsert_chunks(chunks, EVAL_NAMESPACE, EVAL_NAMESPACE, contexts)


def runner() -> dict:
    ensure_indexed()

    with open(DATASET_PATH, "r") as file:
        data = json.load(file)

    scores = []
    resultados = []
    for caso in data:
        # use_cache=False: evals medem o pipeline de verdade a cada rodada, não
        # respostas cacheadas de uma rodada anterior com a mesma pergunta.
        resultado = orchestrator(caso["query"], namespaces=[EVAL_NAMESPACE], plan="pro", use_cache=False)
        score = judge(caso["query"], resultado["resposta"], caso["esperado"])
        print(f"[{score:.2f}] {caso['query'][:55]} → {resultado['resposta'][:70]}")
        scores.append(score)
        resultados.append((caso, resultado))

    retrieval = evaluate_retrieval(data, EVAL_NAMESPACE)

    metricas = {
        "answer_score": sum(scores) / len(data),
        "hit@3": retrieval["hit@3"],
        "hit@5": retrieval["hit@5"],
        "hit@8": retrieval["hit@8"],
        "mrr": retrieval["mrr"],
        "citation_rate": _citation_rate(resultados),
        "correction_rate": _correction_rate(resultados),
    }

    _print_metricas(metricas)
    return metricas


def _citation_rate(resultados: list[tuple[dict, dict]]) -> float:
    """Fração dos casos que exigem documento (tipo != fora_do_documento) cuja
    resposta trouxe pelo menos uma citação verificada deterministicamente."""
    elegiveis = [r for caso, r in resultados if caso.get("tipo") != "fora_do_documento"]
    if not elegiveis:
        return 0.0
    acertos = sum(1 for r in elegiveis if any(c.get("verificada") for c in r.get("citacoes", [])))
    return acertos / len(elegiveis)


def _correction_rate(resultados: list[tuple[dict, dict]]) -> float:
    """Fração dos casos de premissa falsa em que a resposta trouxe o bloco de correção."""
    premissa_falsa = [r for caso, r in resultados if caso.get("tipo") == "premissa_falsa"]
    if not premissa_falsa:
        return 0.0
    acertos = sum(1 for r in premissa_falsa if r.get("correcao") is True)
    return acertos / len(premissa_falsa)


def _print_metricas(metricas: dict) -> None:
    print("\nmétrica          | valor")
    print("------------------|------")
    for nome in _ORDEM_METRICAS:
        print(f"{nome:<17} | {metricas[nome]:.2f}")
