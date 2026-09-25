# Talent Match RAG

A retrieval-augmented generation (RAG) pipeline that matches synthetic job
postings to synthetic candidate profiles, and explains *why* each match was
made using an LLM, grounded strictly in the retrieved data.

This project is a personal build, inspired by a real candidate-to-job
matching problem worked on adjacent to at a previous company. This project was built
independently to understand and demonstrate the underlying RAG mechanics:
embeddings, vector retrieval, grounded generation, and evaluation.

**Status**: in active development. See `PLANNING.md` for current phase
progress. Nothing in this README describes functionality that has not been
implemented and verified; sections not yet built are marked accordingly.

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
Retrieval: given a job, vector-similarity search for top-k candidates
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

Full detail in `TRD.md`. Data shapes in `BACKEND_SCHEMA.md`. Reasoning
behind each technical choice in `DECISIONS.md`. Build progress in
`PLANNING.md`.

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
pip install -r requirements.txt
pip install --no-deps git+https://github.com/openai/evals.git   # eval scripts only (DECISIONS.md D10)
cp .env.example .env   # add PINECONE_API_KEY, PINECONE_INDEX_NAME, GROQ_API_KEY

python data/generate_synthetic_data.py   # optional, data already included
python -m src.ingest                     # embed profiles and populate Pinecone

uvicorn api.main:app --reload --port 8000
```

## Evaluation

Two components, both described in full in `TRD.md` (section 5). Both reports
come from real runs against Pinecone and Groq; the raw outputs are
`eval_retrieval_report.json` and `eval_generation_report.json`.

### Retrieval quality: 0.824 average precision@5

Method: for each of the 25 jobs, the "relevant" set is every candidate
sharing at least 2 of the job's required skills. That skill-overlap set is
a proxy for relevance, not labeled ground truth: a candidate outside it can
still be a legitimate match, and the score measures agreement with that
simple definition. Pinecone's actual top-5 retrieval is scored as the
fraction of each job's top-5 inside the baseline set, averaged over all
jobs. 14 of 25 jobs scored 1.0; the lowest was 0.2. Per-job scores are in
the report.

Reproduce: `python eval_retrieval.py` (Pinecone key required).

### Generation groundedness: 125 of 125 rationales passed

Method: every rationale the pipeline generates (25 jobs, top-5 each) is
graded against the source candidate and job records by a custom eval class
built on OpenAI's open-source Evals framework, using a completion function
that calls Groq instead of OpenAI's paid API (`DECISIONS.md` D6). A
rationale passes only if every factual claim in it (skills, tools,
experience, years, location, job requirements) appears in the source
records; opinions and fit judgments are ignored. The grader is itself an
LLM, so this checks what that grader can detect rather than proving
groundedness in the abstract, and a perfect score on extractive synthetic
summaries is expected. The check earns its place by catching regressions:
if prompts, data, or the model change, invented claims show up as failures.

Rate limits: the Groq free tier allows 8000 tokens per minute, so the eval
paces itself per `TRD.md` section 8: about 26 seconds between generation
jobs, and a sliding-window token limiter during grading (125 grades took
about 17 minutes). Generated rationales are checkpointed to
`eval_generation_samples.json`, so an interrupted run resumes instead of
regenerating.

Reproduce: `python eval_generation.py` (both phases, about 30 minutes
end to end), or `python eval_generation.py generate` / `... grade` to run
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
