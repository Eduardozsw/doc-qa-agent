from agent.orchestrator import orchestrator
from evals.judge import judge
import json
def runner() -> float:
    scores = []
    with open("evals/datasets/qa.json", "r") as file:
        data = json.load(file)
    
    for caso in data:
        resposta =orchestrator(caso["query"])
        score = judge(caso["query"], resposta, caso["esperado"])
        scores.append(score)
    total = sum(scores)
    return total / len(data)