# Timeline Gaps

Find the exact portions of a chosen time window that no dated event uncertainty
interval covers. The complete evidence pack is replayed before any window is
selected. This helps a worker distinguish what the retained timestamps cover
from stretches the evidence cannot place an event in.

Run this from the repository root, with Python 3.10+ and no installation:

```sh
python3 -B line-3/tools/timeline-gaps/timeline_gaps.py demo
```

Tried locally: the explicitly synthetic six-second window contains three
one-second gaps and three seconds of covered time. Two touching event intervals
form one continuous covered component. One undated diagnostic remains counted.
The example is not a real incident or a measured clock-error bound.

For your own evidence pack within the current workspace:

```sh
python3 -B line-3/tools/timeline-gaps/timeline_gaps.py analyze path/to/pack.json --start 2026-10-18T10:00:00Z --end 2026-10-18T10:01:00Z --expect-sha256 TRUSTED_DIGEST
```

Replace `TRUSTED_DIGEST` with an independently retained lowercase SHA-256 of the
exact pack bytes, or omit that option for consistency checking alone. To create
a pack, the fixed Replay snapshot is included:

```sh
python3 -B line-3/tools/timeline-gaps/replay.py pack --ignore-unmatched --clock-uncertainty-ms 250 path/to/worker.log > path/to/pack.json
```

Use existing parent directories and workspace files. No original log path is
opened when analyzing a pack: it contains the exact embedded bytes. No services
are executed, no network is used, and no coin, wallet or account is needed.
This whole folder can be copied independently. Its ordinary Python source
snapshots and SHA-256 provenance are included, without remote dependencies.

## Semantics and limits

- The query is `[start, end)`. Endpoints require offset-aware ISO text, with
  optional seconds and at most six fractional digits. Query endpoints are exact
  instants: `10:00Z` means the instant at the beginning of that minute. Unlike
  log timestamps, query endpoints do not expand to their displayed precision.
- Event intervals retain the fixed parser's displayed-precision truncation
  assumption and optional analyst-supplied symmetric clock bound. Intervals are
  clipped to the query, sorted and unioned. Touching covered intervals leave no
  positive-duration gap. Nested/duplicate intervals do not double-count time.
- Results give exact integer microseconds of covered and uncovered time, the
  longest gap, all component counts, and chronological gap bounds. `--limit`
  (0–200, default 50) limits displayed gaps, with exact omission counts. All
  totals are computed before the display cap.
- Gaps are **absence of interval coverage in this evidence model**. They do not
  establish inactivity, downtime, missing collection, causality or true event
  times. Wider uncertainty can fill a gap without adding evidence. Undated
  lines cannot be placed; their count stays explicit.
- The complete pack must verify, including evidence outside the selected
  window. Replay establishes internal consistency with a fixed parser, not
  authentic or complete collection. Packs contain unredacted evidence; this
  tool's output omits messages and embedded log bytes.
- Invalid input exits 2, emits a diagnostic on stderr, and writes no partial
  stdout. A successful report exits 0 even if the whole window is uncovered.
  Workspace containment and Replay's 16 MiB pack / 2 MiB embedded-byte limits
  apply. The parser supports its existing ISO/epoch text and JSONL grammar,
  not arbitrary log formats, leap seconds or clock-skew estimation.

## Checks

```sh
python3 -B -m unittest discover -s line-3/tools/timeline-gaps -v
```

Observed: all 12 tests passed, including 500 seeded interval sets compared with
an independent discrete-point oracle; clipping, touching and nested intervals;
empty dated evidence; full coverage under asserted uncertainty; exact offset
query endpoints and calendar limits; capped output; immutable deterministic
results; verification of altered evidence outside the window; provenance; and
a standalone copied-folder CLI with good/bad pins, tampered reports, workspace
containment and no partial stdout on failure.
