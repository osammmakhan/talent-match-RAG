import type { FailureKind } from "./types";

interface SkeletonRecordsProps {
  count: number;
}

export function SkeletonRecords({ count }: SkeletonRecordsProps) {
  return (
    <div className="stack" aria-hidden="true">
      {Array.from({ length: count }, (_, index) => (
        <div className="skeleton" key={index}>
          <div className="skeleton-head">
            <span className="sk sk-id" />
            <span className="sk sk-val" />
          </div>
          <span className="sk sk-line" />
        </div>
      ))}
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  body: string;
  action?: { label: string; onRun: () => void };
}

export function EmptyState({ title, body, action }: EmptyStateProps) {
  return (
    <div className="notice">
      <h3 className="notice-title">{title}</h3>
      <p className="notice-body">{body}</p>
      {action && (
        <button type="button" className="retry" onClick={action.onRun}>
          {action.label}
        </button>
      )}
    </div>
  );
}

interface ErrorStateProps {
  kind: FailureKind;
  message: string;
  onRetry: (() => void) | undefined;
}

const TITLES: Record<FailureKind, string> = {
  notfound: "That job is not in the index",
  server: "The search could not be completed",
  network: "Cannot reach the search service",
  timeout: "The service did not answer in time",
};

const RECOVERY: Record<FailureKind, string> = {
  notfound: "The posting is not in the search index. Choose a different one from the list above.",
  server:
    "The service reported a problem while searching. This is a fault in the demo, not in your request.",
  network:
    "The service may be starting up, or the address may be wrong. Check the link you opened and try again in a moment.",
  timeout:
    "The service sleeps when nobody is using it and takes about a minute to wake. Try again once it has had time.",
};

/* Retrying the same request cannot change a missing job, so no retry is
   offered there. The recovery line already says what to do instead. */
const RETRYABLE: Record<FailureKind, boolean> = {
  notfound: false,
  server: true,
  network: true,
  timeout: true,
};

export function ErrorState({ kind, message, onRetry }: ErrorStateProps) {
  const showRetry = RETRYABLE[kind] && onRetry;
  return (
    <div className="notice notice-error" role="alert">
      <h3 className="notice-title">{TITLES[kind]}</h3>
      {/* Omitted when the failure carried nothing safe to show. A server-side
          fault is described by the title and the recovery line, and adding the
          API's own wording underneath would only repeat it. */}
      {message && <p className="notice-detail value-mono">{message}</p>}
      <p className="notice-recovery">{RECOVERY[kind]}</p>
      {showRetry && (
        <button type="button" className="retry" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

interface WaitNoticeProps {
  seconds: number;
  coldStart: boolean;
}

export function WaitNotice({ seconds, coldStart }: WaitNoticeProps) {
  return (
    <div className="wait" role="status">
      <p className="wait-line">
        {/* The counter ticks every second. Inside a live region that re-announced
            the whole sentence sixty times, so it is hidden from assistive tech
            and the surrounding sentence announces once when it changes. */}
        <span className="value-mono wait-secs" aria-hidden="true">
          {seconds}s
        </span>
        {coldStart
          ? " Still working. This service sleeps when nobody is using it, so a request made after a pause can take about a minute."
          : " Retrieving candidates and writing a rationale for each."}
      </p>
    </div>
  );
}
