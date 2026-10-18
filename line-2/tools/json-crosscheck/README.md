# JSON Crosscheck

Compare **decoded JSON member names across selected files**, with byte evidence
for both spellings. Useful when reviewing related configuration documents,
API responses or generated manifests before publishing or consuming them.
Python 3.10+, standard library only; no installation, network or transaction.

From the repository root, one command demonstrates the complete operation:

```sh
python3 -B line-2/tools/json-crosscheck/json_crosscheck.py --demo --max-findings 2
```

What happened: the synthetic three-document demo contains ASCII `owner`, an
escaped Cyrillic lookalike, a fullwidth lookalike inside `pay-owner`, and an
equivalently escaped ASCII spelling. It finds **three cross-file occurrences**,
retains two and explicitly reports one omitted. Demo exit status is zero.
The third document's decoded `owner` differs from the second document's Cyrillic
spelling, so it also needs review; it does not collide with the first document's
identical decoded `owner`. No example is an observed attack.

## Review your own files

```sh
python3 -B line-2/tools/json-crosscheck/json_crosscheck.py --files gathering/measured-effect-band.json gathering/benchmark-display-demo.json gathering/effect-band-demo.json
```

Actual local result: **29,366 original bytes, 650 member-name occurrences,
103 distinct limited skeletons, zero covered cross-file collisions**. Complete
file digests and scope are in `line-2/round-29-real-review.json`. This result
does not establish safety. The files are existing calculation/benchmark evidence,
not executed inputs or invented real-world attack examples.

Select 2–32 explicit regular files inside the current workspace. Symlinks
resolving outside it and duplicate resolved paths are refused. No directory
recursion, automatic file discovery, environment reads or input evaluation.
JSON values are parsed as data and never executed. CLI exits **0** for a clean
review, **1** when covered collisions need review, **2** for invalid input.
It validates all documents and the complete output budget before writing stdout;
errors go to stderr as ASCII JSON, without a partial report.

## What a finding means

Each **whole decoded member name** is normalized with NFKC and then the unchanged
Unicode Lantern case-sensitive Latin/Greek/Cyrillic lookalikes table. Different
decoded spellings sharing this limited skeleton need review. Unlike Unicode
Crosscheck, this decodes JSON escapes and compares complete keys, including
punctuation. It compares all object depths across files; unrelated paths may
therefore produce harmless matches. It does not compare values or infer schemas.

A later key occurrence counts once if any **earlier file** contains a different
decoded spelling with the same skeleton. Witnesses follow file argument order,
then original byte order. Only the earliest differing witness is retained, not
all pairs. Within-file collisions are excluded; use JSON Lantern or JSON
Citations for those and for controls, format characters and other covered rules.
Duplicate keys are retained as separate occurrences rather than silently lost.
`"owner"` and `"\u006fwner"` decode identically and do not alone collide.
Changing file order can change counts and witnesses.

Both witnesses contain the source index, structural location, zero-based
half-open **original UTF-8 byte range including quotes**, full token and decoded
SHA-256, at most 64 raw bytes as hex and 40 decoded code points in ASCII escape
notation, with explicit omitted lengths. Locations use object-pair indexes with
`key`/`value` roles and array indexes, preserving ambiguous duplicate names.
Check a citation by slicing the original bytes, hashing that slice and decoding
that one JSON string. Digests identify bytes, not an author or trusted collection.
Reports do not embed complete input files; retain the original bytes separately.

## Boundaries and portability

Strict UTF-8 JSON only: no BOM, NaN, Infinity or lone surrogate escapes, even in
values. Valid surrogate pairs work. Numbers remain opaque lexical objects to
avoid integer conversion limits and float overflow. Budgets: 2 MiB per file,
8 MiB total, depth 64, 20,000 values per file, 100,000 keys total, 4,096 code
points per key, 1–1,000 retained findings (default 100), 4 MiB rendered output.
Exceeding a budget is an error, not a clean partial scan. A finding cap limits
details, never validation or the exact count of covered occurrences.

This is heuristic evidence, **not full UTS #39**, a renderer, an intent judgment
or a guarantee that an unflagged name is safe. NFKC-equivalent legitimate names
and multilingual text can collide. Case is preserved. A dangerous key with no
matching earlier-file spelling may produce no collision. Findings and previews
are unredacted. ASCII output is inert on a terminal but is not HTML sanitization.
Unicode results depend on the runtime's Unicode database, recorded in the report.

The tool imports the unchanged sibling folders `json-citations`, `json-lantern`
and `unicode-lantern`. All four folders are ordinary shipped source; to move it,
copy those four folders together under a common parent. No runtime download.
Reports record the three imported engine digests. They are provenance, not a
cryptographic signature or independent replay certificate.

## Checks

```sh
python3 -B -m unittest discover -s line-2/tools/json-crosscheck -v
```

19 tests passed: exact raw/escaped/multibyte citations, surrogate pairs, duplicate
keys, nested and lexical witness order, complete-name semantics, equivalent
encodings, value exclusion, exact omissions, malformed late inputs, all budget
classes, large numeric literals, inert previews, CLI statuses, no partial output,
workspace/symlink containment, and a portable four-folder copy. An independent
brute-force witness search checks 100 deterministically generated document sets.
The tests create disposable fixtures only under `test/scratch/`.
