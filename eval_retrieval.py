"""Retrieval evaluation: Pinecone top-5 vs a skill-overlap baseline.

Run from the repository root as: python eval_retrieval.py

Method per TRD.md section 5.1: for every job, the baseline "relevant"
candidate set is those candidates sharing at least MIN_SHARED_SKILLS of
the job's required skills. Pinecone's actual top-5 retrieval is compared
to that set as precision@5. The baseline is a skill-overlap proxy, not
ground truth; the README must say so. Writes eval_retrieval_report.json
in the format defined by BACKEND_SCHEMA.md section 4.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from pinecone import Pinecone

from src.config import get_settings
from src.data import load_candidates, load_jobs
from src.ingest import CANDIDATE_NAMESPACE
from src.match import load_embedding_model
from src.schemas import Candidate, Job

TOP_K = 5
MIN_SHARED_SKILLS = 2
REPORT_PATH = Path(__file__).resolve().parent / "eval_retrieval_report.json"


def baseline_ids(job: Job, candidates: Sequence[Candidate]) -> set[str]:
    """Return ids of candidates sharing at least MIN_SHARED_SKILLS required skills."""
    required = set(job.required_skills)
    return {
        candidate.id
        for candidate in candidates
        if len(set(candidate.skills) & required) >= MIN_SHARED_SKILLS
    }


def main() -> None:
    """Evaluate retrieval for every job and write the JSON report."""
    settings = get_settings()
    model = load_embedding_model(settings.embedding_model)
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index(settings.pinecone_index_name)
    candidates = load_candidates()
    jobs = load_jobs()

    per_job_scores: list[dict[str, object]] = []
    for job in jobs:
        baseline = baseline_ids(job, candidates)
        result = index.query(
            vector=model.encode(job.summary).tolist(),
            top_k=TOP_K,
            namespace=CANDIDATE_NAMESPACE,
            include_metadata=False,
        )
        retrieved = {match.id for match in result.matches}
        precision = len(retrieved & baseline) / TOP_K
        per_job_scores.append({"job_id": job.id, "precision_at_5": precision})

    average = sum(
        float(score["precision_at_5"]) for score in per_job_scores
    ) / len(per_job_scores)
    report = {
        "method": "skill_overlap_baseline_precision_at_5",
        "jobs_evaluated": len(per_job_scores),
        "average_precision_at_5": average,
        "per_job_scores": per_job_scores,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"jobs evaluated: {report['jobs_evaluated']}")
    print(f"average precision@5: {average:.3f}")
    print(f"report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
