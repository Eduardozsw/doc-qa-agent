"""CLI do benchmark de produto do doc-qa-agent.

    uv run python -m benchmark.run [--repeats 3] [--configs naive,hybrid,full]
        [--limit N] [--http-url http://localhost:8080 --http-n 10] [--skip-ingest]

Mede, por config de ablação e por repetição, qualidade (juiz LLM), recuperação
(hit@k/MRR), latência por etapa e custo — chamando os componentes reais do
pipeline (ver `instrumented.py`). Ao final, escreve o JSON bruto em
`docs/benchmark/results-<data>.json` e o relatório em `docs/benchmark.md`
(`report.py`). Continua se um caso falhar (registra o erro) e grava um checkpoint
do JSON após cada config, para não perder tudo numa suspensão da máquina.
"""
import argparse
import json
import subprocess
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from benchmark import cache_bench, envconfig, http_bench, ingest_bench, instrumented, metrics, report
from benchmark.cost import CostTracker, install_judge_wrapper, install_query_wrappers
from core.config import get_settings
from evals.judge import judge
from evals.runner import DATASET_PATH, EVAL_NAMESPACE, ensure_indexed

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_DOCS_DIR = _BACKEND_DIR.parent / "docs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark de produto do doc-qa-agent")
    parser.add_argument("--repeats", type=int, default=3, help="Repetições completas do dataset por config")
    parser.add_argument("--configs", type=str, default="naive,hybrid,full", help="Configs a rodar, separadas por vírgula")
    parser.add_argument("--limit", type=int, default=None, help="Limita o dataset aos N primeiros casos (smoke test)")
    parser.add_argument("--http-url", type=str, default=None, help="Base URL do compose para o benchmark HTTP (ex.: http://localhost:8080)")
    parser.add_argument("--http-n", type=int, default=10, help="Nº de perguntas do benchmark HTTP")
    parser.add_argument("--skip-ingest", action="store_true", help="Pula o benchmark de ingestão")
    args = parser.parse_args()
    args.configs = [c.strip() for c in args.configs.split(",") if c.strip()]
    return args


def load_dataset(limit: int | None) -> list[dict]:
    with open(DATASET_PATH) as f:
        data = json.load(f)
    return data[:limit] if limit else data


def git_commit() -> str | None:
    try:
        resultado = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_BACKEND_DIR, capture_output=True, text=True, timeout=5, check=True,
        )
        return resultado.stdout.strip()
    except Exception:
        return None


def cpu_model() -> str:
    try:
        with open("/proc/cpuinfo") as f:
            for linha in f:
                if linha.startswith("model name"):
                    return linha.split(":", 1)[1].strip()
    except Exception:
        pass
    return "desconhecido"


def ram_gb() -> float:
    try:
        with open("/proc/meminfo") as f:
            for linha in f:
                if linha.startswith("MemTotal"):
                    kb = int(linha.split()[1])
                    return round(kb / 1024 / 1024, 1)
    except Exception:
        pass
    return 0.0


def build_environment(dataset: list[dict], args: argparse.Namespace) -> dict:
    settings = get_settings()
    contagens = dict(Counter(c["tipo"] for c in dataset))
    contagens["total"] = len(dataset)
    return {
        "date": date.today().isoformat(),
        "commit": git_commit(),
        "cpu": cpu_model(),
        "ram_gb": ram_gb(),
        "models": {
            "chat": settings.openai_chat_model,
            "chat_strong": settings.openai_chat_model_strong,
            "embedding": "text-embedding-3-small",
        },
        "dataset_counts": contagens,
        "dataset_limit": args.limit,
        "repeats": args.repeats,
        "configs_run": args.configs,
    }


def _run_case(caso: dict, namespace: str, query_tracker: CostTracker, judge_tracker: CostTracker) -> dict:
    base = {"query": caso["query"], "tipo": caso["tipo"], "esperado": caso.get("esperado"),
            "relevant_pages": caso.get("paginas_relevantes")}

    uso_antes = query_tracker.snapshot()
    try:
        resultado = instrumented.run_case(caso["query"], namespaces=[namespace])
    except Exception as e:
        uso_delta = metrics.diff_usage(uso_antes, query_tracker.snapshot())
        return {**base, "error": str(e), "usage": uso_delta}
    uso_delta = metrics.diff_usage(uso_antes, query_tracker.snapshot())

    juiz_antes = judge_tracker.snapshot()
    try:
        score = judge(caso["query"], resultado["resposta"], caso.get("esperado", ""))
    except Exception:
        score = None
    juiz_delta = metrics.diff_usage(juiz_antes, judge_tracker.snapshot())

    return {
        **base,
        "resposta": resultado["resposta"], "score": score, "correcao": resultado["correcao"],
        "citacoes": resultado["citacoes"], "abstained": resultado["abstained"],
        "ranked_pages": resultado["ranked_pages"], "modelo": resultado.get("modelo"),
        "timings_ms": resultado["timings_ms"], "usage": uso_delta, "judge_usage": juiz_delta,
        "error": None,
    }


def _aggregate_config(reps: list[dict]) -> dict:
    todos = [c for r in reps for c in r["cases"]]
    ok_por_rep = [[c for c in r["cases"] if not c.get("error")] for r in reps]
    todos_ok = [c for casos in ok_por_rep for c in casos]

    quality = metrics.quality_metrics(todos_ok)
    quality_var = metrics.quality_variability(ok_por_rep)

    def _casos_retrieval(casos: list[dict]) -> list[dict]:
        return [
            {"ranked_pages": c["ranked_pages"], "relevant_pages": c["relevant_pages"]}
            for c in casos if c.get("relevant_pages")
        ]

    retrieval = metrics.retrieval_metrics(_casos_retrieval(todos_ok))
    retrieval_var = metrics.retrieval_variability([_casos_retrieval(casos) for casos in ok_por_rep])

    timings_pooled: dict[str, list[float]] = {}
    for c in todos_ok:
        for etapa, valor in c.get("timings_ms", {}).items():
            timings_pooled.setdefault(etapa, []).append(valor)
    latency = metrics.latency_summary(timings_pooled)

    uso_total = metrics.merge_usage(*(c.get("usage", {}) for c in todos_ok))
    custo = metrics.cost_usd(uso_total)
    custo_pergunta = metrics.cost_per_question(custo["total_cost_usd"], len(todos_ok))

    custo_por_rep = []
    for casos in ok_por_rep:
        uso_rep = metrics.merge_usage(*(c.get("usage", {}) for c in casos))
        c_rep = metrics.cost_usd(uso_rep)
        custo_por_rep.append(metrics.cost_per_question(c_rep["total_cost_usd"], len(casos))["usd_per_question"])
    media_custo, desvio_custo = metrics.mean_std(custo_por_rep)

    uso_juiz_total = metrics.merge_usage(*(c.get("judge_usage") or {} for c in todos))
    custo_juiz = metrics.cost_usd(uso_juiz_total)

    return {
        "quality": quality, "quality_variability": quality_var,
        "retrieval": retrieval, "retrieval_variability": retrieval_var,
        "latency_ms": latency,
        "cost": {**custo, **custo_pergunta, "n_questions": len(todos_ok),
                 "usd_per_question_variability": {"mean": media_custo, "std": desvio_custo}},
        "judge_cost_usd": custo_juiz["total_cost_usd"],
        "n_failed": len(todos) - len(todos_ok),
        "n_total_attempts": len(todos),
    }


def run_config(
    nome: str, dataset: list[dict], repeats: int, namespace: str,
    query_tracker: CostTracker, judge_tracker: CostTracker,
) -> dict:
    with envconfig.apply_config(nome):
        reps = []
        for rep in range(1, repeats + 1):
            casos = []
            for i, caso in enumerate(dataset, start=1):
                resultado = _run_case(caso, namespace, query_tracker, judge_tracker)
                status = "ERRO" if resultado.get("error") else f"nota={resultado.get('score')}"
                print(f"[{nome}] rep {rep}/{repeats} caso {i}/{len(dataset)} ({status}) {caso['query'][:60]}", flush=True)
                casos.append(resultado)
            reps.append({"rep": rep, "cases": casos})

    return {"env": {**envconfig.COMMON_ENV, **envconfig.CONFIGS[nome]}, "n_cases": len(dataset),
            "reps": reps, "aggregated": _aggregate_config(reps)}


def _save_checkpoint(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def main() -> None:
    args = parse_args()
    dataset = load_dataset(args.limit)

    print(f"Indexando namespace de eval ({EVAL_NAMESPACE}), se necessário...")
    ensure_indexed()

    query_tracker, judge_tracker = CostTracker(), CostTracker()
    uninstall_query = install_query_wrappers(query_tracker)
    uninstall_judge = install_judge_wrapper(judge_tracker)

    resultado: dict = {
        "generated_at": datetime.now().isoformat(),
        "environment": build_environment(dataset, args),
        "configs": {},
        "ingestion": None,
        "cache": None,
        "http": None,
    }

    _DOCS_DIR.joinpath("benchmark").mkdir(parents=True, exist_ok=True)
    json_path = _DOCS_DIR / "benchmark" / f"results-{date.today().isoformat()}.json"

    try:
        for nome in args.configs:
            print(f"\n=== Config: {nome} ===")
            try:
                resultado["configs"][nome] = run_config(
                    nome, dataset, args.repeats, EVAL_NAMESPACE, query_tracker, judge_tracker
                )
            except Exception as e:
                print(f"Config {nome} falhou: {e}")
                resultado["configs"][nome] = {"error": str(e)}
            _save_checkpoint(json_path, resultado)

        if not args.skip_ingest:
            print("\n=== Ingestão ===")
            try:
                resultado["ingestion"] = ingest_bench.run(query_tracker)
            except Exception as e:
                print(f"Benchmark de ingestão falhou: {e}")
                resultado["ingestion"] = {"error": str(e)}
            _save_checkpoint(json_path, resultado)

        print("\n=== Cache semântico ===")
        try:
            perguntas_cache = [c["query"] for c in dataset if c["tipo"] == "factual"][:5]
            resultado["cache"] = {"resultados": cache_bench.run(EVAL_NAMESPACE, perguntas_cache)}
        except Exception as e:
            print(f"Benchmark de cache falhou: {e}")
            resultado["cache"] = {"error": str(e)}
        _save_checkpoint(json_path, resultado)

        if args.http_url:
            print("\n=== HTTP ponta a ponta ===")
            try:
                perguntas_http = [c["query"] for c in dataset if c["tipo"] == "factual"]
                resultado["http"] = http_bench.run(args.http_url, args.http_n, perguntas_http)
            except Exception as e:
                print(f"Benchmark HTTP falhou: {e}")
                resultado["http"] = {"error": str(e)}
            _save_checkpoint(json_path, resultado)
    finally:
        uninstall_query()
        uninstall_judge()

    _save_checkpoint(json_path, resultado)

    markdown = report.generate_markdown(resultado)
    md_path = _DOCS_DIR / "benchmark.md"
    md_path.write_text(markdown, encoding="utf-8")

    print(f"\nJSON bruto: {json_path}")
    print(f"Relatório:  {md_path}")


if __name__ == "__main__":
    main()
