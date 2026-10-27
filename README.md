# Talent Match RAG

[![Talent Match RAG Logo](/osammmakhan/talent-match-RAG/raw/main/frontend/public/favicon.svg)](/osammmakhan/talent-match-RAG/blob/main/frontend/public/favicon.svg)

A retrieval-augmented generation pipeline that matches synthetic job postings
to synthetic candidate profiles and explains each match in plain English, using
only facts present in the retrieved records.

[Live frontend](https://talent-match-rag.onrender.com) ·
[Live API](https://talent-match-rag-api.onrender.com) ·
[Repository](https://github.com/osammmakhan/talent-match-RAG)

![Screen recording of the live interface, with the ML Engineer job in Zurich selected and five ranked candidate matches shown, each carrying a match score out of 100, a short rationale, and a breakdown of the job's required skills the candidate has and is missing](docs/Talent%20Match%20RAG%20Demo%20GIF%2030%20FPS.gif)

**At a glance**

- **0.824** average precision@5, measured against a skill-overlap proxy rather
  than labeled ground truth
- **124 of 125** rationales passed the groundedness check, from a single
  committed run rather than a fixed property
- **3 of 3** tampered rationales rejected by the grader's negative control

---

## Contents

- [Overview](#overview)
- [Live demo](#live-demo)
- [Architecture](#architecture)
- [How it works](#how-it-works)
- [API reference](#api-reference)
- [Evaluation](#evaluation)
- [Getting started](#getting-started)
- [Frontend](#frontend)
- [Deployment](#deployment)
- [Project structure](#project-structure)
- [Tech stack](#tech-stack)
- [Design decisions](#design-decisions)
- [Known limitations](#known-limitations)
- [Data disclaimer](#data-disclaimer)
- [Documentation](#documentation)

---

## Overview

This project was built independently to understand and demonstrate the
mechanics of a RAG system end to end: embedding records, retrieving the
relevant subset by vector similarity, and generating an explanation that a
reader can check against the source data.

**What it does**

- Embeds and stores 25 jobs and 40 candidate profiles in a vector index
- Retrieves the closest candidates for any chosen job by cosine similarity
- Generates a per-candidate rationale that cites only the retrieved text
- Scores its own retrieval quality and the factual grounding of its own output
- Ships a browser interface for running a search without touching the API
- Runs entirely on free tiers, by design

The problem it models is a real one: given a job posting, which candidates are
actually worth a look, and why? A similarity score alone answers neither
question. The score says how close the wording is, not whether a person fits,
and a number on its own gives the reader nothing to act on. This pipeline
returns both: the ranked candidates and a short rationale for each, written
strictly from the retrieved candidate and job records.

The motivating problem came from a candidate-to-job matching workflow seen at
a previous company. Nothing from that company appears here: no real
candidates, no real job postings, no real data of any kind.

---

## Live demo

| | |
|---|---|
| Frontend | https://talent-match-rag.onrender.com |
| API | https://talent-match-rag-api.onrender.com |
| API docs (Swagger) | https://talent-match-rag-api.onrender.com/docs |

Both services run on Render's free tier. The backend sleeps after 15 minutes
of inactivity. Measured on the live deployment after a 16 minute idle period,
the wake request took 32.96 seconds; once warm, `/health` answers in 0.20
seconds and `/match` in about 4 seconds. Every request from the UI is allowed
90 seconds, so a cold start appears as a wait rather than an error.

---

## Architecture

```
data/jobs.json  data/candidates.json
        |
        v
sentence-transformers  all-MiniLM-L6-v2, 384 dimensions,
                       runs on your machine at ingest time, never on the API
        |
        v
Pinecone serverless index, cosine similarity, two namespaces:
  "jobs"        one vector per job, built from its summary
  "candidates"  one vector per candidate, built from its summary
        |
        v
Retrieval: fetch the chosen job's stored vector, query "candidates" with it,
take the top k
        |
        v
Prompt assembly: the retrieved candidate and job records only
        |
        v
Groq, OpenAI-compatible endpoint, model openai/gpt-oss-120b,
generates one short rationale per candidate under instructions to
reference only what the records contain
        |
        v
FastAPI returns similarity scores and rationales as JSON
        |
        v
React + TypeScript + Vite interface: job picker, ranked results, rationale text
```

Two properties of this design are deliberate:

**The embedding model never runs at request time.** Job vectors are computed
once during ingest and read back from Pinecone when a search runs. This keeps
PyTorch out of the deployed web service, holds its memory footprint at 73.7 MB
against a 512 MB limit, and avoids re-downloading a model onto Render's
ephemeral filesystem on every boot.

**Generation is downstream of retrieval.** The LLM never searches. It receives
the candidate and job text that retrieval already selected, which is what
makes a groundedness check possible: every claim can be compared against a
known input.

---

## How it works

### 1. Ingest

`python -m src.ingest` reads `data/jobs.json` and `data/candidates.json`,
embeds each `summary` field with `all-MiniLM-L6-v2`, and upserts the vectors
plus their flattened metadata into Pinecone. Skills are stored comma-joined
because Pinecone metadata does not carry nested arrays reliably; the API layer
splits them back into lists before responding.

### 2. Retrieval

A search fetches the chosen job's vector from the `jobs` namespace and uses it
to query the `candidates` namespace. This is an approximation of matching
against the job posting directly: the job's summary is what gets compared, so
the query reflects how the posting is worded rather than a structured
requirement list. Scores are cosine similarity, where 1.0 means identical
direction in the embedding space.

### 3. Generation

For each retrieved candidate, the pipeline builds a prompt containing the job
record and the candidate record, then asks Groq for a short rationale. The
instructions are explicit about the failure this pipeline exists to avoid:
reference only skills, tools, experience, and requirements that appear in
the supplied records, and assert nothing the records do not support.

Retrieval and generation are independent stages, and generation is scoped to
the individual candidate. Up to five rationales are generated in parallel
through a thread pool, each call allowed eight retries and a 60 second
timeout. If one candidate's generation fails, that candidate is returned with
`rationale: null` while the rest of the response is unaffected, so a valid
similarity score is never discarded because a downstream call failed
(`DECISIONS.md` D16).

---

## API reference

Base URL (production): `https://talent-match-rag-api.onrender.com`

### `GET /health`

```bash
curl https://talent-match-rag-api.onrender.com/health
```

```json
{ "status": "healthy" }
```

### `GET /jobs`

Returns all 25 job postings.

```json
{
  "id": "job_001",
  "title": "ML Engineer",
  "required_skills": ["PyTorch", "scikit-learn", "Docker", "Python"],
  "min_years_experience": 4,
  "location": "Zurich",
  "summary": "Join our Zurich team as a ML Engineer. You will work with PyTorch, scikit-learn, Docker, and Python and bring at least 4 years of experience."
}
```

### `GET /candidates`

Returns all 40 candidate profiles.

```json
{
  "id": "cand_001",
  "title": "AI Automation Engineer",
  "skills": ["Python", "Git", "RAG", "LangChain"],
  "years_experience": 11,
  "location": "Warsaw",
  "summary": "Experienced AI Automation Engineer (11 years) skilled in Python, Git, RAG, and LangChain. Located in Warsaw."
}
```

### `POST /match/{job_id}`

Runs retrieval and generation for one job.

| Parameter | Location | Required | Notes |
|---|---|---|---|
| `job_id` | path | yes | Must exist, otherwise `404` |
| `top_k` | query | no | Integer, 1 to 50. Defaults to `TOP_K`, which is 5 |

```bash
curl -X POST "https://talent-match-rag-api.onrender.com/match/job_001?top_k=2"
```

```json
{
  "job_id": "job_001",
  "job_title": "ML Engineer",
  "matches": [
    {
      "candidate_id": "cand_004",
      "similarity_score": 0.757098258,
      "rationale": "The candidate's profile shows strong alignment with the role, offering expertise in PyTorch, scikit-learn, and Python, which are core requirements."
    },
    {
      "candidate_id": "cand_013",
      "similarity_score": 0.736309111,
      "rationale": "..."
    }
  ]
}
```

**Error responses**

| Status | Condition | Body |
|---|---|---|
| `404` | Unknown `job_id` | `{"detail":"Unknown job_id: job_999"}` |
| `404` | Unknown route | `{"detail":"Not Found"}` |
| `422` | `top_k` outside 1 to 50 | `{"detail":[{"type":"greater_than_equal", ...}]}` |
| `500` | Retrieval or generation failure | `{"detail":"Pipeline failed: ..."}` |

`rationale` is nullable by design: retrieval can succeed while generation
fails, and the score is still worth returning in that case.

---

## Evaluation

Three scripts under `evals/`, each runnable on its own and each writing a JSON
report to `evals/reports/`. All reported figures come from real runs against
live Pinecone and Groq keys.

| Eval | Command | Result |
|---|---|---|
| Retrieval quality | `python evals/retrieval.py` | 0.824 average precision@5 |
| Generation groundedness | `python evals/generation.py` | 124 of 125 rationales passed |
| Grader negative control | `python evals/grounding_control.py` | 3 of 3 tampered rationales rejected |

### Retrieval: 0.824 average precision@5

For each of the 25 jobs, the "relevant" set is every candidate sharing at
least two of the job's required skills. That skill-overlap set is a proxy for
relevance, not labeled ground truth: a candidate outside it can still be a
legitimate match, so the number measures agreement with a simple definition
rather than correctness in any absolute sense. Pinecone's actual top-5 is
scored as the fraction falling inside that set, averaged over all jobs.

14 of 25 jobs scored 1.0. The lowest was 0.2. Per-job scores are in
`evals/reports/retrieval.json`.

### Generation groundedness: 124 of 125

Every rationale the pipeline generates (25 jobs, top 5 each) is graded against
the source candidate and job records by a custom eval class built on OpenAI's
open-source Evals framework, with a completion function that calls Groq rather
than OpenAI's paid API. A rationale passes only if every factual claim in it
appears in the source records; opinions and fit judgments are ignored.

The single failure in the committed run is a real overstatement, not a grader
quirk. The rationale for `cand_038` against `job_001` claims the candidate
"has over nine years of experience" where the record says
`years_experience: 9`.

**This is one run, not a fixed property.** Generation samples at
`temperature=0.2`, so a rerun produces new wording: a second full run
differed on 123 of 125 rationales while retrieval returned the identical
candidate set. Expect results in the high 120s; a drop into the 110s or below
indicates a real regression rather than sampling noise. The grader is itself
an LLM, so this measures what that grader can detect rather than proving
groundedness in the abstract.

### Grader negative control

A high pass rate proves nothing if the grader cannot fail. This script feeds
the grading step a rationale asserting a skill the candidate record does not
contain, three times over, and confirms each is rejected while an honest
rationale is still accepted. Current result: 3 of 3 caught.

### Eval rate limits and checkpointing

The Groq free tier allows 8000 tokens per minute, so the generation eval paces
itself: roughly 26 seconds between jobs during generation, and a sliding-window
token limiter during grading, where 125 grades take about 17 minutes. Output is
checkpointed to `evals/samples.json`, so an interrupted run resumes instead of
regenerating.

The API applies none of that pacing. It generates with up to five calls in
flight at once, so the default `top_k` of five is a single wave, and the whole
search completes in about four seconds warm, comfortably inside the 90 second
request budget.

---

## Getting started

### Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer
- A [Pinecone](https://www.pinecone.io/) account (free tier)
- A [Groq](https://groq.com/) API key (free tier)

### Backend

```bash
# what the deployed service installs
pip install -r requirements.txt

# additionally required for ingest, the evals, or local development
pip install -r requirements-dev.txt
pip install --no-deps git+https://github.com/openai/evals.git   # eval scripts only

cp .env.example .env
# then fill in PINECONE_API_KEY and GROQ_API_KEY

python data/generate_synthetic_data.py   # optional, the data is already committed
python -m src.ingest                     # embed records and populate Pinecone

uvicorn api.main:app --reload --port 8000
```

Swagger UI is then at http://localhost:8000/docs.

### Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `PINECONE_API_KEY` | yes | none | Vector index access |
| `GROQ_API_KEY` | yes | none | Rationale generation |
| `PINECONE_INDEX_NAME` | no | `talent-match` | Target index |
| `GROQ_MODEL` | no | `openai/gpt-oss-120b` | Generation model |
| `EMBEDDING_MODEL` | no | `all-MiniLM-L6-v2` | Used at ingest time only |
| `TOP_K` | no | `5` | Default match count |
| `CORS_ORIGINS` | no | Vite dev origins | Comma-separated allowed browser origins |

`CORS_ORIGINS` takes scheme and host only, with no trailing slash. Browsers
send `Origin` without one, so a trailing slash matches nothing.

---

## Frontend

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
```

```bash
npm run lint     # oxlint
npm run build    # tsc -b && vite build, output in frontend/dist
```

The interface offers a job picker, a ranked result list, per-candidate skill
comparison against the job's requirements, and the rationale text. It uses
native HTML elements for the parts that behave like native controls: the job
selection is a real `<select>`, and profile details are a real `<details>`
element. Empty, loading, error, and stale-result states are all designed
rather than left to chance.

`VITE_API_BASE_URL` is read at build time and defaults to
`http://localhost:8000`. It must be set before building for a deployed
frontend, because Vite inlines it into the JavaScript bundle and it is never
read at runtime.

Design rationale is recorded in `docs/DESIGN.md`. Visual tokens live in
`frontend/src/tokens.css`.

---

## Deployment

Manual deployment to Render, two services from one repository. No deployment
manifest is committed by choice.

**Backend: Web Service**

| Setting | Value |
|---|---|
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn api.main:app --host 0.0.0.0 --port $PORT` |
| Instance | Free |
| Environment | `PINECONE_API_KEY`, `GROQ_API_KEY`, `PINECONE_INDEX_NAME`, `GROQ_MODEL`, `TOP_K`, `CORS_ORIGINS` |

**Frontend: Static Site**

| Setting | Value |
|---|---|
| Build command | `cd frontend && npm install && npm run build` |
| Publish directory | `frontend/dist` |
| Environment | `VITE_API_BASE_URL` |

The `cd` in the build command is required because no `package.json` exists at
the repository root. The publish directory is relative to the root and takes
no `cd`.

Set `CORS_ORIGINS` on the backend to the frontend origin and
`VITE_API_BASE_URL` on the frontend to the API origin, then redeploy both so
neither ships against stale values.

---

## Project structure

```
api/
  main.py             FastAPI app, routes, CORS configuration
src/
  config.py           environment-driven settings
  data.py             JSON record loading
  schemas.py          Pydantic request and response models
  ingest.py           embed records and upsert to Pinecone
  match.py            retrieval and generation pipeline
data/
  jobs.json           25 synthetic job postings
  candidates.json     40 synthetic candidate profiles
  generate_synthetic_data.py
evals/
  retrieval.py        precision@5 against a skill-overlap baseline
  generation.py       groundedness grading, checkpointed
  grounding_control.py  negative control for the grader
  samples.json        generated rationales, resume point
  reports/            committed eval output
frontend/
  src/                React and TypeScript interface
  public/             static assets, including favicon.svg
docs/
  PRD.md              product requirements
  TRD.md              technical design
  BACKEND_SCHEMA.md   exact data shapes
  DESIGN.md           interface design decisions
DECISIONS.md          technical decisions, with rationale
PLANNING.md           phase checklist
AGENTS.md             instructions for coding agents working in this repo
requirements.txt      dependencies installed by the deployed API
requirements-dev.txt  dependencies for ingest, evals, and local development
```

---

## Tech stack

| Layer | Choice |
|---|---|
| API | Python, FastAPI, Starlette, Uvicorn, Pydantic |
| Embeddings | sentence-transformers, `all-MiniLM-L6-v2`, 384 dimensions |
| Vector store | Pinecone serverless, cosine similarity |
| Generation | Groq via its OpenAI-compatible endpoint, `openai/gpt-oss-120b` |
| Evaluation | OpenAI Evals framework with a Groq completion function |
| Frontend | React, TypeScript, Vite, oxlint |
| Hosting | Render free tier, web service plus static site |

Everything runs on a free tier or locally. There is no paid service anywhere
in the stack.

Runtime and development dependencies are pinned to exact versions. This
matters: the first deployment surfaced a failure where an unpinned transitive
dependency installed a release that broke the generation client, while every
local environment still worked. That is recorded as `DECISIONS.md` D19.

---

## Design decisions

Decisions are written down rather than implied. `DECISIONS.md` records why
each choice was made and what it costs. The ones that shape the project most:

- **D8** Frontend design tooling: `impeccable` owns structure, accessibility,
  and verification; `emil-design-eng` owns motion and craft. The two are
  scoped so their guidance cannot overlap.
- **D11** Dependencies are pinned exactly, because an unpinned reinstall can
  break a working service.
- **D13** No embedding at request time, which keeps PyTorch out of the
  deployed service entirely.
- **D14** Two requirement files, so the web service installs a fraction of
  what ingest and the evals need.
- **D17 and D18** How eval results are reported: as a single committed run
  with its variance stated, not as a claim about what the pipeline always
  achieves.

---

## Known limitations

These are deliberate scope decisions, not oversights:

- No Dockerfile and no CI pipeline
- No authentication, rate limiting, or horizontal scaling, since this is a
  demonstration project rather than a production service
- Retrieval uses plain vector search. Hybrid retrieval and reranking are not
  implemented.
- Relevance for the retrieval eval is a skill-overlap proxy, not a labeled
  test set
- The groundedness grader is an LLM, so it establishes that the grader
  discriminates rather than proving grounding in the abstract
- There is no automated test suite. The measurements above came from
  scripts and manual checks, and nothing currently prevents a regression
  in tokens or interface copy.
- The job's stored summary is used as the retrieval query rather than a
  structured requirement list

---

## Data disclaimer

All candidate and job data in this repository is synthetically generated by
`data/generate_synthetic_data.py`. No real personal data, no real candidate
records, and no real company information appear anywhere in this project.

---

## Documentation

| Document | Contents |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | Product requirements and non-negotiable framing |
| [`docs/TRD.md`](docs/TRD.md) | Architecture, API contract, deployment plan |
| [`docs/BACKEND_SCHEMA.md`](docs/BACKEND_SCHEMA.md) | Exact data shapes for source, index, and API |
| [`docs/DESIGN.md`](docs/DESIGN.md) | Interface design decisions |
| [`DECISIONS.md`](DECISIONS.md) | Technical decisions and their rationale |
| [`PLANNING.md`](PLANNING.md) | Phase-by-phase checklist |
| [`AGENTS.md`](AGENTS.md) | Instructions for coding agents working here |
