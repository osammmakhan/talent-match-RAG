import {
  ApiError,
  type Candidate,
  type Job,
  type MatchResponse,
} from "./types";

const BASE = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

/**
 * Match requests get the long budget because the free hosting tier sleeps when
 * idle and takes roughly a minute to wake. Reads use the same budget: a cold
 * start can make the very first GET /jobs miss a short timeout, which would
 * greet the visitor with an error instead of a wait.
 */
const REQUEST_TIMEOUT_MS = 90_000;

async function request<T>(
  path: string,
  init: RequestInit,
  timeoutMs: number,
): Promise<T> {
  const controller = new AbortController();
  const onAbort = () => controller.abort();
  init.signal?.addEventListener("abort", onAbort);
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);

  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, { ...init, signal: controller.signal });
  } catch (cause) {
    if (init.signal?.aborted) throw cause;
    if (timedOut) {
      throw new ApiError(
        "timeout",
        `No response within ${timeoutMs / 1000} seconds.`,
      );
    }
    throw new ApiError(
      "network",
      cause instanceof Error ? cause.message : "The request failed.",
    );
  } finally {
    clearTimeout(timer);
    init.signal?.removeEventListener("abort", onAbort);
  }

  if (response.status === 404) {
    throw new ApiError("notfound", "The service does not have that record.");
  }
  if (!response.ok) {
    const detail = await readDetail(response);
    if (response.status >= 500 || !isPresentable(detail)) {
      /* Withheld from the screen: a server fault names internal things such as
         the database index, and an infrastructure 4xx can carry a whole HTML
         page. The text goes to the console for whoever is debugging. */
      console.warn(
        `Server error ${response.status}: ${detail || "(empty body)"}`,
      );
      throw new ApiError("server", "");
    }
    throw new ApiError(
      "server",
      detail || `The service could not complete that request.`,
    );
  }
  try {
    return (await response.json()) as T;
  } catch {
    /* The network worked and the service answered; only the reply was
       unreadable. Reporting that as a network fault names the wrong cause. */
    throw new ApiError(
      "server",
      "The service sent a reply this app could not read.",
    );
  }
}

/** True when a body is short enough to be a message rather than a page dump. */
function isPresentable(detail: string): boolean {
  return Boolean(detail) && detail.length <= 200 && !detail.includes("<");
}

/**
 * FastAPI wraps errors as {"detail": "..."}. Printing that envelope put raw
 * JSON in front of the visitor, so the message is unwrapped when it parses.
 * Anything that does not parse is shown as sent.
 */
async function readDetail(response: Response): Promise<string> {
  const raw = (await response.text().catch(() => "")).trim();
  if (!raw.startsWith("{")) return raw;

  try {
    const parsed = JSON.parse(raw) as { detail?: unknown };
    return typeof parsed.detail === "string" ? parsed.detail.trim() : raw;
  } catch {
    return raw;
  }
}

export function fetchJobs(signal: AbortSignal): Promise<Job[]> {
  return request<Job[]>(
    "/jobs",
    { method: "GET", signal },
    REQUEST_TIMEOUT_MS,
  );
}

export function fetchCandidates(signal: AbortSignal): Promise<Candidate[]> {
  return request<Candidate[]>(
    "/candidates",
    { method: "GET", signal },
    REQUEST_TIMEOUT_MS,
  );
}

export function fetchMatches(
  jobId: string,
  topK: number,
  signal: AbortSignal,
): Promise<MatchResponse> {
  return request<MatchResponse>(
    `/match/${encodeURIComponent(jobId)}?top_k=${topK}`,
    { method: "POST", signal },
    REQUEST_TIMEOUT_MS,
  );
}
