# Architecture — Plagiarism_Detected

> The "why" and "what" of this codebase. For the "how to commit" rules see
> [`THINKING_PATTERN.md`](./THINKING_PATTERN.md); for the operational
> harness see the `Makefile` targets (`make verify` runs everything).

## 1. What this app does

Plagiarism_Detected is a two-feature web service:

1. **Plagiarism detection** — drop a document and pick an algorithm; the
   service returns which parts of the document match a reference corpus
   and how strongly.
2. **Authenticity prediction** — upload any document and get back a
   probability distribution over `{human, ai, plagiarised}`.

Stack: **FastAPI** + **React 18** + **scikit-learn** +
**sentence-transformers** (`all-MiniLM-L6-v2`) + **distilgpt2** (for
perplexity features).

## 2. System diagram

```
┌────────────┐    POST /api/v1/documents      ┌──────────────────────────┐
│  Browser   │ ─────────────────────────────► │   FastAPI (uvicorn)      │
│  (React)   │                                 │   ┌────────────────────┐ │
│            │    GET /api/v1/analyses/:id     │   │ Routers            │ │
│            │ ◄─────────────────────────────   │   │  documents        │ │
│            │                                 │   │  corpus           │ │
│            │    POST /api/v1/predict         │   │  analyses         │ │
│            │ ─────────────────────────────►  │   │  predict          │ │
└────────────┘                                 │   └────────┬───────────┘ │
                                                │            │             │
                                                │   ┌────────▼────────┐    │
                                                │   │  Algorithms    │    │
                                                │   │  jaccard       │    │
                                                │   │  tfidf         │    │
                                                │   │  minilm        │    │
                                                │   │  winnowing     │    │
                                                │   └────────┬───────┘    │
                                                │            │             │
                                                │   ┌────────▼────────┐    │
                                                │   │ AI-detect      │    │
                                                │   │  features      │    │
                                                │   │  classifier    │    │
                                                │   │   ├ heuristic   │    │
                                                │   │   └ joblib model│    │
                                                │   └─────────────────┘    │
                                                └──────────────────────────┘
```

The frontend is a single-page React app served by `vite`. It talks to the
backend exclusively over JSON. There is no streaming endpoint in production
today (analysis results return synchronously).

## 3. Data flow

### 3.1 Document upload → analysis

```
upload (multipart) → ingest.parse()         ── extracts text from .pdf/.docx/.txt
                  → chunking.split_into_chunks()   ── 800-char chunks, sentence-aligned
                  → hashing.content_hash()         ── SHA-256 of normalised text
                  → document_store.put()           ── persists to SQLite (sqlalchemy)
                  → analyses router accepts the document_id
                  → vector_index.add()             ── embeds chunks via MiniLM, FIFO-capped
                  → algorithm.fit() + .score()    ── against the active corpus
                  → Match objects returned
                  → reporting.format()             ── JSON / PDF (PDF is best-effort)
```

### 3.2 Predict (3-class)

```
POST /api/v1/predict { document_id }
  → document_store.get(id)
  → ai_detect.classifier.predict_proba(text, model_path)
       → features.extract_features(text)         ── 6-dim feature vector
       → load joblib model if available
            ├─ present: model.predict_proba(features)
            └─ absent:  _heuristic_proba(features)
  → return {label, probabilities, features, model_version}
```

The feature vector has six components. See §6 for the spec.

## 4. The four algorithms

| Algorithm | What it catches | Cost | Notes |
|---|---|---|---|
| **jaccard** | Exact and near-exact copies (word-level) | Very fast | Default n=5. Underperforms on short queries (< ~10 tokens). |
| **tfidf** | Paraphrased / partial matches (n-gram aware) | Fast | sklearn `TfidfVectorizer` with custom tokenizer. |
| **minilm** | Semantic similarity, paraphrases | Slow (one MiniLM forward pass per chunk) | `all-MiniLM-L6-v2`, 384-dim, L2-normalised. Cosine similarity. |
| **winnowing** | Document fingerprinting, fast on large texts | Fast | MOSS-style. Default k=5, w=4 (lowered from MOSS's k=25 to fit essay-length inputs). |

### 4.1 Winnowing fix history (recent)

The original `winnow()` included a `last_min` deduplication guard that is
**not in the Schleimer-Wilkerson-Aiken paper**. It collapsed fingerprints
on small edits — a single word insertion in a near-copy dropped Jaccard
overlap from ~1.0 to ~0.2. The guard was removed in Phase 8.2.

The default k was also lowered from 25 to 5 because MOSS k=25 targets
full papers (~10k tokens); Plagiarism_Detected scores paragraphs and
essays (~50–500 tokens). At k=5 the near-copy overlap on a 62-token
corpus with one inserted word is **0.85**, vs 0.17 at k=25.

## 5. The AI / human / plagiarised classifier

### 5.1 Two paths

```python
def predict_proba(text: str, model_path: str) -> tuple[label, proba, features, version]:
    features = extract_features(text)
    loaded = _load_model(model_path)
    if loaded is None:
        proba = _heuristic_proba(features)
        version = "heuristic-v1"
    else:
        model, version = loaded          # "joblib-<mtime>"
        proba = model.predict_proba(features.to_array())
```

- If `app/ml_models/ai_classifier.joblib` exists, the trained
  `StandardScaler + LogisticRegression` pipeline wins.
- Otherwise the heuristic wins and `version = "heuristic-v1"`.

### 5.2 Why a heuristic at all

A small model file is not always present (fresh clone, no training data,
CI runs that don't retrain). The heuristic keeps the API useful
out-of-the-box and degrades gracefully.

### 5.3 Why the heuristic was rewritten (Phase 8.3)

The original heuristic used `distilgpt2` perplexity as the dominant AI
signal. That model is too small to distinguish AI from unfamiliar human
writing reliably — its high perplexity on human prose conflated the two
classes and floored `P(ai) ≈ 0.02` on every input. The fix drops the
perplexity term and uses burstiness + TTR + sentence length + stopword
ratio (the lexical features that hold up across canonical cases).

**Result on the four canonical test cases:**

| Sample | Before | After |
|---|---|---|
| ai_uniform_short | label=human, P(ai)=0.02 | **label=ai, P(ai)=0.63** |
| ai_gpt_verbose | label=human, P(ai)=0.49 | label=human, P(ai)=0.16 (above floor) |
| human_bursty | P(human)=0.80 | **P(human)=0.96** |
| plag_famous | P(plag)=0.51 | **P(plag)=0.86** |

### 5.4 Why a trained model is still needed (Phase 10+)

The heuristic is a transparent fallback. Decisive AI detection on
**verbose templated text** (high TTR but templated structure, like the
"Furthermore, ... Moreover, ... Consequently, ..." GPT style) cannot be
done with these six lexical features alone — the burstiness is low
(AI-ish) but the TTR is high (human-ish). That case needs the trained
model.

## 6. Feature vector (6 dimensions)

| # | Feature | What it measures |
|---|---|---|
| 1 | `perplexity_mean` | Mean per-sentence perplexity (distilgpt2). Neutral default 50.0 if the model fails to load. |
| 2 | `perplexity_std`  | Std-dev across sentences. Neutral default 10.0. |
| 3 | `burstiness` | stdev(per-sentence token count) / mean. High = human (varied lengths); low = AI (uniform) or plagiarised (one big sentence). |
| 4 | `type_token_ratio` | Unique tokens / total tokens. Vocabulary richness. High = human. |
| 5 | `avg_sentence_length` | Mean words per sentence. Low = AI; very high = plagiarised (one giant sentence). |
| 6 | `stopword_ratio` | Stopwords / total tokens. High = AI/filler-heavy. |

The feature vector is intentionally cheap and interpretable. Perplexity
is a "soft" feature (it falls back gracefully); the lexical four are
deterministic.

## 7. Threat model

| Threat | Where handled |
|---|---|
| **File extension spoofing** (upload `.exe` named `.pdf`) | `services/security.py` MIME-sniffs before accepting. |
| **Oversized upload** (DoS via huge files) | 10 MB cap, returns HTTP 413. |
| **Path traversal** in stored files | `safe_join()` prevents `..` escapes from `data/uploads/`. |
| **MIME spoofing bypassing content checks** | `python-magic` validates magic bytes, not just Content-Type header. |
| **Unbounded memory growth** in long-running deploys | `VectorIndex(max_items=10_000)` FIFO-evicts (Phase 8.2 fix). |
| **PII in uploaded text** | Stored at rest in `data/uploads/`; not exposed back to the API except via `/api/v1/analyses/:id` (text only retrievable by the owner-id, which is empty here). |
| **Secret leakage** | `.gitignore` excludes `.env`; `bandit -lll` runs in CI. |
| **Dependency CVEs** | `pip-audit` + `npm audit --audit-level=high` in `make security`. |
| **Perplexity model tampering via Hugging Face Hub** | `revision="main"` pinned in `perplexity.py:_load_model`. Bump deliberately when upgrading. |

## 8. Operational envelope

These are the canonical latency / memory expectations the algorithm audit
(Phase 15) will use to set hard limits.

| Document size | Jaccard | TF-IDF | MiniLM | Winnowing |
|---|---|---|---|---|
| 1 KB | < 50 ms | < 50 ms | < 500 ms | < 50 ms |
| 100 KB | < 500 ms | < 500 ms | < 5 s | < 500 ms |
| 1 MB | < 5 s | < 5 s | < 30 s | < 5 s |
| 10 MB | < 30 s | < 30 s | reject or stream | < 30 s |

Memory: all algorithms < 500 MB peak on a 10 MB document. The MiniLM
embedding call is the dominant cost.

If your change breaks these, the commit body must say so explicitly and
the new envelope goes in this table.

## 9. Failure modes and API behaviour

| Failure | HTTP code | Body |
|---|---|---|
| Unknown `document_id` on `/predict` | 404 | `{ "detail": "Unknown document_id: ..." }` |
| Unsupported file MIME | 422 | sanitised error |
| File > 10 MB | 413 | content too large |
| Algorithm crashes | 1 | global exception handler returns `{ "error": "internal_error", "message": "An unexpected error occurred." }` (no traceback leak) |
| Corpus empty | empty `matches` list | `[]` |
| Trained model missing | predict still works, `model_version = "heuristic-v1"` | OK |
| Perplexity model load fails | features fall back to neutral defaults | OK |

## 10. Extension points

### 10.1 Adding a 5th algorithm

1. Implement `SimilarityAlgo` (see `services/algorithms/base.py`).
2. Add the class to `services/algorithms/registry.py::ALGOS`.
3. Register in the analysis router's algorithm dispatch.
4. Add a unit test under `tests/unit/test_algorithms.py::test_registry_contains_all_algorithms`.
5. Optionally tune the operational envelope table in §8.

### 10.2 Retraining the AI classifier

```
cd backend
uv run python -m app.services.ai_detect.train \
    --csv data/ai_train.csv \
    --out app/ml_models/ai_classifier.joblib
```

Or via Makefile: `make backend-train`.

### 10.3 Swapping the perplexity model

Edit `services/ai_detect/perplexity.py::MODEL_NAME_DEFAULT` and bump the
`revision=` argument in `_load_model`. The feature vector stays
identical, so the trained classifier does not need retraining.

## 11. Configuration

`.env` keys (see `.env.example`):

| Key | Default | Purpose |
|---|---|---|
| `APP_ENV` | `development` | `production` switches off `/api/docs` and tightens CORS. |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated. Never `*` in production. |
| `AI_CLASSIFIER_PATH` | `./app/ml_models/ai_classifier.joblib` | If file is absent, heuristic-v1 wins. |
| `LOG_LEVEL` | `INFO` | structlog level. |
| `MAX_UPLOAD_BYTES` | `10_485_760` | 10 MB. Returns 413 above this. |

## 12. Directory map

```
backend/
├── app/
│   ├── api (routers) /             — FastAPI endpoints
│   │   ├── documents.py            — upload + list
│   │   ├── corpus.py               — manage reference corpus
│   │   ├── analyses.py             — run / retrieve analyses
│   │   ├── predict.py              — POST /predict 3-class
│   │   └── health.py
│   ├── services/
│   │   ├── algorithms/             — 4 similarity algorithms
│   │   │   ├── base.py             — Match, SimilarityAlgo protocol
│   │   │   ├── jaccard.py
│   │   │   ├── tfidf.py
│   │   │   ├── embeddings.py       — MiniLM
│   │   │   ├── winnowing.py        — MOSS fingerprinting
│   │   │   └── registry.py         — name -> instance
│   │   ├── ai_detect/              — 3-class classifier
│   │   │   ├── features.py         — 6-dim feature vector
│   │   │   ├── classifier.py       — predict_proba() + heuristic
│   │   │   ├── train.py            — CLI: csv -> joblib
│   │   │   ├── perplexity.py       — distilgpt2 wrapper
│   │   │   └── burstiness.py
│   │   ├── vector_index.py          — L2-normalised matrix + max_items cap
│   │   ├── document_store.py        — SQLite-backed
│   │   ├── chunking.py
│   │   ├── ingest.py
│   │   ├── hashing.py
│   │   ├── reporting.py            — JSON / PDF
│   │   └── security.py             — MIME sniffing, safe_join, limits
│   ├── ml_models/
│   │   └── ai_classifier.joblib     — produced by train.py
│   ├── config.py                    — pydantic-settings
│   └── main.py                      — FastAPI app factory
├── data/
│   ├── uploads/                     — user uploads (gitignored)
│   ├── indexes/                     — persisted MiniLM vectors
│   └── ai_train.csv                 — labelled training set
├── tests/                           — unit + integration
└── pyproject.toml

frontend/
├── src/
│   ├── components/                  — Step1Upload, Step2AlgorithmPicker, …
│   ├── pages/                       — Home, Analyse, History
│   ├── api/                         — typed axios client
│   └── App.tsx
├── public/
└── vite.config.ts

deploy/
├── docker-compose.dev.yml
└── Dockerfile (compose)
```

## 13. What this document deliberately omits

- **Per-class F1 / precision / recall on the trained model.** Not yet
  measured. Phase 10 will produce a confusion matrix in
  `docs/releases/...tdd.md`.
- **Cost in dollar terms for the MiniLM forward pass.** Out of scope; the
  app self-hosts and doesn't bill.
- **Cross-language plagiarism.** All algorithms are English-trained;
  the stopword list in `features.py` is English-only. Multilingual
  support is a Phase 16+ concern.