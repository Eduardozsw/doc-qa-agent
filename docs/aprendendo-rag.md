# Aprendendo RAG com o doc-qa-agent

Este documento acompanha a evolução do doc-qa-agent de um RAG "de tutorial" para um pipeline medido etapa por
etapa. Cada seção responde três perguntas: **o que é**, **onde entra no código** e **por que ajudou (ou não)**, sempre
com o número que as evals mostraram. A ideia é você conseguir explicar cada decisão numa entrevista, e também saber
quando **não** aplicar uma técnica.

> Conjunto de avaliação: CAB 37 (Hipertensão, Ministério da Saúde, ~130 páginas), 19 perguntas — 10 factuais,
> 5 com premissa falsa, 4 cuja resposta não está no documento. Juiz: gpt-4o-mini. Números de uma rodada cada;
> a variação entre rodadas é de ±0,05 a 0,07 (ver seção 11).

---

## 1. O mapa do pipeline

```
INGESTÃO (worker)                                   CONSULTA (API)
PDF ─▶ extração estruturada ─▶ chunker ─▶ embed ─▶  pergunta ─▶ cache? ─▶ reescrita (histórico)
        (tabelas, títulos)     (sentença,   │           │                     │
                                tokens)     ▼           ▼                     ▼
                                     Postgres: pgvector + tsvector ◀── busca híbrida (RRF)
                                                                          │
                                           expansão de consulta ─▶ rerank (LLM) ─▶ top-12
                                                                          │
                          resposta com [n] ◀── LLM (citar, corrigir premissa) ◀┘
                                 │
                          verificador (citação literal conferida no chunk) ─▶ payload + SSE
```

Quase todo problema de qualidade de um RAG cai em um destes três lugares:

| Sintoma | Onde costuma estar o problema |
|---|---|
| "Não encontrei" quando a resposta está no documento | **Recuperação** (o trecho certo não chegou ao LLM) |
| Resposta errada com trecho certo no contexto | **Geração** (prompt, modelo, contexto demais/de menos) |
| Resposta certa mas sem como provar | **Rastreabilidade** (citação, página, verificação) |

A primeira lição do projeto: **você só sabe em qual dos três está se medir cada um separadamente.**

---

## 2. Medir antes de mexer (Fase 0)

**O que é.** Separar a métrica de recuperação da métrica de resposta.

- `hit@k`: fração das perguntas em que alguma página correta aparece entre os k primeiros trechos.
- `MRR` (Mean Reciprocal Rank): média de 1/posição do primeiro acerto. Acertar em 1º vale 1; em 4º vale 0,25.
- `answer_score`: juiz LLM compara a resposta com o critério esperado (0 a 1).

**Onde.** `backend/evals/retrieval.py`, `backend/evals/runner.py`, `backend/check_regression.py`. Cada caso do
`qa.json` tem `paginas_relevantes`, rotuladas buscando os termos no PDF.

**O que o número mostrou.**

| answer_score | hit@3 | hit@5 | MRR |
|---|---|---|---|
| **0,84** | **0,30** | 0,50 | **0,21** |

A resposta parecia boa (0,84), mas em 7 de 10 perguntas a página certa nem estava entre os 3 primeiros trechos.
O gpt-4o-mini "salvava" com 10 trechos de contexto. Esse é o padrão mais comum em RAG de mercado: **a geração
esconde a recuperação ruim**, até o dia em que a pergunta é um pouco mais difícil.

**Duas armadilhas que apareceram ao rotular:**
1. Dois casos esperavam respostas que **não existem no PDF** (o CID-10 "I10" e o "nitroprussiato"). Um eval
   assim premia alucinação: o sistema tira nota alta inventando. Viraram casos `fora_do_documento`, que testam se o
   sistema admite não saber. Sempre confira se o "gabarito" está de fato na fonte.
2. Um juiz LLM com nota contínua é ruidoso. Métricas determinísticas (hit@k, MRR, citação verificada) são mais
   confiáveis para gate de CI; o juiz é complemento.

> **Para aplicar em qualquer projeto:** antes de qualquer técnica nova, monte 15–30 perguntas com a página/trecho
> certo rotulado. Sem isso, "melhorou" é opinião.

---

## 3. Citação verificável e correção de premissa (Fase 1)

Este foi o pedido original: responder com embasamento e corrigir o usuário quando a pergunta parte de algo falso.

### 3.1 Rotular o contexto

**Antes** (`answerer.py`): os trechos iam colados com `"\n\n"`. O modelo não tinha como dizer "isto vem do trecho 3".

**Depois** (`agent/context.py`):
```
<trecho id="1" documento="cab37.pdf" pagina="74">
...a meta pressórica para diabéticos é < 130/80 mmHg...
</trecho>
```
Com ids, o prompt pode exigir `[n]` depois de cada afirmação, e o backend sabe exatamente quais trechos foram
usados. `fontes` deixou de ser "o chunk de maior score" e passou a ser "os documentos realmente citados".

### 3.2 Corrigir premissa sem inventar

O prompt distingue três situações, e essa distinção é o que torna a correção confiável:

| Situação | Comportamento |
|---|---|
| Documento **contradiz** a premissa | `> **Correção:** ... Segundo o documento, "citação" [n].` e responde a pergunta corrigida |
| Documento **não fala** da premissa | Diz que o documento não confirma — **sem** "Correção" (ausência ≠ erro) |
| Nada relevante | Frase fixa de "não encontrei" |

Um exemplo few-shot no prompt ensinou o formato melhor do que qualquer instrução. Resultado: **5/5** perguntas
com premissa falsa corrigidas.

**Um erro meu que vale como lição.** O primeiro exemplo few-shot era "a meta pressórica para diabéticos não é
140/90" — ou seja, **um dos próprios casos do eval**. No teste de ponta a ponta, o modelo copiou a citação do
exemplo ("a meta pressórica para diabéticos é menor que 130/80 mmHg"), que não existe com essas palavras no PDF. O
verificador pegou (`verificada=False`), mas o eval estava contaminado: aquele caso tinha a resposta pronta no
prompt. O exemplo foi trocado por um de outro domínio (prazo de rescisão de contrato), com a instrução "nunca
reutilize frases do exemplo", e um teste (`test_system_prompt_nao_vaza_casos_do_eval`) falha se algum valor dos
casos do eval aparecer no prompt. Depois da troca, a correção continuou em **5/5** — o comportamento é real — mas a
nota do caso de diabéticos caiu de 1,0 para 0,6 e a nota média ficou em ~0,86 (duas rodadas: 0,83 e 0,88), contra
~0,92 antes. Parte do número antigo era o exemplo "colando" a resposta.

> **Lição:** exemplos few-shot, dados de teste e casos de eval precisam ser disjuntos, como treino e teste em ML.
> Um exemplo do mesmo domínio que coincide com uma pergunta real vira resposta pronta.

### 3.3 Verificar a citação de forma determinística

O validador antigo respondia "sim/não". O novo (`guardrails/validator.py`) pede ao LLM, via **Structured Outputs**
(JSON schema estrito), a citação **literal** que sustenta cada `[n]` — e depois **o código** confere se o texto
existe no chunk. O LLM não consegue inventar uma citação que passe.

A primeira versão exigia igualdade exata e só 60% das citações passavam. O diagnóstico mostrou que em **todos** os
casos a primeira metade da citação estava no chunk: o que quebrava era texto de PDF (`relati- vamente`, `mmHG` vs
`mmHg`, bullets `\x07`) e citações longas demais. A solução:
- normalizar (casefold, remover hífen de quebra, remover pontuação);
- aceitar se ≥ 80% dos **4-gramas** de palavras da citação existem no chunk;
- pedir no prompt no máximo 30 palavras.

`citation_rate` foi de 0,60 para **0,80**, e depois para ~0,93 com a melhoria da recuperação.

> **Lição:** um verificador que é só outro LLM dizendo "sim" apenas adiciona custo. Grounding de verdade é
> **checagem determinística** contra a fonte. E quando a checagem falha muito, examine os casos: normalmente o
> problema é o texto, não o modelo.

### 3.4 Falhar fechado, com transparência

Você decidiu: se o verificador falhar, tentar de novo, avisar que está demorando e só entregar com garantia. Isso
virou até 3 tentativas com backoff, um evento SSE `status` ("está demorando mais que o normal") e bloqueio
(fail-closed) se todas falharem. Em saúde, uma resposta sem embasamento é pior que "não sei".

Um detalhe que só aparece em produção: a comparação `resposta == "Não encontrei..."` quebrava quando o modelo
acrescentava um ponto final. `is_sem_info()` normaliza antes de comparar. **Nunca compare texto gerado por LLM com
igualdade exata.**

---

## 4. Chunking (Fase 2)

**Antes:** 500 **palavras** fixas (~700 tokens), cortando frases ao meio.
**Depois** (`ingestion/chunker.py`): ~350 **tokens** (tiktoken), quebrando só em fim de sentença, com 60 tokens de
sobreposição.

**Por que tokens e não palavras:** o limite dos modelos é em tokens, e português com termos médicos tem mais tokens
por palavra. Por que sentença: um chunk que começa no meio de uma frase gera embedding pior e citação que não fecha.

**O efeito colateral que o eval pegou:** com chunks pela metade do tamanho e o mesmo top-8, o contexto enviado ao LLM
caiu ~60% e o `answer_score` despencou para **0,69**. Subindo para top-12 voltou a 0,83+.

> **Lição:** tamanho de chunk e top-k são **um único parâmetro** (orçamento de contexto). Mexeu em um, recalibre o
> outro.

`CHUNKER_VERSION` entra no nome do namespace de eval, então toda mudança de chunker reindexa o PDF de teste
sozinha. Sem isso, você mede o chunker novo sobre o índice velho sem perceber.

---

## 5. Busca híbrida (Fase 2)

**O que é.** Rodar em paralelo a busca vetorial (semântica) e a busca por palavra-chave (léxica), e fundir os
rankings.

**Por quê.** Embeddings são ótimos para paráfrase ("pressão alta" ≈ "hipertensão") e ruins para tokens exatos:
siglas, códigos (I10), doses (130/80), nomes de medicamento. Palavra-chave é o oposto. Em documento médico você
precisa dos dois.

**Onde.**
- `db/postgres.py`: coluna gerada `tsv = to_tsvector('portuguese', text)` com índice GIN. Coluna **gerada**
  preenche as linhas existentes sozinha, sem reindexar.
- `db/vectors.py: query_keyword` e `agent/retriever.py`.

**RRF (Reciprocal Rank Fusion).** Os scores das duas buscas não são comparáveis (cosseno vs `ts_rank`). O RRF
ignora o valor e usa só a posição: `score = Σ 1/(60 + posição)`. Simples, sem parâmetro para ajustar, e é o padrão
de mercado.

**A armadilha da vez:** a primeira versão usava `websearch_to_tsquery`, que faz **AND** de todos os termos. Para
"Qual o limite de sódio na dieta para hipertensos?" isso exige todas as palavras no mesmo chunk e retornava vazio
em quase todas as perguntas: a "híbrida" estava, na prática, desligada, e os testes com mock não pegavam. A correção
foi montar um **OR** dos lexemas da própria pergunta (estilo BM25). Segunda armadilha: re-aplicar o stemmer
`portuguese` em lexemas já reduzidos corrompe palavras (`sódi` → `sód`), por isso o `to_tsquery` externo usa a
config `simple`.

| | answer | hit@3 | hit@8 | MRR | citação |
|---|---|---|---|---|---|
| Antes (F1) | 0,81 | 0,47 | 0,73 | 0,35 | 0,80 |
| Híbrida + chunker (F2) | **0,87** | **0,60** | **0,80** | **0,41** | **0,93** |

> **Lição:** teste com mock prova que o código chama as funções; só dado real prova que a busca encontra alguma
> coisa. Sempre inspecione o que cada braço da busca retorna para 2–3 perguntas reais.

---

## 6. Reranking e expansão de consulta (Fase 3)

**Reranker.** A busca devolve 20 candidatos; um segundo modelo lê a pergunta e os 20 trechos juntos e dá uma nota
de relevância (0–3) a cada um. Embedding compara vetores isolados; o reranker "lê" os dois textos lado a lado, por
isso ordena muito melhor.

- Mercado: cross-encoders (bge-reranker, Cohere Rerank). Aqui usamos o próprio gpt-4o-mini em modo *listwise*
  (`agent/reranker.py`) porque a máquina de desenvolvimento não tem GPU e um cross-encoder local exige PyTorch no
  Docker.
- Fail-open: se o reranker falhar, devolve a ordem da busca. Rerank é otimização, não requisito.

**Expansão de consulta (multi-query).** Perguntas curtas ganham até 3 reformulações (sinônimos, siglas por extenso),
cada uma busca, e os resultados se unem antes do rerank (`query_rewriter.expand_query`, `agent/search.py`).

**A armadilha:** o reranker priorizou trechos sobre "riscos" na pergunta "Considerando que o estágio 2 é PAS 140–159,
quais os riscos?" e descartou a tabela de classificação, justamente a evidência para corrigir a premissa. A
correção foi dizer ao reranker que trechos que **confirmam ou contradizem premissas** da pergunta são relevantes.
Toda etapa com LLM precisa conhecer o objetivo do sistema inteiro, não só a sua tarefa local.

| | answer | hit@3 | hit@5 | MRR | citação |
|---|---|---|---|---|---|
| F2 | 0,87 | 0,60 | 0,60 | 0,41 | 0,93 |
| + rerank + multi-query (F3) | **0,93** | **0,80** | **0,93** | **0,64** | **1,00** |

Foi o maior salto do projeto. Custo: +1 chamada ao mini por pergunta (+2 nas curtas); as evals passaram de ~2 para
~3,5 minutos.

---

## 7. Extração estruturada do PDF (Fase 4)

**O problema.** `page.get_text()` transforma tabela em uma sopa de números, e o cabeçalho "Ministério da Saúde |
Secretaria..." entrava em todo chunk, poluindo embedding e busca.

**O que foi feito** (`ingestion/loader.py`):
- `page.find_tables()` → tabela em **markdown**; o chunker trata a tabela como uma unidade indivisível.
- Títulos (fonte maior ou negrito curto) → linhas `## Título`, que nunca ficam órfãs no fim de um chunk.
- Cabeçalho e rodapé repetidos removidos.
- Fallback por página para `get_text()` se algo falhar; OCR opcional para páginas escaneadas.

A Tabela 3 (classificação da PA) passou a existir como `|Hipertensão estágio 2|160 – 179|100 – 109|`, recuperável
e citável.

Resultado: answer **0,95**, hit@3 **0,87**, MRR **0,67**.

> **Lição:** "garbage in, garbage out" vale mais para RAG do que para quase qualquer outro sistema. Antes de trocar
> modelo de embedding ou reranker, olhe o texto que você está indexando.

---

## 8. Quando uma técnica famosa não serve: contextual retrieval (Fase 4)

**O que é.** Técnica popularizada pela Anthropic: para cada chunk, um LLM escreve 1–2 frases situando o chunk no
documento ("este trecho é da seção de tratamento, sobre IECA em gestantes"), prefixadas antes do embedding.

**Onde.** `ingestion/contextualizer.py`. O texto original continua guardado separado, para que as citações
continuem literais.

**O que o eval mostrou (ablação: mesma rodada, com e sem):**

| | answer | hit@5 | MRR | citação |
|---|---|---|---|---|
| Sem contexto | **0,95** | **0,93** | **0,67** | **0,93** |
| Com contexto | 0,89 | 0,87 | 0,59 | 0,80 |

Piorou. A hipótese: a técnica brilha em corpora com **muitos documentos parecidos** (dezenas de contratos, manuais
de versões diferentes), onde o chunk sozinho é ambíguo sobre *de qual* documento é. Com um documento só, o prefixo
repete o mesmo assunto em todo chunk e dilui o que diferencia um trecho do outro. Ficou atrás de uma flag,
desligada.

> **Lição:** técnica de blog post é hipótese, não verdade. Rode ablação (liga/desliga, resto igual) e deixe o
> número decidir.

---

## 9. Produto: feedback, cache, conflitos, visualizador (Fases 5 e 6)

Estas fases não mexem em qualidade de resposta; mexem em **operar** o sistema.

**Feedback 👍/👎** (`POST /query/feedback`): grava no Postgres e anexa como score ao trace no Langfuse. É assim que
você descobre perguntas reais que falham e as transforma em casos de eval. **O eval set de um RAG em produção deve
crescer a partir do feedback negativo.**

**Cache semântico** (`db/query_cache.py`): se uma pergunta nova tem cosseno ≥ 0,97 com uma já respondida (mesmos
documentos), devolve a resposta salva. Medido: **10,5 s → 0,43 s**, sem chamar a OpenAI.
- Por que Postgres/pgvector e não Redis: Redis puro não faz busca por similaridade.
- Por que 0,97: um limiar baixo devolve a resposta de outra pergunta, que é o pior erro possível. Uma paráfrase como
  "meta de pressão arterial para pacientes diabéticos" **não** bate o limiar, e isso é intencional.
- Só sem histórico de conversa (senão a pergunta reescrita muda), invalidado ao apagar o documento, e **as evals
  passam `use_cache=False`**, senão da segunda rodada em diante você mede o cache, não o sistema.

**Conflitos entre documentos:** quando dois documentos divergem, a resposta mostra os dois lados com citação, e o
payload traz `conflitos`. Em protocolos clínicos de anos diferentes isso é comum.

**Visualizador de PDF:** o clique na citação abre o PDF na página e destaca o trecho. Isso exigiu **guardar o PDF**
(antes era apagado após indexar), o que tem custo de armazenamento. O componente é carregado sob demanda
(`React.lazy`), então o bundle principal continua com ~429 kB.

**Roteamento de modelo** (perguntas complexas → gpt-4o): implementado e desligado. Com e sem roteamento a diferença
ficou dentro do ruído (seção 11), e o gpt-4o custa ~15x mais. Sem evidência de ganho, não se paga o custo.

---

## 10. A evolução em uma tabela

| Fase | answer | hit@3 | hit@5 | MRR | citação | correção |
|---|---|---|---|---|---|---|
| F0 baseline | 0,84 | 0,30 | 0,50 | 0,21 | — | — |
| F1 citações + correção* | 0,81 | 0,47 | 0,60 | 0,35 | 0,80 | 1,00 |
| F2 híbrida + chunker | 0,87 | 0,60 | 0,60 | 0,41 | 0,93 | 1,00 |
| F3 rerank + multi-query | 0,93 | 0,80 | 0,93 | 0,64 | 1,00 | 1,00 |
| F4 extração estruturada | 0,95 | 0,87 | 0,93 | 0,67 | 0,93 | 1,00 |
| F5 feedback + cache | 0,95 | 0,87 | 1,00 | 0,69 | 0,93 | 1,00 |
| Após remover o vazamento do few-shot | 0,83–0,88 | 0,87 | 0,93 | 0,67 | 0,87 | 1,00 |

Os valores de `answer` de F1 a F5 estão levemente inflados: o exemplo do prompt continha um caso do eval (seção 3.2).

\* A mudança de hit@k entre F0 e F1 vem principalmente do **conjunto de eval** (2 casos saíram do cálculo de
recuperação e 5 de premissa falsa entraram), não do código. Quando o dataset muda, o baseline antigo deixa de ser
comparável. Registre isso sempre.

---

## 11. Sobre ruído e significância

Na Fase 6, duas rodadas seguidas do **mesmo código de recuperação** deram hit@5 de 1,00 e 0,93. Reranker, expansão
de consulta e juiz são LLMs, e há variação mesmo com `temperature=0`.

Com 15 perguntas rotuladas, **um caso vale 0,067**. Por isso a tolerância do gate de regressão é 0,07 ("um caso"),
e por isso diferenças menores que isso **não são evidência**, nem de melhora nem de piora. Consequências práticas:

- Só conclua "melhorou" quando a diferença passa de um caso **e** é coerente em várias métricas (como na F3).
- Para decisões finas (ex.: roteamento), aumente o conjunto de eval ou rode 3 vezes e compare médias.
- O próximo investimento de maior retorno neste projeto é **crescer o eval** para 50+ casos.

---

## 12. O que eu faria a seguir (em ordem de retorno)

1. **Eval maior e mais variado**: 50+ perguntas, incluindo multi-documento (dois protocolos que divergem) e
   perguntas de conversa (com histórico). Hoje não há caso que exercite conflitos nem o roteamento.
2. **Métricas de fidelidade por afirmação**: quebrar a resposta em afirmações e checar cada uma (estilo RAGAS
   *faithfulness*). O `citation_rate` atual só exige ≥ 1 citação verificada por resposta.
3. **Rodar evals 3x e reportar média ± desvio** no CI, para o gate não disparar por ruído.
4. **Cross-encoder de reranking** hospedado (API) no lugar do LLM listwise: mais barato por chamada e determinístico.
5. **Busca por metadados**: filtrar por seção (os `## títulos` já estão no texto) antes da busca.
6. **Streaming com verificação incremental**: hoje o texto é transmitido e só depois verificado; o usuário vê a
   resposta antes do selo "verificado". Uma alternativa é segurar o bloco de correção até a verificação.
7. **Guardrail de PII na entrada** (CPF, nomes de paciente) antes de mandar a pergunta para a API externa.

---

## 13. Checklist para qualquer RAG que você construir

- [ ] Existe um eval com a **fonte certa rotulada**, e o gabarito está de fato no documento?
- [ ] Recuperação e geração são medidas **separadamente**?
- [ ] O contexto enviado ao LLM tem **id, documento e página** por trecho?
- [ ] A citação é **verificada por código**, não por outro LLM dizendo "sim"?
- [ ] O sistema distingue **"o documento contradiz"** de **"o documento não fala disso"**?
- [ ] Chunk respeita sentença e tabela? Tamanho de chunk e top-k foram calibrados **juntos**?
- [ ] Há busca **léxica** além da vetorial para siglas, códigos e números?
- [ ] Cada técnica nova passou por **ablação** antes de ficar ligada por padrão?
- [ ] O gate de regressão tem tolerância **maior que o ruído** do seu eval?
- [ ] O feedback dos usuários **vira caso de eval**?
- [ ] Os exemplos few-shot do prompt são **disjuntos** dos casos de eval?
