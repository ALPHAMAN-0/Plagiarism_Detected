# Thinking Pattern — Plagiarism_Detected

> How this codebase is meant to be built, derived from a comparative study of
> MiroFish's 322-commit evolution (2025-11-26 → 2026-10-02) and translated
> onto the Plagiarism_Detected stack (FastAPI + React + scikit-learn +
> sentence-transformers).

---

## Reading order

This file is the **why**. The skills are the **how**. Read in this order:

1. `THINKING_PATTERN.md` (this file) — the MiroFish derivation, the phase
   roadmap, the commit-message templates
2. `~/.puku-cli/skills/commit-thinking/SKILL.md` — the cross-repo skill that
   enforces the discipline at every commit
3. `.puku-cli/skills/commit-thinking/SKILL.md` — the Plagiarism_Detected
   layer with algorithm scopes, step names, phase tracker rules, and
   threat-model-aware security defaults

The skills are **invokable**: they activate when you ask for the next
commit, when `tdd-workflow` has just produced a passing test, or when you
explicitly invoke `/commit-thinking`. The markdown file is a reference doc
for humans and for the skill to consult — it does not enforce anything on
its own.

If you change the rules here, update both skills to match.

---

## 0. The principle underneath the pattern

MiroFish did **not** follow Conventional Commits as a religion. Only 37 of 322
commits used a `type:` prefix. The rest were verbose, file-anchored,
intent-describing sentences:

```
Enhance Step2EnvSetup.vue with detailed configuration display and improved styling
Refactor Step3Simulation.vue for improved clarity and user experience
Implement dynamic graph memory update feature for simulations
Fix silent data loss when platform defaults to reddit for Twitter-only simulations
```

What looks like "no discipline" is actually a **different discipline**: every
commit message names the file, names the intent, and reads as a sentence a
new contributor can understand six months later. The code commits to TDD in
phases; the *messages* commit to human readability.

**Plagiarism_Detected keeps the TDD phase discipline (RED → GREEN → REFACTOR)
in the prefix, but adopts the verbose file-anchored style in the body.**

Resulting hybrid:

```
test(frontend): add failing Step1Upload acceptance test (RED)
feat(frontend): implement Step1Upload with MIME sniffing (GREEN)
Refactor Step1Upload.vue to extract useFileValidator composable
Enhance Step1Upload.vue with drag-and-drop visual feedback
```

The first two preserve the test-first audit trail. The last two are the
MiroFish-style "same file, iterated 5-10x in a day" pattern that the
historical record shows produces the most readable diffs.

---

## 1. Where we are right now

```
Phase 0  chore: initial scaffold (root config, license, security policy)   34fcbf0
Phase 1  test: add failing health endpoint tests (RED)                     26d4263
         feat: implement FastAPI health endpoints (GREEN)                  6500e26
Phase 2  feat(ingest+chunking): implement security, ingest, chunking,
         hashing (Phase 2 GREEN)                                          55aece2
Phase 3  feat(algorithms): Jaccard, TF-IDF, MiniLM embeddings,
         Winnowing (Phase 3 GREEN)                                        62aea3e
Phase 4  feat: detect endpoint + AI-detect + reporting
         (Phases 4-5 GREEN, 52 tests pass)                                106cbbd
Phase 5  feat(frontend): React 18 + Vite + TS with TDD
         (Phase 6 GREEN, 30 tests pass)                                   8fbd064
Phase 6  chore(hardening): CI + Docker + ESLint + bandit
         fixes (Phase 7 GREEN)                                            1df25c6
Phase 7  chore(security): upgrade vitest 5 + react-router 7,
         drop CVEs (npm 0 vulns)                                          87951d4
Phase 8  docs(tdd): add TDD evidence report for the build
         (Phase 8 GREEN)                                                  9c99c88
```

**Mapping onto MiroFish's trajectory:**

| MiroFish phase | Plagiarism_Detected equivalent | Status |
|---|---|---|
| Engine alone (txt2graph, OASIS, Zep) | Algorithms + detect + AI-detect | **DONE** |
| LLM rate-limit + provider abstraction | N/A (no LLM in hot path) | N/A |
| Document the engine | README only — `ARCHITECTURE.md` missing | **GAP** |
| UI shell + 4-step workflow | React/Vite/TS scaffolded, no real screens | **GAP** |
| Same-file 5-10x iteration | Not yet started | **GAP** |
| Hardening sweep (i18n, security, deps) | CI/Docker/ESLint/bandit done; CSP/MIME/limits open | **PARTIAL** |
| Audit-and-fan-out (Zep, GPT-5, OASIS) | Each algorithm deserves an audit PR | **GAP** |
| i18n + community plumbing | English-only; no CONTRIBUTING/issue templates | **GAP** |

**The engine is built. The harness around it is not. The next three months
are Phase 9–15 work.**

---

## 2. The pattern, as a sequence

### Phase 9 — Document the engine before touching the UI

**Why first:** MiroFish wrote a 33 KB `ARCHITECTURE.md` *before* shipping any
frontend commits. By the time `Step1GraphBuild.vue` landed, the engine
already had a written contract. A new contributor could read the engine
without reading the code.

**Deliverable:** `ARCHITECTURE.md` covering:
1. System diagram (text or mermaid)
2. Data flow: upload → ingest → chunk → hash → store → algorithm → report
3. Why these four algorithms (and why not more)
4. Threat model (file size, MIME spoofing, replay, exfiltration via response)
5. Extension points (how to add a 5th algorithm)
6. Operational envelope (max document size, max corpus size, expected latency)
7. Failure modes and how each surfaces in the API

**Commit style:**

```
docs: add ARCHITECTURE.md describing engine, threat model, extension points
docs: expand ARCHITECTURE.md data-flow section with mermaid sequence
docs: add operational envelope and failure-mode tables to ARCHITECTURE.md
```

Three commits, each 5–10 KB. Same-file iteration is allowed and expected.

### Phase 10 — UI shell + Step1Upload (TDD, MiroFish style)

**Why this order:** MiroFish's first frontend commit was the home/landing
page + logo. Then the file-upload state. *Then* the visualization library
(D3) was added — at the same time as the upload flow. The lesson: **do not
add the graph viz lib until the upload flow needs it.**

**TDD loop (RED → GREEN → REFACTOR), per behavior:**

```
test(frontend): add failing test for Step1Upload file size rejection (RED)
test(frontend): add failing test for Step1Upload MIME validation (RED)
test(frontend): add failing test for Step1Upload progress reporting (RED)

feat(frontend): implement Step1Upload with size + MIME validation (GREEN)
feat(frontend): wire Step1Upload progress events to backend (GREEN)

Refactor Step1Upload.vue to extract useFileValidator composable
Enhance Step1Upload.vue with drag-and-drop visual feedback
Update Step1Upload.vue to show supported file types
Revamp Step1Upload.vue styling for improved affordance
```

**MiroFish behavioral signal:** the same `Step2EnvSetup.vue` got **8 commits
in a single day** during its construction. Expect the same here. Do not
batch "refactor" with "feat" — keep them as separate, reviewable commits.

### Phase 11 — Step2AlgorithmPicker (TDD)

**Behaviors to test:**
- Default algorithm is Jaccard (fastest, cheapest)
- "Use multiple" toggle enables checkbox per algorithm
- Each algorithm row shows: name, 1-line description, expected latency, cost note
- Selection persists in URL query params (so links are shareable)
- Disables incompatible combinations (e.g. Winnowing on >10 MB without warning)

**Commit shape:**

```
test(frontend): add failing tests for Step2 default selection and toggle (RED)
feat(frontend): implement Step2AlgorithmPicker with default + multi-select (GREEN)
Refactor Step2AlgorithmPicker.vue to extract useAlgorithmMeta composable
Enhance Step2AlgorithmPicker.vue with latency/cost hint per algorithm
Update Step2AlgorithmPicker.vue to sync selection to URL query params
```

### Phase 12 — Step3Results (TDD)

**The hard step.** This is where MiroFish's `Step4Report.vue` lived, and the
one with the most iteration. Behaviors:

- Highlighted matches in the source document (color by algorithm)
- Per-algorithm score breakdown
- "Why this match" expandable detail (which chunk, which n-gram, which
  embedding distance)
- Export to PDF / JSON
- "Run another algorithm on this result" button

**Commit shape:** same as before, with extra "Enhance …" iterations
because the visual design will demand them.

### Phase 13 — Step4History (TDD)

**Behaviors:**
- List of past analyses with timestamp, filename, top score
- Click → reopens results
- "Delete" with confirm
- Pagination
- Empty state

This is the simplest screen. Do not over-engineer it.

### Phase 14 — Hardening sweep (MiroFish "fix everything" phase)

MiroFish's mid-life was a continuous stream of:

```
fix(security): flask debug mode enabled by default, exposed on 0.0.0.0
fix(security): upgrade axios, rollup, picomatch to fix 3 high severity vulnerabilities
fix(graph): enforce PascalCase for entity names and SCREAMING_SNAKE_CASE for edge names
fix: don't drop earlier user messages with same content from chat history
fix: stop polling when simulation fails
```

**Mirror that. Concrete items, one commit each:**

```
fix(security): add CSP and X-Content-Type-Options headers
fix(security): enforce file MIME sniffing, not just extension
fix(security): cap upload size at 10 MB with 413 response
fix(perf): cap TF-IDF vocabulary to prevent OOM on huge inputs
fix(perf): batch MiniLM embedding calls to bound peak memory
fix(perf): add max_items limit to vector_index to prevent unbounded growth
fix: don't drop earlier uploaded documents with same filename from history
fix: stop polling when analysis fails
fix: return 422 (not 500) on unsupported file type
fix(frontend): show local date in history cards, not UTC
fix(frontend): set HTML lang attribute before React mounts
fix(deps): upgrade … to fix CVE-…
```

**One finding, one commit, one file. That is the discipline.**

### Phase 15 — Algorithm audit-and-fan-out

MiroFish's "Zep Cloud comprehensive audit" PR was followed by 6 narrow
fixes. The same shape, applied per algorithm:

```
chore(audit): jaccard algorithm comprehensive review
fix(jaccard): handle empty input
fix(jaccard): normalize whitespace before shingling
fix(jaccard): cap n-gram width to prevent blowup
fix(jaccard): preserve Unicode case folding consistency
fix(jaccard): return 0.0 (not raise) on empty reference corpus
test(jaccard): add property-based test for shingle commutativity

chore(audit): tfidf algorithm comprehensive review
fix(tfidf): ...
…
```

Each audit is **one PR with 3–6 follow-up commits**. Do not bundle.

### Phase 16 — i18n + community plumbing

MiroFish's i18n sweep was 10+ commits translating Chinese → bilingual.
Plagiarism_Detected is English-only. Add:

```
feat(i18n): add i18next with English default and Bengali as second locale
feat(i18n): replace all hardcoded strings in Step1-4 components
docs: add CONTRIBUTING.md
docs: add PR template
docs: add issue templates (bug, feature, algorithm-request)
ci: add dependabot weekly
ci: add CODEOWNERS
```

---

## 3. The recurring micro-patterns

| Pattern | MiroFish example | Plagiarism_Detected equivalent |
|---|---|---|
| Same file, iterated 5–10x in 24h | `Step2EnvSetup.vue` × 8 in one day | `Step1Upload.vue` × 5-8 over a day |
| Verbose file-anchored subject | "Enhance X.vue with Y for improved Z" | Same |
| "Remove obsolete/unused X" as a regular commit | "Remove obsolete simulation files" | "Remove obsolete single-file algorithm endpoint" |
| One feature = one commit | "Implement Interview feature" | "Implement Step1Upload file validator" |
| `chore: … [skip ci]` for bot commits | Star History, dependabot | Dependabot, weekly CVE scan |
| Conventional prefix only on PRs from outside | codex, Ghostubborn, YunyueLi PRs follow `fix(scope):` | Same — your own work uses the hybrid style; external PRs use strict conventional |
| Audit-then-fan-out | "zep-cloud-comprehensive-audit" → 6 follow-ups | One audit PR per algorithm → 3-6 follow-ups each |
| Doc the engine before the UI | ARCHITECTURE.md before Step1GraphBuild.vue | ARCHITECTURE.md before Step1Upload.vue (Phase 9) |
| Same file, 3 commits, one day, different aspects | "Enhance … with X", "Refactor … for Y", "Update … with Z" | Same |

---

## 4. Commit-message templates

### Backend (FastAPI) commits

```
test(backend): add failing <endpoint> <behavior> test (RED)
feat(backend): implement <endpoint> with <constraint> (GREEN)
fix(backend): <one-sentence root cause and fix>
refactor(backend): <what moved, why>
docs(backend): <what was added to README/ARCHITECTURE>
chore(backend): <deps, config, tooling>
```

### Frontend (React/Vite/TS) commits

```
test(frontend): add failing <Component> <behavior> test (RED)
feat(frontend): implement <Component> with <capability> (GREEN)

Enhance <Component>.tsx with <one visual/UX detail>
Refactor <Component>.tsx to extract <hook-or-subcomponent>
Update <Component>.tsx for improved <clarity|affordance|consistency>
Revamp <Component>.tsx styling for improved <audience> experience
```

The 4-line block above is the **default** for screen work. The first two
lines (test + feat) are mandatory. The latter three may repeat indefinitely
during a single day's iteration.

### Operational / security commits

```
fix(security): <one finding, one sentence>
fix(perf): <one bottleneck, one sentence>
fix: <one bug, one sentence>
chore(deps): upgrade <pkg> to <version> to fix CVE-<id>
chore(audit): <scope> comprehensive review
```

### Documentation commits

```
docs: add <DocName>.md covering <one aspect>
docs: expand <DocName>.md <section> with <detail>
docs(readme): <one fix or polish>
```

---

## 5. Anti-patterns (what MiroFish did *not* do, and what we should avoid)

1. **No "WIP" commits on `main`.** MiroFish used feature branches + PRs even
   for solo work. We mirror that: branch per phase, PR per phase.
2. **No bundled "fixed stuff" commits.** One fix per commit, one file. The
   `1df25c6 chore(hardening): CI + Docker + ESLint + bandit fixes` style is
   acceptable **only** for genuinely orthogonal fixes in one PR; prefer
   splitting.
3. **No "feat: add everything" commits.** Each phase adds *one* user-visible
   capability. Resist the urge to ship a phase in one commit.
4. **No doc debt at the end.** ARCHITECTURE.md in Phase 9, not Phase 15.
5. **No "improve code" commits without a reason.** Every commit message
   names a file, a behavior, and a "why."

---

## 6. The single-sentence takeaway

**Engine first, document the engine, build the UI as four iterated steps,
harden with one-fix-one-commit, audit each algorithm with fan-out PRs,
then i18n and community. We are at Phase 9. ARCHITECTURE.md is the next
commit.**

---

## 7. Phase tracker (living section)

| Phase | Name | Started | Completed | Notes |
|---|---|---|---|---|
| 0 | Initial scaffold | 2026-10-10 | 2026-10-10 | `34fcbf0` |
| 1 | Health endpoint (TDD) | 2026-10-10 | 2026-10-10 | `26d4263` → `6500e26` |
| 2 | Ingest + chunking | 2026-10-10 | 2026-10-10 | `55aece2` |
| 3 | Algorithms | 2026-10-10 | 2026-10-10 | `62aea3e` |
| 4 | Detect + AI-detect + reporting | 2026-10-10 | 2026-10-10 | `106cbbd` |
| 5 | Frontend scaffold (TDD) | 2026-10-10 | 2026-10-10 | `8fbd064` |
| 6 | Hardening (CI/Docker/ESLint/bandit) | 2026-10-10 | 2026-10-10 | `1df25c6` |
| 7 | Dep upgrade (CVE) | 2026-10-10 | 2026-10-10 | `87951d4` |
| 8 | TDD evidence report | 2026-10-10 | 2026-10-10 | `9c99c88` |
| 8.1 | Thinking pattern + skills wired up | 2026-10-10 | 2026-10-10 | this file + `~/.puku-cli/skills/commit-thinking/SKILL.md` + `.puku-cli/skills/commit-thinking/SKILL.md` |
| 8.2 | Winnowing near-copy + vector_index cap (maintenance) | 2026-10-10 | 2026-10-10 | branch `fix/winnowing-near-copy`: `37fe413` (RED test), `5167b7d` (GREEN fix), `f1b813d` (RED test), `9bc4ed9` (GREEN cap). 59 passed, 1 skipped. |
| 8.3 | AI-detect P(ai) floor fix | 2026-10-10 | 2026-10-10 | branch `fix/heuristic-fixes`: `2175726` (RED test), `1fa309f` (GREEN heuristic rewrite). 63 passed, 1 skipped. Trained model still pending. |
| 9 | **ARCHITECTURE.md** | 2026-10-10 | 2026-10-10 | `b724bdf` — 13 sections, 325 lines. Includes §4.1 (Winnowing fix history) and §5.3 (heuristic rewrite history) so post-mortems don't get re-introduced. |
| 9.5 | Trained AI classifier | 2026-10-10 | 2026-10-10 | `fe6bb91` (RED smoke test), `5614c2e` (labelled training set, 45 rows), `ec9f9f6` (drop deprecated `multi_class` kwarg), `5503ecf` (`make backend-train`). 5-fold CV accuracy 0.931 ± 0.002. `backend/app/ml_models/ai_classifier.joblib` is gitignored (reproducible build artifact). 67 passed, 1 skipped, 85.45% coverage. |
| 10 | Step1Upload | — | — | **NEXT** |
| 11 | Step2AlgorithmPicker | — | — | — |
| 12 | Step3Results | — | — | — |
| 13 | Step4History | — | — | — |
| 14 | Hardening sweep | — | — | — |
| 15 | Algorithm audits | — | — | — |
| 16 | i18n + community | — | — | — |

Update this table as phases close.

### Closing a phase

When a phase closes, the closing commit must:

1. Carry the phase marker: `(PHASE N GREEN)` or `(PHASE N RED)`.
2. Update this table in the same commit (Started, Completed, Notes).
3. Reference the prior TDD evidence at `docs/releases/<phase>/...tdd.md` if
   one was produced by the `tdd-workflow` skill.
4. Include the test count or coverage delta in the body.
5. Trigger the repo-level `commit-thinking` skill (see
   `.puku-cli/skills/commit-thinking/SKILL.md` §9 "Closing a Phase").

The repo-level skill will refuse to write the commit if the table is not
updated. The user-level skill will refuse to write the commit if the
subject does not carry the phase marker. Both gates are intentional.

### Skill locations (for future reference)

| Skill | Path | Purpose |
|---|---|---|
| User-level `commit-thinking` | `~/.puku-cli/skills/commit-thinking/SKILL.md` | Cross-repo MiroFish-derived discipline (prefixes, templates, anti-patterns) |
| Repo-level `commit-thinking` | `.puku-cli/skills/commit-thinking/SKILL.md` | Plagiarism_Detected layer (algorithm scopes, step names, phase tracker, threat-model, perf envelope) |
| TDD workflow | `~/.puku-cli/skills/tdd-workflow/SKILL.md` | Produces RED/GREEN evidence; pairs with `commit-thinking` for the commit-message shape |
| Git workflow | `~/.puku-cli/skills/git-workflow/SKILL.md` | Branching, PR conventions; sits below `commit-thinking` |
| Verification loop | `~/.puku-cli/skills/verification-loop/SKILL.md` | Run before closing a phase; produces the evidence file referenced above |
| Security review | `~/.puku-cli/skills/security-review/SKILL.md` | Produces findings that the `fix(security):` template wraps |

When any of these skills change, update this table.
