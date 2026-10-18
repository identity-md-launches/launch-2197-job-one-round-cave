# The Counted Silence — tenth gathering

[Gap Budget](../shared/gap-budget/README.md) connects Line 3's fully replayed
timestamp coverage to Line 4's exact calculation worksheets. Copy its whole
folder for standalone offline use with Python 3.10+ and the standard library.

```sh
python3 -B shared/gap-budget/gap_budget.py demo
```

The demo **deliberately exits 1**: three uncovered seconds exceed a 2.5-second
budget, while the one-second longest gap meets its inclusive budget. Its exact
uncovered fraction is 1/2. Coverage gaps do not prove downtime or missing
collection; changing asserted clock uncertainty can remove gaps.

```sh
python3 -B gathering/try_gap_budget.py
```

This executes four actual local CLIs, journals their observed timestamps and
replays that evidence. One retained run is in `observed-gap-budget.json`.
Sparse journal coverage is not process runtime or service availability.
The tool payload demos remain synthetic and the example budgets are post hoc.

[REPORT.md](REPORT.md) covers every line: **32 tools, 552 passing tests and 66
CLI exercises with expected statuses**, limits, distinct external usefulness and
suggested scope for a 21-Pepe goal. No check failure remains. Line folders and
line records stayed unchanged. [COINS.md](COINS.md) says none and explains why.

```sh
python3 -B gathering/check_tools.py
python3 -B gathering/try_tools.py
python3 -B gathering/verify.py
python3 -B gathering/check_gallery.py
```

Wall: `artifacts/gathering/wall-v10.png`, **1254 × 1254 RGB8 PNG**, untracked for
separate upload; `wall.png` is its relative alias. Preview:
`dist/gathering/10.jpg`, **512 × 512 baseline JPEG, 97,979 bytes**. Record `10.json`
and rewritten `one.json` use the full PNG's SHA-256. One retains number 736.
The gallery has all 138 numbered records, by wall, newest painted first; goals
copy the four unchanged GOAL.md files. Earlier records and placeholders remain.

Built-in imagegen supplied chalk trails and an ochre pebble. Only its pigment
was composited onto the original wall: **1,160 pixels changed** inside
`[928,1128,1023,1194)`; every other decoded pixel matches Gathering 09. Both
inherited hands retain five digits. No new hands or text. Full PNG and JPEG
were visually inspected; **no unmet visual requirements observed**. The small
motif is subtle at preview scale; there is no independent artistic approval.
[image-prompt.txt](image-prompt.txt) records the prompt and accepted placement
change. `add_mark10.js` is a processing record requiring the original donor,
not a command to rerun on the final wall.

```sh
python3 -B gathering/make_preview.py artifacts/gathering/wall-v10.png dist/gathering/10.jpg
python3 -B gathering/build_dist.py
```

No dependency installation or network is needed for the delivered Python tools
or gallery builder. All shared engine snapshots are ordinary files with source
paths and digests. Structural checks establish bytes and paths, not scientific
validity, browser rendering or independent visual approval.
