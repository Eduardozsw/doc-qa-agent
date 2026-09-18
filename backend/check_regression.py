import json
import os
from pathlib import Path

from db.postgres import init_db
from evals.runner import runner

BASE_DIR = Path(__file__).parent
BASELINE_PATH = BASE_DIR / "baseline" / "main.json"
LAST_RUN_PATH = BASE_DIR / "evals" / "last_run.json"

# ≈ 1 caso em 15 — abaixo disso é ruído do conjunto de eval
TOLERANCE = 0.07


def comparar(baseline: dict, atual: dict) -> list[tuple[str, float, float, bool]]:
    """Para cada métrica do baseline, retorna (métrica, baseline, atual, regrediu)."""
    linhas = []
    for metrica, valor_baseline in baseline.items():
        valor_atual = atual.get(metrica, 0.0)
        regrediu = valor_atual < valor_baseline - TOLERANCE
        linhas.append((metrica, valor_baseline, valor_atual, regrediu))
    return linhas


def formatar_tabela(linhas: list[tuple[str, float, float, bool]]) -> str:
    cabecalho = "| métrica | baseline | atual | status |\n|---|---|---|---|"
    corpo = "\n".join(
        f"| {metrica} | {valor_baseline:.2f} | {valor_atual:.2f} | {'FALHOU' if regrediu else 'OK'} |"
        for metrica, valor_baseline, valor_atual, regrediu in linhas
    )
    return f"{cabecalho}\n{corpo}"


def main() -> None:
    init_db()

    baseline = json.loads(BASELINE_PATH.read_text())
    atual = runner()

    LAST_RUN_PATH.write_text(json.dumps(atual, indent=2, ensure_ascii=False))

    linhas = comparar(baseline, atual)
    tabela = formatar_tabela(linhas)
    print(f"\n{tabela}")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a") as summary:
            summary.write(f"\n## Resultado dos evals\n\n{tabela}\n")

    if any(regrediu for _, _, _, regrediu in linhas):
        print("FALHOU - regressão detectada")
        raise SystemExit(1)

    print("OK - dentro do limite aceitável")


if __name__ == "__main__":
    main()
