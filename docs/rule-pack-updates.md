# Keeping the CDCP rule pack current

How Ophi notices that CDCP changed a document its rules cite, drafts the matching rule update, and
puts it in force only after a named person reviews it.

Code: `ophi/rules/watch.py` (check), `ophi/rules/draft.py` (draft), `ophi/rules/approve.py` (approve),
`ophi/rules/auto.py` (the weekly check on page visits), `ophi/rules/loader.py` (which pack is in force),
the `/rules` review page in `ophi/web/app.py`, and `ophi pack ...` in `ophi/cli.py` for engineers.

Nobody has to run a command. The app checks the sources once a week when someone opens a page, drafts
an update when CDCP changed something relevant, and a person reviews it on the `/rules` page.

## Why

- CDCP publishes rule changes as PDFs and web pages, not as data. Example: the April 2026 factsheet
  retired lab fee codes 99222 and 99333 and replaced them with 99112 and 99113.
- The rule pack (`packs/cdcp/<version>/pack.yaml`) is a hand-written copy of those rules. If CDCP
  changes a rule and the pack does not, Ophi keeps checking cases against the old rule and nothing
  warns anyone.
- Every packet cites the pack version and the content hash of the exact `pack.yaml` bytes it used. So
  a pack is never edited in place. A change always becomes a new dated pack next to the old one, and
  requests checked under the old one stay explainable.

For a clinic reader: Ophi re-reads the CDCP documents its rules come from every week, and looks for new
ones on the CDCP provider pages. When something changes, the board says "A CDCP rule update is waiting
for review." and links to the review page, where a person reads the proposed update and uses it before
it changes how any request is checked.

## The flow

```
a page visit, last check a week old ──► background check ──► status file ──► board line, linked to /rules
       │                                   (or "Check now" on /rules; or `ophi pack check`)
   something relevant pending, no draft waiting ──► draft: packs/cdcp/drafts/<today>/
       │                                   (pack.yaml, sources/, sources.lock.json, draft.json, report.md)
   /rules: a person reads the changes, quotes, dates and impact, ticks each needs-a-person item
       │
"Use this rule update" (or `ophi pack approve`) ──► packs/cdcp/<version>/ + CHANGELOG line
       │
   each request uses the pack in force on its own date; older packs stay as they are
```

### 0. The automatic check

- Any HTML page request (`_render` in the app) calls `auto.maybe_start`. If the status file's last
  attempt is 7 days old or more, or there is none, a background thread runs the check and the page is
  served without waiting. After a failed attempt (nothing could be reached, e.g. the network was down)
  the wait is 1 day, not every visit. The time of the last attempt (`attempted_at`) is kept apart from
  the day of the last good check (`checked_on`, what the board shows). It goes by the real clock, not
  the demo's frozen chart day.
- One check at a time: a lock in the process, plus a `checking_since` marker in the status file, set and
  read under a file lock, so another worker or a restart does not run a second one. A marker older than
  30 minutes is treated as left behind by a dead process.
- The job checks, then drafts if something relevant is pending and no draft of the newest pack is
  waiting. It never uses a draft: only a person does, on `/rules`. When the new documents turn out to
  have nothing for this pack, they are marked seen and the board stops showing them.
- Manual sources (the Sun Life grid) are not fetched, as with the CLI.
- Switch: `create_app(auto_rules_check=...)`. Like `live_ml`, it defaults on only for the app's own
  service without a base path (plain `ophi serve`), following `OPHI_AUTO_RULES_CHECK` (on unless `0`,
  `false`, `off` or `no`); it is off for the proxied public demo and when a caller brings its own service
  (tests). The tests and `scripts/demo-parity.*` also turn it off explicitly, so they never touch the
  network.

### 1. Check

- Each pack version has a baseline: `sources.lock.json` (URL, fingerprint, fetch date per source) and
  `sources/<key>.txt` (the normalized text of each source).
- A check re-fetches every source the newest pack cites, as `ophi-rules-watch/1 (+https://cortico.health)`,
  reading at most 20 MB per document, except sources `watch.yaml` marks `manual: true` (the Sun Life
  grid), which are read only from a local copy given with `--file`. It compares the text, not the bytes: PDFs go through
  `pdftotext -layout` (with a timeout; the error names poppler-utils if it is not installed); HTML is
  reduced to visible text without scripts, nav, footer and the page header (a `<header>` inside
  `<main>` or `<article>` is content and is kept); whitespace is collapsed and canada.ca's "Date
  modified" stamp is dropped, both the `<gcds-date-modified>` element and the older
  `<dl id="wb-dtmd">` footer. The fingerprint is the sha256 of that text. So a republish that only
  changes page chrome or the date stamp is not a change.
- Each source ends up:
  - `unchanged`, or `changed` (with a text diff against the snapshot);
  - `shrank`: the text is under half the baseline's length. It could be a holding page or a gutted
    rewrite, so it is pending and a person decides (`baseline --force` accepts it once read);
  - `unreachable`: a fetch error or an empty page. Never counted as a change;
  - `manual`: a hand-checked source with no local copy this time. The check reports the last day it was
    read.
- `--file <source>=<path>` reads that source from a local copy instead of the web (see "Sun Life grid"
  below). It works on `check`, `draft` and `baseline`.
- It also reads each page in `packs/cdcp/watch.yaml` and lists document links it has not seen before
  (not in the lock's `seen_links` and not already a pack source). A link counts only if it is English,
  on a dental/CDCP URL, and looks like a guide, grid, factsheet, bulletin or update.
- The result goes to `var/rules-watch.json` (the service's var dir, `OPHI_VAR_DIR`), written whole
  (temp file and rename). The board route reads it and shows "Rules checked against CDCP sources on
  <date>.", or "Could not reach N CDCP sources on <date>." only when a fetch genuinely failed (a source
  or a watch page); then "Sun Life grid last checked by hand on <date>." for each manual source; and,
  while something is pending, "CDCP published changes on <date>. A rule update is waiting for review."
  A missing or malformed status file shows no line, never an error page.
- The check compares against the newest pack directory, in force or not: a change is measured against
  what a person last reviewed.

### 2. Draft

The draft is deterministic. It does one thing: find code replacements.

- **Extraction.** On lines a changed source newly says (lines added since the snapshot), and on every
  line of a new document, it looks for `A, B -> C, D`, `→`, `=>`, or "replaced by/with", and pairs
  codes by position. Lines where the codes cannot be paired one to one, or where codes are "retired"
  or "discontinued" with no replacement, go to the needs-a-person list.
- **Crowns-only scope.** `retired_codes` holds lab fee codes only (99xxx to 99xxx; the pack loader
  refuses anything else), because the engine checks only a request's lab codes against it. A 99xxx
  swap is applied. A 27xxx crown code swap, or one touching a code the schedule names, goes to a person
  (the schedule and frequency lists need an engineer's edit). Anything else, such as sedation 922xx, is
  listed as out of scope and not applied.
- **Checks against the pack.** A swap the pack already has is listed as "already in the pack". A swap
  that contradicts the pack (same old code, different new code), or whose new code the pack already
  retires, goes to a person. The pack loader refuses a `retired_codes` list that retires a code twice
  or loops back on itself.
- **Chains.** If a new swap retires a code that was itself a replacement (99222 -> 99112, now
  99112 -> 99122), the older entry is left as it is and the report notes "99222 now resolves to 99122
  through 99112". The engine's retired-code check and Ophi's lab code fix follow the chain to its end
  under the pack in force, so a 99222 request is told to use 99122 from the new pack's date and 99112
  before it. The gap text gives each step its own date: "99222 was replaced by 99112 on 2026-04-01, and
  99112 by 99122 on 2027-04-01".
- **Dated copy.** The April 2026 pack's `lab_codes_current` label and gap text say 2026 is the only
  retirement date. A draft that adds retirements rewrites those two lines to undated wording in the
  new pack; the 2026-01-26 pack's bytes are never edited.
- **Quote verification.** Each applied change cites the exact source line. The quote must be non-empty,
  must be in the source's text, and re-extracting it must give the same old and new code. The draft
  refuses to write otherwise; approve checks all of this again.
- **Effective date.** A date on the change's own line, or else the closest date within 4 lines on a
  line that says "effective", "as of" or "starting". For a changed source, only lines that are new in
  the source count, so an unchanged neighbouring line never dates a new change. None found: the draft
  uses today and asks a person to set `effective_from`. Different dates: it uses the latest and says
  so. Dates approval will refuse are needs-a-person items in the draft too: before today, or on or
  before the superseded pack's `effective_from` (that pack would never be in force). A date of today
  is a needs-a-person item that approval accepts only with `--ack`.
- **Impact.** Every case under `cases/` (except `lookback/`) is assessed with the current pack and
  with the draft. The report lists each case whose verdict, requirement results or first action would
  differ as if the draft applied to it. Once approved, only requests dated on or after its effective
  date use it.
- **Output.** `packs/cdcp/drafts/<today>/` (ignored by git): `pack.yaml` (the old pack with the SME's
  comments kept, `version` set to today, `supersedes`, `effective_from`, `verified_on`, new sources,
  new `retired_codes` lines with `effective_on`), a fresh `sources/` and `sources.lock.json` (a source
  that could not be read keeps its last snapshot and its real `fetched_on`), `draft.json` (the
  needs-a-person items and each snapshot's fingerprint, which approve checks) and `report.md`. A
  source that shrank is a needs-a-person item with its diff in the report.
- If nothing relevant changed, no draft is written. New documents that state only out-of-scope changes
  are added to the pack's `seen_links`, so they stop showing as pending.

### 3. Review and use

On `/rules` (linked from the board line and from Settings) a person sees:

- the last check: its date and each source's state. "Check now" starts the same background check
  (forced, unless one is already running) and returns at once; the page shows "Checking CDCP sources…"
  while it runs;
- the draft waiting for review, from its `draft.json`: each change with its quote and effective date,
  chained codes, out-of-scope swaps and the needs-a-person items;
- "Your open requests": the clinic's own requests not yet with Sun Life, each assessed under the pack in
  force for it and under the draft, with the draft applied only where it covers the request's date of
  service. Each that changes is listed by patient and tooth, linked to the case, in the board's words
  ("Ready to send → Paperwork; would need: Replace lab code 99112 with 99122 (from Apr 1, 2027)"), or
  "None of your open requests change." Beyond 8 rows the rest fold away. The fixture-case impact
  stays in `draft.json` and `report.md` for engineers.

Only the treating dentist can press "Use this rule update" (others see who puts updates into use), and a
request without a chosen actor is refused. Each needs-a-person item has a tick box; the button is enabled
only once every one is ticked, and the server checks it too. The form carries a hash of `draft.json`: if
the draft changed since the page was opened (a re-draft), it is refused and must be reviewed again, so
ticks never carry over. The ticks are the `--ack`, and the changelog records the items with the
dentist's name. It calls the same `approve()` as the CLI; if approve refuses, the page says why. On the
proxied public demo the page is read-only: "Check now" and "Use this rule update" are refused.

Engineers can still read `report.md` and use `ophi pack approve <draft dir> --by "Name" [--ack]`.
Approve refuses when:

- the draft is not under `packs/cdcp/drafts/`, or has no `draft.json`;
- `version` or `supersedes` is not a `YYYY.MM.DD` version, or that version already exists;
- the draft was made from a pack that is no longer the newest one (draft again);
- `effective_from` is not after the superseded pack's (it would never be in force), or is before the
  day of approval; a date of today needs `--ack`;
- a source snapshot differs from the fingerprint `draft.json` recorded when drafting;
- `pack.yaml`'s `effective_from` or its added code changes differ from what `draft.json` says (what the
  review page showed is what goes in force; an engineer who edits `pack.yaml` edits `draft.json` too);
- a retirement it adds cites an unknown source, has no quote, has a quote that is not in the
  snapshot, or has a quote that does not state that change (this catches a hand-edited `replaced_by`);
- needs-a-person items are open, unless `--ack` is given. The acknowledged items go in the changelog.

Then it:

1. builds the new pack under `packs/cdcp/drafts/` (where the loader never looks) with `reviewed_by`
   (quoted; a name with control characters is refused) and `reviewed_on` added, the source snapshots
   and lock, and the parent's `denial_map.yaml`, then renames it to `packs/cdcp/<version>/` in one step,
   so a request never sees half a pack;
2. appends one line to `packs/cdcp/CHANGELOG.md`;
3. deletes the draft and clears the pending flag on the board.

The previous pack directory is not touched.

### 4. In force

Each request is checked under the pack in force on its date of service, as CDCP judges it: the
appointment date when one is booked, else the later of the chart's date and the plan's date (a plan is
written before the chart is read, so usually the chart's date). A plan written 2027-03-20 for a crown
seated 2027-04-15 gets the pack in force on 2027-04-15. See `rules_date` and `pack_for` in
`ophi/rules/loader.py`. The web service, `ophi assess`/`packet`, the eval runner and Ophi's fixes all
resolve the pack this way; the Look-Back judges each past submission under the pack in force on the
day it was sent. Screens that are not about one request (settings, results) show the pack in force on
the chart's day. Before the first pack took effect (2026-04-01) the first pack stands in, since Ophi
holds no older rules.

`pack_in_force(day)` (also named `default_pack`) picks the newest pack whose `effective_from` has
arrived. An approved pack dated in the future waits. The loader notices new pack files, so a running
server picks up an approved pack without a restart. A `pack.yaml` that fails to load is skipped and
logged rather than failing every request; if no pack loads at all, it fails. In the fixture run below, the approved pack takes over on 2027-04-01:

```
approved -> /tmp/claude-1000/pack-watch-docs/cdcp/2026-09-26
  in force 2026-09-26: 2026.01.26
  in force 2027-03-31: 2026.01.26
  in force 2027-04-01: 2026.09.26
```

## Commands

Run from the repo root.

| Command | What it does | Writes |
|---|---|---|
| `ophi pack check [--file source=path]` | Check sources and watch pages; print diffs of changed sources | `var/rules-watch.json` |
| `ophi pack draft [--file source=path]` | Check, then draft an update if anything relevant changed | `var/rules-watch.json`, `packs/cdcp/drafts/<today>/` |
| `ophi pack approve <draft_dir> --by "Name" [--ack]` | Turn a reviewed draft into a new pack | `packs/cdcp/<version>/`, `CHANGELOG.md`; deletes the draft |
| `ophi pack baseline [--note "..."] [--force] [--file source=path]` | Re-fetch everything now and record it as the newest pack's baseline. Refuses while a change is pending unless `--force`; prints which snapshots it replaced; clears pending only if every source was reached | newest pack's `sources.lock.json` and `sources/` |

The app runs the check itself (see "The automatic check"); these commands stay for engineers.

`ophi pack check` against the fixtures (every source fetched), with CDCP's providers page listing a new
April 2027 factsheet:

```
check: pack 2026.01.26 against 4 sources — 0 changed, 0 shrank, 1 new documents, 0 unreachable
  unchanged   matrix
  unchanged   guide
  unchanged   grid
  unchanged   factsheet
  new         Factsheet on CDCP Guide and Grids updates, April 2027  https://www.canada.ca/en/services/benefits/dental/dental-care-plan/providers/fact-sheet-guide-grids-april-2027.html
```

The live check on 2026-09-26, with the grid checked by hand:

```
check: pack 2026.01.26 against 4 sources — 0 changed, 0 shrank, 0 new documents, 0 unreachable
  unchanged   matrix
  unchanged   guide
  manual      grid       checked by hand; last read 2026-09-26 (pass --file grid=<path>)
  unchanged   factsheet
```

`ophi pack draft` then prints `draft: <dir>  N changes, N need a person, N out of scope, N cases
change` and points to `report.md`. The fixture's report, shortened:

```
# Draft rule pack 2026.09.26

Drafted 2026-09-26 from a source check of pack 2026.01.26. Effective from 2027-04-01. Nothing applies
until a person approves it with `ophi pack approve <this dir> --by "Name"` (add `--ack` to approve with
needs-a-person items open).

## Changes in this draft

- 99112 -> 99122 (effective 2027-04-01)
  - factsheet_2026_09_26: "Lab fee codes billed with crowns are replaced, effective April 1, 2027: 99112, 99113 → 99122, 99123"
- 99113 -> 99123 (effective 2027-04-01)
  - factsheet_2026_09_26: "Lab fee codes billed with crowns are replaced, effective April 1, 2027: 99112, 99113 → 99122, 99123"

Older replacements follow the new code (the engine and Ophi's lab code fix follow the chain):

- 99222 now resolves to 99122 through 99112
- 99333 now resolves to 99123 through 99113

## Needs a person

None.

## Out of scope for the crowns pack (not applied)

- 92211 -> 92215 (effective 2027-04-01)
  - factsheet_2026_09_26: "Sedation codes 92211, 92212 replaced by 92215, 92216"
- 92212 -> 92216 (effective 2027-04-01)
  - factsheet_2026_09_26: "Sedation codes 92211, 92212 replaced by 92215, 92216"

## Impact

42 of 50 cases change.

- adversarial/fully_ready.yaml: verdict READY_TO_SUBMIT -> BLOCKED; lab_codes_current satisfied -> unsatisfied; first action "none" -> "Replace retired lab fee code"
- demo/fontaine.yaml: verdict READY_TO_SUBMIT -> BLOCKED; lab_codes_current satisfied -> unsatisfied; first action "none" -> "Replace retired lab fee code"
- ...
```

The denture-liner row in the same factsheet states no code replacement, so it is not in the draft.
When a changed source says something like that, the draft lists it as "read the diff".

The CHANGELOG line approve writes:

```
- 2026-09-26: 2026.09.26 (effective 2027-04-01, from 2026.01.26) reviewed by Dr. Test Reviewer: 99112 -> 99122, 99113 -> 99123
```

To see all of this without touching the real packs or the network:

```
PYTHONPATH=. .venv/bin/python scripts/pack-watch-fixture.py /tmp/<scratch dir> [--approve "Name"]
```

It copies the current pack to the scratch dir and serves the fixtures in `fixtures/pack_watch/`
(a providers page and a fake April 2027 factsheet) in place of the real sites. The fake web is
`ophi/rules/fixture_web.py`, which the pack watch tests use too.

`scripts/rules-review-serve.py <scratch dir> <port>` serves the app with the fixture draft waiting on
`/rules`. `scripts/rules-auto-live.sh <base url> <var dir>` shows a live on-visit check: with the status
file backdated, one page visit starts it and the board then shows today's date.

`scripts/demo-parity.sh <scratch dir> [ref]` renders every demo page from this tree and from `ref`
(default `main`), each with a fresh var dir, and diffs them.

## Where files live

| File | Purpose |
|---|---|
| `packs/cdcp/<YYYY-MM-DD>/pack.yaml` | A pack version. Never edited after it is in use. |
| `packs/cdcp/<version>/sources.lock.json` | Baseline: URL, sha256 of normalized text, fetch date per source; `seen_links` from the watch pages; optional `note` |
| `packs/cdcp/<version>/sources/<key>.txt` | Normalized text snapshot per source, used for diffs and quote checks |
| `packs/cdcp/watch.yaml` | CDCP pages scanned for new documents; sources checked by hand (`manual: true`) |
| `packs/cdcp/drafts/<YYYY-MM-DD>/` | Draft awaiting review, with `draft.json` (its needs-a-person items); one per day, a re-draft the same day replaces it; ignored by git |
| `packs/cdcp/CHANGELOG.md` | One line per approved version |
| `var/rules-watch.json` | Latest check result for the board: `checked_on`, `pending`, `found_on`, changed keys, new links, unreachable, each manual source's last hand check, each source's state, and the automatic check's `attempted_at`, `last_error` and `checking_since` |

## What it does not do

- **No language model.** Extraction is pattern matching. It extracts code replacements and nothing
  else. A new requirement, a changed frequency limit, a new document rule: all of these show up only
  as a diff or a "read it" item for a person.
- **"Published on" means found on.** The board's "CDCP published changes on <date>" is the day a
  check first saw the change, kept until someone reviews it. It is not CDCP's publication date.
- **The current baseline is newer than the pack's review.** Pack 2026.01.26 was verified on
  2026-09-17, but its lock was taken on 2026-09-26 (the lock's `note` says so). A change CDCP made
  between those days is already in the baseline and will not be flagged.
- **Many existing pack quotes are not verbatim in the sources.** `scripts/pack-quote-audit.py` lists
  every quoted clause in the newest pack and whether it appears in the snapshot it cites. Today 18 are
  missing and 2 match. The draft and approve steps verify quotes only for the swaps they add, not for
  clauses already in the pack.
- **Crown code changes are not drafted.** A 27xxx retirement is a needs-a-person item: the schedule,
  frequency lists and requirement code lists need an engineer's edit.
- **Discovery is limited to the watch pages.** A document CDCP publishes elsewhere, or links only
  from a page rendered by JavaScript (such as Sun Life's grids page), will not be found as new. The
  grid itself is still checked because it is a pack source.
- **Impact is not date-aware.** It shows what would change for every case under the draft; once
  approved, only requests dated on or after the effective date use it.
- **A changed source with only out-of-scope swaps stays pending.** Unlike a new document, it is a
  source the pack cites, so it is not marked seen; re-baseline (`ophi pack baseline --force`) once a
  person has read it.

## Adding a watched page or source

**A watch page** (a page that lists CDCP documents):

1. Run `ophi pack check` and make sure nothing is pending.
2. Add the URL to `pages:` in `packs/cdcp/watch.yaml`.
3. Run `ophi pack baseline --force --note "added <page>"`. The new page's links read as pending until
   they are recorded, hence `--force`. This records them as seen, so they do not all show up as new
   documents. It also re-fetches every source and rewrites the newest pack's lock, which is why step 1
   matters: with `--force`, baseline absorbs any pending change without review.

**A source** (a document the rules cite): sources are listed under `sources:` in `pack.yaml`, so adding
one is a pack change. Do it in a new dated pack version, not in place, then run `ophi pack baseline`
to lock it. A new document found on a watch page that states code replacements is added as a source
by the draft automatically (key like `factsheet_2026_09_26`).

## Sun Life grid

The benefit grid is hosted by Sun Life, behind a bot wall (DataDome). Ophi sends one honest client name
with a contact, `ophi-rules-watch/1 (+https://cortico.health)`, and never poses as a browser (product
owner's decision). So the grid is marked as checked by hand in `packs/cdcp/watch.yaml`:

```yaml
sources:
  grid: { manual: true, label: Sun Life grid }
```

A check does not fetch it. It lists the grid as `manual` with the last day it was read, and the board
says "Sun Life grid last checked by hand on <date>." To check it, download it in a browser and pass the
copy:

```
ophi pack check --file grid=~/Downloads/cdcp-on-gpsp-benefit-grid-2026-e.pdf
```

The copy is compared with the baseline like a fetched document, and the board's date moves to that
day. `--file` also works with `ophi pack draft` and `ophi pack baseline`, and for any source key. The
current baseline's grid text was fetched automatically on 2026-09-26 (Sun Life served that client name
then; curl's default got 403), so "last checked by hand" starts from that date.

To fetch a manual source automatically again, remove its entry from `sources:` in `watch.yaml`.
