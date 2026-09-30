"""Embed the synthetic datasets and upsert them into Pinecone.

Run from the repository root as: python -m src.ingest

Creates the serverless index if it does not exist: 384 dimensions with the
default all-MiniLM-L6-v2 model, cosine metric, per TRD.md. Upserts all
records into the "candidates" and "jobs" namespaces per BACKEND_SCHEMA.md.
"""

from __future__ import annotations

import time
from typing import Any

from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

from src.config import get_settings
from src.data import load_candidates, load_jobs
from src.schemas import (
    CANDIDATE_NAMESPACE,
    JOB_NAMESPACE,
    Candidate,
    Job,
)

SERVERLESS_CLOUD = "aws"
SERVERLESS_REGION = "us-east-1"
INDEX_READY_TIMEOUT_SECONDS = 120.0


def index_is_ready(pc: Pinecone, name: str) -> bool:
    """Return True if the named index reports a ready status."""
    description = pc.describe_index(name)
    status = getattr(description, "status", None)
    if status is None:
        return False
    if isinstance(status, dict):
        return bool(status.get("ready", False))
    return bool(getattr(status, "ready", False))


def ensure_index(pc: Pinecone, name: str, dimension: int) -> None:
    """Create the serverless cosine index if missing, then wait until it is ready."""
    if not pc.has_index(name):
        pc.create_index(
            name=name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud=SERVERLESS_CLOUD, region=SERVERLESS_REGION),
        )
        print(f"Created index {name!r} ({dimension}-dim, cosine, serverless)")
    deadline = time.monotonic() + INDEX_READY_TIMEOUT_SECONDS
    while not index_is_ready(pc, name):
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Index {name} not ready after {INDEX_READY_TIMEOUT_SECONDS:.0f}s"
            )
        time.sleep(1.0)


def candidate_record(candidate: Candidate, model: SentenceTransformer) -> dict[str, Any]:
    """Build one Pinecone vector record (id, values, metadata) for a candidate."""
    values = model.encode(candidate.summary).tolist()
    metadata = {
        "title": candidate.title,
        "skills": ", ".join(candidate.skills),
        "years_experience": candidate.years_experience,
        "location": candidate.location,
        "summary": candidate.summary,
    }
    return {"id": candidate.id, "values": values, "metadata": metadata}


def job_record(job: Job, model: SentenceTransformer) -> dict[str, Any]:
    """Build one Pinecone vector record (id, values, metadata) for a job."""
    values = model.encode(job.summary).tolist()
    metadata = {
        "title": job.title,
        "required_skills": ", ".join(job.required_skills),
        "min_years_experience": job.min_years_experience,
        "location": job.location,
        "summary": job.summary,
    }
    return {"id": job.id, "values": values, "metadata": metadata}


def main() -> None:
    """Embed both datasets and upsert them into their Pinecone namespaces."""
    settings = get_settings()
    model = SentenceTransformer(settings.embedding_model)
    dimension = model.get_embedding_dimension()
    if dimension is None:
        raise RuntimeError(
            f"Could not determine embedding dimension for {settings.embedding_model!r}"
        )
    pc = Pinecone(api_key=settings.pinecone_api_key)
    ensure_index(pc, settings.pinecone_index_name, dimension)
    index = pc.Index(settings.pinecone_index_name)
    candidates = load_candidates()
    jobs = load_jobs()
    index.upsert(
        vectors=[candidate_record(c, model) for c in candidates],
        namespace=CANDIDATE_NAMESPACE,
    )
    index.upsert(
        vectors=[job_record(j, model) for j in jobs],
        namespace=JOB_NAMESPACE,
    )
    print(f"Upserted {len(candidates)} candidates into namespace {CANDIDATE_NAMESPACE!r}")
    print(f"Upserted {len(jobs)} jobs into namespace {JOB_NAMESPACE!r}")


if __name__ == "__main__":
    main()
