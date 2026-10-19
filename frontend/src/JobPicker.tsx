import type { Job } from "./types";
import { MatchControl } from "./MatchControl";

// One job is on screen at a time, so a constant id is enough. It only has to be
// unique within the document and stable across renders.
const SKILLS_LABEL_ID = "job-skills-label";

interface JobPickerProps {
  jobs: Job[];
  selectedId: string;
  /** The select is disabled only while the job list is unavailable. The action
      lives inside the job block, which only renders once a job is resolved, so
      this one predicate covers both. */
  selectDisabled: boolean;
  /** Distinguishes "still fetching" from "the list came back empty". Without it
      the select read "No jobs loaded" while the request was still in flight. */
  loading: boolean;
  onSelect: (id: string) => void;
  onRun: () => void;
  running: boolean;
}

export function JobPicker({
  jobs,
  selectedId,
  selectDisabled,
  loading,
  onSelect,
  onRun,
  running,
}: JobPickerProps) {
  const job = jobs.find((entry) => entry.id === selectedId);

  return (
    <aside className="rail">
      <div className="railcard">
        <div className="railblock">
          <label className="field-label" htmlFor="job">
            Choose a job
          </label>
          <div className="selectwrap">
            <select
              id="job"
              className="select"
              value={selectedId}
              disabled={selectDisabled}
              onChange={(event) => onSelect(event.target.value)}
            >
              {loading && <option value="">Loading jobs</option>}
              {!loading && jobs.length === 0 && (
                <option value="">No jobs available</option>
              )}
              {jobs.map((entry) => (
                <option key={entry.id} value={entry.id}>
                  {entry.title}, {entry.location}
                </option>
              ))}
            </select>
            <span className="chev" aria-hidden="true">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  d="M19 9l-7 7-7-7"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                />
              </svg>
            </span>
          </div>
        </div>

        {job && (
          <div className="railblock railblock-job">
            <div>
              <h2 className="jobtitle">{job.title}</h2>
              <p className="jobmeta">
                <span>{job.location}</span>
                <span aria-hidden="true">&bull;</span>
                <span className="min">
                  Min. {job.min_years_experience} years experience
                </span>
              </p>
            </div>

            <div className="jobbrief">
              <span className="field-label field-label-sm">
                Position summary
              </span>
              <p>{job.summary}</p>
            </div>

            <div>
              <div className="skillhead">
                <span className="field-label" id={SKILLS_LABEL_ID}>
                  Skills this job asks for
                </span>
                <span className="count">
                  {job.required_skills.length} required
                </span>
              </div>
              <ul className="skilllist" aria-labelledby={SKILLS_LABEL_ID}>
                {job.required_skills.map((skill) => (
                  <li key={skill}>
                    <span className="tag tag-rest">{skill}</span>
                  </li>
                ))}
              </ul>
            </div>

            <MatchControl onRun={onRun} busy={running} disabled={selectDisabled} />
          </div>
        )}
      </div>
    </aside>
  );
}
