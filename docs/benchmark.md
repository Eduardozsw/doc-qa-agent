# Benchmark de produto — doc-qa-agent

Resultados da config `full` (híbrida + rerank + multi-query), 3 repetições:

- **Acurácia** (nota do juiz ≥ 0,7): 94% (141/150)
- **Nota média do juiz**: 0.95
- **Correção de premissa falsa**: 100% (30/30)
- **Abstenção correta** (fora do documento): 100% (30/30)
- **Taxa de alucinação** (fora do documento): 0% (0/30)
- **hit@3** de recuperação: 92% (n=120)
- **Busca híbrida** (pgvector + full-text, sem LLM): p50 561 ms / p95 840 ms
- **Busca de contexto completa** (expansão de consulta + híbrida + rerank por LLM): p50 3151 ms / p95 6887 ms
- **Ponta a ponta** (busca + geração + verificação): p50 6791 ms / p95 11380 ms
- **Custo**: US$ 0.0024/pergunta (US$ 2.41 por 1.000 perguntas)
- Ablação: hit@3 subiu de 82% (naive) para 92% (full)

## Metodologia

Cada config roda os componentes reais do pipeline (`agent.search.search`, `agent.retriever.retrieve`, `agent.answerer.answer`, `guardrails.validator.verify`) numa réplica instrumentada do `agent.orchestrator.orchestrator()` não-streaming (`benchmark/instrumented.py`), cronometrando cada etapa com `time.perf_counter()`. `retrieve()` é chamado uma vez a mais, fora da janela do tempo total, só para medir a busca híbrida/vetorial pura (sem rerank/multi-query) como métrica isolada.

As 3 configs de ablação (naive/hybrid/full) são aplicadas via variável de ambiente (`HYBRID_SEARCH`, `RERANK_ENABLED`, `MULTI_QUERY_ENABLED`) seguida de `get_settings.cache_clear()` — nunca editam `.env`. `MODEL_ROUTING_ENABLED` e o cache semântico ficam desligados em todas (medidos à parte). Cada config roda N repetições completas do dataset; percentis de latência (p50/p95) juntam TODAS as chamadas (todas as repetições e casos); taxas de qualidade/recuperação são calculadas sobre o conjunto de casos somado das repetições (N explícito em cada porcentagem), com a variação entre repetições (média ± desvio-padrão) reportada à parte.

O custo conta os tokens de toda chamada OpenAI do pipeline de consulta (chat e embeddings) via um wrapper instalado só durante o benchmark nos clients reais (`agent.answerer.client`, `guardrails.validator.client`, `agent.reranker.client`, `agent.query_rewriter.client`, `ingestion.embedder._client()`); o custo do juiz (`evals.judge.client`) é contado à parte, como "custo de avaliação", e nunca entra no custo por pergunta do produto. Preços por 1M tokens (US$, conferir em openai.com/api/pricing): gpt-4o-mini 0.15/0.60 (entrada/saída), gpt-4o 2.50/10.00, text-embedding-3-small 0.02.

## Ambiente

| Item | Valor |
|---|---|
| Data | 2026-09-18 |
| Commit | 867aba4 |
| CPU | 12th Gen Intel(R) Core(TM) i5-1235U |
| RAM | 7.5 GB |
| Modelo de chat | gpt-4o-mini |
| Modelo de chat forte | gpt-4o |
| Modelo de embedding | text-embedding-3-small |
| Dataset | 50 casos (30 factuais, 10 premissa falsa, 10 fora do documento) |
| Repetições | 3 |
| Configs rodadas | naive, hybrid, full |

## Qualidade

| Config | Acurácia | Nota média | Correção premissa | Abstenção correta | Alucinação | Falsa abstenção | Citação verificada | Precisão de citação |
|---|---|---|---|---|---|---|---|---|
| naive (RAG vetorial simples) | 86% (129/150) | 0.90 | 90% (27/30) | 100% (30/30) | 0% (0/30) | 10% (9/90) | 93% (103/111) | 86% (160/187) |
| hybrid (+ busca híbrida) | 91% (136/150) | 0.94 | 100% (30/30) | 100% (30/30) | 0% (0/30) | 0% (0/90) | 97% (116/120) | 87% (176/203) |
| full (híbrida + rerank + multi-query) | 94% (141/150) | 0.95 | 100% (30/30) | 100% (30/30) | 0% (0/30) | 3% (3/90) | 97% (114/117) | 89% (186/210) |

## Recuperação e ablação

| Config | hit@1 | hit@3 | hit@5 | MRR | n |
|---|---|---|---|---|---|
| naive (RAG vetorial simples) | 50% | 82% | 88% | 0.64 | 120 |
| hybrid (+ busca híbrida) | 45% | 75% | 80% | 0.61 | 120 |
| full (híbrida + rerank + multi-query) | 72% | 92% | 98% | 0.82 | 120 |

A busca híbrida sozinha ficou abaixo da vetorial no hit@3 (75% vs 82%): a fusão RRF promove trechos com muitas palavras em comum com a pergunta que nem sempre são a página rotulada. Mesmo assim, na qualidade de resposta a híbrida zerou a falsa abstenção (as palavras exatas trazem o trecho que o LLM precisa, ainda que não no topo). O ganho de ranking vem do rerank por LLM, que reordena os candidatos das duas buscas.

## Latência (p50/p95, ms)

### naive (RAG vetorial simples)

| Etapa | p50 | p95 | n chamadas |
|---|---|---|---|
| Busca de contexto (search) | 405 ms | 549 ms | 150 |
| Busca híbrida/vetorial (retrieve, sem rerank) | 425 ms | 748 ms | 150 |
| Geração (answer) | 1488 ms | 2986 ms | 150 |
| Verificação (verify) | 1525 ms | 3291 ms | 150 |
| Ponta a ponta | 3459 ms | 6708 ms | 150 |

### hybrid (+ busca híbrida)

| Etapa | p50 | p95 | n chamadas |
|---|---|---|---|
| Busca de contexto (search) | 409 ms | 639 ms | 150 |
| Busca híbrida/vetorial (retrieve, sem rerank) | 443 ms | 909 ms | 150 |
| Geração (answer) | 1496 ms | 2698 ms | 150 |
| Verificação (verify) | 1639 ms | 3131 ms | 150 |
| Ponta a ponta | 3694 ms | 6235 ms | 150 |

### full (híbrida + rerank + multi-query)

| Etapa | p50 | p95 | n chamadas |
|---|---|---|---|
| Busca de contexto (search) | 3151 ms | 6887 ms | 150 |
| Busca híbrida/vetorial (retrieve, sem rerank) | 561 ms | 840 ms | 150 |
| Geração (answer) | 1613 ms | 2756 ms | 150 |
| Verificação (verify) | 1650 ms | 3014 ms | 150 |
| Ponta a ponta | 6791 ms | 11380 ms | 150 |

## Custo

| Config | US$/pergunta | US$/1.000 perguntas | Custo de avaliação (juiz) | n perguntas |
|---|---|---|---|---|
| naive (RAG vetorial simples) | US$ 0.0011 | US$ 1.12 | US$ 0.0053 | 150 |
| hybrid (+ busca híbrida) | US$ 0.0013 | US$ 1.27 | US$ 0.0053 | 150 |
| full (híbrida + rerank + multi-query) | US$ 0.0024 | US$ 2.41 | US$ 0.0053 | 150 |

## Ingestão

Reindexação do PDF de demonstração no namespace `bench_ingest` (apagado antes e depois):

- Páginas: 130
- Chunks: 334
- Tempo total: 25.8 s
- Páginas/min: 302.5
- Contextualização (contextual retrieval) habilitada: False
- Custo de embedding: US$ 0.0022

## Cache semântico

5 perguntas, cada uma consultada 2x (fria, depois repetida) num namespace limpo (cache invalidado antes e depois). Latências calculadas só sobre as 4 em que a 2ª chamada veio do cache:

- Latência média fria (miss): 9498 ms
- Latência média com hit: 555 ms (17x mais rápido, sem chamada ao LLM)
- 1 pergunta(s) não foram cacheadas: por design, respostas "não encontrei" e respostas bloqueadas pelo verificador não entram no cache.

## HTTP ponta a ponta

10 perguntas via `POST /api/query/stream`, respeitando o limite de 5/min (dormindo 13s entre requisições):

- Time-to-first-token: mediana 7164 ms (mín. 6004, máx. 11375)
- Tempo total (até `[DONE]`): mediana 10950 ms (mín. 9184, máx. 14301)
- O primeiro token só sai depois da busca completa (expansão + híbrida + rerank), por isso o TTFT fica próximo da latência de busca somada ao início da geração.

## Limitações

- A nota de qualidade vem de um juiz LLM (gpt-4o-mini) com critério textual livre, não de um gabarito determinístico — pode divergir da avaliação humana caso a caso.
- Um único documento (Cadernos de Atenção Básica nº 37) indexado; retrieval/ablação não generalizam necessariamente para outros documentos ou domínios.
- Dataset de 50 casos: cada caso individual pesa ~2.0 pontos percentuais numa taxa — amostra pequena para produção real.
- Chamadas de LLM têm variação entre rodadas (temperature=0 reduz mas não elimina); a variabilidade entre repetições está reportada nos campos `*_variability` do JSON bruto.

## Como reproduzir

```bash
cd backend
uv run python -m benchmark.run --repeats 3 --configs naive,hybrid,full
# ponta a ponta via HTTP (compose no ar):
uv run python -m benchmark.run --skip-ingest --http-url http://localhost:8080 --http-n 10
```
