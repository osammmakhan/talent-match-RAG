import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fetchCandidates, fetchJobs, fetchMatches } from "./api";
import { JobPicker } from "./JobPicker";
import { SpecRecord } from "./SpecRecord";
import { EmptyState, ErrorState, SkeletonRecords, WaitNotice } from "./states";
import {
  ApiError,
  type Candidate,
  type FailureKind,
  type Job,
  type MatchResponse,
} from "./types";
import "./App.css";

const TOP_K = 5;
const COLD_START_AFTER_S = 3;
const REPO_URL = "https://github.com/osammmakhan/talent-match-RAG";
const REPO_LABEL = "github.com/osammmakhan/talent-match-RAG";

type LoadState = "loading" | "ready" | "failed";

export default function App() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobsState, setJobsState] = useState<LoadState>("loading");
  const [selectedId, setSelectedId] = useState("");
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [candidatesState, setCandidatesState] = useState<"idle" | "ready" | "failed">("idle");

  const [response, setResponse] = useState<MatchResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [failure, setFailure] = useState<{
    kind: FailureKind;
    message: string;
  } | null>(null);

  const candidatesById = useMemo(
    () => new Map(candidates.map((candidate) => [candidate.id, candidate])),
    [candidates],
  );

  const pending = useRef<AbortController | null>(null);

  /* Named so the failure state can retry the job list. Wiring the job-list
     error's Try again to run() looked right and did nothing: with no job
     selected, run() returns before issuing any request. */
  const loadJobs = useCallback((signal: AbortSignal) => {
    fetchJobs(signal)
      .then((loaded) => {
        setJobs(loaded);
        setSelectedId((current) => current || loaded[0]?.id || "");
        setJobsState("ready");
        setFailure(null);
      })
      .catch((cause: unknown) => {
        if (signal.aborted) return;
        setJobsState("failed");
        setFailure(toFailure(cause));
      });
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    loadJobs(controller.signal);
    return () => controller.abort();
  }, [loadJobs]);

  useEffect(() => () => pending.current?.abort(), []);

  useEffect(() => {
    if (!running) return;
    const started = Date.now();
    const id = window.setInterval(
      () => setElapsed(Math.round((Date.now() - started) / 1000)),
      1000,
    );
    return () => window.clearInterval(id);
  }, [running]);

  /* The job the current results were actually searched for. Must not be the
     selected job: changing the picker re-labels the rail without re-running
     the search, and feeding the new job's skills into the old results printed a
     measured comparison between two documents nobody searched together. */
  const searchedJob = useMemo(
    () => jobs.find((job) => job.id === response?.job_id),
    [jobs, response],
  );

  /* The job the picker is on. Drives the rail, and is named in the note that
     appears when it no longer matches the results. */
  const selectedJob = useMemo(
    () => jobs.find((job) => job.id === selectedId),
    [jobs, selectedId],
  );

  /* The job the results belong to. Falls back to the title the API returned,
     so a job id that no longer resolves locally still names the search rather
     than silently dropping the name. */
  const searchedJobLabel = searchedJob
    ? `${searchedJob.title}, ${searchedJob.location}`
    : (response?.job_title ?? "");

  const run = useCallback(() => {
    if (!selectedId || pending.current) return;
    const controller = new AbortController();
    pending.current = controller;
    setRunning(true);
    setElapsed(0);
    setFailure(null);
    setResponse(null);

    // The profile lookup runs in parallel and updates state when it lands; it
    // deliberately does not gate the reveal. Both requests hit the same
    // backend, so on a cold start they wake it together and the records arrive
    // with their profiles. A shorter budget here used to strip the profiles
    // off exactly the slow path the wait notice advertises.
    if (candidates.length === 0) {
      fetchCandidates(controller.signal)
        .then((loaded) => {
          setCandidates(loaded);
          setCandidatesState("ready");
        })
        .catch(() => {
          // Never swallowed. A silent failure here used to strip every profile
          // detail off every card while the page still looked complete, and the
          // header went on to print a corpus total it had never received.
          if (!controller.signal.aborted) setCandidatesState("failed");
        });
    }

    fetchMatches(selectedId, TOP_K, controller.signal)
      .then((result) => setResponse(result))
      .catch((cause: unknown) => {
        if (controller.signal.aborted) return;
        setFailure(toFailure(cause));
      })
      .finally(() => {
        pending.current = null;
        setRunning(false);
      });
  }, [selectedId, candidates]);

  const coldStart = elapsed >= COLD_START_AFTER_S;
  const shownCandidates = candidates.length;
  const incompleteCount = (response?.matches ?? []).reduce(
    (total, match) => (match.rationale === null ? total + 1 : total),
    0,
  );

  /* True when the picker has moved on but the results have not. Both jobs stay
     on screen at once, so the surface says so rather than letting the rail's
     job details sit next to another job's matches. */
  const resultsAreStale =
    Boolean(response) && Boolean(selectedId) && selectedId !== response?.job_id;

  /* Spoken once, when results land. The card text itself is not a live region:
     announcing five cards' prose would be far worse than announcing the count.
     The corpus clause is included only once the profile list has arrived, so on
     a cold start the cards filling in later is announced rather than silent. */
  const announcement =
    !running && response
      ? `${response.matches.length} ${
          response.matches.length === 1 ? "match" : "matches"
        } found${searchedJobLabel ? ` for ${searchedJobLabel}` : ""}.${
          shownCandidates > 0
            ? ` Searched ${shownCandidates} profiles.`
            : " Profile details are still loading."
        }${
          incompleteCount > 0
            ? ` ${incompleteCount} could not be given a written explanation.`
            : ""
        }`
      : "";

  return (
    <>
      <header className="topbar">
        <div className="topbar-in">
          <div className="brand">
            <span className="brand-mark" aria-hidden="true">
              <span />
            </span>
            <span className="brand-name">Talent Match RAG</span>
          </div>
          <a
            className="repo"
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
          >
            {REPO_LABEL}
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
              />
            </svg>
          </a>
        </div>
      </header>

      <main className="page">
        <section className="intro">
          <h1>See how retrieval and an LLM match candidates to a job.</h1>
          <p>
            Pick a job, and the system finds the closest candidate profiles, then
            explains each match using only facts from the profile. The score
            reflects how similar the wording of a profile is to the job posting.
            It is not a judgement about the person.
          </p>
        </section>

        <div className="grid">
          <JobPicker
            jobs={jobs}
            selectedId={selectedId}
            selectDisabled={jobsState !== "ready"}
            loading={jobsState === "loading"}
            onSelect={setSelectedId}
            onRun={run}
            running={running}
          />

          <section className="results" aria-labelledby="res-h" aria-busy={running || jobsState === "loading"}>
            {/* Always present, so the region's accessible name resolves in the
                empty, loading and error states too. The visible heading below
                only exists once there is something to count. */}
            <h2 id="res-h" className="sr-only">
              Matches
            </h2>

            {/* Always present so the content change is announced. A live region
                mounted together with its own text is unreliable, so this element
                exists from the first render and only its contents change. */}
            <p className="sr-only" role="status">
              {announcement}
            </p>

            {/* Hidden entirely when nothing came back: "Top 0 matches" above
                "No profiles matched this job" reads as a contradiction. */}
            {response && !running && response.matches.length > 0 && (
              <div className="reshead">
                <h2>Top {response.matches.length} {response.matches.length === 1 ? "match" : "matches"}</h2>
                {/* The corpus total only appears when it was actually received.
                    Substituting a request parameter for an unknown count would
                    print a number nothing measured. */}
                <p className="shown">
                  {shownCandidates > 0 ? (
                    <>
                      Showing{" "}
                      <span className="value-mono">{response.matches.length}</span>{" "}
                      of <span className="value-mono">{shownCandidates}</span> profiles
                      {searchedJobLabel && (<>{" "}for {searchedJobLabel}</>)}
                      .
                    </>
                  ) : (
                    <>
                      Showing{" "}
                      <span className="value-mono">{response.matches.length}</span> matches
                      {searchedJobLabel && (<>{" "}for {searchedJobLabel}</>)}
                      .
                    </>
                  )}
                </p>
              </div>
            )}

            {jobsState === "loading" && (
              <div className="stack">
                {/* Same notice card as the search wait, and above the
                    skeletons, so the loading UI reads as one thing rather than a
                    message stranded below five cards. */}
                <div className="wait" role="status">
                  <p className="wait-line">Loading job postings.</p>
                </div>
                <SkeletonRecords count={TOP_K} />
              </div>
            )}

            {jobsState === "failed" && failure && (
              <ErrorState
                kind={failure.kind}
                message={failure.message}
                onRetry={() => loadJobs(new AbortController().signal)}
              />
            )}

            {running && (
              <div className="stack">
                <WaitNotice seconds={elapsed} coldStart={coldStart} />
                <SkeletonRecords count={TOP_K} />
              </div>
            )}

            {!running && failure && jobsState === "ready" && (
              <ErrorState
                kind={failure.kind}
                message={failure.message}
                onRetry={run}
              />
            )}

            {!running && !failure && jobsState === "ready" && !response && (
              <EmptyState
                title="No search run yet"
                body="Choose a job posting and run a search to see the closest profiles, how similar each one is, and why."
                action={{ label: "Run search", onRun: run }}
              />
            )}

            {response && !running && (
              <>
                {resultsAreStale && (
                  <p className="partial-note">
                    These results are for {searchedJobLabel}. The job you have
                    selected is {selectedJob?.title}, {selectedJob?.location}, so
                    run the search again to see its matches.
                  </p>
                )}

                {candidatesState === "failed" && (
                  <p className="partial-note">
                    Profile details could not be loaded, so each result below shows
                    its score and explanation only. Every score and explanation is
                    the value the search actually returned.
                  </p>
                )}

                {incompleteCount > 0 && (
                  <p className="partial-note">
                    {incompleteCount === 1 ? "1 profile" : `${incompleteCount} profiles`}{" "}
                    could not be given a written explanation, so{" "}
                    {incompleteCount === 1 ? "it is" : "they are"} shown by score
                    only. Every score below is still the measured value.
                  </p>
                )}

                {response.matches.length === 0 ? (
                  <EmptyState
                    title="No profiles matched this job"
                    body="The search returned nothing for this posting. Pick another job posting and run the search again."
                  />
                ) : (
                  <div className="stack">
                    {response.matches.map((match, index) => (
                      <SpecRecord
                        key={match.candidate_id}
                        match={match}
                        candidate={candidatesById.get(match.candidate_id)}
                        job={searchedJob}
                        candidatesState={candidatesState}
                        index={index}
                      />
                    ))}
                  </div>
                )}
              </>
            )}
          </section>
        </div>
      </main>

      <footer className="foot">
        <div className="foot-in">
          <p>
            All candidate and job profiles are synthetic. No real people or
            companies are involved. Explanations are written by an LLM using only
            the job posting and the matched profile.
          </p>
        </div>
      </footer>
    </>
  );
}

function toFailure(cause: unknown): { kind: FailureKind; message: string } {
  if (cause instanceof ApiError) {
    return { kind: cause.kind, message: cause.message };
  }
  /* No AbortError branch. request() rethrows one only when the caller's own
     signal aborted, and both callers return early on that, so it cannot reach
     here. Timeouts arrive already wrapped as ApiError("timeout"). */
  return {
    kind: "network",
    message: cause instanceof Error ? cause.message : "Unexpected failure.",
  };
}
