"""Load the synthetic source datasets from the data directory."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from src.schemas import Candidate, Job

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def load_candidates() -> tuple[Candidate, ...]:
    """Return all candidate records from data/candidates.json."""
    raw = json.loads((DATA_DIR / "candidates.json").read_text(encoding="utf-8"))
    return tuple(Candidate.model_validate(item) for item in raw)


@lru_cache(maxsize=1)
def load_jobs() -> tuple[Job, ...]:
    """Return all job records from data/jobs.json."""
    raw = json.loads((DATA_DIR / "jobs.json").read_text(encoding="utf-8"))
    return tuple(Job.model_validate(item) for item in raw)


def get_job(job_id: str) -> Job | None:
    """Return the job with the given id, or None if it does not exist."""
    return next((job for job in load_jobs() if job.id == job_id), None)
