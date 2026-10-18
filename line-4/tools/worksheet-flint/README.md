# Worksheet Flint

Check a chain of named calculations without copying rounded intermediate
numbers. Exact rational quantities carry length, mass, time and data dimensions
through every step. Python 3.10+, standard library only; copy this entire folder
to use it independently. Nothing is installed or fetched.

Run from the repository root:

```sh
python3 -B line-4/tools/worksheet-flint/worksheet_flint.py demo
```

The demo deliberately exits **1**: supplied example inputs of 750 MiB at
12 MiB/s give 62.5 seconds; adding 1500 ms gives exactly 64 seconds. The
`expect: 64 s` check passes, but the inclusive `at_most: 1 min` budget fails.
These are hypothetical inputs, not measured performance. A failed claim does
not substitute its claimed value for the computed result. Later steps still
use the exact computed quantity, and the whole worksheet remains failed.

## Check your own worksheet

Feed one UTF-8 JSON document on stdin; the tool accepts no input filenames:

```sh
printf '%s\n' '{"schema":"worksheet-flint/1","steps":[{"name":"distance","expression":"10 km"},{"name":"duration","expression":"2 h"},{"name":"speed","expression":"$distance / $duration","to":"m/s","expect":"5 km/h","at_least":"1 m/s","at_most":"2 m/s"}]}' | python3 -B line-4/tools/worksheet-flint/worksheet_flint.py check
```

This exits **0** with exact speed `25/18 m/s` and three passing checks.
Single quotes in this shell example preserve the literal dollar signs.

The document has exactly `schema` and `steps`. Each step requires `name` and
`expression`; optional fields are `to`, `expect`, `at_least`, `at_most`.
All field values are strings. Unknown fields, nulls, duplicate JSON keys,
JSON numbers and nonfinite constants are rejected. Names match
`[A-Za-z][A-Za-z0-9_]{0,31}` and must be unique.

Use `$name` for an **earlier** step's exact quantity. Unprefixed names retain
the engine's unit meaning: a step called `m` does not redefine the metre.
Explicit multiplication is required (`2 * $distance`, not `2 $distance`).
References are allowed in expressions and checks, but `to` accepts units only.
Self references, forward references and cycles fail. Each row lists the direct
references used by its expression and checks, sorted by name; this list is not
a transitive dependency closure. No source-code evaluation or textual expansion
of computed values occurs.

The inherited grammar supports `+ - * / ^ **`, parentheses, decimal/scientific
numbers, unit quantities, and integer powers -12..12. `2 m^2` means `(2 m)^2`;
use `2 * m^2` for two square metres. Supported units: m, cm, mm, km, in, ft, mi;
kg, g, mg, t; s, ms, min, h, day; B, KiB, MiB, GiB; L, mL; N, J, W. Addition,
subtraction, comparisons and conversion require identical dimensions, even for
zero. Lower and upper bounds are inclusive and must be ordered. A conversion
changes only the display; subsequent references always use base-unit quantities.

Output includes the original request, direct dependencies, exact base value,
base unit, dimension exponents, converted value and check outcomes per step.
Integers and fractions are strings; finite display decimals are exact. No
rounding is performed. Exit **0** means all supplied checks pass (or no checks
were supplied); **1** means a valid worksheet contains a failed check; **2**
means invalid input or a resource limit. Invalid late steps produce **no stdout**,
so a valid-looking prefix cannot be mistaken for a complete worksheet.

## Bounds, checks and limitations

Input is at most 65,536 bytes, eight JSON nesting levels and 32 steps. Each
expression is at most 4096 characters and 256 tokens; nesting is at most 32,
exact numerator/denominator at most 2048 bits and dimension powers within
-256..256. References do not expand expression text or bypass arithmetic limits.
The tool reads only stdin and its local imported source; it does not read
configuration, environment variables, wallets, keys or arbitrary files, and
never contacts a service or sends a transaction.

```sh
python3 -B -m unittest discover -s line-4/tools/worksheet-flint -v
```

Tried locally: **13 tests passed**, including 300 seeded independent Fraction
oracles for conversion and multi-step chains; non-rounding propagation; failed
checks; zero/dimension errors; forward/cyclic/duplicate references; resource
limits; malformed JSON; immutability; repeatability; real CLI exit statuses and
no partial stdout on a late error. The documented passing command and failing
demo also ran successfully, including with the folder copied to scratch.
All **56 inherited tests** passed unchanged. These are local observations,
not independent certification.

`engine.py` is a byte-identical ordinary-file snapshot of
`../unit-flint/unit_flint.py`, SHA-256
`c683e558cdbdf6cf73d4b32572b6fa498b80e7816483b882bf2d51adfff3062e`.
The new parser only adds explicit reference tokens around that engine. The
inherited tools remain untouched. Worksheet Flint checks supplied arithmetic,
not measurement accuracy, completeness of a model, provenance or authorship.
It has no currency/exchange-rate, uncertainty, offset-temperature or symbolic
solver support. No coin or price is needed for this capability.
