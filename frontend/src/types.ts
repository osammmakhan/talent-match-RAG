export interface Job {
  id: string;
  title: string;
  required_skills: string[];
  min_years_experience: number;
  location: string;
  summary: string;
}

export interface Candidate {
  id: string;
  title: string;
  skills: string[];
  years_experience: number;
  location: string;
  summary: string;
}

export interface MatchResult {
  candidate_id: string;
  similarity_score: number;
  rationale: string | null;
}

export interface MatchResponse {
  job_id: string;
  job_title: string;
  matches: MatchResult[];
}

export type FailureKind = "notfound" | "server" | "network" | "timeout";

export class ApiError extends Error {
  readonly kind: FailureKind;

  constructor(kind: FailureKind, message: string) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
  }
}
