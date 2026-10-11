# MiroFish — System Architecture (Rebuild Specification)

> A complete, self-contained blueprint an AI agent (or human) can follow to
> reimplement **MiroFish** — *A Simple and Universal Swarm Intelligence Engine
> for Predicting Anything*.

---

## 0. High-Level One-Liner

MiroFish takes **seed text** (news, reports, novel chapters, policy drafts) +
a **natural-language prediction request** and produces:
1. A **Zep-backed knowledge graph** of the seed world.
2. An **OASIS multi-agent simulation** (Twitter + Reddit platforms, parallel)
   where thousands of persona-driven agents interact.
3. A **ReACT-style Report Agent** that queries the post-simulation graph and
   writes a structured prediction report.
4. An **interactive chat layer** to interrogate any agent or the report.

---

## 1. Repository Layout (top-down)

```text
MiroFish/
├── backend/                      # Python 3.11+ Flask service
│   ├── app/
│   │   ├── __init__.py           # create_app() factory
│   │   ├── config.py             # Config (loads .env from repo root)
│   │   ├── api/                  # Blueprints: graph, simulation, report
│   │   ├── services/             # Business logic (graph builder, runner, etc.)
│   │   ├── models/               # Project, Task dataclasses + managers
│   │   └── utils/                # zep, llm_client, file_parser, logger, locale
│   ├── scripts/                  # Standalone simulation runners
│   │   ├── run_parallel_simulation.py
│   │   ├── run_twitter_simulation.py
│   │   ├── run_reddit_simulation.py
│   │   ├── action_logger.py      # JSONL per-action writer
│   │   └── validate_zep_cloud_integration.py
│   ├── tests/                    # pytest suites
│   ├── run.py                    # Entrypoint: `uv run python run.py`
│   ├── pyproject.toml            # uv-managed Python project
│   └── requirements.txt
│
├── frontend/                     # Vue 3 + Vite SPA
│   ├── index.html
│   ├── vite.config.js            # Proxies /api → :5001
│   ├── package.json              # vue 3.5, vue-router, vue-i18n, axios, d3
│   └── src/
│       ├── main.js               # createApp + router + i18n
│       ├── App.vue               # <router-view/>
│       ├── router/index.js       # 5 routes
│       ├── api/                  # axios client + per-domain wrappers
│       ├── views/                # Home, MainView, SimulationView, ...
│       ├── components/           # Step1..5 + GraphPanel + LanguageSwitcher
│       ├── store/pendingUpload.js
│       ├── i18n/index.js
│       └── assets/logo/
│
├── locales/                      # Shared i18n (en.json, zh.json, languages.json)
├── scripts/                      # Root-level utility scripts
├── static/image/                 # README assets + logos
├── tests/                        # Cross-stack tests
│
├── package.json                  # Root: setup:all, dev (concurrently)
├── docker-compose.yml            # Single-container deploy
├── Dockerfile                    # python:3.11 + node + uv
├── .env.example                  # LLM_API_KEY, LLM_BASE_URL, ZEP_API_KEY
└── README.md / README-ZH.md
```text

---

## 2. Architectural Style

* **Two-tier service**: Vue 3 SPA  ⇄  Flask REST backend  ⇄  External services.
* **Process-spawn pattern** for the heavy OASIS simulator: Flask keeps a
  lightweight state machine, launches the simulator as a **subprocess**, and
  communicates via **filesystem-based IPC** (`commands/`, `responses/`).
* **Asynchronous long tasks** (ontology generation, graph build, report
  generation) are tracked by a thread-safe `TaskManager`; the frontend polls
  via `GET /api/graph/task/<id>` and `POST /api/simulation/prepare/status`.
* **State persistence** for projects is on-disk JSON
  (`backend/uploads/projects/<project_id>/project.json`); simulation data and
  reports are folders under `backend/uploads/simulations/` and
  `backend/uploads/reports/`.

```text
┌──────────────────────────────────────────────────────────────────┐
│                          Browser (Vue 3)                         │
│  Router: /  /process/:pid  /simulation/:sid  /report/:rid  ...  │
│  Components: Step1Graph → Step2Env → Step3Sim → Step4Report     │
│              → Step5Interact                                    │
│  HTTP via axios (Accept-Language header)                        │
└──────────────────────────────────────────────────────────────────┘
              │  /api/*  (Vite dev-proxy → :5001)
              ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Flask Backend (port 5001)                      │
│  Blueprints: /api/graph  /api/simulation  /api/report            │
│  Services:                                                         │
│   • OntologyGenerator    – LLM-extracted schema                  │
│   • GraphBuilderService  – Zep batch ingest                      │
│   • OasisProfileGenerator – entity→persona                       │
│   • SimulationConfigGenerator – time/events/agents/params        │
│   • SimulationRunner     – subprocess + JSONL + IPC + locks      │
│   • SimulationManager    – CRUD over Simulation records          │
│   • ReportAgent          – ReACT over Zep tools                  │
│   • ZepGraphMemoryUpdater – writes sim events back to Zep        │
│  Models: Project (disk), Task (in-mem singleton)                 │
│  Utils:   LLMClient (OpenAI SDK), Zep helpers, file_parser       │
└──────────────────────────────────────────────────────────────────┘
       │            │              │                │
       ▼            ▼              ▼                ▼
  ┌────────┐  ┌──────────┐  ┌─────────────┐  ┌──────────────┐
  │  LLM   │  │ Zep Cloud│  │  OASIS sub- │  │ Filesystem   │
  │ (OpenAI│  │ (graph + │  │  processes  │  │ IPC:         │
  │  SDK)  │  │  memory) │  │ (Twitter+   │  │ commands/,   │
  │        │  │          │  │  Reddit)    │  │ responses/   │
  └────────┘  └──────────┘  └─────────────┘  └──────────────┘
```text

---

## 3. Tech Stack

| Layer       | Choice                                          |
| ----------- | ----------------------------------------------- |
| Frontend    | Vue 3.5, Vite 7, vue-router 4, vue-i18n 11      |
| Charts      | D3.js v7 (graph rendering in `GraphPanel.vue`)  |
| HTTP        | axios 1.x with interceptors (locale header)     |
| Backend     | Python 3.11–3.12, Flask 3, flask-cors 6         |
| LLM         | OpenAI SDK 1.x (any OpenAI-compatible endpoint) |
| Graph/Mem   | Zep Cloud 3.25 (`zep-cloud` SDK)                |
| Simulator   | `camel-oasis 0.2.5` + `camel-ai 0.2.78`         |
| File parse  | PyMuPDF (PDF), charset-normalizer, chardet      |
| Data model  | pydantic 2, dataclasses                         |
| Packaging   | uv (backend), npm (frontend), concurrently      |
| Container   | python:3.11 + nodejs + uv (single image)        |

---

## 4. Core Domain Model

### 4.1 Project (disk-persisted)
```python
class ProjectStatus(Enum):
    CREATED, ONTOLOGY_GENERATED, GRAPH_BUILDING, GRAPH_COMPLETED, FAILED

@dataclass
class Project:
    project_id: str                # "proj_<12hex>"
    name: str
    status: ProjectStatus
    created_at, updated_at: str
    files: list[dict]              # [{original_filename, saved_filename, path, size}]
    total_text_length: int
    ontology: dict | None          # output of OntologyGenerator
    analysis_summary: str | None
    graph_id: str | None           # Zep graph UUID
    graph_build_task_id: str | None
    zep_batch_id, zep_batch_operation_id: str | None
    simulation_requirement: str
    chunk_size: int = 500
    chunk_overlap: int = 50
    error: str | None
```python
Stored at `backend/uploads/projects/<project_id>/project.json` with siblings
`files/` and `extracted_text.txt`.

### 4.2 Task (in-memory singleton, thread-safe)
States: `PENDING → PROCESSING → COMPLETED|FAILED`. Fields include
`progress (0-100)`, `message`, `result`, `error`, `progress_detail`,
`metadata`. Task IDs are UUID4.

### 4.3 SimulationRunState (per-simulation, in-memory)
Tracks dual-platform state for **Twitter + Reddit** running in parallel:
* `current_round`, `total_rounds`
* `twitter_current_round`, `reddit_current_round`
* `twitter_simulated_hours`, `reddit_simulated_hours`
* `twitter_actions_count`, `reddit_actions_count`
* `twitter_completed`, `reddit_completed`
* `recent_actions` (max 50), full `rounds[]` of `RoundSummary`
* `runner_status ∈ {IDLE, STARTING, RUNNING, PAUSED, STOPPING, STOPPED, COMPLETED, FAILED}`
* `process_pid`, `started_at`, `completed_at`, `error`

### 4.4 AgentAction
```python
round_num, timestamp, platform, agent_id, agent_name,
action_type (e.g. CREATE_POST, LIKE_POST, REPOST, ...),
action_args, result, success
```python

### 4.5 IPC
* `IPCCommand` with `CommandType ∈ {INTERVIEW, BATCH_INTERVIEW, CLOSE_ENV}`
* `IPCResponse` with `CommandStatus ∈ {PENDING, PROCESSING, COMPLETED, FAILED}`
* Channels: per-simulation `commands/<command_id>.json` and
  `responses/<command_id>.json` (file-based async RPC).

---

## 5. Backend Services — Responsibilities

### 5.1 `OntologyGenerator` (services/ontology_generator.py)
* **Input**: extracted text + `simulation_requirement`.
* **Action**: prompts LLM to design a social-simulation schema
  (entity types + relationship types in PascalCase / UPPER_SNAKE_CASE).
* **Output**: `{ entity_types: [...], relationship_types: [...],
  analysis_summary: str }` written into `project.ontology`.
* Uses `LLMClient` (utils/llm_client.py) and helpers from
  `utils/ontology.py` (`MAX_ONTOLOGY_TYPES`, attribute/edge normalizers).

### 5.2 `GraphBuilderService` (services/graph_builder.py)
* **Input**: project + ontology + extracted text chunks.
* **Action**:
  1. Create a Zep `graph` via `Zep(...).graph.create(...)`.
  2. For each text chunk call LLM to extract `(entities, edges)` aligned
     to ontology.
  3. Batch-insert using `BatchAddItem`, `EntityEdgeSourceTarget`
     (`zep_cloud` types).
  4. Poll until ingestion completes (deadline
     `ZEP_INGESTION_WAIT_TIMEOUT_SECONDS = 600`).
* **Output**: `graph_id`, `node_count`, `edge_count`, `entity_types`.
* Persists IDs in `project.graph_id`, `project.zep_batch_id`,
  `project.graph_build_task_id`.

### 5.3 `OasisProfileGenerator` (services/oasis_profile_generator.py)
* **Input**: `graph_id` (+ optional entity-type filter).
* **Action**:
  1. Reads nodes via `ZepEntityReader` + Zep search to enrich context.
  2. For each entity, prompts LLM to craft a *detailed persona*:
     `{ name, persona, age, occupation, bio, characteristics, ... }`.
  3. Batches profile generation; parallelized with
     `parallel_profile_count`.
* **Output**: list of agent profiles consumable by OASIS.

### 5.4 `SimulationConfigGenerator` (services/simulation_config_generator.py)
Generates the full simulation config in **four LLM steps** to avoid
context overflow:
1. Time config (start, end, sim hours per round).
2. Event config (news injects, shocks).
3. Agent-platform assignment (which agents go to Twitter / Reddit / both).
4. Platform config (action probabilities, recommendation engine tuning).
Writes a JSON the runner can consume.

### 5.5 `SimulationRunner` (services/simulation_runner.py)
* **Spawns** `scripts/run_parallel_simulation.py` (or single-platform
  variants) via `subprocess.Popen` with `cwd=backend`. Each child runs
  its own `asyncio` event loop driving OASIS.
* **Action buffer**: per-sim `queue.Queue` collects parsed JSONL events
  before they are folded into `SimulationRunState`.
* **Communicates** via the per-sim folder layout:
  ```
  uploads/simulations/<sim_id>/
    ├── twitter/actions.jsonl      # streamed per-action events
    ├── reddit/actions.jsonl
    ├── simulation.log             # stdout+stderr
    ├── run_state.json
    ├── commands/<id>.json         # IPC requests
    └── responses/<id>.json
  ```
* **Monitor thread** tail-reads `actions.jsonl` to update
  `SimulationRunState` (rounds, counts, recent actions, completion flags).
* **Lifecycle**: `register_cleanup()` uses `atexit` + `signal` to kill
  children if Flask is killed.
* **Concurrency**: per-simulation `finalization_lock` + per-graph
  `graph_lifecycle_lock` (re-entrant) — guarantees only one writer
  touches Zep graph for a given sim and that the graph isn't deleted
  while readers are attached.
* **Graph memory updates**: `ZepGraphMemoryManager` writes agent
  interactions back to the Zep graph between rounds (optional toggle).
* **APIs supported**: start / stop / pause / resume / interview single
  agent / batch interview / interview all / close environment.

### 5.6 `ReportAgent` (services/report_agent.py)
* ReACT loop over Zep tools: `Search`, `InsightForge`, `Panorama`,
  `Interview` (see `zep_tools.py`).
* Pipeline:
  1. Outline the report structure (sections, depth).
  2. For each section: think → call tool → reflect (up to
     `REPORT_AGENT_MAX_REFLECTION_ROUNDS=2`) → write.
  3. Persist `agent_log.jsonl` and `console.log` for streaming to UI.
* Configurable: `REPORT_AGENT_MAX_TOOL_CALLS=5`,
  `REPORT_AGENT_TEMPERATURE=0.5`.

### 5.7 `ZepToolsService` (services/zep_tools.py)
Implements the four tools the ReportAgent can call:
* **Search** — Zep graph search.
* **InsightForge** — derive higher-level insight from multiple facts.
* **Panorama** — summarize a region of the graph.
* **Interview** — runs an in-simulation interview via `SimulationIPCClient`.

### 5.8 Support Services
* `services/text_processor.py` — chunking helper that splits large
  documents into 500-char / 50-overlap chunks for ontology + graph
  ingestion.
* `services/zep_entity_reader.py` — reads Zep entity nodes
  (`EntityNode` dataclass) and re-queries Zep to enrich them with
  surrounding context for profile generation.
* `services/simulation_manager.py` — in-memory + on-disk CRUD over
  `Simulation` records (list, get, delete, status transitions).

### 5.9 Utils
* `utils/zep.py` — shared `Zep` client (`get_zep_client()`),
  `ZEP_HTTP_REQUEST_TIMEOUT_SECONDS=60`, `MAX_ZEP_SEARCH_RESULTS=50`,
  `MAX_ZEP_SEARCH_QUERY_CHARS=400`, retry helpers.
* `utils/llm_client.py` — OpenAI-format client; raises
  `LLMResponseError` on unusable outputs; supports `LLM_BOOST_*` envs for
  fast/slow model split.
* `utils/file_parser.py` — PDF (PyMuPDF) / MD / TXT, chunker (default
  500/50 overlap), `split_text_into_chunks`.
* `utils/logger.py` — namespaced `get_logger('mirofish.<x>')`.
* `utils/locale.py` — `t(key)`, `set_locale()`, returns
  `get_language_instruction()` injected into LLM prompts.
* `utils/openai_chat_compat.py` — `create_chat_completion` shim used
  everywhere instead of raw `client.chat.completions.create`.
* `utils/retry.py` — generic exponential backoff.

---

## 6. REST API Surface

Base URL: `http://localhost:5001`  ·  All under `/api/{graph,simulation,report}`
·  CORS open on `/api/*`. Responses use `ensure_ascii=False` (Chinese OK).

### 6.1 `/api/graph`  (graph.py blueprint)
| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET    | `/project/<project_id>`                | Fetch project JSON |
| GET    | `/project/list`                        | List projects |
| DELETE | `/project/<project_id>`                | Delete project + cloud graph |
| POST   | `/project/<project_id>/reset`          | Clear graph reference |
| POST   | `/ontology/generate` (multipart)       | Upload files + requirement → ontology |
| POST   | `/build`                               | Build Zep graph (async) |
| GET    | `/task/<task_id>`                      | Poll task status |
| GET    | `/tasks`                               | List tasks |
| GET    | `/data/<graph_id>`                     | Read full graph (nodes/edges) |
| DELETE | `/delete/<graph_id>`                   | Delete Zep cloud graph |

### 6.2 `/api/simulation`  (simulation.py blueprint)
| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET    | `/entities/<graph_id>[/<uuid>][/by-type/<type>]` | List/filter graph entities |
| POST   | `/create`                              | Create sim (binds to graph) |
| POST   | `/prepare`                             | Generate profiles + config (async) |
| POST   | `/prepare/status`                      | Poll prepare progress |
| GET    | `/<simulation_id>`                     | Simulation metadata |
| GET    | `/list`                                | All sims |
| GET    | `/history`                             | History list |
| GET    | `/<id>/profiles` & `/profiles/realtime`| Generated agent profiles |
| GET    | `/<id>/config` & `/config/realtime`    | Simulation config |
| GET    | `/<id>/config/download`                | JSON download |
| GET    | `/script/<name>/download`              | Download one of `run_*.py` |
| POST   | `/generate-profiles`                   | Regenerate profiles only |
| POST   | `/start`                               | Launch OASIS subprocess |
| POST   | `/stop`                                | Stop a running sim |
| GET    | `/<id>/run-status` & `/run-status/detail` | Live status (no/with recent actions) |
| GET    | `/<id>/actions`                        | Streamed action log |
| GET    | `/<id>/timeline`                       | Timeline view |
| GET    | `/<id>/agent-stats`                    | Per-agent stats |
| GET    | `/<id>/posts` & `/<id>/comments`       | Browse content |
| POST   | `/interview` / `/interview/batch` / `/interview/all` / `/interview/history` | In-sim interviews via IPC |
| POST   | `/env-status`                          | Check sim env alive |
| POST   | `/close-env`                           | Send CLOSE_ENV IPC |

### 6.3 `/api/report`  (report.py blueprint)
| Method | Path | Purpose |
| ------ | ---- | ------- |
| POST   | `/generate`                           | Start report (async) |
| POST   | `/generate/status`                    | Poll report status |
| GET    | `/<report_id>`                        | Report metadata + content |
| GET    | `/by-simulation/<sim_id>`             | Reports for a sim |
| GET    | `/list`                               | All reports |
| GET    | `/<id>/download`                      | Markdown/PDF download |
| DELETE | `/<id>`                               | Delete report |
| POST   | `/chat`                               | Chat with ReportAgent |
| GET    | `/<id>/progress`                      | 0–100 progress |
| GET    | `/<id>/sections`                      | All section texts |
| GET    | `/<id>/section/<int>`                 | One section |
| GET    | `/check/<sim_id>`                     | Can a report be built? |
| GET    | `/<id>/agent-log` & `/agent-log/stream`| Tool-call trace (poll/stream) |
| GET    | `/<id>/console-log` & `/console-log/stream` | Console trace |
| POST   | `/tools/search` & `/tools/statistics` | Direct Zep-tool calls |

### 6.4 Misc
* `GET /health` → `{ status: ok, service: 'MiroFish Backend' }`.

---

## 7. Frontend (Vue 3)

### 7.1 Router (`src/router/index.js`)
```text
/                                  → Home (landing)
/process/:projectId                → MainView (5-step workflow)
/simulation/:simulationId          → SimulationView
/simulation/:simulationId/start    → SimulationRunView (live)
/report/:reportId                  → ReportView
/interaction/:reportId             → InteractionView
```python

### 7.2 5-Step Workflow (MainView)
1. **Step1GraphBuild** — Upload files, edit `simulation_requirement`,
   trigger `/api/graph/ontology/generate` then `/api/graph/build`. Shows
   task progress and final graph.
2. **Step2EnvSetup** — Filter entity types, generate profiles
   (`/api/simulation/generate-profiles` + `/prepare`), inspect generated
   OASIS profiles.
3. **Step3Simulation** — Configure platforms, `/api/simulation/create`,
   `/prepare`, then `/start`. Live progress.
4. **Step4Report** — `/api/report/generate`, stream `agent-log` &
   `console-log` to UI, render sections.
5. **Step5Interaction** — Chat with any agent (`/api/simulation/interview`)
   and with ReportAgent (`/api/report/chat`).

### 7.3 Layout Modes (`MainView.vue`)
Header exposes `viewMode ∈ {graph, split, workbench}` — toggles
left/right panel widths (graph on left, step components on right).

### 7.4 Components
* `GraphPanel.vue` — D3-rendered Zep graph (nodes, edges, zoom/pan).
* `Step1..5*.vue` — one per pipeline stage.
* `LanguageSwitcher.vue` — flips `i18n.locale` between `en`/`zh`.
* `HistoryDatabase.vue` — history modal.

### 7.5 API layer (`src/api/*`)
* `index.js` — axios instance with `Accept-Language` request header and
  response interceptor that unwraps `{success, data, error}` and normalizes
  errors.
* `graph.js`, `simulation.js`, `report.js` — one file per backend blueprint.

### 7.6 State
* `store/pendingUpload.js` — carries uploaded files + requirement from
  Home to MainView (avoids sending large data through the URL).
* `i18n/index.js` — loads `locales/{en,zh}.json` + `languages.json`.

---

## 8. Data Flow (Happy Path)

```text
1. User uploads files + requirement on Home
   └─→ setPendingUpload() in store, navigate /process/:projectId

2. Step1GraphBuild calls /api/graph/ontology/generate (multipart)
   └─→ FileParser extracts text, TextProcessor chunks (500/50)
   └─→ OntologyGenerator → LLM → ontology JSON saved to project
   └─→ frontend triggers /api/graph/build
        └─→ GraphBuilderService:
             • Zep graph.create() → graph_id
             • chunked extraction via LLM
             • Zep batch add (BatchAddItem)
             • poll ingestion → COMPLETED
        └─→ task marked COMPLETED with graph_id

3. Step2EnvSetup calls /api/simulation/generate-profiles
   └─→ OasisProfileGenerator: entity→persona (parallel batches)
   └─→ /api/simulation/prepare
        └─→ SimulationConfigGenerator (4-step LLM)
        └─→ writes simulation config JSON
        └─→ creates Simulation record

4. Step3Simulation calls /api/simulation/start
   └─→ SimulationRunner.spawn_subprocess("run_parallel_simulation.py")
   └─→ monitor thread tails actions.jsonl → updates run_state
   └─→ UI polls /run-status or subscribes to /actions

5. Step4Report calls /api/report/generate
   └─→ ReportAgent (ReACT over ZepTools) produces sections
   └─→ streamed to UI via /agent-log/stream and /console-log/stream

6. Step5Interaction
   └─→ chat → /api/report/chat (LLM + ZepTools)
   └─→ talk to an agent → /api/simulation/interview (IPC)
```text

---

## 9. Configuration (`.env`)

```env
LLM_API_KEY=...                    # any OpenAI-compatible key
LLM_BASE_URL=https://dashscope...  # default = OpenAI
LLM_MODEL_NAME=qwen-plus           # any model name
# Optional fast LLM split:
LLM_BOOST_API_KEY=...
LLM_BOOST_BASE_URL=...
LLM_BOOST_MODEL_NAME=...

ZEP_API_KEY=...                    # Zep Cloud only
# ZEP_API_URL is unsupported

SECRET_KEY=...                     # Flask
FLASK_DEBUG=false
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
OASIS_DEFAULT_MAX_ROUNDS=10
REPORT_AGENT_MAX_TOOL_CALLS=5
REPORT_AGENT_MAX_REFLECTION_ROUNDS=2
REPORT_AGENT_TEMPERATURE=0.5
```bash

`Config.validate()` enforces `LLM_API_KEY` + `ZEP_API_KEY` and rejects
`ZEP_API_URL`.

---

## 10. Build / Run / Deploy

### 10.1 Source
```bash
cp .env.example .env && $EDITOR .env
npm run setup:all           # npm + frontend + uv sync
npm run dev                 # concurrently runs backend :5001 + frontend :3000
```bash

### 10.2 Docker
```bash
docker compose up -d
# image: ghcr.io/666ghj/mirofish:latest  (or ghcr.nju.edu.cn mirror)
# ports 3000/5001; volume ./backend/uploads
```bash

### 10.3 CI
`.github/workflows/release.yml` builds + pushes GHCR image on tags and
manual dispatch.

---

## 11. External Dependencies (must be reachable)

1. **LLM endpoint** with OpenAI-compatible `/v1/chat/completions`
   (default: Alibaba Bailian qwen-plus).
2. **Zep Cloud** (`https://api.getzep.com/api/v2`). Free monthly quota.
3. **OASIS** (`camel-oasis`) + **CAMEL-AI** for the simulator — installed
   from PyPI; no network needed at runtime.

---

## 12. Implementation Recipe (for an AI to rebuild)

If asked to reimplement MiroFish from this spec, follow this order:

1. **Scaffold** the monorepo (`backend/`, `frontend/`, `locales/`,
   `docker-compose.yml`, `Dockerfile`, root `package.json`).
2. **Backend skeleton**: `Config`, `create_app()`, three empty blueprints,
   `/health`, CORS, request logger.
3. **Models**: `Project` + `ProjectManager` (disk JSON), `Task` +
   `TaskManager` (singleton, in-memory, thread-safe).
4. **Utils**: `LLMClient` (OpenAI SDK), `Zep` client + retry,
   `FileParser` (PDF/MD/TXT), `logger`, `locale`.
5. **Services (linear pipeline)**:
   a. `OntologyGenerator` (LLM JSON out).
   b. `GraphBuilderService` (Zep create + batch + poll).
   c. `OasisProfileGenerator` (entity→persona).
   d. `SimulationConfigGenerator` (4-step LLM).
   e. `SimulationRunner` (subprocess + JSONL monitor + IPC + locks).
   f. `ReportAgent` (ReACT + ZepTools).
6. **Wire** API blueprints to services; emit tasks for long jobs.
7. **Frontend**: Vite + Vue + Router + i18n + axios with locale header.
8. **Views**: Home → MainView (5 steps) → SimulationView/RunView →
   ReportView → InteractionView. Mirror state from `api/*` endpoints.
9. **GraphPanel** with D3.
10. **Locales** (`en.json`, `zh.json`, `languages.json`).
11. **Docker** image, `docker-compose.yml`, root `npm run dev`.
12. **GH Actions** for image publish.

Acceptance checks:
* `POST /api/graph/ontology/generate` returns an ontology with ≤
  `MAX_ONTOLOGY_TYPES` types.
* `POST /api/graph/build` reaches `GRAPH_COMPLETED` and exposes a
  renderable graph via `GET /api/graph/data/<id>`.
* `POST /api/simulation/start` spawns a process, populates
  `uploads/simulations/<id>/{twitter,reddit}/actions.jsonl`, and the
  `/run-status` endpoint shows advancing rounds.
* `POST /api/report/generate` streams sections, and
  `/api/report/chat` returns grounded answers using Zep search.

---

## 13. Reusable Building Blocks (snippets worth porting)

```python
# Thread-safe in-memory task store (singleton)
class TaskManager:
    _instance = None
    _lock = threading.Lock()
    def __new__(cls): ...           # double-checked locking
    def create_task(self, task_type, metadata=None) -> str: ...
    def update_task(self, task_id, status=None, progress=None, ...): ...
    def complete_task / fail_task / list_tasks / cleanup_old_tasks

# Project persistence
class ProjectManager:
    PROJECTS_DIR = uploads/projects
    create_project(name) -> Project
    save_project / get_project / list_projects / delete_project
    save_file_to_project / save_extracted_text / get_extracted_text

# File-based async RPC
class SimulationIPCClient:
    send_command(command: IPCCommand) -> IPCResponse
    poll_response(command_id, timeout) -> IPCResponse

# LLM retry/format
class LLMClient:                       # OpenAI SDK
    def chat(messages, response_format=None) -> str
    # raises LLMResponseError on unusable output
    # supports LLM_BOOST_* for hot/cold split

# Subprocess state monitor
class SimulationRunner:
    spawn_subprocess(config_path) -> simulation_id
    monitor_thread() -> tail actions.jsonl -> update SimulationRunState
    stop / pause / resume via signal
    atexit cleanup kills all child processes
```python

---

## 14. What an AI Reimplementer Should NOT Change

* The 5-step UX flow (Graph → Env → Sim → Report → Interact).
* The dual-platform parallel (Twitter + Reddit) design.
* Zep Cloud as the single source of truth for graph + episodic memory.
* OASIS as the simulator (it supplies action types, time loop, profile
  schema, recommendation engine).
* The IPC pattern (filesystem commands/responses) — it works across
  Windows/Linux/macOS without sockets.
* The two-process separation (Flask stays responsive while OASIS
  consumes CPU/IO).

---

## 15. What IS Safe to Swap

* LLM provider (anything OpenAI-SDK compatible).
* Frontend chart library (replace D3 with ECharts/cytoscape) as long as
  the `GET /api/graph/data/<id>` JSON shape is preserved.
* The default chunking strategy (`DEFAULT_CHUNK_SIZE=500`).
* Theme / styling / i18n languages (add any JSON under `locales/`).
* `OASIS_DEFAULT_MAX_ROUNDS` (10) — raise for longer runs (costs grow).

---

## 16. Quick File-to-Feature Index

| File | Purpose |
| ---- | ------- |
| `backend/app/__init__.py` | Flask app factory, blueprint registration, request logs, simulation cleanup |
| `backend/app/config.py` | Loads `.env` from repo root; LLM/Zep/upload config |
| `backend/run.py` | `flask run` entrypoint, port 5001, validates config |
| `backend/app/api/graph.py` | Project + ontology + graph-build endpoints |
| `backend/app/api/simulation.py` | Create / prepare / start / stop / interview endpoints |
| `backend/app/api/report.py` | Report generation + chat + streaming logs |
| `backend/app/services/ontology_generator.py` | LLM-extracted schema |
| `backend/app/services/graph_builder.py` | Zep batch ingestion |
| `backend/app/services/oasis_profile_generator.py` | Entity → persona |
| `backend/app/services/simulation_config_generator.py` | 4-step LLM config |
| `backend/app/services/simulation_runner.py` | Process spawn + JSONL monitor + IPC + locks |
| `backend/app/services/simulation_ipc.py` | File-based RPC client |
| `backend/app/services/zep_tools.py` | Search / InsightForge / Panorama / Interview tools |
| `backend/app/services/report_agent.py` | ReACT report writer |
| `backend/app/services/zep_graph_memory_updater.py` | Writes sim events back to Zep |
| `backend/app/services/text_processor.py` | Text chunking helper (500/50 overlap) |
| `backend/app/services/zep_entity_reader.py` | Reads + enriches Zep entity nodes for profile generation |
| `backend/app/services/simulation_manager.py` | CRUD over Simulation records (in-memory + disk) |
| `backend/app/models/project.py` | Disk-persisted project |
| `backend/app/models/task.py` | In-memory task tracker |
| `backend/app/utils/llm_client.py` | OpenAI-SDK wrapper |
| `backend/app/utils/zep.py` | Shared Zep client, timeouts, retries |
| `backend/app/utils/file_parser.py` | PDF/MD/TXT + chunker |
| `backend/app/utils/locale.py` | i18n + LLM prompt language hint |
| `backend/scripts/run_parallel_simulation.py` | Twitter+Reddit parallel runner |
| `backend/scripts/run_twitter_simulation.py` | Single-platform runner |
| `backend/scripts/run_reddit_simulation.py` | Single-platform runner |
| `backend/scripts/action_logger.py` | JSONL writer per platform |
| `backend/scripts/test_profile_format.py` | OASIS profile-format validator (test script) |
| `backend/scripts/validate_zep_cloud_integration.py` | End-to-end Zep Cloud integration smoke test |
| `frontend/src/main.js` | App bootstrap |
| `frontend/src/router/index.js` | 6 routes |
| `frontend/src/api/index.js` | axios + locale + error unwrap |
| `frontend/src/api/{graph,simulation,report}.js` | Endpoint wrappers |
| `frontend/src/views/Home.vue` | Landing + upload trigger |
| `frontend/src/views/MainView.vue` | 5-step workflow shell |
| `frontend/src/views/SimulationView.vue` | Pre-run config + start |
| `frontend/src/views/SimulationRunView.vue` | Live status |
| `frontend/src/views/ReportView.vue` | Render report + log streams |
| `frontend/src/views/InteractionView.vue` | Chat with report + agents |
| `frontend/src/components/Step1..5*.vue` | One per step |
| `frontend/src/components/GraphPanel.vue` | D3 graph renderer |
| `frontend/src/components/LanguageSwitcher.vue` | en/zh toggle |
| `frontend/src/store/pendingUpload.js` | Cross-route upload state |
| `locales/{en,zh}.json` | UI strings |
| `docker-compose.yml` + `Dockerfile` | Single-container deploy |
| `.github/workflows/release.yml` | Image publish |

---

**End of architecture spec.** Any AI reading this should be able to
rebuild the system end-to-end by following §12 step-by-step and matching
each file to §16.
