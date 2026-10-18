"""Offline integration oracles, validation, immutability and standalone CLI checks."""
import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

import gap_budget as tool

START = '2026-10-18T10:00:00Z'
END = '2026-10-18T10:00:06Z'
HERE = Path(__file__).resolve().parent


def pack(raw=b'2026-10-18T10:00:01Z private-message\n', bound=0):
    return tool.gaps.replay.make_pack([('private-path.log', raw)], True, bound)


class GapBudgetTests(unittest.TestCase):
    def test_demo_distinguishes_total_and_longest(self):
        result = tool.demo()
        self.assertFalse(result['passes'])
        self.assertEqual(result['coverage']['durations_us']['uncovered'], 3000000)
        steps = {r['request']['name']: r for r in result['worksheet_result']['steps']}
        self.assertFalse(steps['uncovered']['passes'])
        self.assertTrue(steps['longest_gap']['passes'])
        self.assertTrue(steps['accounted']['passes'])
        self.assertEqual(steps['uncovered_fraction']['value'], '0.5')
        self.assertEqual(result['coverage']['counts']['gaps_not_shown'], 2)

    def test_inclusive_exact_budgets_and_conversions(self):
        report = tool.review(pack(), START, END, '5000 ms', '1 min / 15')
        self.assertTrue(report['passes'])
        self.assertFalse(tool.review(pack(), START, END, '4999.999 ms', '4 s')['passes'])
        self.assertFalse(tool.review(pack(), START, END, '5 s', '3999.999 ms')['passes'])

    def test_zero_coverage_and_full_coverage(self):
        empty = tool.review(pack(b'undated\n'), START, END, '6 s', '6 s')
        self.assertTrue(empty['passes'])
        self.assertEqual(empty['coverage']['counts']['undated_lines'], 1)
        full = tool.review(pack(bound=5000), START, END, '0 s', '0 s')
        self.assertTrue(full['passes'])
        self.assertEqual(full['coverage']['durations_us']['uncovered'], 0)

    def test_cap_cannot_change_checks(self):
        p = pack()
        all_gaps = tool.review(p, START, END, '5 s', '4 s', 200)
        none = tool.review(p, START, END, '5 s', '4 s', 0)
        self.assertEqual(none['coverage']['gaps'], [])
        self.assertEqual(none['worksheet_result'], all_gaps['worksheet_result'])
        self.assertEqual(none['coverage']['counts']['gaps_not_shown'], 2)

    def test_time_dimensions_sign_and_invalid_expressions(self):
        for expression in ['0 m', '1', '-1 s', '1 s / 0', '$uncovered', 'm + s', '', 'a'*4097]:
            with self.subTest(expression=expression), self.assertRaises((ValueError, tool.worksheet.engine.UnitError)):
                tool.review(pack(), START, END, expression, '1 s')

    def test_full_replay_before_query_and_no_mutation_or_message_echo(self):
        p = pack(b'2026-10-18T09:00:00Z private-message\n')
        original = copy.deepcopy(p)
        a = tool.review(p, START, END, '6 s', '6 s')
        self.assertEqual(p, original)
        self.assertEqual(a, tool.review(p, START, END, '6 s', '6 s'))
        self.assertNotIn('private-message', json.dumps(a))
        self.assertNotIn('private-path.log', json.dumps(a))
        p['timeline']['events'][0]['message'] = 'forged-outside-window'
        with self.assertRaises(ValueError):
            tool.review(p, START, END, '6 s', '6 s')

    def test_microsecond_exact_independent_point_oracle(self):
        rng = random.Random(73710)
        for _ in range(100):
            positions = sorted(set(rng.randrange(20) for _ in range(rng.randrange(10))))
            raw = ''.join(f'2026-10-18T10:00:00.{i:06d}Z e\n' for i in positions).encode() or b'undated\n'
            result = tool.review(pack(raw), START, '2026-10-18T10:00:00.000020Z', '1 s', '1 s')
            steps = result['worksheet_result']['steps']
            expected = 20-len(positions)
            self.assertEqual(Fraction(steps[2]['base_value']), Fraction(expected, 1000000))
            self.assertEqual(Fraction(steps[-1]['base_value']), Fraction(expected, 20))
            self.assertTrue(result['passes'])

    def test_provenance_unchanged_sources(self):
        for row in json.loads((HERE/'provenance.json').read_text()):
            snapshot = HERE / Path(row['snapshot']).relative_to('shared/gap-budget')
            self.assertEqual(hashlib.sha256(snapshot.read_bytes()).hexdigest(), row['sha256'])

    def test_standalone_cli_pins_status_and_atomic_errors(self):
        scratch = Path('test/scratch'); scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            base = Path(folder).resolve(); shutil.copytree(HERE, base/'tool')
            raw = tool.gaps.replay.canonical(pack())+b'\n'
            (base/'pack.json').write_bytes(raw)
            command = [sys.executable, '-B', 'tool/gap_budget.py', 'check', 'pack.json',
                       '--expected-sha256', hashlib.sha256(raw).hexdigest(), '--start', START,
                       '--end', END, '--max-uncovered', '5 s', '--max-gap', '4 s']
            def run(args):
                return subprocess.run(args, cwd=base, capture_output=True, timeout=10)
            good = run(command)
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertTrue(json.loads(good.stdout)['passes'])
            fail = run(command[:-1]+['3 s'])
            self.assertEqual(fail.returncode, 1, fail.stderr)
            self.assertFalse(json.loads(fail.stdout)['passes'])
            for index, value in [(6, 'f'*64), (4, '../outside.json'), (-1, '0 m')]:
                bad_args = command.copy(); bad_args[index] = value
                bad = run(bad_args)
                self.assertEqual(bad.returncode, 2, bad.stderr)
                self.assertEqual(bad.stdout, b'')
            altered = json.loads(raw); altered['timeline']['events'][0]['message'] = 'forged'
            altered_raw = tool.gaps.replay.canonical(altered)
            (base/'pack.json').write_bytes(altered_raw)
            command[6] = hashlib.sha256(altered_raw).hexdigest()
            bad = run(command)
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(bad.stdout, b'')

    def test_window_validation(self):
        for start, end in [(END, START), (START, START), ('invalid', END)]:
            with self.assertRaises(ValueError):
                tool.review(pack(), start, end, '1 s', '1 s')
        with self.assertRaises(ValueError):
            tool.review(pack(), START, END, '1 s', '1 s', True)


if __name__ == '__main__':
    unittest.main()
