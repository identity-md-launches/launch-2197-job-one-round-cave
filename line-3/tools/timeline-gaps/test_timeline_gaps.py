"""Offline adversarial checks; fixtures are explicitly synthetic."""
import copy
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

import replay
import timeline_gaps as gaps

START = '2026-10-18T10:00:00Z'
END = '2026-10-18T10:00:06Z'
HERE = Path(__file__).resolve().parent


def pack(raw=b'2026-10-18T10:00:01Z first\n', uncertainty=0, ignore=False):
    return replay.make_pack([('worker.log', raw)], clock_uncertainty_ms=uncertainty,
                            ignore_unmatched=ignore)


class GapTests(unittest.TestCase):
    def test_demo(self):
        result = gaps.demo()
        self.assertEqual(result['durations_us'], dict(window=6000000, covered=3000000,
                         uncovered=3000000, longest_gap=1000000))
        self.assertEqual(result['counts']['gaps_total'], 3)
        self.assertEqual(result['counts']['covered_components'], 2)
        self.assertEqual(result['counts']['undated_lines'], 1)

    def test_clipping_and_touching_boundaries(self):
        covered, holes = gaps.partition([(-1, 1), (1, 2), (2, 3), (5, 8), (8, 9)], 0, 6)
        self.assertEqual(covered, [[0, 3], [5, 6]])
        self.assertEqual(holes, [[3, 5]])
        self.assertEqual(gaps.partition([(-1, 0), (6, 7)], 0, 6), ([], [[0, 6]]))

    def test_seeded_union_complement_against_integer_point_oracle(self):
        rng = random.Random(737)
        for _ in range(500):
            intervals = []
            for _ in range(rng.randrange(30)):
                a = rng.randrange(-10, 30)
                intervals.append((a, a+rng.randrange(1, 15)))
            covered, holes = gaps.partition(intervals, 0, 20)
            expected = {i for i in range(20) if any(a <= i < b for a, b in intervals)}
            actual = {i for a, b in covered for i in range(a, b)}
            missing = {i for a, b in holes for i in range(a, b)}
            self.assertEqual(expected, actual)
            self.assertEqual(missing, set(range(20))-expected)
            self.assertEqual(sum(b-a for a, b in covered+holes), 20)
            self.assertTrue(all(covered[i][1] < covered[i+1][0] for i in range(len(covered)-1)))

    def test_no_dated_events_whole_window_uncovered(self):
        result = gaps.analyze(pack(b'diagnostic\n', ignore=True), START, END)
        self.assertEqual(result['durations_us']['uncovered'], 6000000)
        self.assertEqual(result['counts']['undated_lines'], 1)
        self.assertEqual(result['counts']['gaps_total'], 1)

    def test_full_coverage_and_uncertainty(self):
        result = gaps.analyze(pack(uncertainty=5000), START, END)
        self.assertEqual(result['gaps'], [])
        self.assertEqual(result['durations_us']['covered'], 6000000)
        self.assertEqual(result['durations_us']['longest_gap'], 0)

    def test_offset_endpoints_are_exact_not_precision_expanded(self):
        self.assertEqual(gaps.instant('2026-10-18T12:00+02:00'), gaps.instant(START))
        result = gaps.analyze(pack(), '2026-10-18T12:00:01.500000+02:00',
                              '2026-10-18T10:00:02.500000Z')
        self.assertEqual(result['durations_us']['covered'], 500000)
        self.assertEqual(result['durations_us']['uncovered'], 500000)

    def test_calendar_end_and_invalid_endpoints(self):
        self.assertEqual(gaps.instant('9999-12-31T23:59:59.999999Z'), replay.engine.MAX_MICROS)
        self.assertEqual(gaps.instant('0001-01-01T00:00:00Z'), replay.engine.MIN_MICROS)
        for value in ['2026-10-18T10:00:00', '2026-02-30T00:00Z',
                      '2026-10-18T10:00:00+24:00', '2026-10-18T10:00:00+00:60',
                      '2026-10-18T10:00:00.0000001Z', '0001-01-01T00:00+01:00', True]:
            with self.assertRaises((ValueError, OverflowError)):
                gaps.instant(value)
        for a, b in [(END, START), (START, START)]:
            with self.assertRaises(ValueError):
                gaps.analyze(pack(), a, b)

    def test_limit_counts_and_totals(self):
        evidence = pack()
        full = gaps.analyze(evidence, START, END)
        for limit in [0, 1, 2]:
            result = gaps.analyze(evidence, START, END, limit)
            self.assertEqual(result['durations_us'], full['durations_us'])
            self.assertEqual(result['counts']['gaps_not_shown'], max(0, 2-limit))
            self.assertEqual(len(result['gaps']), min(2, limit))
        for limit in [True, -1, 201, 1.5]:
            with self.assertRaises(ValueError):
                gaps.analyze(evidence, START, END, limit)

    def test_all_evidence_verified_even_outside_query(self):
        evidence = pack(b'2026-10-18T09:00:00Z outside\n')
        evidence['timeline']['events'][0]['message'] = 'forged'
        with self.assertRaises(replay.ReplayError):
            gaps.analyze(evidence, START, END)

    def test_immutable_deterministic_no_log_text_echo(self):
        evidence = pack(b'2026-10-18T10:00:01Z PRIVATE_MESSAGE\n')
        before = copy.deepcopy(evidence)
        first = replay.canonical(gaps.analyze(evidence, START, END))
        self.assertEqual(first, replay.canonical(gaps.analyze(evidence, START, END)))
        self.assertEqual(evidence, before)
        self.assertNotIn(b'PRIVATE_MESSAGE', first)
        self.assertNotIn(b'worker.log', first)

    def test_provenance(self):
        provenance = json.loads((HERE/'PROVENANCE.json').read_text())
        for item in provenance['dependencies']:
            self.assertEqual(hashlib.sha256((HERE/item['path']).read_bytes()).hexdigest(), item['sha256'])

    def test_portable_cli_pinned_digest_and_atomic_failure(self):
        # All scratch files stay under the task workspace; no environment access.
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as tmp:
            root = Path(tmp).resolve()
            copied = root/'tool'
            shutil.copytree(HERE, copied)
            raw = replay.canonical(pack())+b'\n'
            evidence = root/'pack.json'
            evidence.write_bytes(raw)
            command = [sys.executable, '-B', str(copied/'timeline_gaps.py'), 'analyze', str(evidence),
                       '--start', START, '--end', END]
            okay = subprocess.run(command+['--expect-sha256', replay.digest(raw)], cwd=root,
                                  capture_output=True)
            self.assertEqual(okay.returncode, 0, okay.stderr)
            self.assertEqual(json.loads(okay.stdout)['pack_sha256'], replay.digest(raw))
            bad = subprocess.run(command+['--expect-sha256', '0'*64], cwd=root, capture_output=True)
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(bad.stdout, b'')
            changed = json.loads(raw)
            changed['timeline']['events'][0]['message'] = 'changed'
            evidence.write_bytes(replay.canonical(changed))
            bad = subprocess.run(command, cwd=root, capture_output=True)
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(bad.stdout, b'')
            outside = root.parent/'outside.json'  # only a name; never opened
            command[4] = str(outside)
            bad = subprocess.run(command, cwd=root, capture_output=True)
            self.assertEqual(bad.returncode, 2)
            self.assertIn(b'outside', bad.stderr)
            self.assertEqual(bad.stdout, b'')


if __name__ == '__main__':
    unittest.main()
