# MindDoc

Agente de Q&A sobre PDFs: você sobe um documento, faz perguntas em linguagem natural e recebe respostas
em streaming baseadas apenas no conteúdo do arquivo, com um guardrail que bloqueia respostas sem base no
material indexado. Também gera um resumo estruturado do PDF e mantém histórico de conversa por documento.

Projeto de portfólio: roda inteiramente local (Postgres, Redis, backend e frontend em containers ou
nativo), sem depender de contas de terceiros além de uma chave de API da OpenAI.

## O que faz

- Upload de PDF (assíncrono, via fila) e acompanhamento do status de indexação.
- Perguntas e respostas em streaming (SSE), com a fonte (trecho + página) usada para responder.
- Guardrail de validação: se a resposta não tiver base nos trechos recuperados, o agente recusa em vez de
  inventar.
- Resumo automático do PDF, com cache por hash do arquivo (mesmo PDF reaproveita o resumo/indexação).
- Histórico de conversa por usuário, com sumarização das trocas mais antigas para não perder contexto.
- Login local com email/senha (JWT), sem OAuth externo.

## Arquitetura

```
                         ┌────────────┐        ┌─────────────┐
   navegador  ───────▶   │  frontend  │──/api─▶│   FastAPI   │
                         │ React+Vite │        │  (backend)  │
                         └────────────┘        └──────┬──────┘
                                                       │
                              upload PDF               │ pergunta
                                 │                      ▼
                                 ▼               ┌─────────────┐
                          ┌────────────┐         │  rewriter   │
                          │Redis (fila)│         └──────┬──────┘
                          └─────┬──────┘                ▼
                                │                ┌─────────────┐
                                ▼                │  retriever  │──▶ pgvector (Postgres)
                          ┌────────────┐         └──────┬──────┘
                          │   worker   │                ▼
                          │ (Python)   │         ┌─────────────┐
                          └─────┬──────┘         │  answerer   │──▶ OpenAI gpt-4o-mini
                                │                 └──────┬──────┘
                    embeddings  ▼                        ▼
                  OpenAI text-embedding-3-small   ┌─────────────┐
                                │                 │  validator  │  (guardrail)
                                ▼                 └─────────────┘
                        Postgres + pgvector
                     (chunks, usuários, jobs,
                      conversas, resumos)
```

Fluxo de ingestão: PDF enviado → job na fila Redis → worker extrai texto, faz chunking, gera embeddings na
OpenAI e grava os vetores no Postgres (extensão `pgvector`).

Fluxo de pergunta: pergunta → *rewriter* (reformula com contexto do histórico) → *retriever* (busca híbrida
no `pgvector`, por namespace/documento) → *answerer* (`gpt-4o-mini`, responde só com os trechos recuperados)
→ *validator* (guardrail que verifica se a resposta é sustentada pelo contexto).

Busca híbrida: o retriever combina similaridade vetorial (`pgvector`, cosseno) com busca full-text do
Postgres (`tsvector`/`tsquery` na configuração `portuguese`, útil para siglas e termos exatos que o
embedding às vezes dilui) e funde os dois rankings por Reciprocal Rank Fusion. Dá pra desligar via
`HYBRID_SEARCH=false` e cair na busca puramente vetorial. Chunker atual (`v2`) quebra o texto por token
(`tiktoken`) respeitando fronteira de sentença, em vez de cortar por contagem fixa de palavras; documentos
indexados antes desta versão continuam funcionando, mas reenvie o PDF para aproveitar o chunker novo.

Acima do retrieve híbrido, `agent/search.py` roda um pipeline de duas otimizações opcionais: expansão de
consulta (`MULTI_QUERY_ENABLED`, default `true`) gera até 3 reformulações em PT-BR para perguntas curtas
(< 8 palavras) e une os resultados por RRF antes de seguir; e um reranker listwise (`RERANK_ENABLED`,
default `true`) usa `gpt-4o-mini` para reordenar os `RERANK_CANDIDATES` (default 20) melhores candidatos por
relevância (0-3) antes do corte final. Ambos são fail-open: qualquer erro do LLM devolve o ranking anterior
em vez de quebrar a resposta.

Extração estruturada (`ingestion/loader.py`, chunker `v3`): tabelas do PDF (`page.find_tables()`) viram
markdown no lugar do bloco original — é assim que a Tabela 3 do CAB 37 (classificação da pressão arterial)
chega inteira a um único chunk — e títulos (fonte maior ou negrito curto) viram linhas `## Título`;
cabeçalho/rodapé repetido é removido. O chunker nunca deixa um `## Título` sozinho no fim de um chunk nem
quebra uma tabela markdown no meio (tabelas grandes são fatiadas por linha, repetindo o cabeçalho).
Contextual retrieval (`ingestion/contextualizer.py`, `CONTEXTUAL_RETRIEVAL_ENABLED`, default `false`): 1
chamada a `gpt-4o-mini` por chunk gera 1-2 frases situando o trecho no documento, usadas só no embedding
(o texto citado/exibido continua o original) — custo de +1 chamada mini por chunk na ingestão, fail-open.
Vem desligado por padrão: medido no CAB 37 (documento único de 130 páginas), não trouxe ganho — hit@5, MRR
e citation_rate pioraram vs. sem contexto — porque o prefixo tende a ajudar mais em corpora com muitos
documentos parecidos, não num documento longo isolado. Ligue com `CONTEXTUAL_RETRIEVAL_ENABLED=true`.
OCR opcional (`OCR_ENABLED`, default `false`) usa `pytesseract` quando uma página não tem texto extraível
(PDF escaneado); exige `tesseract-ocr` + `tesseract-ocr-por` no host e `uv sync --extra ocr`.

## Stack

- **Backend**: FastAPI, Postgres + `pgvector` (dados relacionais e vetores no mesmo banco), Redis (fila de
  ingestão), OpenAI (`gpt-4o-mini` para geração, `text-embedding-3-small` para embeddings).
- **Frontend**: React + Vite, TypeScript.
- **Auth**: JWT (HS256) local, senha com hash `bcrypt`. Sem OAuth/terceiros.
- **Toolchain**: `uv` (Python/backend), `npm` (frontend), Podman/Docker Compose para orquestração.

## Pré-requisitos

- Uma chave de API da OpenAI (`OPENAI_API_KEY`) — necessária mesmo para rodar localmente, pois a
  geração de respostas e os embeddings usam a API da OpenAI.
- Para rodar via compose: Docker ou Podman com suporte a `docker compose` (Podman rootless funciona; o
  comando `docker` pode ser o shim do `podman-docker`).
- Para rodar nativo: `uv` (Python 3.12) e `npm` (Node — ver `.nvmrc`/`.mise.toml` do frontend).

## Como rodar com Docker/Podman Compose

```bash
cp backend/.env.example backend/.env   # edite OPENAI_API_KEY e JWT_SECRET
docker compose up --build -d
```

Acesse `http://localhost:8080` e faça login com o usuário demo `demo@local` / `demo1234`.

O compose sobe `postgres` (`pgvector/pgvector:pg16`) e `redis` sem publicar as portas 5432/6379 no host
(para não conflitar com instâncias locais); `backend` fica em `8000` e `frontend` (nginx servindo o build
+ proxy de `/api/` para o backend) em `8080`. Nenhum serviço usa a porta 80 do host.

```bash
docker compose down          # para tudo
docker compose down -v       # também remove o volume do Postgres
```

## Como rodar nativo

```bash
# Postgres e Redis (fora do compose)
podman run -d --name pg    -p 5432:5432 -e POSTGRES_USER=docqa -e POSTGRES_PASSWORD=docqa -e POSTGRES_DB=docqa pgvector/pgvector:pg16
podman run -d --name redis -p 6379:6379 redis:alpine

# Backend (terminal 1)
cd backend
cp .env.example .env   # edite OPENAI_API_KEY e JWT_SECRET
uv sync
uv run uvicorn main:app --reload

# Worker de ingestão (terminal 2)
cd backend
uv run python worker.py

# Frontend (terminal 3)
cd frontend
npm ci
npm run dev   # http://localhost:5173, proxy /api -> localhost:8000
```

O schema do Postgres (`CREATE TABLE IF NOT EXISTS ...` e a extensão `vector`) é criado automaticamente no
boot da API e do worker; não há passo manual de migração.

## PDF de exemplo

```bash
cd backend
uv run python scripts/fetch_demo_pdf.py
```

Baixa o Caderno de Atenção Básica nº 37 (Hipertensão Arterial Sistêmica, Ministério da Saúde) para
`backend/docs/examples/`, usado nos evals e para testar manualmente o fluxo de upload/pergunta/resumo.

## Testes

```bash
cd backend
uv run pytest -q
```

Testes marcados com `@pytest.mark.db` exigem um Postgres real e são pulados automaticamente se ele não
responder; os demais mockam as camadas `db.*` e não precisam de infraestrutura.

## Evals

Avaliação de qualidade das respostas com LLM-as-judge (OpenAI), rodando um dataset fixo de perguntas sobre
o PDF de exemplo e comparando com um baseline salvo (`baseline/main.json`, score 0.75, tolerância 0.05):

```bash
cd backend
uv run python scripts/fetch_demo_pdf.py
uv run python check_regression.py
```

Não roda a cada push (custa tokens de API): é um workflow manual (`workflow_dispatch`) no GitHub Actions.

## Endpoints

Prefixo `/api`. Todos exceto `auth/register` e `auth/login` exigem `Authorization: Bearer <token>`.

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/auth/register` | Cria usuário (plano `pro`) |
| POST | `/api/auth/login` | Login, devolve `access_token` |
| GET | `/api/auth/me` | Dados do usuário autenticado |
| PATCH | `/api/auth/me` | Atualiza nome/senha |
| POST | `/api/auth/logout` | Logout (stateless, sem efeito no servidor) |
| GET | `/api/ingest` | Lista documentos indexados |
| POST | `/api/ingest` | Envia PDF(s), enfileira job de indexação |
| GET | `/api/ingest/status` | Status de um job de ingestão |
| DELETE | `/api/ingest` | Remove documento(s) e seus vetores |
| POST | `/api/query` | Pergunta, resposta completa |
| POST | `/api/query/stream` | Pergunta, resposta em streaming (SSE) |
| DELETE | `/api/query/history` | Limpa histórico de conversa |
| POST | `/api/summarize` | Gera/reaproveita resumo de um documento |
| GET | `/api/summarize` | Lista resumos disponíveis |
| GET | `/health` | Liveness |
| GET | `/health/db` | Status do Postgres e do Redis |

## Limites por plano

O código mantém o conceito de planos (`core/limits.py`), mas como não há cobrança, todo usuário criado
localmente nasce com plano `pro` (limite mais alto de perguntas, documentos e resumos por mês). Os planos
`free`/`solo` continuam existindo no código só para não descartar essa lógica, mas não são atribuíveis por
nenhum fluxo da aplicação.

## Observabilidade (opcional)

O backend suporta tracing via [Langfuse Cloud](https://cloud.langfuse.com), desligado por padrão. Sem as
chaves, nada relacionado ao langfuse é importado ou inicializado — o comportamento é idêntico ao de não ter
essa seção no código.

Para habilitar:

1. Crie um projeto gratuito em https://cloud.langfuse.com (ou https://us.cloud.langfuse.com para a região US).
2. Copie `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` e `LANGFUSE_BASE_URL` do projeto para `backend/.env`
   (ver `backend/.env.example`).
3. Reinicie a API.

Com as chaves configuradas, cada pergunta gera um trace (`doc-qa` ou `doc-qa-stream`) com spans para
reescrita da pergunta, busca de trechos, geração da resposta e validação, além de uma generation por
chamada à OpenAI com tokens e custo calculados automaticamente. Respostas bloqueadas (sem trechos ou
reprovadas pelo validador) ficam marcadas com a tag `blocked`.

## Decisões e limitações

Este projeto foi originalmente construído sobre serviços de produção (Supabase, Pinecone, Stripe/PIX,
Resend, Langfuse) que exigiam contas e chaves que não fazia sentido manter só para portfólio. Para rodar
de forma reproduzível — na minha máquina e na de quem for avaliar — cada um foi substituído por algo local
equivalente:

- **Supabase (auth + tabelas)** → Postgres próprio + JWT local (`pyjwt` + `bcrypt`). Sem OAuth/Google, sem
  recuperação de senha por email.
- **Pinecone (banco vetorial)** → `pgvector` na mesma instância de Postgres (um serviço a menos para rodar).
- **Stripe/PIX, Resend (billing e email)** → removidos; sem cobrança, todo usuário é `pro`.
- **Langfuse (observabilidade)** → opcional via Langfuse Cloud (ver seção "Observabilidade" acima); sem
  chaves configuradas, o backend roda sem tocar nessa dependência.
- O LLM de produção continua sendo a API da OpenAI (`gpt-4o-mini` e `text-embedding-3-small`); não há
  configuração para outro provedor.

Sem números de performance/latência publicados aqui — não foram medidos de forma que valesse a pena
reportar; o baseline dos evals (0.75) é sobre qualidade de resposta (LLM-as-judge), não sobre performance.
