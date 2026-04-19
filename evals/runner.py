from agent.orchestrator import orchestrator
from evals.judge import judge
import json

def runner() -> float:
    scores = []

    with open("evals/datasets/qa.json", "r") as file:
        data = json.load(file)

    for caso in data:
        resultado = orchestrator(caso["query"])
        score = judge(caso["query"], resultado["resposta"], caso["esperado"])
        print(f"[{score:.2f}] {caso['query'][:55]} → {resultado['resposta'][:70]}")
        scores.append(score)

    return sum(scores) / len(data)