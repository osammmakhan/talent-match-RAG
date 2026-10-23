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
      `/match/{job_id}`, per docs/BACKEND_SCHEMA.md
- [x] Smoke test: imports, `/health`, `/jobs`, `/candidates`, 404 handling
- [x] Run one real end-to-end `/match/{job_id}` call with real Pinecone and
      Groq keys and confirm sensible output
- [x] **Gate**: nothing in Phase 2 starts until this end-to-end call is
      verified working with real keys, not mocked

## Phase 2 — Evaluation

- [x] `evals/retrieval.py`: skill-overlap baseline, precision@5 comparison
      against Pinecone's actual retrieval, per docs/BACKEND_SCHEMA.md report format
- [x] `evals/generation.py`: custom OpenAI Evals eval class, completion
      function wired to Groq, checks generated rationales for invented
      skills or claims not present in the source candidate text
- [x] Add both eval reports and a short explanation of methodology to
      README.md
- [x] **Gate**: both eval scripts must produce a real report from a real run
      before being referenced anywhere as "done"

## Phase 3 — Frontend

- [x] Backend CORS allowlist so a browser frontend can call the API
      (env-driven via `CORS_ORIGINS`, DECISIONS.md D12)
- [x] Scaffold React + TypeScript app (Vite, `frontend/`)
- [x] Job picker (dropdown, populated from `/jobs`)
- [x] "Find Matches" action calling `/match/{job_id}`
- [x] Result cards: candidate id, similarity score, rationale, plus an
      expandable candidate summary
- [x] Distinguish "searching" from "server waking up" in the loading state,
      with a live elapsed-seconds readout
- [x] Partial-result handling: one failed rationale degrades a single record
      rather than failing the response (DECISIONS.md D15, D16), verified by
      injecting a failure and by intercepting the response in a browser
- [x] Loading, empty, and error states (network, 404, 500, timeout), verified
      by capture
- [x] Apply UI/UX direction per DECISIONS.md D8 (`emil-design-eng` for craft,
      `impeccable` for structure and audit)
- [x] Replace the datasheet surface with the Stitch design and rebuild it in
      React (DECISIONS.md D17). Palette, layout, typography and motion sections
      of docs/DESIGN.md rewritten from the built surface; the two `impeccable detect`
      false positives recorded in an external review were measured against the
      datasheet, so they are reopened rather than carried over
- [x] Verified on the built surface: 32 text pairs measured from rendered
      pixels with 0 failures; zero horizontal overflow at 1280px and 390px in
      the initial and results states; 8 tab stops in document order with no
      positive tabindex; loading, empty, error and partial states each
      captured, the partial case by nulling two rationales out of a live
      response; zero console or page errors in any state
- [x] Finish review round 1 on the new surface. Run as two isolated
      assessments per `reference/critique.md`: a design review and a detector
      pass, neither seeing the other. Found and fixed one P0 that the rebuild
      introduced (a failed `/candidates` silently stripped every profile detail
      off every card and printed a corpus total derived from the request
      parameter), one P2 accessibility defect (the results region had no
      accessible name in the empty, loading and error states because its
      heading only existed once results rendered), and one inherited side-accent
      bar. Removed nine unused tokens and a per-job id helper
- [x] Finish review round 2 on the new surface. Fixed one P0 the round-1 work
      left behind (changing the job picker re-scored the previous results
      against the new posting's skills, printing a measured comparison between
      two documents nobody had searched together), a dead "Try again" that
      issued no request because no job was selected, and a layout bug where the
      column lived on `body`, whose only child is `#root`, so the page stopped
      161px short of the viewport and left a band under the footer
- [x] Finish review round 3. Fixed one P1 (cards claimed a profile load had
      failed while the load was still in flight, then silently rewrote
      themselves when it landed), a reduced-motion setting that left the record
      stagger in force so later cards sat invisible for up to 160ms, an 18px
      repository link on the smallest viewport, and a timeout title that said
      "Still waiting" after the request had already given up
- [x] Finish review round 4. Fixed a regression the round-3 pass introduced
      (removing the nested stack left the five loading skeletons with 0px gaps,
      so they fused into one block), a job select that read "No jobs loaded"
      while the job list was still in flight, a loading message stranded below
      the skeletons instead of in the same notice card as the search wait, an
      unannounced silent rewrite when profile details landed late, "Top 1
      matches", 10px tick glyphs against the file's own 11px floor, a duplicated
      comment in tokens.css, and two docs/DESIGN.md statements describing copy and a
      marker the build no longer renders
- [x] Contrast verified against the WCAG AA target for every text pair
- [x] Finish review round 1 returned `fix` with 22 findings; all material ones
      addressed, including three that were false claims in the interface copy
- [x] Finish review round 2 (verdict on the fixes) returned `fix` with 1
      unresolved, 1 partial, 2 new problems and 6 false statements in
      docs/DESIGN.md; all addressed and verified by measurement
- [x] Finish review round 3 returned `fix`: found two further real AA failures
      of the same class (`.result-count` and `.footnote` using `--muted` on the
      ground at 4.31:1), a `--control` border at 2.79:1 on the ground, a
      regression where a 15s profile-lookup budget stripped profiles off the
      cold-start path, and a focus capture that never held keyboard focus. All
      addressed; the full contrast audit now passes every pair
- [x] `docs/DESIGN.md` and its `.impeccable/design.json` sidecar written;
      `impeccable doctor` reports only `config-build-path-unset`, which its own
      guidance says to leave unset when no image generation tool exists
- [x] Two `impeccable detect` findings remain and are recorded as false
      positives with measurements, not silently ignored

## Phase 4 — Deployment

- [x] Confirm the app fits Render's free 512 MB tier: measured 73.7 MB on the
      request path after DECISIONS.md D13 removed the in-process embedding
      call. The dependency split keeps PyTorch off the web service, and
      D13's ban on request-path embeddings is enforced in code review
- [x] Confirm the embedding model is not needed at request time, so the
      ephemeral-filesystem model re-download problem no longer applies to the
      API (it applies only if ingest is ever run on Render)
- [x] Deploy backend to Render (free web service tier) at
      https://talent-match-rag-api.onrender.com. Build command
      `pip install -r requirements.txt`; start command
      `uvicorn api.main:app --host 0.0.0.0 --port $PORT`.
- [x] Deploy frontend to Render static site at
      https://talent-match-rag.onrender.com. Build command
      `cd frontend && npm install && npm run build`, which needs the `cd`
      because no `package.json` exists at the repo root; publish directory
      `frontend/dist`, which is relative to the root and takes no `cd`.
- [x] Set `CORS_ORIGINS` on the backend to the deployed frontend origin.
      Verified live: the allowed origin returns `access-control-allow-origin`
      and `vary: Origin`, while a foreign origin returns neither. The value
      must carry no trailing slash, because browsers send scheme and host
      only; the first saved value had one and matched nothing.
- [x] Point frontend at deployed backend URL through `VITE_API_BASE_URL`,
      which Vite bakes in at build time. Verified in the deployed bundle: it
      contains the API host and not the `localhost:8000` fallback.
- [x] Handle Render cold starts in the UI (free tier sleeps after 15 minutes
      idle, roughly one minute to wake), since NFR3 will otherwise appear to
      fail on the first request after idle. Measured live after a 16 minute
      idle period: wake request 32.96s, immediate retry 0.20s, `/match`
      4.18s returning 200. The frontend allows 90s for every call
      (`frontend/src/api.ts:19`), so the slow first request presents as a
      wait rather than an error.
- [x] Final smoke test against live URLs: health 200, jobs 25, candidates 40,
      `/match` 200 with 5 matches and a grounded rationale, 404 for an unknown
      route, 404 for an unknown job id, 422 for `top_k=0`. The first run found
      `POST /match` failing with an httpx `proxies` error that only appeared
      on a clean install; fixed by the pin in D19 and re-verified after
      redeploy.
- [x] Confirm live link works from a fresh browser session with no local
      setup: headless Chrome loaded the deployed site with no local process
      running, fetched the job list from the deployed API, and rendered the
      picker and job detail.

## Deferred (not in current scope)

- Dockerfile
- CI pipeline
- Hybrid retrieval / reranking
- Labeled precision@k test set (currently using skill-overlap proxy only)

## How to use this file (for the coding agent)

- Read docs/PRD.md, docs/TRD.md, and docs/BACKEND_SCHEMA.md before starting any phase.
- Check off items only after they run successfully, not after the code is
  written.
- If a technical decision changes from what docs/TRD.md or DECISIONS.md says,
  update DECISIONS.md first, then proceed. Do not silently diverge from the
  documented plan.
- Do not claim a phase is complete in any README or resume-facing text until
  its gate condition above is met.
