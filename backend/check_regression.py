import json
from pathlib import Path

from db.postgres import init_db
from evals.runner import runner

BASE_DIR = Path(__file__).parent
BASELINE_PATH = BASE_DIR / "baseline" / "main.json"

TOLERANCE = 0.05


def main() -> None:
    init_db()

    baseline = json.loads(BASELINE_PATH.read_text())
    score = runner()

    print(f"score atual: {score:.2f}")
    print(f"score baseline: {baseline['avg_score']:.2f}")

    if score < baseline["avg_score"] - TOLERANCE:
        print("FALHOU - regressão detectada")
        raise SystemExit(1)

    print("OK - dentro do limite aceitável")


if __name__ == "__main__":
    main()
