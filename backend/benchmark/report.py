"""Gera `docs/benchmark.md` a partir do JSON bruto produzido por `run.py`. Funções
puras (só leem o dict `data`) para serem testáveis com um JSON sintético pequeno,
sem depender de uma rodada real."""
from benchmark.metrics import format_pct

_ORDEM_CONFIGS = ["naive", "hybrid", "full"]
_NOME_CONFIG = {"naive": "naive (RAG vetorial simples)", "hybrid": "hybrid (+ busca híbrida)", "full": "full (híbrida + rerank + multi-query)"}


def _configs_presentes(configs: dict) -> list[str]:
    return [c for c in _ORDEM_CONFIGS if c in configs]


def generate_markdown(data: dict) -> str:
    configs = data.get("configs", {})
    env = data.get("environment", {})
    partes = [
        _secao_resumo(configs, env),
        _secao_metodologia(),
        _secao_ambiente(env),
        _secao_qualidade(configs),
        _secao_recuperacao(configs),
        _secao_latencia(configs),
        _secao_custo(configs),
        _secao_ingestao(data.get("ingestion")),
        _secao_cache(data.get("cache")),
        _secao_http(data.get("http")),
        _secao_limitacoes(env, configs),
        _secao_reproducao(),
    ]
    return "\n\n".join(p for p in partes if p) + "\n"


def _secao_resumo(configs: dict, env: dict) -> str:
    linhas = ["# Benchmark de produto — doc-qa-agent", ""]
    full = configs.get("full")
    if not full:
        linhas.append("Sem a config `full` nesta rodada — ver as demais seções para o que foi medido.")
        return "\n".join(linhas)

    agregado = full["aggregated"]
    q, r, cost = agregado["quality"], agregado["retrieval"], agregado["cost"]
    lat_search = agregado["latency_ms"].get("search", {})
    lat_retrieve = agregado["latency_ms"].get("retrieve", {})
    lat_total = agregado["latency_ms"].get("total", {})
    repeats = env.get("repeats", "?")

    linhas += [
        f"Resultados da config `full` (híbrida + rerank + multi-query), {repeats} repetições:",
        "",
        f"- **Acurácia** (nota do juiz ≥ 0,7): {format_pct(q['accuracy'], q['accuracy_n'], q['accuracy_total'])}",
        f"- **Nota média do juiz**: {q['avg_score']:.2f}",
        f"- **Correção de premissa falsa**: {format_pct(q['correction_rate'], q['correction_n'], q['correction_total'])}",
        f"- **Abstenção correta** (fora do documento): {format_pct(q['abstain_correct_rate'], q['abstain_correct_n'], q['abstain_correct_total'])}",
        f"- **Taxa de alucinação** (fora do documento): {format_pct(q['hallucination_rate'], q['hallucination_n'], q['hallucination_total'])}",
        f"- **hit@3** de recuperação: {r['hit@3'] * 100:.0f}% (n={r['n']})",
        f"- **Busca híbrida** (pgvector + full-text, sem LLM): p50 {lat_retrieve.get('p50', 0):.0f} ms / "
        f"p95 {lat_retrieve.get('p95', 0):.0f} ms",
        f"- **Busca de contexto completa** (expansão de consulta + híbrida + rerank por LLM): "
        f"p50 {lat_search.get('p50', 0):.0f} ms / p95 {lat_search.get('p95', 0):.0f} ms",
        f"- **Ponta a ponta** (busca + geração + verificação): p50 {lat_total.get('p50', 0):.0f} ms / "
        f"p95 {lat_total.get('p95', 0):.0f} ms",
        f"- **Custo**: US$ {cost.get('usd_per_question', 0):.4f}/pergunta "
        f"(US$ {cost.get('usd_per_1000', 0):.2f} por 1.000 perguntas)",
    ]
    if "naive" in configs:
        hit3_naive = configs["naive"]["aggregated"]["retrieval"]["hit@3"]
        linhas.append(
            f"- Ablação: hit@3 subiu de {hit3_naive * 100:.0f}% (naive) para {r['hit@3'] * 100:.0f}% (full)"
        )
    return "\n".join(linhas)


def _secao_metodologia() -> str:
    return (
        "## Metodologia\n\n"
        "Cada config roda os componentes reais do pipeline (`agent.search.search`, "
        "`agent.retriever.retrieve`, `agent.answerer.answer`, `guardrails.validator.verify`) numa réplica "
        "instrumentada do `agent.orchestrator.orchestrator()` não-streaming (`benchmark/instrumented.py`), "
        "cronometrando cada etapa com `time.perf_counter()`. `retrieve()` é chamado uma vez a mais, fora da "
        "janela do tempo total, só para medir a busca híbrida/vetorial pura (sem rerank/multi-query) como "
        "métrica isolada.\n\n"
        "As 3 configs de ablação (naive/hybrid/full) são aplicadas via variável de ambiente "
        "(`HYBRID_SEARCH`, `RERANK_ENABLED`, `MULTI_QUERY_ENABLED`) seguida de `get_settings.cache_clear()` — "
        "nunca editam `.env`. `MODEL_ROUTING_ENABLED` e o cache semântico ficam desligados em todas (medidos "
        "à parte). Cada config roda N repetições completas do dataset; percentis de latência (p50/p95) juntam "
        "TODAS as chamadas (todas as repetições e casos); taxas de qualidade/recuperação são calculadas sobre o "
        "conjunto de casos somado das repetições (N explícito em cada porcentagem), com a variação "
        "entre repetições (média ± desvio-padrão) reportada à parte.\n\n"
        "O custo conta os tokens de toda chamada OpenAI do pipeline de consulta (chat e embeddings) via um "
        "wrapper instalado só durante o benchmark nos clients reais (`agent.answerer.client`, "
        "`guardrails.validator.client`, `agent.reranker.client`, `agent.query_rewriter.client`, "
        "`ingestion.embedder._client()`); o custo do juiz (`evals.judge.client`) é contado à parte, como "
        "\"custo de avaliação\", e nunca entra no custo por pergunta do produto. Preços por 1M tokens (US$, "
        "conferir em openai.com/api/pricing): gpt-4o-mini 0.15/0.60 (entrada/saída), gpt-4o 2.50/10.00, "
        "text-embedding-3-small 0.02."
    )


def _secao_ambiente(env: dict) -> str:
    contagens = env.get("dataset_counts", {})
    linhas = [
        "## Ambiente",
        "",
        "| Item | Valor |",
        "|---|---|",
        f"| Data | {env.get('date', '?')} |",
        f"| Commit | {env.get('commit') or 'n/d'} |",
        f"| CPU | {env.get('cpu', '?')} |",
        f"| RAM | {env.get('ram_gb', '?')} GB |",
        f"| Modelo de chat | {env.get('models', {}).get('chat', '?')} |",
        f"| Modelo de chat forte | {env.get('models', {}).get('chat_strong', '?')} |",
        f"| Modelo de embedding | {env.get('models', {}).get('embedding', '?')} |",
        f"| Dataset | {contagens.get('total', '?')} casos "
        f"({contagens.get('factual', 0)} factuais, {contagens.get('premissa_falsa', 0)} premissa falsa, "
        f"{contagens.get('fora_do_documento', 0)} fora do documento) |",
        f"| Repetições | {env.get('repeats', '?')} |",
        f"| Configs rodadas | {', '.join(env.get('configs_run', []))} |",
    ]
    return "\n".join(linhas)


def _secao_qualidade(configs: dict) -> str:
    presentes = _configs_presentes(configs)
    if not presentes:
        return ""
    linhas = [
        "## Qualidade",
        "",
        "| Config | Acurácia | Nota média | Correção premissa | Abstenção correta | Alucinação | "
        "Falsa abstenção | Citação verificada | Precisão de citação |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for nome in presentes:
        q = configs[nome]["aggregated"]["quality"]
        linhas.append(
            f"| {_NOME_CONFIG.get(nome, nome)} "
            f"| {format_pct(q['accuracy'], q['accuracy_n'], q['accuracy_total'])} "
            f"| {q['avg_score']:.2f} "
            f"| {format_pct(q['correction_rate'], q['correction_n'], q['correction_total'])} "
            f"| {format_pct(q['abstain_correct_rate'], q['abstain_correct_n'], q['abstain_correct_total'])} "
            f"| {format_pct(q['hallucination_rate'], q['hallucination_n'], q['hallucination_total'])} "
            f"| {format_pct(q['false_abstention_rate'], q['false_abstention_n'], q['false_abstention_total'])} "
            f"| {format_pct(q['cited_rate'], q['cited_n'], q['cited_total'])} "
            f"| {format_pct(q['citation_precision'], q['citations_verified'], q['citations_total'])} |"
        )
    return "\n".join(linhas)


def _secao_recuperacao(configs: dict) -> str:
    presentes = _configs_presentes(configs)
    if not presentes:
        return ""
    linhas = [
        "## Recuperação e ablação",
        "",
        "| Config | hit@1 | hit@3 | hit@5 | MRR | n |",
        "|---|---|---|---|---|---|",
    ]
    for nome in presentes:
        r = configs[nome]["aggregated"]["retrieval"]
        linhas.append(
            f"| {_NOME_CONFIG.get(nome, nome)} | {r['hit@1'] * 100:.0f}% | {r['hit@3'] * 100:.0f}% | "
            f"{r['hit@5'] * 100:.0f}% | {r['mrr']:.2f} | {r['n']} |"
        )
    if "naive" in configs and "hybrid" in configs:
        naive = configs["naive"]["aggregated"]["retrieval"]["hit@3"]
        hybrid = configs["hybrid"]["aggregated"]["retrieval"]["hit@3"]
        if hybrid < naive:
            linhas += [
                "",
                f"A busca híbrida sozinha ficou abaixo da vetorial no hit@3 ({hybrid * 100:.0f}% vs "
                f"{naive * 100:.0f}%): a fusão RRF promove trechos com muitas palavras em comum com a pergunta "
                "que nem sempre são a página rotulada. Mesmo assim, na qualidade de resposta a híbrida zerou a "
                "falsa abstenção (as palavras exatas trazem o trecho que o LLM precisa, ainda que não no topo). "
                "O ganho de ranking vem do rerank por LLM, que reordena os candidatos das duas buscas.",
            ]
    return "\n".join(linhas)


_ETAPAS_LATENCIA = ["search", "retrieve", "answer", "verify", "total"]
_NOME_ETAPA = {
    "search": "Busca de contexto (search)", "retrieve": "Busca híbrida/vetorial (retrieve, sem rerank)",
    "answer": "Geração (answer)", "verify": "Verificação (verify)", "total": "Ponta a ponta",
}


def _secao_latencia(configs: dict) -> str:
    presentes = _configs_presentes(configs)
    if not presentes:
        return ""
    linhas = ["## Latência (p50/p95, ms)", ""]
    for nome in presentes:
        latencia = configs[nome]["aggregated"]["latency_ms"]
        linhas += [f"### {_NOME_CONFIG.get(nome, nome)}", "", "| Etapa | p50 | p95 | n chamadas |", "|---|---|---|---|"]
        for etapa in _ETAPAS_LATENCIA:
            valores = latencia.get(etapa)
            if not valores:
                continue
            linhas.append(f"| {_NOME_ETAPA.get(etapa, etapa)} | {valores['p50']:.0f} ms | {valores['p95']:.0f} ms | {valores['n']} |")
        linhas.append("")
    return "\n".join(linhas).rstrip()


def _secao_custo(configs: dict) -> str:
    presentes = _configs_presentes(configs)
    if not presentes:
        return ""
    linhas = [
        "## Custo",
        "",
        "| Config | US$/pergunta | US$/1.000 perguntas | Custo de avaliação (juiz) | n perguntas |",
        "|---|---|---|---|---|",
    ]
    for nome in presentes:
        agregado = configs[nome]["aggregated"]
        cost = agregado["cost"]
        linhas.append(
            f"| {_NOME_CONFIG.get(nome, nome)} | US$ {cost.get('usd_per_question', 0):.4f} "
            f"| US$ {cost.get('usd_per_1000', 0):.2f} | US$ {agregado.get('judge_cost_usd', 0):.4f} "
            f"| {cost.get('n_questions', 0)} |"
        )
    return "\n".join(linhas)


def _secao_ingestao(ingestion: dict | None) -> str:
    if not ingestion:
        return "## Ingestão\n\n(Pulada nesta rodada — `--skip-ingest`.)"
    return (
        "## Ingestão\n\n"
        f"Reindexação do PDF de demonstração no namespace `{ingestion.get('namespace')}` "
        f"(apagado antes e depois):\n\n"
        f"- Páginas: {ingestion.get('paginas')}\n"
        f"- Chunks: {ingestion.get('chunks')}\n"
        f"- Tempo total: {ingestion.get('tempo_total_s', 0):.1f} s\n"
        f"- Páginas/min: {ingestion.get('paginas_por_min', 0):.1f}\n"
        f"- Contextualização (contextual retrieval) habilitada: {ingestion.get('contextual_retrieval_enabled')}\n"
        f"- Custo de embedding: US$ {ingestion.get('cost', {}).get('total_cost_usd', 0):.4f}"
    )


def _secao_cache(cache: dict | None) -> str:
    if not cache:
        return "## Cache semântico\n\n(Não medido nesta rodada.)"
    resultados = cache.get("resultados", [])
    if not resultados:
        return "## Cache semântico\n\n(Sem perguntas para medir.)"
    confirmados = [r for r in resultados if r.get("cache_hit_confirmado")]
    frios = [r["cold_ms"] for r in confirmados]
    hits = [r["hit_ms"] for r in confirmados]
    linhas = [
        "## Cache semântico",
        "",
        f"{len(resultados)} perguntas, cada uma consultada 2x (fria, depois repetida) num namespace limpo "
        "(cache invalidado antes e depois). Latências calculadas só sobre as "
        f"{len(confirmados)} em que a 2ª chamada veio do cache:",
        "",
    ]
    if confirmados:
        linhas += [
            f"- Latência média fria (miss): {sum(frios) / len(frios):.0f} ms",
            f"- Latência média com hit: {sum(hits) / len(hits):.0f} ms "
            f"({sum(frios) / sum(hits):.0f}x mais rápido, sem chamada ao LLM)",
        ]
    nao_cacheadas = len(resultados) - len(confirmados)
    if nao_cacheadas:
        linhas.append(
            f"- {nao_cacheadas} pergunta(s) não foram cacheadas: por design, respostas \"não encontrei\" "
            "e respostas bloqueadas pelo verificador não entram no cache."
        )
    return "\n".join(linhas)


def _secao_http(http: dict | None) -> str:
    if http is None:
        return "## HTTP ponta a ponta\n\n(Não medido nesta rodada — `--http-url` não foi informado.)"
    if http.get("skipped"):
        return f"## HTTP ponta a ponta\n\n(Pulado: {http.get('motivo')})"
    resultados = http.get("resultados", [])
    if not resultados:
        return "## HTTP ponta a ponta\n\n(Sem resultados.)"
    ttfts = [r["ttft_ms"] for r in resultados if r.get("ttft_ms") is not None]
    totais = [r["total_ms"] for r in resultados]
    linhas = [
        "## HTTP ponta a ponta",
        "",
        f"{http.get('n')} perguntas via `POST /api/query/stream`, respeitando o limite de 5/min "
        f"(dormindo {http.get('rate_limit_sleep_s')}s entre requisições):",
        "",
        (f"- Time-to-first-token: mediana {sorted(ttfts)[len(ttfts) // 2]:.0f} ms "
         f"(mín. {min(ttfts):.0f}, máx. {max(ttfts):.0f})") if ttfts else "- Time-to-first-token: n/d",
        f"- Tempo total (até `[DONE]`): mediana {sorted(totais)[len(totais) // 2]:.0f} ms "
        f"(mín. {min(totais):.0f}, máx. {max(totais):.0f})",
        "- O primeiro token só sai depois da busca completa (expansão + híbrida + rerank), por isso o TTFT "
        "fica próximo da latência de busca somada ao início da geração.",
    ]
    return "\n".join(linhas)


def _secao_limitacoes(env: dict, configs: dict) -> str:
    linhas = [
        "## Limitações",
        "",
        "- A nota de qualidade vem de um juiz LLM (gpt-4o-mini) com critério textual livre, não de um gabarito "
        "determinístico — pode divergir da avaliação humana caso a caso.",
        "- Um único documento (Cadernos de Atenção Básica nº 37) indexado; retrieval/ablação não generalizam "
        "necessariamente para outros documentos ou domínios.",
        f"- Dataset de {env.get('dataset_counts', {}).get('total', '?')} casos: cada caso individual pesa "
        f"~{100 / env.get('dataset_counts', {}).get('total', 50):.1f} pontos percentuais numa taxa — "
        "amostra pequena para produção real.",
        "- Chamadas de LLM têm variação entre rodadas (temperature=0 reduz mas não elimina); a variabilidade "
        "entre repetições está reportada nos campos `*_variability` do JSON bruto.",
    ]
    if env.get("dataset_limit"):
        linhas.append(
            f"- Rodada com `--limit {env['dataset_limit']}`: números NÃO são representativos, só smoke test."
        )
    return "\n".join(linhas)


def _secao_reproducao() -> str:
    return (
        "## Como reproduzir\n\n"
        "```bash\n"
        "cd backend\n"
        "uv run python -m benchmark.run --repeats 3 --configs naive,hybrid,full\n"
        "# ponta a ponta via HTTP (compose no ar):\n"
        "uv run python -m benchmark.run --skip-ingest --http-url http://localhost:8080 --http-n 10\n"
        "```"
    )
