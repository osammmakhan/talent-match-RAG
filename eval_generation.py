"""Generation groundedness evaluation using OpenAI's Evals framework, wired to Groq.

Run from the repository root as: python eval_generation.py
(or `python eval_generation.py generate` / `... grade` to run phases apart)

Method per TRD.md section 5.2: generate a rationale for every retrieved
candidate with the real pipeline (25 jobs, top-5 each), then grade each
rationale with a custom evals.Eval subclass. Grading goes through a
Completion Function Protocol implementation that calls Groq, never
OpenAI's paid API, per DECISIONS.md D6. A rationale passes only if every
factual claim in it is supported by the source candidate and job records.

Rate limiting: the Groq free tier allows 8000 tokens per minute for every
available model (measured: a grading call costs ~750 tokens). Per TRD.md
section 8, requests are paced rather than switching providers: generation
waits between jobs, and grading passes through a sliding-window token
limiter. Generated rationales are checkpointed to
eval_generation_samples.json after each job so an interrupted run resumes
instead of regenerating.

Writes eval_generation_report.json in the format defined by
BACKEND_SCHEMA.md section 4.
"""

from __future__ import annotations

import json
import os
import random
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

# evals.registry builds an OpenAI client at import time and requires
# OPENAI_API_KEY to be set. This project never calls OpenAI (D6), so a
# dummy value is provided only to satisfy that import; the completion
# function below talks to Groq. setdefault: never overrides a real key.
os.environ.setdefault("OPENAI_API_KEY", "dummy-evals-import-only-never-called")
# Limiter serializes grading starts anyway; threads only overlap in-flight
# calls with limiter waits.
os.environ.setdefault("EVALS_THREADS", "3")

import evals
from evals.base import RunSpec
from evals.record import DummyRecorder, RecorderBase
from openai import OpenAI

from src.config import get_settings
from src.data import load_candidates, load_jobs
from src.match import GROQ_BASE_URL, job_context, match_job
from src.schemas import Candidate, Job

REPORT_PATH = Path(__file__).resolve().parent / "eval_generation_report.json"
SAMPLES_PATH = Path(__file__).resolve().parent / "eval_generation_samples.json"

# Measured Groq free-tier ceilings: 8000 TPM for all chat models.
# Budgets below keep planned usage at 75% of the cap for headroom.
GEN_INTERVAL_SECONDS = 26.0
GRADE_TOKEN_ESTIMATE = 850
GRADING_BUDGET_TOKENS = 6000
TOKEN_WINDOW_SECONDS = 60.0


@dataclass(frozen=True)
class GroundednessSample:
    """One rationale to grade, with its ground-truth source records."""

    job_id: str
    candidate_id: str
    rationale: str
    candidate: Candidate
    job: Job


class TpmLimiter:
    """Sliding-window token limiter approximating Groq's per-minute cap.

    acquire() reserves an estimated number of tokens inside the current
    window and sleeps until the reservation fits. Estimates are set above
    measured usage, so actual consumption stays under the budget.
    """

    def __init__(self, budget_tokens: int, window_seconds: float) -> None:
        self._budget = budget_tokens
        self._window = window_seconds
        self._events: list[tuple[float, int]] = []
        self._lock = threading.Lock()

    def acquire(self, tokens: int) -> None:
        """Block until the estimated token cost fits in the window, then reserve it."""
        with self._lock:
            while True:
                now = time.monotonic()
                self._events = [
                    (stamp, count)
                    for stamp, count in self._events
                    if now - stamp < self._window
                ]
                used = sum(count for _, count in self._events)
                if used + tokens <= self._budget:
                    self._events.append((now, tokens))
                    return
                oldest_stamp = self._events[0][0]
                wait = self._window - (now - oldest_stamp) + 0.1
                time.sleep(max(0.1, wait))


GRADING_LIMITER = TpmLimiter(GRADING_BUDGET_TOKENS, TOKEN_WINDOW_SECONDS)


class GroqCompletionResult(evals.CompletionResult):
    """CompletionResult wrapping a single Groq grader response."""

    def __init__(self, text: str) -> None:
        self._text = text

    def get_completions(self) -> list[str]:
        return [self._text]


class GroqCompletionFn:
    """Completion Function Protocol implementation backed by Groq (D6).

    Structurally satisfies evals.CompletionFn, which the framework checks
    with a runtime_checkable Protocol, so evals.Eval accepts it directly.
    """

    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(
            api_key=api_key, base_url=GROQ_BASE_URL, max_retries=6, timeout=60.0
        )
        self._model = model

    def __call__(self, prompt: str, **kwargs: object) -> GroqCompletionResult:
        GRADING_LIMITER.acquire(GRADE_TOKEN_ESTIMATE)
        response = self._client.chat.completions.create(
            model=self._model,
            temperature=0.0,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise RuntimeError("Groq grader returned an empty response")
        return GroqCompletionResult(text)


def candidate_text(candidate: Candidate) -> str:
    """Flatten a candidate record into source text for the grading prompt."""
    return "\n".join(
        [
            f"Title: {candidate.title}",
            f"Skills: {', '.join(candidate.skills)}",
            f"Years of experience: {candidate.years_experience}",
            f"Location: {candidate.location}",
            f"Summary: {candidate.summary}",
        ]
    )


def build_grading_prompt(
    candidate: Candidate, job: Job, rationale: str
) -> str:
    """Build the fact-check prompt sent to the Groq grader."""
    return "\n".join(
        [
            "You are a strict fact checker for a recruiting RAG demo.",
            "You will see a candidate record, a job record, and a rationale",
            "written about that candidate for that job.",
            "",
            "Determine whether the rationale states any factual claim about",
            "skills, tools, experience, years, location, or job requirements",
            "that is contradicted by, or not present in, the source records.",
            "Ignore opinions, fit judgments, and recommendations such as",
            '"strong match" or "solid fit". A statement that the candidate',
            "lacks a job skill is supported when the candidate record indeed",
            "lacks it. Only unsupported factual claims count as failures.",
            "",
            "Answer with exactly two lines. First line: PASS or FAIL.",
            "If FAIL, second line: the unsupported claim, quoted verbatim.",
            "",
            "CANDIDATE SOURCE (ground truth):",
            candidate_text(candidate),
            "",
            "JOB SOURCE (ground truth):",
            job_context(job),
            "",
            "RATIONALE UNDER REVIEW:",
            rationale,
        ]
    )


def parse_verdict(text: str) -> tuple[bool, str | None]:
    """Parse a two-line PASS/FAIL grader response into (passed, claim)."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("empty verdict")
    head = lines[0].upper()
    if head.startswith("PASS"):
        return True, None
    if head.startswith("FAIL"):
        same_line_claim = lines[0][4:].lstrip(": ").strip()
        claim_parts = ([same_line_claim] if same_line_claim else []) + lines[1:]
        return False, " ".join(claim_parts).strip() or "claim not specified"
    raise ValueError(f"unparseable verdict: {text[:120]!r}")


class GroundednessEval(evals.Eval):
    """Evals-framework eval that grades one rationale per sample."""

    def __init__(
        self,
        samples: list[GroundednessSample],
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._samples = samples

    def eval_sample(
        self, sample: GroundednessSample, rng: random.Random
    ) -> Dict[str, object]:
        """Grade one rationale and return its result record."""
        prompt = build_grading_prompt(sample.candidate, sample.job, sample.rationale)
        verdict_text = self.completion_fn(prompt).get_completions()[0]
        try:
            passed, claim = parse_verdict(verdict_text)
        except ValueError as exc:
            passed, claim = False, f"grader output not parseable: {exc}"
        return {
            "job_id": sample.job_id,
            "candidate_id": sample.candidate_id,
            "passed": passed,
            "invented_claim": claim,
        }

    def run(self, recorder: RecorderBase) -> Dict[str, float]:
        """Grade all samples and write the BACKEND_SCHEMA.md report."""
        results = self.eval_all_samples(recorder, self._samples, show_progress=True)
        total = len(results)
        passed = sum(1 for result in results if result["passed"])
        failed = total - passed
        pass_rate = passed / total if total else 0.0
        failures = [
            {
                "candidate_id": result["candidate_id"],
                "job_id": result["job_id"],
                "invented_claim": result["invented_claim"],
            }
            for result in results
            if not result["passed"]
        ]
        report = {
            "method": "openai_evals_custom_groundedness_check",
            "completion_provider": "groq",
            "total_rationales_checked": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
            "failures": failures,
        }
        REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"rationales checked: {total}")
        print(f"passed: {passed} | failed: {failed} | pass rate: {pass_rate:.3f}")
        print(f"report written to {REPORT_PATH}")
        return {"pass_rate": pass_rate, "rationales_checked": float(total)}


def _load_generated(model: str) -> dict[str, list[dict[str, str]]]:
    """Load the checkpoint of generated rationales, or return an empty dict."""
    if not SAMPLES_PATH.exists():
        return {}
    data = json.loads(SAMPLES_PATH.read_text(encoding="utf-8"))
    if data.get("model") != model:
        print(
            f"checkpoint model {data.get('model')!r} differs from {model!r}; regenerating"
        )
        return {}
    return data.get("generated", {})


def _save_generated(
    model: str, generated: dict[str, list[dict[str, str]]]
) -> None:
    """Write the generation checkpoint to disk."""
    payload = {"model": model, "generated": generated}
    SAMPLES_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def generate_samples(model: str) -> None:
    """Generate rationales for any job not already checkpointed, pacing between jobs."""
    generated = _load_generated(model)
    jobs = load_jobs()
    missing = [job for job in jobs if job.id not in generated]
    print(
        f"generation: {len(jobs) - len(missing)} jobs already checkpointed, "
        f"{len(missing)} to generate"
    )
    for position, job in enumerate(missing, start=1):
        response = match_job(job)
        generated[job.id] = [
            {"candidate_id": match.candidate_id, "rationale": match.rationale}
            for match in response.matches
        ]
        _save_generated(model, generated)
        print(
            f"generated rationales for {job.id} "
            f"({len(generated)}/{len(jobs)} jobs checkpointed)"
        )
        if job is not missing[-1]:
            time.sleep(GEN_INTERVAL_SECONDS)


def load_samples(model: str) -> list[GroundednessSample]:
    """Rebuild grading samples from the checkpoint and the source records."""
    generated = _load_generated(model)
    jobs = load_jobs()
    missing = [job.id for job in jobs if job.id not in generated]
    if missing:
        raise SystemExit(
            f"checkpoint is missing {len(missing)} jobs ({missing[:3]}...); "
            "run: python eval_generation.py generate"
        )
    candidates_by_id = {candidate.id: candidate for candidate in load_candidates()}
    jobs_by_id = {job.id: job for job in jobs}
    samples = [
        GroundednessSample(
            job_id=job_id,
            candidate_id=entry["candidate_id"],
            rationale=entry["rationale"],
            candidate=candidates_by_id[entry["candidate_id"]],
            job=jobs_by_id[job_id],
        )
        for job_id, entries in generated.items()
        for entry in entries
    ]
    return samples


def grade_samples(samples: list[GroundednessSample], model: str) -> None:
    """Grade every generated rationale through the evals framework and Groq."""
    print(f"grading {len(samples)} rationales with Groq via the evals framework")
    completion_fn = GroqCompletionFn(
        api_key=get_settings().groq_api_key, model=model
    )
    run_spec = RunSpec(
        completion_fns=[f"groq:{model}"],
        eval_name="groundedness.main",
        base_eval="groundedness",
        split="main",
        run_config={"model": model},
        created_by="talent-match-rag",
    )
    recorder = DummyRecorder(run_spec, log=False)
    evaluation = GroundednessEval(
        samples=samples,
        completion_fns=[completion_fn],
        eval_registry_path=Path(__file__).resolve().parent,
        name="groundedness.main",
    )
    metrics = evaluation.run(recorder)
    print(f"done: {metrics}")


def main() -> None:
    """Run generation, grading, or both. Optional argv[1]: generate | grade."""
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode not in {"all", "generate", "grade"}:
        raise SystemExit("usage: python eval_generation.py [generate|grade]")
    settings = get_settings()
    if mode in {"all", "generate"}:
        generate_samples(settings.groq_model)
    if mode in {"all", "grade"}:
        samples = load_samples(settings.groq_model)
        grade_samples(samples, settings.groq_model)


if __name__ == "__main__":
    main()
