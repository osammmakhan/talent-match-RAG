"""FastAPI application exposing the Talent Match RAG pipeline.

Endpoints per TRD.md section 3: GET /health, GET /jobs, GET /candidates,
POST /match/{job_id}?top_k=5.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.config import ConfigError, get_cors_origins
from src.data import get_job, load_candidates, load_jobs
from src.match import match_job
from src.schemas import Candidate, Job, MatchResponse

app = FastAPI(title="Talent Match RAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "healthy"}


@app.get("/jobs", response_model=list[Job])
def jobs() -> list[Job]:
    """Return all synthetic job postings."""
    return list(load_jobs())


@app.get("/candidates", response_model=list[Candidate])
def candidates() -> list[Candidate]:
    """Return all synthetic candidate profiles."""
    return list(load_candidates())


@app.post("/match/{job_id}", response_model=MatchResponse)
def match(
    job_id: str,
    top_k: int | None = Query(default=None, ge=1, le=50),
) -> MatchResponse:
    """Run the full RAG pipeline for one job; 404 if the job does not exist."""
    job = get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=404, detail=f"Unknown job_id: {job_id}"
        )
    try:
        return match_job(job, top_k=top_k)
    except ConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Pipeline failed: {exc}"
        ) from exc
