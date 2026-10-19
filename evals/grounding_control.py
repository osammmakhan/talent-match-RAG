"""Negative control for the groundedness grader.

Run from the repository root as: python evals/grounding_control.py

A high pass rate proves nothing unless the grader can fail. This script
feeds the grading step a known-bad rationale, one that asserts a skill the
candidate record does not contain, and reports whether the grader rejects it.

It reuses the real prompt builder, the real Groq completion function and the
real verdict parser from evals/generation.py, so it tests the grader as
shipped rather than a reimplementation. The honest control is included
alongside: a rationale that only claims what the source records contain must
still pass, so a grader that rejects everything is caught too.

Requires GROQ_API_KEY. Costs four small Groq calls.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generation import (
    GroundednessSample,
    GroqCompletionFn,
    build_grading_prompt,
    parse_verdict,
)
from src.config import get_settings
from src.data import get_job, load_candidates

CANDIDATE_ID = "cand_004"
JOB_ID = "job_001"
REPORT_PATH = ROOT / "evals" / "reports" / "grounding_control.json"

# Skills that appear nowhere in cand_004's record. Each is a plausible thing a
# model might hallucinate, which is the point: the control has to look like a
# realistic mistake, not an obvious nonsense string.
INJECTED_SKILLS = ["Kubernetes", "TensorFlow", "GraphQL"]


def main() -> int:
    """Grade an honest rationale and three tampered ones, then report."""
    settings = get_settings()
    candidates = {c.id: c for c in load_candidates()}
    candidate = candidates[CANDIDATE_ID]
    job = get_job(JOB_ID)
    if candidate is None or job is None:
        raise SystemExit(f"missing source data for {CANDIDATE_ID} or {JOB_ID}")

    absent = [s for s in INJECTED_SKILLS if s.lower() not in
              {known.lower() for known in candidate.skills}]
    if not absent:
        raise SystemExit("injected skills are not actually absent from the record")

    honest = (
        f"The candidate has {candidate.years_experience} years of experience, "
        f"meeting the {job.min_years_experience}-year minimum, and lists "
        f"{', '.join(candidate.skills)}. Based in {candidate.location}."
    )
    tampered = [
        f"The candidate has {candidate.years_experience} years of experience "
        f"and lists {', '.join(candidate.skills)}. They also have production "
        f"experience with {skill}, which strengthens the match considerably."
        for skill in absent
    ]

    completion_fn = GroqCompletionFn(
        api_key=settings.groq_api_key, model=settings.groq_model
    )

    def grade(rationale: str) -> tuple[bool, str | None]:
        prompt = build_grading_prompt(candidate, job, rationale)
        verdict = completion_fn(prompt).get_completions()[0]
        return parse_verdict(verdict)

    results: list[dict[str, object]] = []

    honest_passed, honest_claim = grade(honest)
    results.append(
        {
            "case": "control",
            "kind": "honest",
            "injected_skill": None,
            "passed": honest_passed,
            "grader_claim": honest_claim,
        }
    )
    print(f"control  (honest)                 -> {'PASS' if honest_passed else 'FAIL'}")

    for skill, rationale in zip(absent, tampered):
        passed, claim = grade(rationale)
        results.append(
            {
                "case": f"injected:{skill}",
                "kind": "tampered",
                "injected_skill": skill,
                "passed": passed,
                "grader_claim": claim,
            }
        )
        state = "PASS" if passed else "FAIL"
        print(f"injected {skill:<24} -> {state}  {claim or ''}")

    caught = sum(1 for r in results if r["kind"] == "tampered" and not r["passed"])
    total_tampered = sum(1 for r in results if r["kind"] == "tampered")
    control_ok = bool(honest_passed)

    report = {
        "method": "negative_control_on_groundedness_grader",
        "candidate_id": CANDIDATE_ID,
        "job_id": JOB_ID,
        "model": settings.groq_model,
        "honest_control_passed": control_ok,
        "injected_violations": total_tampered,
        "violations_caught": caught,
        "detection_rate": caught / total_tampered if total_tampered else 0.0,
        "grader_is_discriminating": control_ok and caught == total_tampered,
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print()
    print(f"honest rationale passed      : {control_ok}")
    print(f"violations caught           : {caught}/{total_tampered}")
    print(f"grader is discriminating    : {report['grader_is_discriminating']}")
    print(f"report written to           : {REPORT_PATH}")

    if not report["grader_is_discriminating"]:
        print()
        print("A grader that passes everything, or fails everything, cannot support")
        print("the 125/125 result. Do not cite that number until this is clean.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
