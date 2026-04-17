# Doc Agent

Agente de Q&A sobre documentos que responde perguntas em linguagem natural com base no conteúdo de PDFs carregados, sem inventar informações fora do material fornecido.

## O que ele faz

Você sobe um PDF, faz uma pergunta, e o agente busca os trechos mais relevantes do documento e gera uma resposta baseada exclusivamente neles. Se a informação não estiver no documento, ele diz que não encontrou — sem alucinação.

## Arquitetura

```
PDF → loader → chunker → embedder → Pinecone
pergunta → orchestrator → retriever → Pinecone → answerer → resposta
                                                      ↓
                                               validator (guardrail)
```

### Ingestion pipeline

- `ingestion/loader.py` — extrai texto de PDF, MD e TXT
- `ingestion/chunker.py` — divide o texto em chunks de 500 palavras com overlap de 50
- `ingestion/embedder.py` — gera embeddings com `text-embedding-3-small` da OpenAI e indexa no Pinecone

### Agent

- `agent/retriever.py` — converte a pergunta em embedding e busca os chunks mais relevantes no Pinecone
- `agent/answerer.py` — gera resposta usando Claude com os chunks como contexto
- `agent/orchestrator.py` — coordena o fluxo completo
- `guardrails/validator.py` — bloqueia respostas que não têm base nos documentos carregados

### Evals

- `evals/judge.py` — avalia qualidade das respostas com LLM-as-judge (score de 0 a 1)
- `evals/runner.py` — roda o dataset de casos de teste e calcula score médio
- `check_regression.py` — compara score atual com baseline e falha se cair mais de 5%
- CI/CD via GitHub Actions — bloqueia push se score regredir

## Stack

- **Claude** (Anthropic) — geração de respostas e avaliação LLM-as-judge
- **OpenAI** `text-embedding-3-small` — geração de embeddings
- **Langfuse** - observar tempo de resposta e consumo de tokens
- **Pinecone** — banco vetorial
- **FastAPI** — API backend
- **React + Vite** — frontend

## Como rodar localmente

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Preencha o `.env` com suas chaves:

```
ANTHROPIC_API_KEY=sua_chave
OPENAI_API_KEY=sua_chave
PINECONE_API_KEY=sua_chave
PINECONE_INDEX=doc-qa
```

### 3. Indexar o documento de exemplo

```bash
python -c "
from ingestion.loader import load_document
from ingestion.chunker import chunk_text
from ingestion.embedder import upsert_chunks

text = load_document('docs/examples/sample.txt')
chunks = chunk_text(text)
upsert_chunks(chunks, 'sample')
print(f'{len(chunks)} chunks indexados')
"
```

### 4. Subir a API

```bash
uvicorn api:app --reload
```
Em caso do comando não funcionar, tente o seguinte
```bash
python -m uvicorn api:app --reload
```
### 5. Subir o frontend

```bash
cd frontend
npm install
npm run dev
```

A interface estará disponível em `http://localhost:5173`.

### 6. Rodar os evals

```bash
python check_regression.py
```

## Endpoints

### `POST /ingest`

Recebe um arquivo PDF e indexa o conteúdo no Pinecone.

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@documento.pdf"
```

Resposta:
```json
{ "message": "12 chunks indexados" }
```

### `POST /query`

Recebe uma pergunta e retorna a resposta baseada nos documentos indexados.

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Como fazer autenticação?"}'
```

Resposta:
```json
{ "resposta": "A autenticação é feita via Bearer Token no header Authorization." }
```

## Evals e CI/CD

O projeto usa LLM-as-judge para avaliar a qualidade das respostas automaticamente. A cada push, o GitHub Actions roda o dataset de casos de teste e compara o score com o baseline salvo em `baselines/main.json`. Se o score cair mais de 5% abaixo do baseline, o pipeline falha.

Score baseline atual: **0.75**

## Limitações conhecidas

O score dos evals pode variar entre runs devido à natureza probabilística do retriever — o Pinecone pode retornar chunks ligeiramente diferentes para a mesma query. Uma solução mais robusta seria usar média de múltiplas runs para estabilizar a métrica.