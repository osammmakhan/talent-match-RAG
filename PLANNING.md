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

- [x] Backend CORS allowlist so a browser frontend can call the API
      (env-driven via `CORS_ORIGINS`, DECISIONS.md D12)
- [ ] Scaffold React + TypeScript app
- [ ] Job picker (dropdown, populated from `/jobs`)
- [ ] "Find Matches" action calling `/match/{job_id}`
- [ ] Result cards: candidate id, similarity score, rationale
- [ ] Distinguish "searching" from "server waking up" in the loading state.
      Render's free tier sleeps after 15 minutes idle and takes about a minute
      to wake, so a plain spinner on a blank panel reads as a broken page.
      Copy must stay honest about which of the two is happening, and the
      request needs a client-side timeout (NFR3)
- [ ] Loading, empty, and error states (404, 500, and offline)
- [ ] Apply UI/UX direction per DECISIONS.md D8 (`emil-design-eng` for craft,
      `impeccable` for structure and audit; D8 to be closed in DECISIONS.md)

## Phase 4 — Deployment

- [x] Confirm the app fits Render's free 512 MB tier: measured 73.7 MB on the
      request path after DECISIONS.md D13 removed the in-process embedding
      call; `python measure_memory.py` guards against regression
- [x] Confirm the embedding model is not needed at request time, so the
      ephemeral-filesystem model re-download problem no longer applies to the
      API (it applies only if ingest is ever run on Render)
- [ ] Deploy backend to Render (free web service tier)
- [ ] Deploy frontend to Render static site or Cloudflare Pages
- [ ] Set `CORS_ORIGINS` on the backend to the deployed frontend origin
- [ ] Point frontend at deployed backend URL
- [ ] Handle Render cold starts in the UI (free tier sleeps after 15 minutes
      idle, roughly one minute to wake), since NFR3 will otherwise appear to
      fail on the first request after idle
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
