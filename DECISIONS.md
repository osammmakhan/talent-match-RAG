# DECISIONS.md — Talent Match RAG

Log of key technical and scope decisions, in the order they were made. New decisions get appended, not inserted retroactively.

---

### D1 — Vector store: Pinecone
**Decision**: Use Pinecone as the vector store.
**Why**: Pinecone is the most frequently named vector database in target job postings. It is also fully managed, which removes the local-disk persistence problem on free hosting tiers (Render's free tier disk is not reliably persistent across redeploys).
**Alternatives considered**: Qdrant (strong open-source option, rising in job postings, but behind Pinecone in name recognition). Chroma (weaker resume-keyword value and the deployment persistence issue). FAISS (no metadata storage or managed persistence, more work for no resume-keyword benefit here). pgvector (only makes sense if already using Postgres, which this project doesn't need otherwise).
**Verified free tier**: Pinecone Starter plan, $0/month, no credit card, 2GB storage, up to 5 indexes, 1M reads / 2M writes per month.

---

### D2 — Generation provider: Groq
**Decision**: Use Groq for chat/generation, via its OpenAI-compatible endpoint.
**Why**: Free tier, fast inference, minimal code change from a standard OpenAI client, and Groq is already a confirmed skill from prior personal projects (RomanUrdu.ai, Llama-3 Chat App), so this is a legitimate extension of existing evidence rather than a fresh unverified claim.
**Constraint discovered**: Groq does not offer an embeddings endpoint (confirmed by checking their official API reference: chat, audio, batches, fine-tuning, models, no embeddings). This is why embeddings needed a separate provider (see D3).

---

### D3 — Embeddings provider: local sentence-transformers
**Decision**: Use `sentence-transformers` (`all-MiniLM-L6-v2`), running locally, for embeddings.
**Why**: Free with no API key or per-call cost, keeping the whole pipeline's cost at zero regardless of usage volume. Adds a legitimately separate, real skill (local embedding models) rather than just swapping one paid API for another.
**Trade-off accepted**: 384-dimension embeddings, generally lower embedding quality than OpenAI's models for nuanced semantic distinctions, acceptable for a demo-scale project with short profile texts.

---

### D4 — Scope: demo-grade, not production-grade
**Decision**: No authentication, no horizontal scaling, no observability/monitoring stack, no SLA design.
**Why**: Time spent on production infrastructure doesn't produce evidence toward the skill gap this project exists to close, and risks reading as scope inflation on a solo portfolio piece.
**Exception carved out**: Docker and basic CI are cheap and directly close a separately confirmed gap (Docker/CI-CD), so they are deferred to a later phase rather than excluded outright. Full production infrastructure (autoscaling, monitoring stack, secrets rotation) is excluded, not deferred.

---

### D5 — Dockerfile and CI: deferred
**Decision**: Explicitly deferred until after the core pipeline, evaluation, and deployment (Phases 0 to 4) are complete and verified.
**Why**: User's own prioritization; avoid building infrastructure around a pipeline that hasn't been proven to work yet.

---

### D6 — Evaluation: two separate components
**Decision**: (1) A lightweight, framework-free skill-overlap precision@5 script for retrieval quality. (2) A custom eval built on OpenAI's open-source Evals framework, wired to Groq (not OpenAI's paid API), for generation groundedness.
**Why**: Retrieval quality is a ranking/set-overlap metric, not something an LLM should judge, so a plain script is the right, lightest tool. Generation groundedness (does the rationale invent skills not present in the source data) is exactly what a model-graded eval framework is for, and OpenAI Evals is a genuinely recognized name, checkable and defensible, not a stretch claim, as long as it's actually wired up and run.
**Constraint**: OpenAI Evals framework itself is free (MIT license), but historically defaults to calling OpenAI's paid API for model-graded evals. Using its Completion Function Protocol to point at Groq instead keeps this component free too. It is not a clean PyPI package; install via `pip install git+https://github.com/openai/evals.git`.

---

### D7 — Frontend: React + TypeScript
**Decision**: Use React with TypeScript (`.tsx`), not plain JavaScript.
**Why**: TypeScript and React are commonly paired; TypeScript adds a genuinely new, real keyword while building directly on React, which is already a confirmed skill. Not a replacement for React, a language layer on top of it.

---

### D8 — RESOLVED: UI/UX tooling, two skills, divided by concern
**Issue (as originally logged)**: the user named "UI/UX Pro Max skill" for this project's UI work, which conflicted with a previously stated preference to avoid it and use Vercel's Web Design Guidelines stacked with the Emil Kowalski skill instead.
**Resolution**: the standing preference wins. The conflict existed because neither tool was actually installed, so the choice was theoretical. It is now settled with the tooling in place.
**Decision**: use exactly two skills, divided so their guidance cannot overlap.
1. `emil-design-eng`, global at `~/.config/opencode/skills-src/emil-kowalsiki-skills-main/skills/emil-design-eng`, owns the craft layer only: easing curves, durations, press feedback, stagger, `prefers-reduced-motion`, and hover gated behind `(hover: hover) and (pointer: fine)`.
2. `impeccable`, global at `~/.config/opencode/skills/impeccable`, owns structure and verification: mode selection, information architecture, layout, hierarchy, accessibility, edge and error states, plus the objective `impeccable detect` scan.
**Mode**: Operate. The visitor completes a task, so scanability, consistency, and the real usage scene outrank expression. Impeccable's own Operate definition is the reason restraint is correct here rather than a personal preference, and it is why `bolder`, `overdrive`, `delight`, `colorize`, and `quieter` are deliberately unused on this project.
**Workflow order**: `impeccable context` once per session, then `init` to write PRODUCT.md, then `new-work` for the visual world, then `shape` before any code, then `craft-floor.md` immediately before the first UI edit, then build, then `detect` plus `critique` and `audit`, then `polish`.
**Rejected**: UI/UX Pro Max. Not installed and not needed; Impeccable plus `emil-design-eng` cover the same ground with an objective detector.
**Parked, not installed**: `ui-ux-pro-max` and `taste-skill` repositories were downloaded but left outside the scanned skills root at `~/.config/opencode/skills-src/`, so they are not loaded. `taste-skill` was rejected on fit: its own SKILL.md scopes it to "landing pages, portfolios, and redesigns. Not dashboards, not data tables," which is the opposite of this surface. `ui-ux-pro-max` was left available in case concrete palette, font, or chart values turn out to be needed.
**Not used**: Impeccable `hooks`. Installed with `--no-hooks`, because opencode implements hooks as plugins and hard-fails on unrecognised config keys; the detector is run explicitly instead.

---

### D9: Groq generation model: openai/gpt-oss-120b
**Decision**: Use `openai/gpt-oss-120b` as the `GROQ_MODEL` for rationale generation, instead of the `llama-3.3-70b-versatile` example written in TRD.md when this project was planned.
**Why**: At build time, a real call with `llama-3.3-70b-versatile` returned 404 `model_not_found` on the Groq free tier. Groq's `/openai/v1/models` endpoint listed 11 models available to the key; `openai/gpt-oss-120b` is the largest general-purpose chat model among them. This stays within D2: still Groq, still the OpenAI-compatible endpoint, still free.
**Alternatives considered**: `qwen/qwen3.8-27b` and `openai/gpt-oss-20b` (available, smaller). Not usable: `whisper-*` (speech-to-text), `meta-llama/llama-prompt-guard-*` (classifiers), `canopylabs/orpheus-*` (speech synthesis), `allam-2-7b` (Arabic-focused).

---

### D10: Evals install: --no-deps plus a minimal dependency set
**Decision**: Install the OpenAI Evals framework with `pip install --no-deps git+https://github.com/openai/evals.git`, and list the seven packages its import path actually needs (`blobfile`, `dacite`, `beartype`, `backoff`, `lz4`, `tiktoken`, `zstandard`) in `requirements.txt`, instead of letting pip resolve the framework's full declared dependency tree.
**Why**: The full resolve was attempted first, as D6 documents, and pip spent over ten minutes backtracking through a very large declared tree (google-api-core and similar) without converging. Installed with `--no-deps`, `import evals` plus this project's eval path (Eval base class, RunSpec, DummyRecorder, Groq completion function) works with just those seven packages; verified by running `python eval_generation.py` end to end. Components outside that path (the evals CLI, YAML eval configs, its test suite) stay uninstalled by design.
**Scope**: Install mechanics only. The decision to evaluate with Evals wired to Groq (D6) is unchanged.

---

### D11: Dependency pinning, and the fastapi/starlette break
**Decision**: Pin every dependency in `requirements.txt` to an exact version, including an explicit `starlette` pin below 1.0.
**Why**: `requirements.txt` was fully unpinned, so a plain reinstall resolved fastapi to 0.142.2 alongside starlette 1.7.0, and the app stopped importing at all: `TypeError: Router.__init__() got an unexpected keyword argument 'on_startup'`. This is an upstream incompatibility, not a code defect. fastapi 0.142.2 declares `starlette>=0.46.0` with no upper bound, and starlette 1.0 removed the `on_startup`/`on_shutdown` keyword arguments from `Router.__init__`, which fastapi still passes. Unpinned dependencies made a reinstall silently capable of breaking a working project, and Phase 4 deployment would have hit the same failure on Render.
**Verified fix**: starlette 0.52.1 satisfies fastapi's `>=0.46.0` floor and predates the removal. With it pinned, `GET /health`, `GET /jobs`, `GET /candidates`, the 404 path, `top_k` bounds validation (422), and a real `POST /match/job_001?top_k=2` against live Pinecone and Groq all pass.
**Note on environments**: two Python installations are on this machine, and bare `pip` resolves to a different one than `python -m pip`. Always use `python -m pip` so installs land in the interpreter that runs the app.
**Scope**: Install mechanics and reproducibility only. No change to the stack chosen in TRD.md section 2.

---

### D12: CORS allowlist for the browser frontend
**Decision**: Add `CORSMiddleware` to the FastAPI app with an explicit, environment-driven origin allowlist read from `CORS_ORIGINS` (comma-separated, defaulting to the Vite dev server origins `http://localhost:5173` and `http://127.0.0.1:5173`).
**Why**: Phase 3 puts a browser UI in front of this API. A page served from one origin calling an API on another is blocked by the browser's same-origin policy, so without CORS the frontend cannot call any endpoint at all and FR6 ("a UI that lets a non-technical visitor pick a job and view results without touching the API") is unsatisfiable. The allowlist is explicit rather than `allow_origins=["*"]` because TRD.md section 6 requires the deployed frontend to point at the deployed backend via a build-time environment variable, which means the allowed origin differs per deployment and must be pinnable.
**Credentials**: `allow_credentials=False`. D4 excludes authentication entirely, so there are no cookies or auth headers to permit, and omitting it keeps wildcard usage legitimate if the allowlist is ever relaxed.
**Methods and headers**: `GET`, `POST`, `OPTIONS`, and `Content-Type`. `/match/{job_id}` is a POST, so a `fetch` that sets `Content-Type: application/json` triggers a preflight the server must answer; `OPTIONS` is permitted so that preflight is handled.
**Separate loader**: `get_cors_origins()` in `src/config.py` is deliberately independent of `get_settings()`. Calling `get_settings()` at import time would raise `ConfigError` whenever Pinecone or Groq credentials are absent, which would make `api.main` unimportable for local frontend work and would block reading the OpenAPI schema without live keys.
**Verified**: simple GET from an allowed origin returns the echoed `access-control-allow-origin`; a disallowed origin returns no such header; preflight from an allowed origin returns 200 with `GET, POST, OPTIONS` and `Content-Type`; preflight from a disallowed origin returns 400; a request with no `Origin` header (server-to-server or curl) is unaffected. Overriding `CORS_ORIGINS` changes the allowlist, confirming it is not hardcoded.
**Scope**: Browser access control only. No authentication, rate limiting, or origin-authentication scheme, per D4.

---

### D13: Retrieve the query vector from Pinecone instead of embedding in-process
**Decision**: `match_job` fetches the job's query vector from the existing `"jobs"` namespace by id, rather than loading `sentence-transformers` and encoding `job.summary` inside the request. Embeddings remain `all-MiniLM-L6-v2` at 384 dimensions and are still created by `src/ingest.py`; only the request path changes. This supersedes the runtime-embedding step shown in TRD.md section 1.
**Why**: Render's free web service tier provides 512 MB of RAM, and the application does not fit in it. Measured on this machine with `measure_memory.py`, walking the real import path: 14.3 MB baseline, 44.0 MB after `fastapi`, 67.8 MB after `pinecone` and `openai`, 481.4 MB after importing `sentence_transformers` (PyTorch alone accounts for roughly 414 MB of that), 482.5 MB after importing `api.main`, and 593.2 MB once `all-MiniLM-L6-v2` is loaded. The service would be OOM-killed rather than merely slowed, and it would fail on `/match`, which is the one endpoint that matters.
**Why this is cheap here**: the job corpus is 25 fixed synthetic records, and `src/ingest.py` already upserts every job vector into the `"jobs"` namespace per BACKEND_SCHEMA.md section 2. Retrieving that vector costs one Pinecone read and keeps Pinecone as the single source of truth, so there is no second copy of the data to keep in sync and no new artifact to maintain.
**Verified equivalence**: the stored vector for `job_001` and a fresh in-process encode of the same summary agree to a maximum absolute difference of 3.03e-09, cosine 0.99999998. Retrieval is therefore unchanged, the existing `eval_retrieval_report.json` result of 0.824 average precision@5 remains truthful, and no re-ingest is required.
**Alternatives considered**: Render's `1c-2g` compute plan at $25/month supplies 2 GB and would also remove the free-tier spin-down, but it breaks the zero-cost goal in PRD.md section 4 and NFR1. Render's $7/month `0.5c-512mb` plan was rejected because it also provides only 512 MB and solves nothing. Switching the embedding runtime to ONNX was rejected because ONNX and PyTorch can produce slightly different values for the same text, which would invalidate the stored index and both evaluation reports. Making the `sentence_transformers` import lazy was rejected because it only defers the failure: `/health`, `/jobs`, and `/candidates` would survive while the first `/match` still exceeded the limit. Lowering `TOP_K` was rejected because the memory is the resident model, not the request volume.
**Trade-off accepted**: the API can only match the 25 job ids present in the index. It cannot rank an arbitrary new job string, because doing so would require embedding it, which is exactly what this decision removes. Acceptable for a fixed synthetic corpus and a demo; it would need revisiting if the project ever ingested live job postings.
**Scope**: Retrieval step only. Generation is unchanged, embeddings are still local and free per D3, and D1 and D5 are unaffected (still Render, still no Docker).
