# AGENTS.md — Talent Match RAG

Instructions for any coding agent (OpenCode, or others) operating in this repository.

## Read first, in this order

1. `PRD.md` — what this project is and is not, and the non-negotiable framing constraint
2. `TRD.md` — architecture, stack, API contract, deployment plan
3. `BACKEND_SCHEMA.md` — exact data shapes for source JSON, Pinecone records, and API models
4. `PLANNING.md` — the phase-by-phase checklist; this is the current source of truth for what's done and what isn't
5. `DECISIONS.md` — why each technical choice was made, and one open unresolved item (D8) to flag to the user, not silently resolve

## Ground rules

- **Never mark a PLANNING.md item complete until it has actually run successfully.** Writing code is not the same as verifying it. If a step requires a real API key (Pinecone, Groq), it is not done until it has been run with real keys and produced real output.
- **Never write documentation, a README line, or a resume-facing claim describing functionality that hasn't been implemented and verified.** This project exists specifically to be defensible under scrutiny; padding it defeats the purpose.
- **If a technical decision needs to change from what TRD.md or DECISIONS.md says, update DECISIONS.md first** with a new entry (append, don't rewrite history), then proceed. Don't silently diverge from the documented plan.
- **Stay within the stack specified in TRD.md**: sentence-transformers for embeddings, Pinecone for retrieval, Groq for generation, FastAPI backend, React + TypeScript frontend. Don't substitute a different provider or library without adding a DECISIONS.md entry explaining why.
- **Everything must stay free.** Every service used needs a free tier sufficient for this project's scale. If a chosen approach would incur real cost at this project's scale, stop and flag it rather than proceeding.
- **This is a demo-grade project, deliberately.** Don't add authentication, horizontal scaling, monitoring/observability infrastructure, or other production-grade concerns unless explicitly asked. Docker and CI are deferred, not needed yet (see PLANNING.md).

## Open item requiring user input before frontend work starts

DECISIONS.md D8: the user named "UI/UX Pro Max skill" for this project's UI work, which conflicts with a previously stated preference to avoid UI/UX Pro Max in favor of Vercel's Web Design Guidelines stacked with the Emil Kowalski skill. Do not pick one silently. Ask the user to confirm before Phase 3 (frontend) styling work begins.

## Commands

```bash
# install
pip install -r requirements.txt
pip install --no-deps git+https://github.com/openai/evals.git   # eval scripts only (DECISIONS.md D10)

# generate synthetic data (already included, regenerate only if needed)
python data/generate_synthetic_data.py

# ingest into Pinecone
python -m src.ingest

# run the backend
uvicorn api.main:app --reload --port 8000

# run retrieval evaluation
python eval_retrieval.py

# run generation groundedness evaluation
python eval_generation.py
```

## Conventions

- Python: type hints throughout, docstrings on public functions, no bare `except:` clauses.
- Commit messages: describe what changed and why, not just what file was touched.
- No em dashes in any generated documentation or code comments; use commas, colons, or separate sentences.
- No filler language, forced enthusiasm, or AI-sounding phrasing in README or comments; plain and functional.
