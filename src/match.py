"""Retrieval and grounded generation for job to candidate matching.

Pipeline per TRD.md: embed the job summary with sentence-transformers,
query the Pinecone "candidates" namespace for top-k vector similarity,
then ask Groq for a short rationale per candidate, grounded strictly in
the retrieved candidate metadata.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Any

from openai import OpenAI
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

from src.config import Settings, get_settings
from src.ingest import CANDIDATE_NAMESPACE
from src.schemas import Job, MatchResponse, MatchResult

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

SYSTEM_PROMPT = (
    "You write short match rationales for a recruiting demo. "
    "Only mention skills, tools, and experience that appear explicitly in the "
    "CANDIDATE and JOB text given to you. "
    "If something is not in that text, do not mention it. "
    "Two or three sentences of plain prose, no bullet points."
)


@lru_cache(maxsize=1)
def load_embedding_model(model_name: str) -> SentenceTransformer:
    """Load and cache a sentence-transformers model by name."""
    return SentenceTransformer(model_name)


def job_context(job: Job) -> str:
    """Flatten a job into source text for the generation prompt."""
    return "\n".join(
        [
            f"Title: {job.title}",
            f"Required skills: {', '.join(job.required_skills)}",
            f"Minimum years of experience: {job.min_years_experience}",
            f"Location: {job.location}",
            f"Summary: {job.summary}",
        ]
    )


def candidate_context(metadata: dict[str, Any]) -> str:
    """Flatten retrieved candidate metadata into source text for the prompt.

    Pinecone metadata values are flat, so the comma-joined skills string is
    split back into a list here per BACKEND_SCHEMA.md section 5.
    """
    skills = [
        skill.strip()
        for skill in str(metadata.get("skills", "")).split(",")
        if skill.strip()
    ]
    return "\n".join(
        [
            f"Title: {metadata.get('title', '')}",
            f"Skills: {', '.join(skills)}",
            f"Years of experience: {metadata.get('years_experience', 'not stated')}",
            f"Location: {metadata.get('location', '')}",
            f"Summary: {metadata.get('summary', '')}",
        ]
    )


def generate_rationale(
    client: OpenAI,
    settings: Settings,
    job: Job,
    candidate_id: str,
    metadata: dict[str, Any],
) -> str:
    """Generate one grounded rationale via Groq, or raise if the call fails."""
    response = client.chat.completions.create(
        model=settings.groq_model,
        temperature=0.2,
        max_tokens=2048,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"JOB:\n{job_context(job)}\n\n"
                    f"CANDIDATE ({candidate_id}):\n{candidate_context(metadata)}\n\n"
                    "Write the match rationale."
                ),
            },
        ],
    )
    rationale = response.choices[0].message.content
    if not rationale or not rationale.strip():
        raise RuntimeError(f"Groq returned an empty rationale for {candidate_id}")
    return rationale.strip()


def match_job(job: Job, top_k: int | None = None) -> MatchResponse:
    """Run retrieval and generation for one job, returning scores and rationales.

    Raises ConfigError if environment variables are missing, and propagates
    Pinecone or Groq errors so the API layer can return a 500 with detail.
    """
    settings = get_settings()
    k = top_k if top_k is not None else settings.top_k
    model = load_embedding_model(settings.embedding_model)
    query_vector = model.encode(job.summary).tolist()
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index(settings.pinecone_index_name)
    query_result = index.query(
        vector=query_vector,
        top_k=k,
        namespace=CANDIDATE_NAMESPACE,
        include_metadata=True,
    )
    client = OpenAI(
        api_key=settings.groq_api_key,
        base_url=GROQ_BASE_URL,
        max_retries=8,
        timeout=60.0,
    )
    matches = list(query_result.matches)

    def rationale_for(match: Any) -> str:
        metadata = dict(match.metadata or {})
        return generate_rationale(client, settings, job, match.id, metadata)

    with ThreadPoolExecutor(max_workers=min(5, max(1, len(matches)))) as executor:
        rationales = list(executor.map(rationale_for, matches))
    # Pinecone returns `score` as cosine similarity (1 - cosine distance)
    # for cosine-metric indexes, so it is passed through unchanged here.
    results = [
        MatchResult(
            candidate_id=match.id,
            similarity_score=float(match.score),
            rationale=rationale,
        )
        for match, rationale in zip(matches, rationales)
    ]
    return MatchResponse(job_id=job.id, job_title=job.title, matches=results)
