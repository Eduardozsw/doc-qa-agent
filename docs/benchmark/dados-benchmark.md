# Dados do benchmark — doc-qa-agent

Arquivo gerado a partir de `docs/benchmark/results-2026-09-18.json`, sem interpretação. Números, definições e limitações conhecidas.

## 1. O sistema medido
- Tipo: perguntas e respostas sobre documentos PDF (RAG).
- Stack: Python/FastAPI, PostgreSQL + pgvector, Redis (fila de ingestão), OpenAI API, frontend React.
- Pipeline de consulta (config `full`): expansão de consulta (LLM, só perguntas com < 8 palavras) → busca vetorial + full-text (Postgres) fundidas por RRF → rerank por LLM de 20 candidatos → 12 trechos ao LLM → resposta com marcadores de citação [n] → verificação por LLM + checagem determinística da citação no texto do trecho → bloqueio se não fundamentada.
- Modelos: chat `gpt-4o-mini` (todas as etapas), embedding `text-embedding-3-small`. Roteamento para `gpt-4o` desligado.
- Suíte de testes automatizados do repositório no momento da medição: 299 testes (pytest).

## 2. Condições do experimento
- Data: 2026-09-18. Commit: 98e5fca.
- Hardware: 12th Gen Intel(R) Core(TM) i5-1235U, 7.5 GB RAM, sem GPU. APIs da OpenAI via internet residencial.
- Corpus: 1 documento (Cadernos de Atenção Básica nº 37 — Hipertensão Arterial Sistêmica, Ministério da Saúde, 130 páginas, 334 chunks).
- Dataset: 50 perguntas — 30 factuais, 10 com premissa falsa, 10 com resposta ausente do documento.
- Repetições: 3 execuções completas do dataset por configuração (N = 150 execuções por configuração).
- Configurações: `naive` = só busca vetorial; `hybrid` = vetorial + full-text (RRF); `full` = hybrid + expansão de consulta + rerank por LLM. Cache semântico desligado nessas medições.

## 3. Definições das métricas
- Acurácia: fração de respostas com nota do juiz ≥ 0,7. Juiz = gpt-4o-mini comparando a resposta com um critério textual ("deve mencionar ..."), nota de 0 a 1.
- Correção de premissa: fração das perguntas com premissa falsa em que o verificador marcou `correcao=true`.
- Abstenção correta: fração das perguntas sem resposta no documento respondidas com a frase fixa "não encontrei". Alucinação = complemento.
- Falsa abstenção: fração das perguntas factuais respondidas com "não encontrei".
- Resposta com citação verificada: fração das respostas (excluindo abstenções e perguntas fora do documento) com ≥ 1 citação cujo texto foi encontrado no trecho citado (containment normalizado ou ≥ 80% dos 4-gramas).
- Precisão de citação: citações verificadas / citações totais.
- hit@k: fração das perguntas com página rotulada em que alguma página correta está entre os k primeiros trechos enviados ao LLM. MRR: média de 1/posição do primeiro acerto. n = 120 (40 perguntas com página rotulada × 3).
- Latências: medidas em processo (Python, `time.perf_counter`) por etapa; p50/p95 sobre 150 execuções.
- Custo: tokens reais de todas as chamadas à OpenAI do pipeline de consulta × preço público por token (gpt-4o-mini US$ 0,15/0,60 por 1M entrada/saída; text-embedding-3-small US$ 0,02/1M). Não inclui o juiz, infraestrutura nem armazenamento.

## 4. Qualidade (150 execuções por configuração)
| Métrica | naive | hybrid | full |
|---|---|---|---|
| Acurácia | 86.0% (129/150) | 90.7% (136/150) | 94.0% (141/150) |
| Correção de premissa | 90.0% (27/30) | 100.0% (30/30) | 100.0% (30/30) |
| Abstenção correta | 100.0% (30/30) | 100.0% (30/30) | 100.0% (30/30) |
| Alucinação | 0.0% (0/30) | 0.0% (0/30) | 0.0% (0/30) |
| Falsa abstenção | 10.0% (9/90) | 0.0% (0/90) | 3.3% (3/90) |
| Resposta com citação verificada | 92.8% (103/111) | 96.7% (116/120) | 97.4% (114/117) |
| Precisão de citação | 85.6% (160/187) | 86.7% (176/203) | 88.6% (186/210) |
| Nota média do juiz | 0.897 | 0.941 | 0.947 |

Desvio-padrão entre as 3 repetições (config full): avg_score 0.003, accuracy 0.000, correction_rate 0.000, abstain_correct_rate 0.000, hallucination_rate 0.000, false_abstention_rate 0.000, cited_rate 0.044, citation_precision 0.028.

## 5. Recuperação (n = 120 por configuração)
| Métrica | naive | hybrid | full |
|---|---|---|---|
| hit@1 | 50.0% | 45.0% | 71.7% |
| hit@3 | 82.5% | 75.0% | 92.5% |
| hit@5 | 87.5% | 80.0% | 97.5% |
| MRR | 0.644 | 0.609 | 0.816 |

## 6. Latência em ms (p50 / p95, 150 execuções)
| Etapa | naive | hybrid | full |
|---|---|---|---|
| Busca vetorial ou híbrida (sem LLM) | 425 / 748 | 443 / 909 | 561 / 840 |
| Busca de contexto completa (inclui expansão e rerank quando ligados) | 405 / 549 | 409 / 639 | 3151 / 6887 |
| Geração da resposta | 1488 / 2986 | 1496 / 2698 | 1613 / 2756 |
| Verificação | 1525 / 3291 | 1639 / 3131 | 1650 / 3014 |
| Total (busca + geração + verificação) | 3459 / 6708 | 3694 / 6235 | 6791 / 11380 |

## 7. Custo de API (US$)
| | naive | hybrid | full |
|---|---|---|---|
| Por pergunta | 0.00112 | 0.00127 | 0.00241 |
| Por 1.000 perguntas | 1.12 | 1.27 | 2.41 |

## 8. Ingestão (1 execução)
- 130 páginas → 334 chunks em 25.8 s (302 páginas/min), custo de embedding US$ 0.0022. Inclui extração do PDF, chunking, embeddings e gravação no Postgres. Executado em processo, não pela fila/worker.

## 9. Cache semântico (5 perguntas, 1 execução)
- 4 de 5 perguntas foram servidas pelo cache na 2ª chamada; a outra não foi cacheada. O sistema não grava no cache respostas "não encontrei" nem respostas bloqueadas pelo verificador; o conteúdo da resposta dessa execução não foi registrado pelo benchmark.
- Nas 4 com acerto: 1ª chamada média 9498 ms, 2ª chamada média 555 ms. O cache só casa perguntas com similaridade de cosseno ≥ 0,97 (paráfrases em geral não casam).

## 10. Ponta a ponta via HTTP (10 perguntas, stack em containers no mesmo notebook)
- Tempo até o primeiro token: mediana 7164 ms, mín. 6004, máx. 11375.
- Tempo total até o fim do stream: mediana 10950 ms, mín. 9184, máx. 14301.
- O primeiro token só é emitido após a busca completa (com rerank por LLM).

## 11. Limitações conhecidas
- Um único documento; resultados podem não se generalizar para outros documentos ou corpora com muitos documentos.
- As perguntas, os critérios esperados e as páginas rotuladas foram escritos pelo próprio desenvolvedor com auxílio de um agente de IA, a partir do documento. As páginas rotuladas passaram por checagem automática (termo-chave presente na página), não por revisão de especialista clínico.
- O juiz é o mesmo modelo usado no pipeline (gpt-4o-mini); pode haver viés a favor das respostas do próprio modelo. Não houve avaliação humana.
- 50 perguntas: cada pergunta pesa 2 pontos percentuais; as 3 repetições reduzem a variação do LLM, não o tamanho da amostra.
- A correção de premissa é detectada pelo verificador (LLM), não por gabarito; a métrica mede se o sistema sinalizou correção, não se o texto da correção está perfeito.
- Durante o desenvolvimento, um exemplo do prompt coincidia com um caso do eval; foi removido antes desta medição e há um teste que impede reincidência.
- Latências medidas num notebook com internet residencial; dependem majoritariamente da latência da API da OpenAI.
- Não há medição de carga/concorrência; o endpoint de consulta tem limite de 5 requisições/min por usuário.
- Os preços usados no custo são os públicos da OpenAI na data da medição e podem mudar.
