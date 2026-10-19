# Design System: Talent Match RAG frontend

Durable visual decisions for the match results surface. The direction is
Operate: a visitor picks a job posting, runs one search, and reads the matches.
That mode is why the surface is restrained rather than expressive, and why
`bolder`, `overdrive`, `delight`, `colorize` and `quieter` are unused here.

**This supersedes the previous version of this file.** That version described a
grey-green datasheet with red annotation, a 0-to-100 track under every reading,
and uppercase mono micro-labels throughout. None of that exists any more. The
palette, layout, typography and motion sections below were rewritten from the
built surface, not adapted from the old text.

## Provenance

The visual design was generated in Google Stitch, reviewed over roughly twenty
iterations against rendered screenshots at 1280px and 390px, then rebuilt as
React components against real API responses. The Stitch HTML was not shipped:
it used Tailwind via CDN and inline styles, and it had no states. Every value
below is expressed as a token in `tokens.css` and a rule in `App.css`.

## Direction

A neutral operations surface. Cards, hairline borders, a white reading surface
on a near-white page, and a dark top bar for the frame. Colour is reserved for
exactly one job: telling the reader whether a skill the posting asked for
appears in the profile. Nothing else is tinted.

Explicitly refused: avatar initials, coloured score badges, gradients, glass,
decorative shadows beyond a 1px hairline, icon sets, and display serif.

## Colors

| Token | Value | Role |
|---|---|---|
| `--page` | `#fafafa` | Page background |
| `--card` | `#ffffff` | Card surface |
| `--bar` | `#0d0f12` | Sticky top bar |
| `--ink` | `#111111` | Primary text |
| `--n50` to `--n300` | `#fafafa` to `#d4d4d4` | Recessed fills, hairlines, chips |
| `--n400` | `#a3a3a3` | **Top bar only.** Repository link. Never text on a card |
| `--n500` | `#737373` | Weakest permitted card text, 11px labels |
| `--n600` | `#525252` | Secondary text, counts, source lines |
| `--n700` | `#404040` | Labels |
| `--n800` | `#262626` | Section headings, body prose |
| `--n900` | `#171717` | Candidate ids, scores, rank badge fill |
| `--hit-bg/bd/ink` | `#ecfdf5` / `#a7f3d0` / `#065f46` | Skill listed in the profile |
| `--gap-bg/bd/ink` | `#fffbeb` / `#fde68a` / `#92400e` | Job skill absent from the profile |
| `--focus` | `#2563eb` | Focus ring, top bar mark |
| `--mark` | `#3b82f6` | Top bar logo square |

### Contrast, measured from rendered pixels

Every value below was read out of the running page at 1280px and recomputed,
not derived from the token by eye. 32 text pairs were sampled.

| Pair | Ratio | Need |
|---|---|---|
| ink on card | 18.88:1 | 4.5 |
| n900 on card | 17.93:1 | 4.5 |
| n900 score on card | 17.93:1 | 3.0 (24px) |
| n700 label on card | 10.37:1 | 4.5 |
| n700 jobbrief body on n50 | 9.93:1 | 4.5 |
| n800 body on card | 15.13:1 | 4.5 |
| n800 section heading on page | 14.50:1 | 4.5 |
| n600 on card | 7.81:1 | 4.5 |
| n600 on page | 7.49:1 | 4.5 |
| hit ink on hit bg | 7.68:1 | 4.5 |
| gap ink on gap bg | 7.09:1 | 4.5 |
| n500 on card | 4.74:1 | 4.5 |
| n500 on page | 4.54:1 | 4.5 |
| n400 on bar | 7.61:1 | 4.5 |
| brand name on bar | 17.60:1 | 4.5 |
| white on ink button | 17.85:1 | 4.5 |
| white on n900 rank badge | 17.93:1 | 4.5 |

**`--n400` is the trap.** It measures 7.61:1 on the dark bar and **2.52:1** on a
white card. It is used for the repository link and nowhere else. Text on a card
never goes below `--n500`.

### Focus ring

`#2563eb` at 2px with a 2px offset, applied via `:focus-visible`. It measures
3.71:1 against `--bar` and 3.45:1 against the ink button, so it clears the 3:1
non-text requirement on both the light and dark surfaces without needing a
contrasting offset colour. The previous design used an ink ring with a
sheet-coloured offset precisely because ink on ink was invisible; the blue
accent removes that problem.

### Why the previous red-annotation rule is gone

The earlier system reserved one red for annotation so it could never be
mistaken for the error colour. There is no annotation layer now: the reading is
the score, and the score is set in `--n900`. Error, focus, and the primary
action are all carried by ink, blue and the notice card respectively, so no
colour is overloaded and the rule has no work left to do.

## Typography

Inter for the interface and prose, JetBrains Mono for identifiers, values,
counts and labels. Both are loaded from Google Fonts. This reverses the earlier
decision to use system stacks only; see DECISIONS.md D17 for why, and for the
weight that decision costs.

| Size | Use |
|---|---|
| 11px | Uppercase mono row labels, rationale label, disclosure summary, source line |
| 12px | Scores caption, counts, chips, metadata |
| 13px | Sentence-case labels |
| 14px | Body, controls |
| 16px | Card candidate id, job title |
| 22px | Page title only |

Sizes are written as literal values in `App.css` rather than held in tokens.
An earlier pass declared a six-step type scale in `tokens.css` and then never
referenced it, which left six tokens that no rule read. They were deleted rather
than wired up: a scale used at exactly one call site each is indirection, not a
system. The table above is the record of the scale.

The previous rule held an 11px floor for functional labels, because anything
smaller fails on high-DPI displays and small viewports. That floor still holds:
the smallest text on the surface is 11px.

Numerals in tabular data use `font-variant-numeric: tabular-nums` so score
columns align.

### The uppercase mono exception

Six labels were sentence-case sans in an earlier iteration of this design and
read as too quiet. The three skill-comparison row labels are now deliberately
**uppercase mono**, while every other label is sentence-case sans. This is an
exception, not an inconsistency: the three sit in one fixed 96px column and
have to read as a single aligned group, which uppercase mono does and sentence
case does not.

The rationale label ("Why this profile") also returned to uppercase mono on
review. All other labels are sentence case.

## Layout

- Page capped at **1280px**, centred, padding `24px 16px 64px`, rising to
  `24px 24px 64px` at 640px.
- Grid is **12 columns**. The job rail spans 4 and is `position: sticky` at
  `top: 64px` from 1024px up. Results span 8. Below 1024px they stack.
- Cards: `1px` border, `8px` radius, no shadow beyond a 1px hairline.
- **The score drops to its own row below 640px.** The caption "match score, out
  of 100" measures about 158px wide in mono at 12px; side by side with the
  identity block it left roughly 70px for the candidate id at 390px and broke
  the experience chip across two lines. Measured, then fixed.
- Verified at 1280px and 390px: zero horizontal overflow at both, in the initial
  state and the results state.

## Motion

| Moment | Property | Duration | Easing |
|---|---|---|---|
| Record entrance | opacity, translateY(6px) | 220ms | `cubic-bezier(0.23, 1, 0.32, 1)` |
| Record stagger | 40ms per record | | |
| Card hover border | `border-color` | 160ms | same |

Rules held: only `transform`, `opacity` and `border-color` animate; no
`transition: all`; nothing over 300ms; hover is gated behind
`@media (hover: hover) and (pointer: fine)`; `prefers-reduced-motion` collapses
all durations to 0.01ms.

The record entrance animates `transform` and `opacity` from a
`translateY(6px)` start, so the fill width is never an animated layout property.

## Components

- **Select**: native control, not reinvented. Disabled state uses `--n100`
  with a not-allowed cursor.
- **Button**: ink fill (`#0f172a`) when actionable, `--n100` and `--n500` when
  not. Kept in the tab order while a search runs, via `aria-disabled`, so a
  keyboard user does not lose focus for up to a minute on a cold start.
- **Skill chips**: one component, three meanings, carried entirely by colour
  and one glyph: green tick (listed), amber cross (not listed), plain grey (other
  skills, and the job's own required list). Chips are `white-space: nowrap` and
  `flex: none` so a long name never wraps mid-chip.
- **Disclosure**: native `<details>` with a monospace `+` / `-` text marker,
  because the native marker is suppressed.

### Non-interactive chips

The job's required-skill list and the "Other skills" chips are data, not
controls. They carry no hover rule, no pointer cursor, and no `tabindex`, so
they are absent from the tab order. The job's list uses `<ul>` with
`aria-labelledby` pointing at its own heading.

The job's own skill list is deliberately **neutral grey**, not blue. Blue in
this palette means "found on a profile", and tinting the job's list the same
way would make the two indistinguishable at a glance.

## States

Loading renders five skeleton cards plus a wait notice carrying a live
elapsed-seconds readout. The readout's counter is `aria-hidden`, because inside a
live region a counter that ticks every second re-announces the whole sentence
once a second for as long as the notice is on screen. The counter is
`role="status"`. At 3 seconds the copy changes from "retrieving" to "still
working, this service sleeps when nobody is using it". It does not claim the
service *was* idle: at that point all that is known is that the request is slow.

The job-list load uses the same notice card and sits above the skeletons, so the
loading surface reads as one thing. While it is in flight the job select reads
"Loading jobs", not "No jobs loaded", which states a conclusion the page has not
reached.

Error states name the problem and the recovery in the visitor's language, use
`role="alert"`, and carry a retry action. No environment variable names, no
instructions to run the ingest.

**A server-side fault never shows the server's own wording.** The backend
reports pipeline failures in terms that name internal things, such as the
database index and its namespace. That text goes to the browser console for
whoever is debugging and is not put on screen. A 500 renders as the heading and
the recovery line with no detail block at all. A 404 still shows a message,
because a missing job is something the visitor can act on.

Empty states teach the interface and both offer an action.

**Partial results.** A candidate whose generation failed still shows its real
similarity score, its skill breakdown, and its profile disclosure. Only the
written explanation is replaced by an explicit statement that none could be
produced. A note above the results states how many were affected. Verified by
intercepting a real response with two rationales nulled: five records, five
scores, five breakdowns, two unavailable panels, one note, zero page errors.

Candidate profiles load in parallel with the search and deliberately do not
gate the reveal. Both requests hit the same backend, so on a cold start they
wake it together.

**A failed profile load is announced, never absorbed.** If `/candidates` fails,
each record says "Profile details could not be loaded, so this record shows its
score and explanation only" in place of the skill breakdown, a note above the
results says so, and the results header drops its "of N profiles" clause rather
than substituting a number it never received. The earlier build swallowed that
failure, which stripped every profile detail off every card while the page still
looked complete, and printed a corpus total derived from the request parameter.
Verified by routing `/candidates` to a 500: header reads "Showing 5 matches.",
all five scores and explanations intact, and the omission is stated.

Until a profile lands, its role chip, meta line, skill breakdown and disclosure
are omitted rather than rendered as placeholders.

## Accessibility

WCAG 2.1 AA is the committed target. Verified on the built surface:

- 32 text pairs measured from rendered pixels, 0 failures.
- Focus ring 2px `#2563eb` with 2px offset on every focusable element.
- **8 tab stops**, in document order: repository link, job select, Find matches,
  then one disclosure summary per record. No positive `tabindex` anywhere, so
  nothing hijacks the sequence.
- One new stop exists relative to the previous design: the repository link in
  the top bar, required by the corrected URL.
- `aria-live`: `role="status"` for waits and loading, `role="alert"` for
  failures. `aria-busy` is not set on an ancestor of a live region.
- The results section is labelled by its heading; each record is labelled by
  its candidate id; the job skill list is labelled by its own heading.
- Heading order is `h1` (page title) to `h2` (section) to `h3` (card ids).
- Zero console or page errors in every state at both widths.

## Known limitations

- Dark mode is not implemented. The token set is light-surface only and adding
  dark mode is a decision, not a toggle.
- **No automated test suite exists.** The contrast, layout, keyboard and state
  checks recorded here were run with a Playwright script, not as a test that
  runs in CI. Nothing prevents these strings and tokens from regressing.
  Deferred by explicit decision.
- Google Fonts is a third-party request and adds roughly 180 KB of font data.
  Self-hosting or reverting to system stacks would remove it.
- The rationale text carries no emphasis. The Stitch mockups bolded skill names
  inside the explanation, but that markup was hand-authored. Reproducing it
  against model-written text would require a heuristic, and a heuristic that
  bolds a skill name would also bold it inside a clause that denies it, for
  example "the candidate does not list Docker". Emphasis is therefore not
  applied, and the reason is recorded at the rule in `App.css`.
