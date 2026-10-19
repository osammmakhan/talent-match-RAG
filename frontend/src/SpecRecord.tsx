import type { Candidate, Job, MatchResult } from "./types";

interface SpecRecordProps {
  match: MatchResult;
  candidate: Candidate | undefined;
  job: Job | undefined;
  /** Three states, not two. "Not loaded yet" and "failed to load" are
      different facts and the surface used to report the second while the first
      was still true. */
  candidatesState: "idle" | "ready" | "failed";
  index: number;
}

interface SkillSplit {
  listed: string[];
  notListed: string[];
  other: string[];
}

/**
 * Compare the job's required skills with the profile's skill list.
 *
 * "notListed" means the skill is absent from the profile record. It does not
 * mean the person lacks it, which is why the interface says the skill is not
 * listed on the profile rather than using a word that reads as a gap in the
 * person. The comparison is a set intersection of two lists the API already
 * returns; nothing is inferred and nothing is generated.
 */
function splitSkills(job: Job | undefined, candidate: Candidate | undefined): SkillSplit {
  const split: SkillSplit = { listed: [], notListed: [], other: [] };
  if (!candidate) return split;

  const owned = new Set(candidate.skills.map((skill) => skill.toLowerCase()));
  const required = job ? job.required_skills : [];

  for (const skill of required) {
    if (owned.has(skill.toLowerCase())) {
      split.listed.push(skill);
    } else {
      split.notListed.push(skill);
    }
  }

  const requiredKeys = new Set(required.map((skill) => skill.toLowerCase()));
  split.other = candidate.skills.filter(
    (skill) => !requiredKeys.has(skill.toLowerCase()),
  );

  return split;
}

export function SpecRecord({ match, candidate, job, candidatesState, index }: SpecRecordProps) {
  const { listed, notListed, other } = splitSkills(job, candidate);

  /* A cosine similarity runs 0 to 1. Anything outside that is not a weak match,
     it is an unreadable value, and printing it as 0.0 would state that the
     candidate is a total mismatch when nothing was measured at all. Clamping an
     out-of-range value to 100.0 was worse: it claimed a perfect match. */
  const raw = match.similarity_score;
  const measured =
    typeof raw === "number" && Number.isFinite(raw) && raw >= 0 && raw <= 1;

  return (
    <article
      className="record"
      style={{ animationDelay: `${index * 40}ms` }}
      aria-labelledby={`h-${match.candidate_id}`}
    >
      <div className="record-head">
        <div className="ident">
          <span className="rank" aria-hidden="true">
            #{index + 1}
          </span>
          <div>
              <div className="idline">
                <h3 id={`h-${match.candidate_id}`} className="cid">
                  {match.candidate_id}
                </h3>
              {candidate && (
                <span className="rolechip">{candidate.title}</span>
              )}
            </div>
            {candidate && (
              <p className="sub">
                <span className="expchip">
                  {candidate.years_experience} yrs experience
                </span>
                <span className="dot" aria-hidden="true">
                  &bull;
                </span>
                <span className="where">{candidate.location}</span>
              </p>
            )}
          </div>
        </div>

        <div className="score">
          {measured ? (
            <>
              <p className="score-num">{(raw * 100).toFixed(1)}</p>
              <p className="score-cap">match score, out of 100</p>
            </>
          ) : (
            <>
              <p className="score-none">Score unavailable</p>
              <p className="score-cap">
                the response carried no readable value
              </p>
            </>
          )}
        </div>
      </div>

      <div className="why">
        <p className="why-label">Why this profile</p>
        {match.rationale ? (
          <p className="why-body">{match.rationale}</p>
        ) : (
          /* Short on purpose. The page-level note above the results already
             says the scores are unaffected, and repeating it on every card
             turned one fact into six. */
          <p className="rationale-missing">
            No written explanation could be produced for this profile.
          </p>
        )}
      </div>

      {candidate ? (
        job && (
          <div className="breakdown">
            <div className="row">
              <span className="row-label hit" id={`skills-listed-${match.candidate_id}`}>Listed</span>
              <ul className="row-chips" aria-labelledby={`skills-listed-${match.candidate_id}`}>
                {listed.length === 0 ? (
                  <li><span className="tag tag-rest">none of these listed</span></li>
                ) : (
                  listed.map((skill) => (
                    <li key={skill}>
                      <span className="tag tag-hit">
                        <span className="tag-mark" aria-hidden="true">
                          &#10003;
                        </span>
                        {skill}
                      </span>
                    </li>
                  ))
                )}
              </ul>
            </div>

            <div className="row">
              <span className="row-label gap" id={`skills-gap-${match.candidate_id}`}>Not listed</span>
              <ul className="row-chips" aria-labelledby={`skills-gap-${match.candidate_id}`}>
                {notListed.length === 0 ? (
                  <li><span className="tag tag-rest">all listed</span></li>
                ) : (
                  notListed.map((skill) => (
                    <li key={skill}>
                      <span className="tag tag-gap">
                        <span className="tag-mark" aria-hidden="true">
                          &#10005;
                        </span>
                        {skill}
                      </span>
                    </li>
                  ))
                )}
              </ul>
            </div>

            {other.length > 0 && (
              <div className="row row-other">
                <span className="row-label rest" id={`skills-other-${match.candidate_id}`}>Other skills</span>
                <ul className="row-chips" aria-labelledby={`skills-other-${match.candidate_id}`}>
                  {other.map((skill) => (
                    <li key={skill}>
                      <span className="tag tag-rest">{skill}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )
      ) : candidatesState === "failed" ? (
        /* Only when it actually failed. While the profile list is still in
           flight this renders nothing at all, because "could not be loaded" is
           a claim about the future and the card fills in a moment later. */
        <div className="why">
          <p className="why-label">Profile details</p>
          <p className="why-body">Not available for this record.</p>
        </div>
      ) : null}

      {candidate && (
        <details className="profile">
          <summary>Candidate summary</summary>
          <div className="profile-body">
            <p>{candidate.summary}</p>
            <p className="profile-src">from candidates.json, {candidate.id}</p>
          </div>
        </details>
      )}
    </article>
  );
}
