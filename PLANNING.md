# PLANNING.md — Talent Match RAG Implementation Plan

Source of truth for build progress. This is a from-scratch build; there is no
prior MVP code to modify. Update checkboxes as items complete. Do not mark an
item done until it has been verified running, not just written.

## Phase 0 — Scaffolding

- [x] Create project structure: `data/`, `src/`, `api/`
- [x] Write `data/generate_synthetic_data.py`: plain random sampling from
      fixed skill/title/city lists, no external tool or API needed
- [x] Generate `candidates.json` (40 records) and `jobs.json` (25 records)

## Phase 1 — Core pipeline

- [x] `src/config.py`: environment-driven settings for `PINECONE_API_KEY`,
      `PINECONE_INDEX_NAME`, `GROQ_API_KEY`, `GROQ_MODEL`, `EMBEDDING_MODEL`,
      `TOP_K`
- [x] `src/ingest.py`: embed candidate and job summaries locally with
      sentence-transformers (`all-MiniLM-L6-v2`), upsert into a Pinecone
      serverless index (384-dim, cosine metric), two namespaces:
      `candidates` and `jobs`
- [x] `src/match.py`: retrieval (Pinecone query for top-k candidates given a
      job) plus generation (Groq, OpenAI-compatible client, grounded
      rationale under explicit guardrails against inventing skills)
- [x] `api/main.py`: FastAPI app with `/health`, `/jobs`, `/candidates`,
      `/match/{job_id}`, per BACKEND_SCHEMA.md
- [x] Smoke test: imports, `/health`, `/jobs`, `/candidates`, 404 handling
- [x] Run one real end-to-end `/match/{job_id}` call with real Pinecone and
      Groq keys and confirm sensible output
- [x] **Gate**: nothing in Phase 2 starts until this end-to-end call is
      verified working with real keys, not mocked

## Phase 2 — Evaluation

- [x] `eval_retrieval.py`: skill-overlap baseline, precision@5 comparison
      against Pinecone's actual retrieval, per BACKEND_SCHEMA.md report format
- [x] `eval_generation.py`: custom OpenAI Evals eval class, completion
      function wired to Groq, checks generated rationales for invented
      skills or claims not present in the source candidate text
- [x] Add both eval reports and a short explanation of methodology to
      README.md
- [x] **Gate**: both eval scripts must produce a real report from a real run
      before being referenced anywhere as "done"

## Phase 3 — Frontend

- [ ] Scaffold React + TypeScript app
- [ ] Job picker (dropdown, populated from `/jobs`)
- [ ] "Find Matches" action calling `/match/{job_id}`
- [ ] Result cards: candidate id, similarity score, rationale
- [ ] Apply UI/UX direction per DECISIONS.md D8 (pending resolution before
      this phase starts)

## Phase 4 — Deployment

- [ ] Deploy backend to Render (free web service tier)
- [ ] Deploy frontend to Render static site or Cloudflare Pages
- [ ] Point frontend at deployed backend URL
- [ ] Final smoke test against live URLs
- [ ] Confirm live link works from a fresh browser session with no local
      setup

## Deferred (not in current scope)

- Dockerfile
- CI pipeline
- Hybrid retrieval / reranking
- Labeled precision@k test set (currently using skill-overlap proxy only)

## How to use this file (for the coding agent)

- Read PRD.md, TRD.md, and BACKEND_SCHEMA.md before starting any phase.
- Check off items only after they run successfully, not after the code is
  written.
- If a technical decision changes from what TRD.md or DECISIONS.md says,
  update DECISIONS.md first, then proceed. Do not silently diverge from the
  documented plan.
- Do not claim a phase is complete in any README or resume-facing text until
  its gate condition above is met.
