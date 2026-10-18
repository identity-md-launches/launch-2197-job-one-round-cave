# Gap Budget

Connect Line 3's verified Timeline Gaps to Line 4's exact Worksheet Flint.
Check total uncovered time and longest gap against explicit time quantities,
while checking that covered plus uncovered exactly equals the query duration.
Copy this whole folder to use independently: Python 3.10+, standard library only,
no installation or network. Engine snapshots are ordinary unchanged files.

```sh
python3 -B shared/gap-budget/gap_budget.py demo
```

**The demo deliberately exits 1.** Its synthetic six-second window has three
seconds uncovered and a longest gap of one second. A total budget of `2500 ms`
fails; a longest-gap budget of `1 s` passes inclusively. The exact uncovered
fraction is `1/2`. Only one of three gaps is displayed; two omissions are
explicit. Display caps cannot change the totals or checks. This is hypothetical
evidence and an illustrative policy, not a measured incident or availability claim.

For an existing Timeline Replay pack inside the current workspace:

```sh
python3 -B shared/gap-budget/gap_budget.py check YOUR_PACK.json --expected-sha256 RETAINED_PACK_DIGEST --start 2026-10-18T10:00:00Z --end 2026-10-18T10:01:00Z --max-uncovered '500 ms' --max-gap '200 ms' --limit 10
```

Replace the file and digest with your own exact pack and independently retained
lowercase SHA-256. A pack can be prepared with the included replay snapshot:

```sh
python3 -B shared/gap-budget/engines/timeline/replay.py pack --ignore-unmatched YOUR_LOG.log > YOUR_PACK.json
```

Keep the original pack bytes: the review does not embed them. The whole pack is
replayed before selecting the half-open window, including events outside it.
All embedded evidence and stored report must match the fixed shipped parser.
Pack digests and source hashes identify bytes, not trust or authorship. No
original source path from a pack is opened. Output includes the complete coverage
summary, worksheet request, recalculated exact result, direct dependencies and
individual checks. Microseconds become rational seconds without floating point
or rounding. Message text and original source names are not echoed.

Budgets must be nonnegative time expressions, including zero with time units.
Query endpoints are exact offset-aware instants, not precision-expanded timestamps.
`--limit` is 0–200 and limits details only. Inherited pack limits: 16 MiB pack,
2 MiB embedded logs. Expression limits: 4096 characters, 256 tokens, bounded
rational arithmetic. Input paths must resolve to regular files in the current
workspace. Invalid input emits no stdout and exits 2. Valid failed checks exit 1;
all supplied checks passing exits 0. The CLI writes only stdout/stderr.

**Interpretation:** a gap is absence of timestamp interval coverage. It does
not establish downtime, inactivity, missing collection, service concurrency or
causality. Wider asserted clock uncertainty can remove a gap without adding
any evidence. Undated lines stay counted. The model assumes displayed timestamp
precision represents truncation. Exact calculation cannot establish clock
accuracy, evidence completeness or a suitable policy. This tool does not measure
service runtime and should not be used as an uptime/SLO monitor.

```sh
python3 -B -m unittest discover -s shared/gap-budget -v
```

Tried: 10 integration tests passed, including 100 seeded microsecond cases
checked against independent discrete coverage counts and Fractions, inclusive
budgets, dimension errors, caps, full/empty coverage, immutability, out-of-window
tampering, source digests, standalone copied-folder CLI, bad pins, workspace
containment, exit statuses and atomic errors. `provenance.json` names all six
unchanged source snapshots, upstream paths and SHA-256 digests.

A repository-only observed example is also available:

```sh
python3 -B gathering/try_gap_budget.py
```

This actually executes the four latest line demos, journals their observed
start/end timestamps, constructs a replay pack, and applies the shared tool.
`gathering/observed-gap-budget.json` retains one execution, its exact pack,
commands, statuses, payload digests and review. The payload demos remain
synthetic; the journal timestamps are real local process observations. Such
sparse timestamp coverage is not process runtime, service availability or a
clock calibration. The one-second budgets are post hoc illustrations.
