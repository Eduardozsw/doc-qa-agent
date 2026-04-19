from agent.orchestrator import orchestrator

query = input("Pergunta: ")
resposta = orchestrator(query)
print(resposta)