# Appendix

[← Delivery](09-delivery.md) · [Plan overview](README.md)

## A. Configuration skeleton

`config/app.yaml` is versioned, and every run manifest records its SHA-256.

```yaml
version: "2026.10.26-1"
dataset: {version: "0.10.0", payload_sha256: "49862eeaace8edc53b31849813e4f46195dbbe1c619948cb7614327a47afaf26"}
models:
  supervisor:  {id: openai/gpt-4.1,      temperature: 0.2, max_tokens: 600}
  specialist:  {id: openai/gpt-4.1-mini, temperature: 0.0, max_tokens: 500}
  tutor:       {id: openai/gpt-4.1-mini, temperature: 0.3, max_tokens: 400}
  reflection:  {id: openai/gpt-4.1,      temperature: 0.3, max_tokens: 400}
  judge:       {id: google/gemini-3.1-flash-lite, temperature: 0.0}
  simulator:   {id: meta-llama/llama-3.3-70b-instruct, temperature: 0.7}
  safety:      {id: meta-llama/llama-guard-4-12b}
  injection:   {id: meta-llama/Llama-Prompt-Guard-2-86M, runtime: local_cpu}
  embeddings:  {id: BAAI/bge-small-en-v1.5, runtime: fastembed}
  reranker:    {id: Xenova/ms-marco-MiniLM-L-6-v2, runtime: fastembed}
openrouter: {provider: {require_parameters: true, data_collection: deny}}
retrieval: {candidate_k: 20, final_k: 5, rrf_k: 60, rerank: true, rewrite: true, collections: [cards, textbook]}
memory: {enabled: true, summarise_trigger_tokens: 6000, keep_messages: 8}
learner_model:
  bkt: {p_init: 0.25, p_learn: 0.15, p_slip: 0.10, p_guess: {numeric: 0.05, boolean: 0.5, classification: by_labels}}
  mastered: 0.95
  prerequisite_ready: 0.80
  stuck: {sessions: 3, min_gain: 0.10}
budgets: {per_turn: {llm_calls: 8, tool_calls: 10, usd: 0.03}, per_session: {usd: 0.40}, turn_timeout_s: 120}
features: {defences: all, hints: socratic, playbook: null, max_revisions: 1}
prompts: {planner: v1, diagnostician: v1, tutor: v1, grader: v1, question_setter: v1, judge: v1, reflection: v1, rewrite: v1}
```

## B. Repository layout

> [!NOTE]
> The Architecture Guide in `Docs/` proposes a different layout (`src/tutor/`, `content/`, `ops/`), with a named owner per folder. Which layout to use is open decision [Q1](README.md#open-decisions), and we recommend the guide's. This sketch shows only which parts the plan needs.

```
docker-compose.yml   .env.example   README.md   pyproject.toml   uv.lock
config/              app.yaml, users.yaml, eval_gate.yaml
prompts/             <agent>.md  (six slots, versioned)
data/                runtime/ (copies the tutor may see), MANIFEST.json
tutor/
  api/  ui/  graph/  agents/  memory/  diagnosis/  retrieval/  guardrails/  observability/
  mcp_servers/{textbook_kb, math_tools, learner_store, question_bank}/
eval/
  harness/ (run, checks, simstudent, judge, recorders)   scorers/   configs/   schemas/
  private/ (held-out cases, cards, keys; mounted only by the eval service)
  attacks/   playbook/   PREREGISTRATION.md
infra/               docker/, prometheus/, grafana/{provisioning, dashboards, alerting}
scripts/             trace.py, fire_leak_alert.py, seed_demo.py
tests/               mcp/, graph/, guardrails/, memory/, retrieval/, prompts/
Docs/
  plan/              this plan
  DECISIONS.md   EXPERIMENT_LOG.md   CONTRIBUTIONS.md   THREAT_MODEL.md   MEMORY_POLICY.md
  REPORT.md   ci_failure.md   contracts/   spikes/   policy/   architecture/
socratic_tutor_dataset_v2/   frozen data source (unchanged; builds are not committed)
```

**Never committed:**
- `.env`;
- NCERT PDFs and page images;
- text derived from the textbook;
- dataset builds;
- personal data.

## C. Sources

<details>
<summary><strong>Checked directly on 24 Oct 2026</strong></summary>

- The PyPI JSON API for every package listed in [02 · Starting point](02-starting-point.md#package-versions-pypi-24-oct-2026).
- The OpenRouter `/api/v1/models` listing, for model availability, prices, and tool and JSON-schema support.

</details>

<details>
<summary><strong>Documentation</strong></summary>

**LangGraph**
- [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [Stores](https://docs.langchain.com/oss/python/langgraph/stores)
- [Streaming](https://docs.langchain.com/oss/python/langgraph/streaming)
- [Migrating to LangGraph v1](https://docs.langchain.com/oss/python/migrate/langgraph-v1)

**LangChain**
- [Built-in middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in)
- [Human in the loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)
- [Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)
- [MCP adapter migration](https://docs.langchain.com/oss/python/migrate/langchain-mcp-adapters)
- [`langchain-mcp-adapters` archive notice](https://github.com/langchain-ai/langchain-mcp-adapters)

**FastMCP and MCP**
- [Tools](https://gofastmcp.com/servers/tools)
- [Testing](https://gofastmcp.com/patterns/testing)
- [Upgrading from FastMCP 3](https://gofastmcp.com/getting-started/upgrading/from-fastmcp-3)
- [MCP SDK v2 migration](https://py.sdk.modelcontextprotocol.io/v2/migration/)

**OpenRouter and models**
- [Usage accounting](https://openrouter.ai/docs/use-cases/usage-accounting)
- [Provider routing](https://openrouter.ai/docs/guides/routing/provider-selection)
- [Limits](https://openrouter.ai/docs/api-reference/limits)
- [OpenAI deprecations](https://developers.openai.com/api/docs/deprecations)

**Guardrails**
- [Llama Guard 4](https://huggingface.co/meta-llama/Llama-Guard-4-12B)
- [Prompt Guard 2](https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M)
- [Presidio supported entities](https://presidio.dataprivacystack.org/supported_entities/)

**Retrieval and ingestion**
- [Chroma in Docker](https://docs.trychroma.com/guides/deploy/docker)
- [Chroma metadata filtering](https://docs.trychroma.com/docs/querying-collections/metadata-filtering)
- [Reciprocal Rank Fusion (Cormack et al., SIGIR 2009)](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- [fastembed](https://pypi.org/project/fastembed/)
- [Docling enrichments](https://docling-project.github.io/docling/usage/enrichments/)

**Observability**
- [Langfuse self-hosting requirements](https://langfuse.com/self-hosting/deployment/docker-compose)
- [Grafana alert provisioning](https://grafana.com/docs/grafana/latest/alerting/set-up/provision-alerting-resources/file-provisioning/)
- [Prometheus client with FastAPI](https://prometheus.github.io/client_python/exporting/http/fastapi-gunicorn/)

**Serving and CI**
- [FastAPI server-sent events](https://fastapi.tiangolo.com/tutorial/server-sent-events/)
- [Streamlit navigation](https://docs.streamlit.io/develop/concepts/multipage-apps/page-and-navigation)
- [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/)
- [setup-uv](https://github.com/astral-sh/setup-uv)

</details>

<details>
<summary><strong>Research literature</strong></summary>

**Learner modelling**
- [Corbett & Anderson 1995: Bayesian Knowledge Tracing](https://doi.org/10.1007/BF01099821)
- [Pelánek & Řihák 2017: mastery thresholds](https://doi.org/10.1145/3079628.3079667)
- [Knowledge space theory and the outer fringe](https://arxiv.org/abs/1511.06757)

**Simulated students**
- [MathDial](https://aclanthology.org/2023.findings-emnlp.372)
- [Generative Students](https://arxiv.org/abs/2405.11591)
- [Dinucu-Jianu et al. 2025: pre/post design](https://arxiv.org/abs/2505.15607)
- [Over-agreeable simulators](https://arxiv.org/abs/2605.12748)
- [The competence paradox](https://arxiv.org/abs/2601.05473)
- [Persona drift](https://arxiv.org/abs/2609.24532)

**Tutor evaluation**
- [MRBench (Maurya et al., NAACL 2025)](https://aclanthology.org/2025.naacl-long.57)
- [LearnLM](https://arxiv.org/abs/2407.12687)

**Lesson libraries**
- [Reflexion](https://arxiv.org/abs/2303.11366)
- [ExpeL](https://arxiv.org/abs/2308.10144)
- [ACE](https://arxiv.org/abs/2510.04618)
- [Error propagation in agent memory](https://arxiv.org/abs/2505.16067)

**Judges and agreement**
- [Judge biases (Zheng et al. 2023)](https://arxiv.org/abs/2306.05685)
- [Self-preference](https://arxiv.org/abs/2404.13076)
- [Landis & Koch 1977: agreement bands](https://doi.org/10.2307/2529310)
- [Hake 1998: normalised gain](https://doi.org/10.1119/1.18809)

</details>

<details>
<summary><strong>Law and copyright</strong></summary>

- [DPDP Rules 2025: notification](https://www.scconline.com/blog/post/2025/11/14/meity-notified-digital-personal-data-protection-rules-2025/)
- [DPDP Rules: commencement status](https://consentos.in/learn/dpdp-rules-notification-status/)
- [DPDP Fourth Schedule](https://www.dpdpa.com/schedule/schedule4.html)
- [NCERT copyright advisory](https://ddnews.gov.in/en/ncert-warns-against-copyright-infringement-of-educational-materials/)
- [Tele-MANAS helpline](https://ehrc.iiitb.ac.in/project/tele-manas)

</details>

### Not yet verified

These are tested during the spikes or need a primary source:
- How fast Prompt Guard 2, Docling's formula enrichment and the reranker run on CPU (spikes S3 and S4).
- Whether Llama Guard 4 on OpenRouter accepts custom categories (spike S4).
- The exact DPDP commencement dates, which need checking against the Gazette.
- A primary research source for the "dividing by x" misconception, which is common teaching knowledge.

---

[← Delivery](09-delivery.md) · [Plan overview](README.md)
