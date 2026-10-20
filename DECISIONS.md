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
**Decision**: Use `openai/gpt-oss-120b` as the `GROQ_MODEL` for rationale generation, instead of the `llama-3.3-70b-versatile` example written in docs/TRD.md when this project was planned.
**Why**: At build time, a real call with `llama-3.3-70b-versatile` returned 404 `model_not_found` on the Groq free tier. Groq's `/openai/v1/models` endpoint listed 11 models available to the key; `openai/gpt-oss-120b` is the largest general-purpose chat model among them. This stays within D2: still Groq, still the OpenAI-compatible endpoint, still free.
**Alternatives considered**: `qwen/qwen3.8-27b` and `openai/gpt-oss-20b` (available, smaller). Not usable: `whisper-*` (speech-to-text), `meta-llama/llama-prompt-guard-*` (classifiers), `canopylabs/orpheus-*` (speech synthesis), `allam-2-7b` (Arabic-focused).

---

### D10: Evals install: --no-deps plus a minimal dependency set
**Decision**: Install the OpenAI Evals framework with `pip install --no-deps git+https://github.com/openai/evals.git`, and list the seven packages its import path actually needs (`blobfile`, `dacite`, `beartype`, `backoff`, `lz4`, `tiktoken`, `zstandard`) in `requirements.txt`, instead of letting pip resolve the framework's full declared dependency tree.
**Why**: The full resolve was attempted first, as D6 documents, and pip spent over ten minutes backtracking through a very large declared tree (google-api-core and similar) without converging. Installed with `--no-deps`, `import evals` plus this project's eval path (Eval base class, RunSpec, DummyRecorder, Groq completion function) works with just those seven packages; verified by running `python evals/generation.py` end to end. Components outside that path (the evals CLI, YAML eval configs, its test suite) stay uninstalled by design.
**Scope**: Install mechanics only. The decision to evaluate with Evals wired to Groq (D6) is unchanged.

---

### D11: Dependency pinning, and the fastapi/starlette break
**Decision**: Pin every dependency in `requirements.txt` to an exact version, including an explicit `starlette` pin below 1.0.
**Why**: `requirements.txt` was fully unpinned, so a plain reinstall resolved fastapi to 0.142.2 alongside starlette 1.7.0, and the app stopped importing at all: `TypeError: Router.__init__() got an unexpected keyword argument 'on_startup'`. This is an upstream incompatibility, not a code defect. fastapi 0.142.2 declares `starlette>=0.46.0` with no upper bound, and starlette 1.0 removed the `on_startup`/`on_shutdown` keyword arguments from `Router.__init__`, which fastapi still passes. Unpinned dependencies made a reinstall silently capable of breaking a working project, and Phase 4 deployment would have hit the same failure on Render.
**Verified fix**: starlette 0.52.1 satisfies fastapi's `>=0.46.0` floor and predates the removal. With it pinned, `GET /health`, `GET /jobs`, `GET /candidates`, the 404 path, `top_k` bounds validation (422), and a real `POST /match/job_001?top_k=2` against live Pinecone and Groq all pass.
**Note on environments**: two Python installations are on this machine, and bare `pip` resolves to a different one than `python -m pip`. Always use `python -m pip` so installs land in the interpreter that runs the app.
**Scope**: Install mechanics and reproducibility only. No change to the stack chosen in docs/TRD.md section 2.

---

### D12: CORS allowlist for the browser frontend
**Decision**: Add `CORSMiddleware` to the FastAPI app with an explicit, environment-driven origin allowlist read from `CORS_ORIGINS` (comma-separated, defaulting to the Vite dev server origins `http://localhost:5173` and `http://127.0.0.1:5173`).
**Why**: Phase 3 puts a browser UI in front of this API. A page served from one origin calling an API on another is blocked by the browser's same-origin policy, so without CORS the frontend cannot call any endpoint at all and FR6 ("a UI that lets a non-technical visitor pick a job and view results without touching the API") is unsatisfiable. The allowlist is explicit rather than `allow_origins=["*"]` because docs/TRD.md section 6 requires the deployed frontend to point at the deployed backend via a build-time environment variable, which means the allowed origin differs per deployment and must be pinnable.
**Credentials**: `allow_credentials=False`. D4 excludes authentication entirely, so there are no cookies or auth headers to permit, and omitting it keeps wildcard usage legitimate if the allowlist is ever relaxed.
**Methods and headers**: `GET`, `POST`, `OPTIONS`, and `Content-Type`. `/match/{job_id}` is a POST, so a `fetch` that sets `Content-Type: application/json` triggers a preflight the server must answer; `OPTIONS` is permitted so that preflight is handled.
**Separate loader**: `get_cors_origins()` in `src/config.py` is deliberately independent of `get_settings()`. Calling `get_settings()` at import time would raise `ConfigError` whenever Pinecone or Groq credentials are absent, which would make `api.main` unimportable for local frontend work and would block reading the OpenAPI schema without live keys.
**Verified**: simple GET from an allowed origin returns the echoed `access-control-allow-origin`; a disallowed origin returns no such header; preflight from an allowed origin returns 200 with `GET, POST, OPTIONS` and `Content-Type`; preflight from a disallowed origin returns 400; a request with no `Origin` header (server-to-server or curl) is unaffected. Overriding `CORS_ORIGINS` changes the allowlist, confirming it is not hardcoded.
**Scope**: Browser access control only. No authentication, rate limiting, or origin-authentication scheme, per D4.

---

### D13: Retrieve the query vector from Pinecone instead of embedding in-process
**Decision**: `match_job` fetches the job's query vector from the existing `"jobs"` namespace by id, rather than loading `sentence-transformers` and encoding `job.summary` inside the request. Embeddings remain `all-MiniLM-L6-v2` at 384 dimensions and are still created by `src/ingest.py`; only the request path changes. This supersedes the runtime-embedding step shown in docs/TRD.md section 1.
**Why**: Render's free web service tier provides 512 MB of RAM, and the application does not fit in it. Measured on this machine, walking the real import path: 14.3 MB baseline, 44.0 MB after `fastapi`, 67.8 MB after `pinecone` and `openai`, 481.4 MB after importing `sentence_transformers` (PyTorch alone accounts for roughly 414 MB of that), 482.5 MB after importing `api.main`, and 593.2 MB once `all-MiniLM-L6-v2` is loaded. The service would be OOM-killed rather than merely slowed, and it would fail on `/match`, which is the one endpoint that matters.
**Why this is cheap here**: the job corpus is 25 fixed synthetic records, and `src/ingest.py` already upserts every job vector into the `"jobs"` namespace per docs/BACKEND_SCHEMA.md section 2. Retrieving that vector costs one Pinecone read and keeps Pinecone as the single source of truth, so there is no second copy of the data to keep in sync and no new artifact to maintain.
**Verified equivalence**: the stored vector for `job_001` and a fresh in-process encode of the same summary agree to a maximum absolute difference of 3.03e-09, cosine 0.99999998. Retrieval is therefore unchanged, the existing `evals/reports/retrieval.json` result of 0.824 average precision@5 remains truthful, and no re-ingest is required.
**Alternatives considered**: Render's `1c-2g` compute plan at $25/month supplies 2 GB and would also remove the free-tier spin-down, but it breaks the zero-cost goal in docs/PRD.md section 4 and NFR1. Render's $7/month `0.5c-512mb` plan was rejected because it also provides only 512 MB and solves nothing. Switching the embedding runtime to ONNX was rejected because ONNX and PyTorch can produce slightly different values for the same text, which would invalidate the stored index and both evaluation reports. Making the `sentence_transformers` import lazy was rejected because it only defers the failure: `/health`, `/jobs`, and `/candidates` would survive while the first `/match` still exceeded the limit. Lowering `TOP_K` was rejected because the memory is the resident model, not the request volume.
**Trade-off accepted**: the API can only match the 25 job ids present in the index. It cannot rank an arbitrary new job string, because doing so would require embedding it, which is exactly what this decision removes. Acceptable for a fixed synthetic corpus and a demo; it would need revisiting if the project ever ingested live job postings.
**Scope**: Retrieval step only. Generation is unchanged, embeddings are still local and free per D3, and D1 and D5 are unaffected (still Render, still no Docker).

---

### D14: Split runtime and local-only dependencies
**Decision**: `requirements.txt` now contains only what the deployed API needs. `sentence-transformers`, the OpenAI Evals framework and its dependencies, and `httpx` move to a new `requirements-dev.txt` that includes the runtime file.
**Why**: D13 established that the request path never loads the embedding model. Walking that import path measures 73.7 MB. Shipping `sentence-transformers` to the web service anyway would pull PyTorch, roughly 2 GB of wheels, on every build, for code that never runs there. Render's Hobby workspace includes 500 build minutes per month, and the frontend depends on the backend building often enough that wasting minutes on a two-gigabyte download is a real cost rather than a tidiness concern.
**How the runtime set was derived, not assumed**: the actual import graph was walked from `api/main.py` at build time. It resolves to `src/config.py`, `src/data.py`, `src/match.py` and `src/schemas.py`, with the third-party set `fastapi`, `pydantic`, `python-dotenv`, `pinecone` and `openai`. No heavy dependency is reachable, which is the machine-checked form of the claim D13 makes.
**Effect on local setup**: `python -m src.ingest` still needs the embedding model, so anyone working on data or evaluation installs `requirements-dev.txt`. AGENTS.md and README are updated to say which file to install for which task.
**Not verified**: this was not tested against a clean virtualenv, because that would mean reinstalling PyTorch locally. The claim rests on the static import closure and the runtime memory measurement, both recorded above.
**Scope**: Dependency packaging only. No change to the stack in docs/TRD.md section 2, and D1, D3 and D13 are unaffected.

---

### D15: One Groq call per candidate, issued in parallel
**Decision**: `match_job` issues five independent generation calls concurrently, one per retrieved candidate, via `ThreadPoolExecutor` with a worker count capped at `top_k`. This is the design in the initial commit `f928891` and it was previously undocumented. Logging it here records the shape and its consequences, not a rationale, because no record of the original reasoning exists and inventing one would be worse than the gap.
**What the documentation actually said**: docs/TRD.md states only "a short grounded rationale per candidate" (docs/TRD.md:24) and is silent on mechanism, so this was never a divergence from a specified batched design. An external review claimed docs/TRD.md prescribed one batched call per job; that was incorrect, and the docs/TRD.md reference was verified before acting on it.
**Why per candidate rather than one batched call**: one rationale per call keeps each prompt small and its failure isolated to a single candidate, and it lets the calls run concurrently. A single batched call would be one request for all five, but then one malformed or truncated item in the batch risks the whole response, and parsing JSON that a language model emitted for five different candidates is fragile.
**Cost, and the reason D16 exists**: `executor.map` is lazy, and forcing it with `list()` re-raised on the first exception, discarding every successful result. One rate-limited candidate returned a 500 with zero results even though four rationales had generated. D16 fixes the failure handling; this entry records that the concurrency is why the blast radius existed.
**Scope**: Generation call shape only. Retrieval, generation and the API contract are otherwise unchanged.

---

### D16: A failed rationale degrades one record, not the response
**Decision**: `MatchResult.rationale` is `str | None`. A candidate whose generation fails is still returned, with its real similarity score and `rationale: null`. The frontend renders an explicit "Rationale unavailable" panel for that record and a quiet note above the results stating how many profiles are score-only. Failures are logged at warning level with the candidate id and job id.
**Why**: the similarity score is produced by Pinecone and is entirely unaffected by a generation failure. Retrieval already succeeded, so discarding a valid retrieval result because the prose step failed throws away a correct answer. It also contradicts the architecture, in which retrieval and generation are independent stages and so ought to fail independently.
**Why not a specific 429 instead**: an earlier position was all-or-nothing with a distinct error, on the reasoning that a shorter list is harder to trust. The flaw in that argument was "silently": the problem was never partial results, it was unannounced partial results. A record with a valid score and an explicitly absent rationale is an honest report of what a two-stage pipeline actually produced, and on a recruiter-facing surface a structured error reads as "broken" where four working results and one labelled gap reads as "mostly works". The degradation is therefore visible and neutral in styling, not styled as an error.
**Verified**: injecting a failure for one of five candidates returns five matches, four rationales, one `null`, with all five scores intact and no other record affected. Verified end to end in a browser by intercepting the response, which renders 5 records, 4 rationale panels, 1 unavailable panel and the partial note, with all 5 readings shown and no page errors.
**Not addressed**: eight SDK retries with backoff on a 429 can still outlast the frontend's 90-second timeout, in which case the visitor sees the waiting state rather than the partial result. Reducing the retry count or lowering the timeout is a tuning question left open; the fault tolerance is what makes the slow path survivable rather than fatal.
**Scope**: Failure handling for generation only. No change to the ranking method, the groundedness guarantee, or the retrieval stage.

---

### D17: Replace the datasheet surface with the Stitch design, and load webfonts
**Decision**: the match results surface is rebuilt to the design generated in Google Stitch and iterated against rendered screenshots: a sticky dark top bar, an intro card, a 12-column grid with a sticky job rail, and result cards carrying a rank badge, score, explanation and a skill breakdown. Inter and JetBrains Mono are loaded from Google Fonts. This supersedes the datasheet direction documented in the previous docs/DESIGN.md, and reverses that file's "system stacks only" typography rule.

**Why the surface changed**: the datasheet treated each result as a laboratory record: a rated specification, a 0-to-100 track beneath the reading, and one reserved red for annotation. It was internally consistent and passed its own review, but it was built to look like a measurement instrument rather than to let a visitor read five matches quickly. Four finish-review rounds were spent on it and each found real defects in the previous round's fixes, which is itself evidence that the surface had become hard to hold. The visitor's task is to compare five profiles, and the instrument framing worked against that.

**Why webfonts now**: the Stitch design's character depends on Inter and JetBrains Mono specifically. The earlier rule against webfonts was sound on its own terms, that a surface whose backend already makes visitors wait should not add a blocking request. It is being traded against design fidelity, and the trade is stated rather than hidden: roughly 180 KB of additional font data and a third-party request to fonts.googleapis.com. Self-hosting the two families would remove the third-party request and is the obvious next step if this direction holds.

**Why the emphasis inside the explanation is not reproduced**: the Stitch mockups bolded skill names inside the rationale. That markup was hand-authored in the mockup. Against model-written text it would have to be inferred, and any heuristic that bolds a skill name would also bold it inside a clause that denies it. "The candidate does not list Docker" would render with Docker emphasised, spotlighting the thing that is absent. On a surface whose entire claim is that its statements are checkable, that inversion is worse than flat prose, so the rationale is rendered plain. The rule and the reason are recorded in App.css.

**Why "Not listed" rather than "Missing"**: a job skill absent from a profile record means the record does not mention it, not that the person lacks it. The wording change is a correctness fix, not a tone preference.

**Verified**: typecheck, lint and build pass; 32 text pairs measured from rendered pixels at 1280px with 0 failures; zero horizontal overflow at 1280px and 390px in both the initial and results states; 8 tab stops in document order with no positive tabindex and a 2px focus ring on every one; loading, empty, error and partial states each captured and confirmed, the partial case by nulling two rationales out of a live response; zero console or page errors in any state. The score-caption collision at 390px was found by measurement and fixed.

**Scope**: Frontend presentation and user-visible strings only. No change to the `/match` contract, the generation prompt, the retrieval stage, the eval scripts, or any API field. The design work does not alter the groundedness result, because no model-written text was altered. The rationale copy the eval graded is exactly what the surface still renders. The committed score is 124 of 125; see D18 for why it is reported that way.

**Supersedes**: the design direction in the previous docs/DESIGN.md, and its system-fonts-only rule. The two `impeccable detect` false positives recorded in an external review were measured against the datasheet and do not carry over; they are reopened rather than carried forward.

**Known limitations**: there is still no automated test suite, deferred by decision. The Playwright checks that produced the measurements above are ad hoc and will not run in CI, so nothing prevents these tokens and strings from regressing.

---

### D18: Report the groundedness score as a single run, not as a fixed result
**Decision**: the groundedness score in the README is the score of one committed run, 124 of 125, presented as a snapshot with its variance stated. It is not described as a property the pipeline achieves. An earlier run of identical code scored 125 of 125; that earlier number was not restored once the discrepancy was found.

**Why this was not simply reverted to 125/125**: a rerun from a cleared checkpoint produced 124 of 125. The failure is genuine, not a grader artifact. The rationale for `cand_038` against `job_001` states the candidate "has over nine years of experience" where the source record says `years_experience: 9`. The grader is correct to reject an overstated figure. Restoring 125/125 would have meant deleting the evidence that the grader caught a real hallucination, which is the one behaviour this eval exists to demonstrate.

**Why the score varies at all**: generation runs at `temperature=0.2`, so each run writes new wording. A second full run produced 123 of 125 rationales that differed textually from the first, while retrieval returned the byte-identical candidate set both times. Retrieval is deterministic; generation is not. The score therefore fluctuates by a sample or two between runs on unchanged code, and quoting a single figure as though it were reproducible overstates what was measured.

**How a real regression is distinguished from sampling noise**: the baseline for this code sits in the high 120s. The signal this eval provides is a trend, not a threshold: if the prompt, the data, or the model changes in a way that breaks grounding, failures climb into double digits rather than moving by one. The separate negative control is what establishes that the grader discriminates at all, by confirming it accepts an honest rationale and rejects three tampered ones (`python evals/grounding_control.py`).

**Cost of this choice**: a reader comparing against a rerun may see 125 and conclude the committed number was wrong. That is the honest failure mode here. The alternative, pinning the reported figure to the best observed run, would make the number less informative, not more, because it would conceal the variance that makes the figure meaningful.

**Scope**: Documentation and reporting only. No change to the eval script, the grader, the generation prompt, the retrieval stage, or any API contract.

### D19: Pin httpx in the runtime requirements, not only in dev
**Decision**: `httpx==0.27.2` is pinned in `requirements.txt`, the set Render installs, and the duplicate pin was removed from `requirements-dev.txt`, which already includes it.

**Why it became necessary**: the first Render smoke test returned 500 on `POST /match/job_001` with `Pipeline failed: Client.__init__() got an unexpected keyword argument 'proxies'`, while `/health`, `/jobs`, and `/candidates` all returned 200. `openai` 1.42.0 passes `proxies=` to `httpx.Client` on every construction (`openai/_base_client.py:848`), and `httpx` 0.28.0 removed that keyword. The range declared by openai is `httpx<1,>=0.23.0`, which admits 0.28.1, so a plain install on a clean machine resolves to 0.28.1 and client construction raises.

**Why only /match failed**: `src/match.py:143` is the only place in the request path that constructs an `OpenAI` client. `/jobs` and `/candidates` read local JSON, and stored job vectors are fetched from Pinecone rather than embedded at request time (D13). The one endpoint that did build the client was the one that failed, so three green endpoints hid a completely broken pipeline.

**Why local development did not catch it**: `requirements-dev.txt` had carried `httpx==0.27.2` as a test-client pin since before the deployment, so every local environment was already on the version that still accepts `proxies`. The pin existed, just in the file the web service does not install. The code was correct on every machine except the one that mattered.

**Alternative considered**: upgrading `openai` to a release that does not pass `proxies` unconditionally. Rejected: D11 pins exact versions deliberately, and raising a pinned top-level dependency to work around a transitive one is a wider blast radius than pinning the transitive dependency itself. `httpx==0.27.2` also satisfies `pinecone` 10.0.0, which requires `httpx[http2]>=0.27,<1.0`.

**Scope**: dependency pinning only. No change to application code, the API contract, or the evals.
