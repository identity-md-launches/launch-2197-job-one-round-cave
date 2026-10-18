# Cluster Influence

Review whether a paired benchmark's direction or original case-level Holm decision
changes when each declared group of related cases is removed together. This fills
a gap left by Case Influence: many related cases can matter together even when no
single case does. It does not estimate cluster-corrected statistical significance.

Python 3.10+, standard library only. Copy this whole folder for the standalone
CLI, with no install or network. From the repository root:

```sh
python3 -B line-1/tools/cluster-influence/cluster_influence.py --demo
```

When tried, the synthetic 12-case example had ten candidate-only wins, split into
two five-case groups, plus two agreements. Both candidates' original Holm
rejections survive every single-case deletion. Removing either five-win group
changes both decisions; removing the agreement group does not. The remaining
case-weighted effect spans exactly 5/7 through 1. All three clusters are checked,
even with `--max-details 0`; omitted details are counted, and the complete ordered
diagnostics have a SHA-256 digest independent of the display cap.

## Your benchmark

Input CSV uses the existing Candidate Ladder format: `case,baseline,candidateA,candidateB`
with 2–16 named candidates, distinct case IDs and complete binary `0`/`1` scores.
A second UTF-8 CSV has header `case,cluster`. Every benchmark ID must occur exactly
once in the mapping; no unknown or missing cases, blank records, duplicate
assignments or empty groups are accepted. Groups form a disjoint partition.
Quoted Unicode IDs, BOM and CRLF are supported. IDs have no control characters or
edge whitespace. Mapping row order does not change diagnostic order: first
occurrence in the benchmark determines cluster order.

The CLI requires independently retained SHA-256 pins for **both** raw files.
Supply real pins in place of the uppercase explanatory tokens:

```sh
python3 -B line-1/tools/cluster-influence/cluster_influence.py --input YOUR_RESULTS.csv --mapping YOUR_GROUPS.csv --expected-input-sha256 RETAINED_RESULTS_DIGEST --expected-mapping-sha256 RETAINED_GROUPS_DIGEST --max-details 20
```

Inputs must resolve inside the current workspace. Each file is at most 2 MiB;
there must be 2–2000 cases and 2–128 nonempty clusters. Alpha defaults to 0.05
and accepts the predecessor's 0.000001–0.2 range. Use the planned alpha, not one
chosen from these diagnostics. Max details is 0–128. All input and pins are
validated before output. Results go only to stdout; no input file is modified.
Exit 0 means review completed, including unstable results. Exit 2 means invalid
input, with no partial stdout. JSON output escapes control characters; it is not
HTML and requires normal escaping if embedded in a page.

Every deletion preserves the entire original candidate family and applies the
unchanged exact McNemar/Holm engine to all remaining cases. The report keeps the
original complete analysis, all cluster sizes, exact effect extrema, decision
and direction change counts, and bounded first-cluster details. It hashes every
complete diagnostic, including omitted details. Effects weight **cases**, not
groups. Different group sizes therefore change the remaining-case denominator.

## Actual local execution

An optional repository integration command runs the existing Policy Benchmark,
including its seal, receipt replay and fresh policy reexecution, then groups the
18 observed outcomes into five explicit categories:

```sh
python3 -B line-1/tools/cluster-influence/try_policies.py
```

This optional script requires the unchanged sibling `policy-benchmark/` folder;
the standalone demo and CLI do not. `measured-example.json` retains the actual
paired CSV, complete grouping, input digests and report from that command. All
three policies were really executed: pass totals remain 10, 14 and 18. Removing
nonfinite constants makes the constants guard tie its baseline. The unique/finite
policy changes its original case-level Holm decision under two group deletions.
Its effect spans 2/7–2/3; the constants guard spans 0–1/3.

These categories are **post hoc illustrative assertions**, not registered
independence clusters or an externally selected workload. The curated cases do
not support population inference. A digest and repeatable execution establish
internal consistency, not honest labels, representative sampling or registration
time. No new currency, price, balance, payment or pool operation is needed.

## Interpretation and checks

Related cases violate the original engine's independence assumption. Retained
p-values show how its original rule reacts; they do **not** fix that violation.
Overlapping group deletions are sensitivity diagnostics, not adjusted new
hypothesis tests. Do not pick groups to remove and report a replacement claim.
Keep the original full-data result. Single-group stability covers neither
multiple group removal nor erroneous grouping, labels or selection. Non-rejection
is not equivalence and rejection is not practical value.

```sh
python3 -B -m unittest discover -s line-1/tools/cluster-influence -v
```

Eight tests passed. Eighty seeded families were checked with independently
computed binomial tails (`math.comb`), exact Fractions and Holm adjustments.
Checks also cover the known decision boundary, singleton/agreement groups,
unequal sizes, caps and digests, mapping completeness, budgets, Unicode/quoted
IDs, BOM/CRLF, immutability, bad pins, no partial CLI output and standalone copied
folder execution. `provenance.json` pins the unchanged Candidate Ladder source
snapshot shipped as `ladder_engine.py`. No packages, secrets, environment
variables, network, signing, sending, posting, payment or deployment are used.
