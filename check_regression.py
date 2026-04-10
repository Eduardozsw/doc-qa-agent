import json
from evals.runner import runner

baseline = json.load(open("baseline/main.json", "r"))
score = runner()

print(f"score atual: {score:.2f}")
print(f"score baseline: {baseline['avg_score']:.2f}")

if score < baseline["avg_score"] - 0.05:
    print("FALHOU - regressão detectada")
    exit(1)

print("OK - dento do limite aceitável")