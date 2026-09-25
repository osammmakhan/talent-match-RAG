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

### D8 — OPEN: UI/UX tooling conflict, unresolved
**Issue**: The user named "UI/UX Pro Max skill" as a tool to use for this project. Prior stated preference (recorded before this project started) explicitly says to avoid UI/UX Pro Max and to use Vercel's Web Design Guidelines stacked with the Emil Kowalski skill instead, for a restrained, opinionated result.
**Current status**: Unresolved. AGENTS.md reflects the standing preference (Vercel guidelines + Emil Kowalski) rather than the newly named tool, pending explicit confirmation from the user on which one to actually use.
**Action needed**: User to confirm whether this is an intentional change from the standing preference or an inconsistency to correct.

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
