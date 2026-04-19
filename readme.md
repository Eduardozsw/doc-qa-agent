# Doc Agent

Agente de Q&A sobre documentos que responde perguntas em linguagem natural com base no conteúdo de PDFs carregados, sem inventar informações fora do material fornecido. O acesso é restrito a usuários autenticados via Google OAuth.

## O que ele faz

Você faz login com sua conta Google, sobe um PDF, faz uma pergunta, e o agente busca os trechos mais relevantes do documento e gera uma resposta baseada exclusivamente neles. Se a informação não estiver no documento, ele diz que não encontrou — sem alucinação.

## Arquitetura

```
Google OAuth → Supabase Auth → JWT token
                                    ↓
PDF → loader → chunker → embedder → Pinecone
pergunta → orchestrator → retriever → Pinecone → answerer → resposta
                                                      ↓
                                               validator (guardrail)
```

### Autenticação

- `auth/middleware.py` — valida o JWT do Supabase em cada request da API
- **Supabase Auth** — gerencia sessões e OAuth com Google
- Todos os endpoints da API exigem `Authorization: Bearer <token>`
- Tabela `profiles` no Supabase armazena o plano do usuário (`free`, `basic`, `premium`)

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
- **Supabase** — autenticação (Google OAuth) e perfis de usuário
- **Langfuse** — observabilidade: tempo de resposta e consumo de tokens
- **Pinecone** — banco vetorial
- **FastAPI** — API backend
- **React + Vite** — frontend

## Como rodar localmente

### 1. Instalar dependências

```bash
cd backend
pip install -r requirements.txt
```

> **Windows:** o pacote `supabase` requer compilação C++. Instale o [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) marcando "Desenvolvimento para desktop com C++" antes de rodar o pip install.

```bash
cd frontend
npm install
```

### 2. Configurar variáveis de ambiente

**Backend:**
```bash
cp backend/.env.example backend/.env
```

Preencha o `.env`:

```
ANTHROPIC_API_KEY=sua_chave
OPENAI_API_KEY=sua_chave
PINECONE_API_KEY=sua_chave
PINECONE_INDEX=doc-qa
SUPABASE_URL=https://<projeto>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sua_secret_key
ALLOWED_ORIGINS=http://localhost:5173
```

**Frontend:**
```bash
cp frontend/.env.example frontend/.env
```

Preencha o `frontend/.env`:

```
VITE_SUPABASE_URL=https://<projeto>.supabase.co
VITE_SUPABASE_ANON_KEY=sua_publishable_key
```

### 3. Configurar o Supabase

1. Crie um projeto em [supabase.com](https://supabase.com)
2. Ative Google OAuth em **Authentication → Providers → Google**
3. Adicione `http://localhost:5173` em **Authentication → URL Configuration → Redirect URLs**
4. Execute o SQL abaixo no **SQL Editor**:

```sql
create table profiles (
  id uuid references auth.users on delete cascade,
  plan text not null default 'free',
  created_at timestamptz default now(),
  primary key (id)
);

alter table profiles enable row level security;

create policy "Users can view own profile" on profiles
  for select using (auth.uid() = id);

create policy "Users can update own profile" on profiles
  for update using (auth.uid() = id);

create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id) values (new.id);
  return new;
end;
$$ language plpgsql security definer set search_path = public;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
```

### 4. Subir o Redis

O projeto usa Redis para rastrear os documentos indexados. Suba uma instância local com Docker:

```bash
docker run -d --name redis-doc-qa -p 6379:6379 redis
```

A variável `REDIS_URL=redis://localhost:6379` já está configurada no `.env.example`.

### 5. Subir a API

```bash
cd backend
uvicorn api:app --reload
```

Em caso do comando não funcionar, tente:
```bash
cd backend
python -m uvicorn api:app --reload
```

### 6. Subir o frontend

```bash
cd frontend && npm run dev
```

Acesse `http://localhost:5173` — você será redirecionado para a tela de login.

### 7. Rodar os evals

```bash
cd backend
python check_regression.py
```

## Endpoints

Todos os endpoints exigem o header `Authorization: Bearer <token>`.

### `POST /ingest`

Recebe arquivos PDF e indexa o conteúdo no Pinecone.

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Authorization: Bearer <token>" \
  -F "files=@documento.pdf"
```

Resposta:
```json
{ "message": "12 chunks indexados", "arquivos": ["documento"] }
```

### `GET /ingest`

Lista os documentos indexados.

```bash
curl http://localhost:8000/ingest \
  -H "Authorization: Bearer <token>"
```

### `DELETE /ingest`

Remove documentos indexados.

```bash
curl -X DELETE http://localhost:8000/ingest \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"namespaces": ["documento"]}'
```

### `POST /query`

Recebe uma pergunta e retorna a resposta baseada nos documentos indexados.

```bash
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "Como fazer autenticação?", "namespaces": ["documento"]}'
```

Resposta:
```json
{ "resposta": "A autenticação é feita via Bearer Token no header Authorization." }
```

## Planos de usuário

O campo `plan` na tabela `profiles` suporta os valores `free`, `basic` e `premium`. Por ora o plano é apenas informativo e visível no menu do usuário — a integração com meio de pagamento será adicionada futuramente.

## Evals e CI/CD

O projeto usa LLM-as-judge para avaliar a qualidade das respostas automaticamente. A cada push, o GitHub Actions roda o dataset de casos de teste e compara o score com o baseline salvo em `baselines/main.json`. Se o score cair mais de 5% abaixo do baseline, o pipeline falha.

Score baseline atual: **0.75**

## Limitações conhecidas

O score dos evals pode variar entre runs devido à natureza probabilística do retriever — o Pinecone pode retornar chunks ligeiramente diferentes para a mesma query. Uma solução mais robusta seria usar média de múltiplas runs para estabilizar a métrica.
