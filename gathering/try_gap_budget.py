#!/usr/bin/env python3
"""Timestamp actual local CLI executions, then check their journal's coverage."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('gathering_gap_budget', ROOT/'shared/gap-budget/gap_budget.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def main():
    commands = [
        ('clusters', ['line-1/tools/cluster-influence/cluster_influence.py', '--demo'], 0),
        ('json-keys', ['line-2/tools/json-crosscheck/json_crosscheck.py', '--demo'], 0),
        ('gaps', ['line-3/tools/timeline-gaps/timeline_gaps.py', 'demo'], 0),
        ('worksheet', ['line-4/tools/worksheet-flint/worksheet_flint.py', 'demo'], 1)]
    rows, lines = [], []
    start = now()
    for name, arguments, expected in commands:
        began = now()
        result = subprocess.run([sys.executable, '-B', *arguments], cwd=ROOT,
                                capture_output=True, timeout=30)
        ended = now()
        if result.returncode != expected:
            raise ValueError(f'{name} returned {result.returncode}, expected {expected}')
        lines.extend([f'{began} {name} start\n', f'{ended} {name} exit={result.returncode}\n'])
        rows.append({'tool': name, 'arguments': arguments, 'expected_exit': expected,
                     'observed_exit': result.returncode, 'start': began, 'end': ended,
                     'stdout_sha256': app.gaps.replay.digest(result.stdout)})
    end = now()
    raw_log = ''.join(lines).encode('ascii')
    pack = app.gaps.replay.make_pack([('local-cli-journal.log', raw_log)])
    raw_pack = app.gaps.replay.canonical(pack) + b'\n'
    # These are illustrative post hoc budgets on journal coverage, not runtime SLOs.
    review = app.review(pack, start, end, '1 s', '1 s', 2)
    result = {'data_kind': 'observed_local_process_journal', 'executions': rows,
              'pack': pack, 'pack_sha256': app.gaps.replay.digest(raw_pack), 'review': review,
              'limitations': 'These are actual process-observation timestamps, not real incident logs. Timestamp coverage measures discrete journal entries, not process runtime or availability. Clock accuracy is not measured; budgets are post hoc examples. Tool payload demos remain synthetic.'}
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
