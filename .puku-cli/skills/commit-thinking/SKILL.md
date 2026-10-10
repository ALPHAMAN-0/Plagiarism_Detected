---
name: commit-thinking
description: Plagiarism_Detected-specific commit rules layered on top of the user-level commit-thinking skill. Adds algorithm-audit enforcement, the 4-step UI workflow (Step1Upload → Step2AlgorithmPicker → Step3Results → Step4History), and the phase tracker in THINKING_PATTERN.md. Activates when working in the Plagiarism_Detected repo, after the user-level commit-thinking and tdd-workflow skills.
metadata:
  origin: Plagiarism_Detected
  inherits: ~/.puku-cli/skills/commit-thinking
  reference: ../../THINKING_PATTERN.md
---

# Commit Thinking — Plagiarism_Detected Layer

This is the **project-level layer** that sits on top of the user-level
`commit-thinking` skill at `~/.puku-cli/skills/commit-thinking/SKILL.md`.

Read both, in this order:
1. User-level skill (cross-repo MiroFish-derived discipline)
2. This file (Plagiarism_Detected-specific additions)
3. `../../THINKING_PATTERN.md` (the "why" doc and the phase tracker)

The user-level skill defines prefixes, templates, and anti-patterns. This
file **adds Plagiarism_Detected-specific rules** that the user-level skill
cannot know.

## Plagiarism_Detected-Specific Additions

### 1. The 4-Step UI Workflow Has Named Components

When the UI is being built (Phase 10–13), the named steps are:

| Step | Component | Phase |
|---|---|---|
| Step1Upload | `Step1Upload.tsx` | 10 |
| Step2AlgorithmPicker | `Step2AlgorithmPicker.tsx` | 11 |
| Step3Results | `Step3Results.tsx` | 12 |
| Step4History | `Step4History.tsx` | 13 |

Always include the step name in the commit subject. The same MiroFish
"5-10x iteration per day on the same file" pattern applies — the component
name goes in the subject so the diff is searchable by step.

### 2. Algorithm Changes Must Use Algorithm-Scoped Prefixes

The four algorithms have their own scope tokens. When committing an
algorithm-specific change, use the algorithm name as the scope:

| Algorithm | Scope token | Module |
|---|---|---|
| N-gram shingling + Jaccard | `jaccard` | `backend/app/services/algorithms/jaccard.py` |
| TF-IDF + Cosine | `tfidf` | `backend/app/services/algorithms/tfidf.py` |
| Sentence-Transformer MiniLM | `minilm` | `backend/app/services/algorithms/minilm.py` |
| Winnowing (MOSS-style) | `winnowing` | `backend/app/services/algorithms/winnowing.py` |

Examples:

```
fix(jaccard): handle empty input without raising
fix(tfidf): cap vocabulary to prevent OOM on huge inputs
fix(minilm): batch embedding calls to bound peak memory
fix(winnowing): preserve Unicode case folding consistency
test(jaccard): add property-based test for shingle commutativity
chore(audit): jaccard algorithm comprehensive review
```

If a commit touches more than one algorithm, split it.

### 3. AI-Detect and Reporting Have Their Own Scopes

| Feature | Scope token | Module |
|---|---|---|
| AI-detect (3-class classifier) | `ai-detect` | `backend/app/services/ai_detect/` |
| Reporting (PDF/JSON export) | `reporting` | `backend/app/services/reporting.py` |
| Ingest / upload pipeline | `ingest` | `backend/app/services/ingest.py` |
| Chunking | `chunking` | `backend/app/services/chunking.py` |
| Hashing | `hashing` | `backend/app/services/hashing.py` |
| Vector index | `vector-index` | `backend/app/services/vector_index.py` |
| Document store | `store` | `backend/app/services/document_store.py` |
| Security (file validation, limits) | `security` | `backend/app/services/security.py` |

### 4. The Phase Tracker Must Be Updated

Every time a phase closes (a `(PHASE N GREEN)` or `(PHASE N RED)` commit
lands), the `## 7. Phase tracker` table in `THINKING_PATTERN.md` must be
updated in the **same commit**. Format the table cells as:

```
| N | Phase Name | YYYY-MM-DD | YYYY-MM-DD | `<short-sha>` one-line summary |
```

The closing commit subject must include `(PHASE N GREEN)` or
`(PHASE N RED)` so the marker is searchable.

### 5. Threat-Model-Aware Security Defaults

When writing a `fix(security):` commit in this repo, the body **must**
reference which threat from the ARCHITECTURE.md threat model the fix
addresses. If ARCHITECTURE.md does not yet have a threat model, the
security commit must include a one-line threat description and the doc
update is filed as a follow-up.

### 6. Algorithm Performance Has Hard Limits

If a commit changes an algorithm's memory or time behavior, the body **must**
include before/after numbers for at least one canonical test case. Use
the canonical cases from `tests/fixtures/`:

| Fixture | Size | Algorithm expectations |
|---|---|---|
| `small.txt` | 1 KB | All algorithms < 50 ms, < 50 MB |
| `medium.txt` | 100 KB | Jaccard < 500 ms, TF-IDF < 1 s, MiniLM < 5 s, Winnowing < 500 ms |
| `large.txt` | 1 MB | All algorithms < 30 s, < 500 MB |
| `huge.txt` | 10 MB | Must not OOM; MiniLM must reject or stream |

If your change breaks these, the body must say so explicitly and reference
the new envelope.

### 7. Test Files Live Beside the Code They Test

When proposing a test commit, the body must name the test file path
relative to the repo root:

```
test(backend): add failing detect endpoint validation (RED)

Adds tests/backend/app/routers/test_detect.py::test_rejects_unsupported_mime
expected to fail. Run: `uv run pytest tests/backend/app/routers/test_detect.py -x`.
```

### 8. The Verb Lexicon

For the MiroFish-style same-file iteration commits, prefer these verbs in
this order of frequency (matches the MiroFish log distribution):

1. `Enhance` — adding visual polish, edge case handling, or UX detail
2. `Update` — small change to existing behavior, often clarification
3. `Refactor` — behavior-preserving restructure
4. `Implement` — new feature, sub-component, or capability
5. `Add` — new file, new dependency, new option
6. `Remove` — deletion of obsolete code, deps, or files
7. `Fix` — bug
8. `Revamp` — major visual or structural overhaul
9. `Replace` — substitution of one approach for another
10. `Normalize` — bring data into a canonical form

Avoid `Improve` and `Update code` — too vague. Every verb should be paired
with a *what* and a *for what audience*.

### 9. Closing a Phase

A phase is closed with one of:

```
docs: add ARCHITECTURE.md (PHASE 9 GREEN)
feat(frontend): Step1Upload with size + MIME validation (PHASE 10 GREEN)
chore(hardening): CSP + MIME sniffing + upload limits (PHASE 14 GREEN)
chore(audit): jaccard algorithm (PHASE 15 GREEN)
```

The closing commit:
- Updates the phase tracker table in `THINKING_PATTERN.md`
- References the prior TDD evidence in `docs/releases/<phase>/...tdd.md`
  (created by the `tdd-workflow` skill)
- Includes the test count or coverage delta in the body

### 10. Refuse to Generate When

This is **in addition to** the user-level anti-patterns:

- A frontend commit does not name the step (`Step1Upload` etc.) — refuse,
  ask which step
- An algorithm commit does not include before/after numbers — refuse,
  ask for the benchmark
- A `fix(security):` body does not name the threat — refuse, ask which
  threat from the threat model
- A `(PHASE N)` commit does not update the phase tracker — refuse, point
  to the table that needs updating
- A test commit does not name the test file path — refuse, ask for it
- A `feat:` commit without a scope token — refuse, ask which algorithm,
  step, or feature

## Interaction with This Repo

When activated in this repo:

1. Read `../../THINKING_PATTERN.md` first — it has the phase tracker
2. Read the user-level `commit-thinking` skill for the cross-repo rules
3. Apply the Plagiarism_Detected-specific rules above
4. If `THINKING_PATTERN.md` does not exist, point the user to it and ask
   whether to create it before proceeding

## Reference Examples (Plagiarism_Detected-specific)

Good:

```
test(backend): add failing detect endpoint MIME validation (RED)

Adds tests/backend/app/routers/test_detect.py::test_rejects_unsupported_mime.
Run: uv run pytest tests/backend/app/routers/test_detect.py -x.
Expected: import error or assertion failure (RED).
```

```
feat(backend): implement /api/detect with Jaccard default (GREEN)

backend/app/routers/detect.py now accepts upload, validates MIME, and runs
Jaccard by default. Validated GREEN with same pytest command.
```

```
Enhance Step1Upload.tsx with drag-and-drop visual feedback
Refactor Step2AlgorithmPicker.tsx to extract useAlgorithmMeta composable
Fix silent data loss when document exceeds vector index capacity
fix(security): enforce file MIME sniffing, not just extension
  Threat: file extension spoofing bypassing content-type check
chore(deps): upgrade sentence-transformers 3.x to fix CVE-2025-XXXXX
```

Bad:

```
fixed stuff
update
WIP
chore: hardening
feat: add the new feature
test: added some tests
```

## Closing Note for This Repo

The engine is built (Phases 1–8). The harness is not (Phases 9–16). Every
commit from here forward either closes one of those phases or maintains
the engine already shipped. Both are valid; the verb and the prefix tell
the reader which.
