# Product Requirements Document — Talent Match RAG

## 1\. What this is

A portfolio project demonstrating a retrieval-augmented generation (RAG) pipeline applied to candidate-to-job matching. Recreated, based on my previous employer's experience, using entirely synthetic data this time.

## 2\. Why it exists

RAG and vector databases are the most frequently required skills across current job postings in this candidate's target role (AI/Automation Engineer), and are confirmed gaps with no verifiable prior evidence. This project closes that gap honestly, through original work the candidate can defend line by line in an interview.

## 3\. Framing constraint (non-negotiable)

* No claim in any generated document (this PRD, the TRD, the README, resume bullets) may describe functionality that has not actually been implemented and verified end to end.

## 4\. Goals

* A working, deployed, end-to-end RAG pipeline: retrieval (vector similarity) + grounded generation (LLM explains the match).
* A live demo link, usable by a non-technical recruiter without needing to read code or run commands.
* Quantitative evidence the retrieval and generation stages actually work (not just "it runs") — see evaluation in the TRD.
* Zero ongoing cost — every service used must have a genuinely free tier sufficient for this project's scale.
* A project the candidate can explain and defend technically in an interview, including trade-offs and alternatives considered (see DECISIONS.md).

## 5\. Non-goals

* Production-scale infrastructure: no auth, no horizontal scaling, no observability stack, no SLA-driven uptime design. This is a demo-grade project by deliberate choice, not an oversight.
* Real candidate or company data. All profiles are synthetically generated.
* Full feature parity with a real recruiting platform. This demonstrates one pipeline (job → top-k candidate matches with rationale), not a product.

## 6\. Users

* **Primary**: interviewers and hiring managers evaluating the candidate's technical portfolio.
* **Secondary**: non-technical recruiters skimming a live link before a screening call.

## 7\. Functional requirements

* FR1: List available job postings.
* FR2: List available candidate profiles.
* FR3: Given a job, retrieve the top-k most relevant candidates by vector similarity.
* FR4: Generate a short, grounded rationale for each retrieved candidate explaining the match, without inventing skills or experience not present in the source data.
* FR5: Surface a similarity score alongside each match.
* FR6: A UI that lets a non-technical visitor pick a job and view results without touching the API directly.

## 8\. Non-functional requirements

* NFR1: Every third-party service used (embeddings, vector store, generation, evaluation) must have a free tier that covers this project's scale (65 profiles, low query volume).
* NFR2: The backend must not depend on non-persistent local disk state surviving a redeploy (see TRD deployment section).
* NFR3: Response time for a single match request should stay under a few seconds; no strict SLA.
* NFR4: All generated text must pass a groundedness check before being considered part of "working" functionality (see evaluation in TRD).

## 9\. Success criteria

* Live, publicly reachable demo link.
* Retrieval evaluation score reported in the README with methodology explained.
* Generation groundedness evaluation reported in the README with methodology explained.
* End-to-end match request verified against real API keys, not just mocked or assumed.
* Every technology named in the resume bullet for this project is actually present and runnable in the repository.

## 10\. Explicitly deferred

* Dockerfile and CI pipeline — deferred to a later phase, after the core pipeline and evaluation are complete and verified.
* Hybrid (keyword + vector) retrieval, reranking, and a labeled precision@k test set — noted as future extensions in the README, not built now.

## 11\. Open questions

* Final UI/UX tooling choice is pending (see DECISIONS.md log for the UI/UX Pro Max conflict to resolve).
* Frontend framework confirmed as React + TypeScript; final component structure to be defined in the TRD.

