"""Pydantic models for source data and API responses, per BACKEND_SCHEMA.md."""

from __future__ import annotations

from pydantic import BaseModel

CANDIDATE_NAMESPACE = "candidates"
JOB_NAMESPACE = "jobs"


class Candidate(BaseModel):
    """A synthetic candidate profile from data/candidates.json."""

    id: str
    title: str
    skills: list[str]
    years_experience: int
    location: str
    summary: str


class Job(BaseModel):
    """A synthetic job posting from data/jobs.json."""

    id: str
    title: str
    required_skills: list[str]
    min_years_experience: int
    location: str
    summary: str


class MatchResult(BaseModel):
    """One retrieved candidate with similarity score and generated rationale."""

    candidate_id: str
    similarity_score: float
    rationale: str


class MatchResponse(BaseModel):
    """Full response for POST /match/{job_id}."""

    job_id: str
    job_title: str
    matches: list[MatchResult]
