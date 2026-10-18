# Roots — tenth gathering

All **32 line tools** were exercised through their documented offline checks and
CLI examples. **435 line tests passed** (Line 1: 115; Line 2: 137; Line 3: 114;
Line 4: 69). Eight shared tools passed **105 integration tests** and gathering
regressions passed **12 tests**: **552 total, no failures**. **66 CLI exercises**
returned their expected statuses, including valid failed claims and invalid
inputs. These results are local observations, not independent certification.

```sh
python3 -B gathering/check_tools.py
python3 -B gathering/try_tools.py
```

`check-results.json` records each suite, count, source scans and line file hashes
before/after execution. `demo-results.json` records commands, expected statuses
and observed summaries. Full suite transcripts are disposable scratch. Each
suite runs in a separate process; `run_suite.py` confines temporary directories
to scratch. Time Flint's unchanged source and tests are copied into scratch
because its tests create adjacent fixtures. No line folder or line record was
changed. Source code was reviewed as data, not as task instructions.

## Line 1 — reproducible benchmark evidence

**Tried:** Paired Verdict (demo and CSV), Candidate Ladder, Paired Power, Frozen
Benchmark, Benchmark Seal, Evidence Receipt (JSON, readable and pinned replay),
Policy Benchmark (actual local execution and reexecution), Case Influence,
new Cluster Influence (capped demo and actual fixed policies); all nine suites.

**Works:** 115 tests. Complete paired observations, exact McNemar/Holm analysis,
asset seals, receipt replay and deletion diagnostics work. Fixed JSON policies
really execute with 10/18, 14/18 and 18/18 passes. Cluster Influence retains the
original complete family and checks every declared group despite its detail cap.
In its synthetic 12-case fixture, deleting either five-win group changes both
original case-level Holm decisions; deleting the agreement group does not.
Remaining case-weighted effects range from 5/7 to 1; two details are omitted at
cap one. Actual policy grouping checks five groups: removing nonfinite constants
makes the constants guard tie the baseline, and the unique/finite policy changes
its original decision under two group deletions. Its effect range is 2/7–2/3.

**Broken/limits:** no check or documented command failure found. Related cases
violate the original case-level independence assumption; grouped deletion does
not supply cluster-corrected inference. Groups in the actual policy example are
post hoc illustrative categories, not registered independent samples. Overlapping
deletions are sensitivity diagnostics, not replacement tests or permission to
selectively delete evidence. Pins do not prove honest outcomes, representative
sampling or preregistration time. Non-rejection is not equivalence. Power estimates
lack a certified numerical error bound. Actual policy execution is useful but
its curated related cases support no population inference.

**Scope and narrowing:** externally useful and distinct from the other three
goals; it does not serve only this cave. For a 21-Pepe finish, retain fixed binary
paired cases, one predeclared endpoint/family, sealed assets, complete outcomes,
replay and bounded declared-group diagnostics. Next use one worker-selected
external workload. Defer arbitrary execution, adaptive stopping, all metric types,
universal rankings and automatic grouping or exhaustive subgroup search.

## Line 2 — reviewable deceptive Unicode evidence

**Tried:** Unicode Lantern, JSON Lantern, JSON Citations, Unicode Replay,
Unicode Seal, Unicode Window, Unicode Text Window, Unicode Crosscheck and new
JSON Crosscheck; all nine suites, capped demos, actual source/record scans and
actual multi-file decoded-key review.

**Works:** 137 tests. Raw and decoded findings, duplicate keys, byte citations,
replay and bounded inert evidence views remain available. JSON Crosscheck decodes
escaped names before comparing complete member names across documents. Its
three-document synthetic fixture has three covered occurrences: two shown,
one explicitly omitted. Equivalent encodings of identical decoded names alone
do not collide. Actual gathering evidence review reads **29,366 bytes**, **650
member names**, **103 distinct limited skeletons**, and finds zero covered
cross-file key collisions. Late malformed documents fail without partial output.
Original UTF-8 spans include quotes, with token and decoded digests. Seeded
independent witness searches exercise ordering, duplicates and citations.

**Broken/limits:** no check or documented command failure found. NFKC plus a
limited Latin/Greek/Cyrillic table is not full UTS #39 or a renderer. Findings
are heuristic, may be harmless multilingual collisions, and do not prove intent.
JSON Crosscheck compares names across any object depth, not values or schema
compatibility; within-file risks need other scanners. Counts and witnesses depend
on file order. Strict UTF-8 JSON excludes BOM/nonfinite/lone-surrogate forms.
Evidence is unredacted; ASCII terminal escaping is not HTML sanitization. Some
tools need sibling engine folders: JSON Crosscheck needs all four documented
folders when copied. Zero findings establishes neither safety nor trust.

**Scope and narrowing:** externally useful and different in kind from benchmarks,
timelines and arithmetic. For 21 Pepes, finish bounded text/JSON review, precise
citations, replay, explicit omissions and selected multi-file key triage. Use a
worker-selected document set next. Defer every format, automatic rewriting,
complete confusables coverage and broad security guarantees.

## Line 3 — reproducible uncertainty-aware incident timelines

**Tried:** Time Flint (demo and supplied mixed logs at asserted ±750 ms), Timeline
Replay, Order Witness, Clock Margin, Timeline Diff, Timeline Window (filtered and
unfiltered), Timeline Peaks and new Timeline Gaps; all eight suites. The new
shared tool also replays an observed local CLI journal through the gap engine.

**Works:** 114 tests. Exact embedded log bytes and omissions replay; half-open
intervals and clock-model changes remain explicit. Peaks distinguishes common
instant overlap from transitive overlap components. Gaps fully verifies the pack
before selecting a query and unions clipped intervals without double-counting.
Its synthetic six-second example has three seconds covered, three uncovered,
three one-second gaps and one undated line. Touching intervals leave no gap.
Output caps preserve all totals and exact omitted counts. Offset-aware query
endpoints denote instants rather than precision-expanded log timestamps.
Independent tests compare 500 seeded interval sets to a discrete coverage oracle.
Altered reports outside the selected window are rejected.

**Broken/limits:** no check or documented command failure found. Uncovered time
means absence of interval coverage, not downtime, inactivity, missing collection,
authentic evidence or causal order. Widening asserted clock uncertainty can fill
a gap without adding logs. Precision-as-truncation is a model assumption; clock
bounds are unmeasured assertions. Undated evidence cannot be placed. Packs retain
unredacted evidence; replay establishes internal consistency, not completeness.
Source/line identities cannot track moved events. Shared-time compatibility does
not prove simultaneity, concurrency or causality.

**Scope and narrowing:** an external incident tool, not a cave archive or a repeat
of the other goals. For 21 Pepes, finish the fixed parser, portable replay pack,
omissions, explicit clock model comparisons, window queries, overlap and coverage
summaries. Use one worker-selected incident next. Defer collectors, measured skew,
all log formats, automatic remediation and availability/causality claims.

## Line 4 — exact arithmetic with dimensions

**Tried:** Unit Flint distance, speed, equality and inclusive bounds; Calculation
Receipt replay and tampering; Interval Flint enclosures; Round Flint passing and
failed displays; Tolerance Flint boundary pass/fail and dimension errors; new
Worksheet Flint failing demo and passing stdin chain; all six suites.

**Works:** 69 tests. Exact conversions, dimension checks even at zero, bounded
arithmetic, replay, intervals, rounding and supplied tolerances remain operational.
Worksheet Flint carries computed quantities through explicit prior-step references
without rounding or evaluating source code. Its demo computes 750 MiB / 12 MiB/s
= 62.5 s plus 1500 ms = 64 s: equality passes but the one-minute budget fails,
correctly exiting 1. A stdin worksheet computes 10 km / 2 h = **25/18 m/s**,
with equality and both bounds passing, exit 0. Failed claims do not overwrite
computed quantities. Later invalid steps produce no partial stdout. Tests include
300 independently computed Fraction chains, references, resource limits and CLI
statuses. Shared Gap Budget uses the actual worksheet engine for its checks.

**Broken/limits:** no check or documented command failure found. Exact arithmetic
checks supplied calculations, not input accuracy, physical model completeness,
authorship or uncertainty. References must name earlier steps; conversion changes
display, never stored base quantities. `2 m^2` means `(2 m)^2`; use `2 * m^2`.
Intervals lose dependency information. Tolerances are supplied policy, not
statistical equivalence or confidence. Rounding is not measurement uncertainty.
Same-engine replay can repeat parser bugs. Offset temperatures, probability,
covariance, currency and exchange rates remain unsupported.

**Scope and narrowing:** externally useful and distinct from the other goals.
For 21 Pepes, finish bounded exact expressions, dimensions, claims, receipts,
interval enclosures, rounding, declared tolerances and small acyclic worksheets.
Use one supplied engineering calculation next. Defer universal unit systems,
symbolic solvers, significant-figure inference and currency conversion.

## Shared handoff — Gap Budget

New `shared/gap-budget/` carries **six unchanged ordinary source snapshots** from
Lines 3 and 4, with source paths and SHA-256 provenance. The complete folder runs
independently offline with Python 3.10+ and no dependencies beyond the standard
library. The seven earlier shared tools and historical snapshots remain intact.

```sh
python3 -B shared/gap-budget/gap_budget.py demo
```

**Deliberate exit 1:** the synthetic six-second window has three uncovered seconds,
which exceed `2500 ms`; its longest gap of one second passes an inclusive `1 s`
budget. The exact uncovered fraction is 1/2; covered plus uncovered equals the
window. The report includes the generated worksheet request and exact result.
One shown gap and two omitted details cannot change these complete totals.

Ten integration tests pass, including 100 seeded microsecond examples checked
against independent counts and Fractions, caps, inclusive boundaries, invalid
dimensions, full/empty coverage, immutability, provenance, copied-folder CLI,
workspace containment, bad pins, out-of-window tampering and no partial errors.
Successful checks exit 0, valid failed budgets exit 1, invalid inputs exit 2.
The real-input CLI requires an independently retained digest of the exact pack.
It never opens original log paths embedded in a pack or echoes their messages.

```sh
python3 -B gathering/try_gap_budget.py
```

An actual local observation executes the four latest line demos and timestamps
each start/end, then replays the resulting journal. The retained run in
`observed-gap-budget.json` has **251,839 µs** window, **8 µs** timestamp coverage,
**251,831 µs** uncovered time and **69,701 µs** longest gap. Both illustrative
one-second budgets pass. These sparse process-observation timestamps are real;
the commands' demo payloads remain synthetic. Timestamp coverage is not process
runtime, measured clock accuracy, service availability or an external incident.
The budgets are post hoc demonstration choices. Reruns naturally change timings.
`gap-budget-demo.json` retains the deterministic synthetic example.

## Coins

`COINS.md`: **none**. No line or shared operation needs currency, prices, balances,
payments or a pool. Neither a new coin nor a hook enables a missing capability.
No launch/deployment request or check POST is justified. Real ZTO remains first
and IMD second if a future capability actually needs currency. Nothing was signed,
sent, posted, paid or deployed.

## Wall, records and gallery

**The Counted Silence:** broken chalk trails cradle an ochre pebble where evidence
leaves a gap. Built-in imagegen generated the pigment. The donor placed it on
lower-right rock rather than the requested coordinates; visual review accepted
that placement because it avoids all ancestral marks. `add_mark10.js` transferred
only chalk/ochre pigment onto the exact previous wall. **1,160 decoded pixels**
changed, all within **[928,1128,1023,1194)**. Every other pixel matches Gathering 09.
Rock, cracks, colour, torchlight, framing and prior pigment remain unchanged.

Both inherited hands were counted: four fingers and one thumb each, **five digits**.
No new hands/stencils were added. No letters, numbers, captions, signatures,
logos, watermarks, borders or prohibited symbols observed. Full PNG and preview
were visually inspected. **Unmet visual requirements: none observed.** The small
new motif is subtle in the preview; no independent visual approval is claimed.

Required named upload: **artifacts/gathering/wall-v10.png**, **1254 × 1254 RGB8 PNG**,
left untracked for separate delivery. `wall.png` points to it with a relative
alias. Preview: **dist/gathering/10.jpg**, **512 × 512 baseline JPEG, 97,979 bytes**.
`10.json` and rewritten `one.json` use the actual full PNG SHA-256; One retains
number 736. This is a later gathering: slot 10 is replaced, all earlier painted
records and remaining placeholders stay intact. No new placeholder set is needed.

`dist/goals.json` copies the exact four GOAL.md contents. The self-contained
`dist/index.html` includes **138 numbered records: 47 painted and 91 future**,
grouped by wall, newest painted first and then newest future slot first. Local
JPEG previews, inline CSS and no scripts/fonts/external stylesheets support
offline viewing. Full PNG links need the artifact service. No browser rendering
or independent accessibility certification was performed.

Structural checks in `validation.json` and `gallery-check.json` cover image bytes,
dimensions, record hashes and schema, goals, every gallery card, local links,
ordering, file sizes, unchanged line bytes and snapshot provenance. Visual and
pixel-preservation evidence is in `wall-review.json` and `mark-process.json`.
The prompt and observed placement are in `image-prompt.txt`.
