"""Generate the synthetic candidate and job datasets for Talent Match RAG.

Writes candidates.json (40 records) and jobs.json (25 records) into this
directory. Deterministic for a fixed RANDOM_SEED. Uses only the standard
library: plain random sampling from fixed title, skill, and city lists.

Data shapes follow BACKEND_SCHEMA.md. Skills are sampled from per-title
pools so that jobs and candidates with the same title share skills, which
gives the skill-overlap retrieval baseline a real signal to measure.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent
CANDIDATE_COUNT = 40
JOB_COUNT = 25
RANDOM_SEED = 42

CITIES: list[str] = [
    "Berlin",
    "Munich",
    "Hamburg",
    "Frankfurt",
    "Amsterdam",
    "Vienna",
    "Zurich",
    "Dublin",
    "Lisbon",
    "Barcelona",
    "Prague",
    "Warsaw",
]

TITLE_SKILLS: dict[str, list[str]] = {
    "Backend Engineer": [
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Docker",
        "SQL",
        "REST APIs",
        "Git",
    ],
    "Frontend Engineer": [
        "JavaScript",
        "TypeScript",
        "React",
        "CSS",
        "HTML",
        "REST APIs",
        "Git",
    ],
    "Data Engineer": [
        "Python",
        "SQL",
        "Pandas",
        "Airflow",
        "PostgreSQL",
        "dbt",
        "Docker",
    ],
    "ML Engineer": [
        "Python",
        "scikit-learn",
        "PyTorch",
        "SQL",
        "Docker",
        "Pandas",
    ],
    "Cloud Engineer": [
        "AWS",
        "Kubernetes",
        "Terraform",
        "Docker",
        "CI/CD",
        "Linux",
    ],
    "AI Automation Engineer": [
        "Python",
        "LangChain",
        "RAG",
        "LLM APIs",
        "FastAPI",
        "REST APIs",
        "Git",
    ],
}

GLOBAL_SKILLS: list[str] = sorted(
    {skill for skills in TITLE_SKILLS.values() for skill in skills}
)

CANDIDATE_SUMMARY_TEMPLATES: list[str] = [
    "{title} with {years} years of experience working primarily with {skills}. Based in {location}.",
    "{title} based in {location}, {years} years of hands-on experience building with {skills}.",
    "Experienced {title} ({years} years) skilled in {skills}. Located in {location}.",
]

JOB_SUMMARY_TEMPLATES: list[str] = [
    "We are hiring a {title} to join our team in {location}. The role requires {years}+ years of experience with {skills}.",
    "Join our {location} team as a {title}. You will work with {skills} and bring at least {years} years of experience.",
    "Opening for a {title} in {location}. Candidates should have {years}+ years of experience across {skills}.",
]


def skill_phrase(skills: list[str]) -> str:
    """Join a skill list into readable prose: 'a, b, and c'."""
    if len(skills) == 1:
        return skills[0]
    if len(skills) == 2:
        return f"{skills[0]} and {skills[1]}"
    return ", ".join(skills[:-1]) + ", and " + skills[-1]


def make_candidate(rng: random.Random, index: int) -> dict[str, Any]:
    """Build one synthetic candidate record with a padded cand_NNN id."""
    title = rng.choice(list(TITLE_SKILLS))
    skills = rng.sample(TITLE_SKILLS[title], k=4)
    extras = [s for s in rng.sample(GLOBAL_SKILLS, k=3) if s not in skills]
    skills += extras[: rng.randint(0, 2)]
    years = rng.randint(1, 12)
    location = rng.choice(CITIES)
    summary = rng.choice(CANDIDATE_SUMMARY_TEMPLATES).format(
        title=title,
        years=years,
        skills=skill_phrase(skills),
        location=location,
    )
    return {
        "id": f"cand_{index:03d}",
        "title": title,
        "skills": skills,
        "years_experience": years,
        "location": location,
        "summary": summary,
    }


def make_job(rng: random.Random, index: int) -> dict[str, Any]:
    """Build one synthetic job record with a padded job_NNN id."""
    title = rng.choice(list(TITLE_SKILLS))
    required_skills = rng.sample(TITLE_SKILLS[title], k=rng.randint(3, 5))
    min_years = rng.randint(1, 8)
    location = rng.choice(CITIES)
    summary = rng.choice(JOB_SUMMARY_TEMPLATES).format(
        title=title,
        years=min_years,
        skills=skill_phrase(required_skills),
        location=location,
    )
    return {
        "id": f"job_{index:03d}",
        "title": title,
        "required_skills": required_skills,
        "min_years_experience": min_years,
        "location": location,
        "summary": summary,
    }


def main() -> None:
    """Generate both JSON files into DATA_DIR."""
    rng = random.Random(RANDOM_SEED)
    candidates = [make_candidate(rng, i) for i in range(1, CANDIDATE_COUNT + 1)]
    jobs = [make_job(rng, i) for i in range(1, JOB_COUNT + 1)]
    (DATA_DIR / "candidates.json").write_text(
        json.dumps(candidates, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (DATA_DIR / "jobs.json").write_text(
        json.dumps(jobs, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(candidates)} candidates and {len(jobs)} jobs to {DATA_DIR}")


if __name__ == "__main__":
    main()
