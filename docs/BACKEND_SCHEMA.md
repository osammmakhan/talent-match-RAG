# Backend Schema — Talent Match RAG

## 1. Source data schemas (JSON files)

### Candidate
```json
{
  "id": "cand_001",
  "title": "Cloud Engineer",
  "skills": ["JavaScript", "REST APIs", "Pandas", "scikit-learn"],
  "years_experience": 3,
  "location": "Munich",
  "summary": "Cloud Engineer with 3 years of experience working primarily with..."
}
```

### Job
```json
{
  "id": "job_001",
  "title": "Backend Engineer",
  "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
  "min_years_experience": 3,
  "location": "Berlin",
  "summary": "We are hiring a Backend Engineer to join our team in Berlin..."
}
```

## 2. Pinecone vector record schema

Two namespaces in one 384-dimension, cosine-similarity index.

```
namespace: "candidates" | "jobs"
id: string                  # matches the source JSON id, e.g. "cand_001"
values: float[384]          # sentence-transformers embedding of `summary`
metadata:
  title: string
  skills: string             # comma-joined, since Pinecone metadata values must be flat
  years_experience: number   # candidates only
  required_skills: string    # jobs only, comma-joined
  min_years_experience: number  # jobs only
  location: string
  summary: string
```

## 3. API request/response models (Pydantic)

```python
class Candidate(BaseModel):
    id: str
    title: str
    skills: list[str]
    years_experience: int
    location: str
    summary: str

class Job(BaseModel):
    id: str
    title: str
    required_skills: list[str]
    min_years_experience: int
    location: str
    summary: str

class MatchResult(BaseModel):
    candidate_id: str
    similarity_score: float
    rationale: str | None  # null when retrieval succeeded but generation failed

class MatchResponse(BaseModel):
    job_id: str
    job_title: str
    matches: list[MatchResult]
```

## 4. Evaluation output schemas

### Retrieval eval report
```json
{
  "method": "skill_overlap_baseline_precision_at_5",
  "jobs_evaluated": 25,
  "average_precision_at_5": 0.0,
  "per_job_scores": [{"job_id": "job_001", "precision_at_5": 0.0}]
}
```

### Generation groundedness eval report
```json
{
  "method": "openai_evals_custom_groundedness_check",
  "completion_provider": "groq",
  "total_rationales_checked": 0,
  "passed": 0,
  "failed": 0,
  "pass_rate": 0.0,
  "failures": [{"candidate_id": "...", "job_id": "...", "invented_claim": "..."}]
}
```

## 5. Notes

- `skills` and `required_skills` are stored as comma-joined strings in Pinecone metadata because Pinecone metadata does not support nested arrays cleanly across all client versions; the API layer splits them back into lists before returning to the frontend.
- `similarity_score` in the API response is derived from Pinecone's returned distance metric (cosine); the exact transformation (e.g. `1 - distance`) must be documented in code comments in `match.py` once implemented, not left implicit.
- `rationale` is nullable because retrieval and generation are independent stages. A generation failure leaves the similarity score valid, so the record is returned with `rationale: null` rather than dropped, and the frontend labels it rather than implying the rationale is merely absent (DECISIONS.md D16).
