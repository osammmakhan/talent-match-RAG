# Talent Match RAG

A retrieval-augmented generation (RAG) pipeline that matches synthetic job
postings to synthetic candidate profiles, and explains *why* each match was
made using an LLM, grounded strictly in the retrieved data.

This project is a personal build, inspired by a real candidate-to-job
matching problem worked on adjacent to at a previous company. This project was built
independently to understand and demonstrate the underlying RAG mechanics:
embeddings, vector retrieval, grounded generation, and evaluation.

**Status**: backend, evaluation, and frontend are built and verified locally
against live Pinecone and Groq keys. Not yet deployed, so there is no public
link. See `PLANNING.md` for current phase progress. Nothing in this README
describes functionality that has not been implemented and verified; sections
not yet built are marked accordingly.

## Architecture

```
candidates.json / jobs.json
        |
        v
sentence-transformers (all-MiniLM-L6-v2, local, free)
        |
        v
Pinecone (serverless, free tier, namespaces: "candidates" and "jobs")
        |
        v
Retrieval: the job's stored vector is fetched from the "jobs" namespace, then
used to query "candidates" for the top-k matches
        |
        v
Augmented prompt: retrieved candidate text only, nothing invented
        |
        v
Groq (OpenAI-compatible endpoint) generates a short match rationale per
candidate, under explicit guardrails against inventing skills
        |
        v
FastAPI returns similarity scores + rationale as JSON
        |
        v
React + TypeScript frontend: job picker, results with rationale
```

Full detail in `docs/TRD.md`. Data shapes in `docs/BACKEND_SCHEMA.md`. Reasoning
behind each technical choice in `DECISIONS.md`. Build progress in
`PLANNING.md`. Frontend design decisions in `docs/DESIGN.md`.

## Why this design

- **Retrieval, not just similarity scoring.** Vector search narrows the
  candidate pool before the LLM ever sees it. This is the "R" in RAG.
- **Guardrails against hallucination.** The generation step is explicitly
  told to only reference skills or experience present in the retrieved
  text, mirroring the guardrail pattern used in a prior production OpenAI
  integration (character caps, no invented claims).
- **Free end to end.** Every component (embeddings, retrieval, generation,
  evaluation) runs on a genuinely free tier or locally, by design.

## Running it locally

```bash
# the API alone, which is all the deployed service needs
pip install -r requirements.txt

# for ingest, the evals, or local development (adds PyTorch and the Evals deps)
pip install -r requirements-dev.txt
pip install --no-deps git+https://github.com/openai/evals.git   # eval scripts only (DECISIONS.md D10)

cp .env.example .env   # add PINECONE_API_KEY, PINECONE_INDEX_NAME, GROQ_API_KEY

python data/generate_synthetic_data.py   # optional, data already included
python -m src.ingest                     # embed profiles and populate Pinecone

uvicorn api.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, talks to the backend above
```

The frontend reads `VITE_API_BASE_URL` at build time and defaults to
`http://localhost:8000`. The backend's `CORS_ORIGINS` defaults to the Vite dev
origins; set it to the deployed frontend origin in production
(DECISIONS.md D12).

## Evaluation

Two components, both described in full in `docs/TRD.md` (section 5). Both reports
come from real runs against Pinecone and Groq; the raw outputs are
`evals/reports/retrieval.json` and `evals/reports/generation.json`.

### Retrieval quality: 0.824 average precision@5

Method: for each of the 25 jobs, the "relevant" set is every candidate
sharing at least 2 of the job's required skills. That skill-overlap set is
a proxy for relevance, not labeled ground truth: a candidate outside it can
still be a legitimate match, and the score measures agreement with that
simple definition. Pinecone's actual top-5 retrieval is scored as the
fraction of each job's top-5 inside the baseline set, averaged over all
jobs. 14 of 25 jobs scored 1.0; the lowest was 0.2. Per-job scores are in
the report.

Reproduce: `python evals/retrieval.py` (Pinecone key required).

### Generation groundedness: 124 of 125 rationales passed

Method: every rationale the pipeline generates (25 jobs, top-5 each) is
graded against the source candidate and job records by a custom eval class
built on OpenAI's open-source Evals framework, using a completion function
that calls Groq instead of OpenAI's paid API (`DECISIONS.md` D6). A
rationale passes only if every factual claim in it (skills, tools,
experience, years, location, job requirements) appears in the source
records; opinions and fit judgments are ignored. The grader is itself an
LLM, so this checks what that grader can detect rather than proving
groundedness in the abstract, and a near-perfect score on extractive
synthetic summaries is expected.

The one failure in the committed run is a real overstatement, not a grader
quirk. The rationale for `cand_038` against `job_001` says the candidate
"has over nine years of experience"; the source record says
`years_experience: 9`.

**This number is a single run, not a fixed property.** Generation samples at
`temperature=0.2`, so a rerun writes new wording: 123 of 125 rationales came
out different in a second full run, while retrieval returned the identical
candidate set. An earlier run of the same code scored 125 of 125. Expect a
score in the high 120s, and treat a drop into the 110s or lower as a real
regression rather than sampling noise.

What the check is actually for is catching regressions: if the prompt, the
data, or the model change in a way that breaks grounding, failures climb
instead of fluctuating by one. That the grader is discriminating rather than
rubber-stamping is verified separately, by feeding it three tampered
rationales and confirming it rejects all three while accepting an honest one
(`python evals/grounding_control.py`).

Rate limits: the Groq free tier allows 8000 tokens per minute, so the eval
paces itself per `docs/TRD.md` section 8: about 26 seconds between generation
jobs, and a sliding-window token limiter during grading (125 grades took
about 17 minutes). Generated rationales are checkpointed to
`evals/samples.json`, so an interrupted run resumes instead of
regenerating.

Reproduce: `python evals/generation.py` (both phases, about 30 minutes
end to end), or `python evals/generation.py generate` / `... grade` to run
them apart.

## What's next

See `PLANNING.md` for the live checklist. Deferred by deliberate choice,
not oversight: Dockerfile, CI pipeline, hybrid retrieval, reranking, a
labeled precision@k test set beyond the skill-overlap proxy.

## Tech stack

Python, FastAPI, sentence-transformers, Pinecone, Groq, React, TypeScript.

## Data disclaimer

All candidate and job data in this repository is synthetically generated
(`data/generate_synthetic_data.py`). No real personal or company data is
used anywhere in this project.
