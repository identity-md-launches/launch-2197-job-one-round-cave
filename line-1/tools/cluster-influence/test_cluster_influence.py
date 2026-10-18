import csv
from fractions import Fraction
import hashlib
import io
import json
import math
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

import cluster_influence as ci


class Tests(unittest.TestCase):
    def test_boundary_and_caps(self):
        raw, mapping = ci.demo_inputs()
        full = ci.review(raw, mapping, max_details=128)
        self.assertEqual(full['clusters_checked'], 3)
        self.assertEqual(full['clusters_changing_decision_or_direction'], 2)
        self.assertEqual([s['decision_changes'] for s in full['candidates']], [2, 2])
        self.assertTrue(all(c['familywise_reject_equal_discordance'] for c in full['full_data_analysis']['candidates']))
        self.assertEqual(full['candidates'][0]['minimum_effect'], ci.rational(Fraction(5, 7)))
        self.assertEqual(full['candidates'][0]['maximum_effect'], ci.rational(Fraction(1)))
        for cap in (0, 1, 2):
            result = ci.review(raw, mapping, max_details=cap)
            self.assertEqual(result['details'], full['details'][:cap])
            self.assertEqual(result['details_omitted'], 3-cap)
            self.assertEqual(result['complete_diagnostics_sha256'], full['complete_diagnostics_sha256'])

    def test_seeded_independent_reductions(self):
        rng = random.Random(2901)
        for _ in range(80):
            n, k = rng.randint(3, 30), rng.randint(2, 6)
            rows = [tuple(rng.randrange(2) for _ in range(k+1)) for _ in range(n)]
            ids = [f'id-{i}' for i in range(n)]
            names = [f'c{i}' for i in range(k)]
            labels = [i % rng.randint(2, min(n, 8)) for i in range(n)]
            labels[0], labels[1] = 0, 1
            mapping = ('case,cluster\n' + ''.join(f'{c},g{g}\n' for c, g in zip(ids, labels))).encode()
            raw = ci.encoded(names, ids, rows)
            report = ci.review(raw, mapping, '0.2', 128)
            extrema = [[] for _ in names]
            for d in report['details']:
                label = int(d['removed_cluster'][1:])
                kept = [r for r, g in zip(rows, labels) if g != label]
                ps, effects = [], []
                for i in range(k):
                    w = sum(r[0] == 0 and r[i+1] == 1 for r in kept)
                    l = sum(r[0] == 1 and r[i+1] == 0 for r in kept)
                    ps.append(min(Fraction(1), Fraction(2*sum(math.comb(w+l,j) for j in range(min(w,l)+1)), 2**(w+l))))
                    effects.append(Fraction(w-l, len(kept)))
                adjusted = [None]*k
                running = Fraction(0)
                for rank, i in enumerate(sorted(range(k), key=lambda i:(ps[i],i))):
                    running = max(running, min(Fraction(1), (k-rank)*ps[i]))
                    adjusted[i] = running
                for i, c in enumerate(d['candidates']):
                    self.assertEqual(c['effect'], ci.rational(effects[i]))
                    extrema[i].append(effects[i])
                    self.assertEqual(c['reject_equal_discordance'], adjusted[i] <= Fraction(1,5))
                    self.assertEqual({x:c['holm_adjusted_p'][x] for x in ('numerator','denominator')}, ci.rational(adjusted[i]))
            for i, c in enumerate(report['candidates']):
                self.assertEqual(c['minimum_effect'], ci.rational(min(extrema[i])))
                self.assertEqual(c['maximum_effect'], ci.rational(max(extrema[i])))

    def test_mapping_validation(self):
        raw, mapping = ci.demo_inputs()
        lines = mapping.splitlines(keepends=True)
        bad = [b'', b'case,group\n', b''.join(lines[:-1]), mapping+lines[1],
               mapping+b'unknown,g\n', mapping.replace(b'related-a', b' bad'),
               b'case,cluster\n'+b''.join(f'synthetic-{i},same\n'.encode() for i in range(12)),
               mapping.replace(b'agreement', b'bad\x00group')]
        for value in bad:
            with self.assertRaises(ValueError):
                ci.review(raw, value)
        for cap in (-1, 129, True, 1.5):
            with self.assertRaises(ValueError):
                ci.review(raw, mapping, max_details=cap)
        with self.assertRaises(ValueError):
            ci.review(raw, mapping, 'NaN')

    def test_order_bom_quotes_and_immutability(self):
        raw, mapping = ci.demo_inputs()
        original = raw, mapping
        a = ci.review(raw, mapping)
        reversed_mapping = b'\xef\xbb\xbf'+b'case,cluster\r\n'+b'\r\n'.join(reversed(mapping.splitlines()[1:]))+b'\r\n'
        b = ci.review(raw, reversed_mapping)
        self.assertEqual(a['candidates'], b['candidates'])
        self.assertEqual(a['complete_diagnostics_sha256'], b['complete_diagnostics_sha256'])
        self.assertNotEqual(a['mapping_sha256'], b['mapping_sha256'])
        self.assertEqual((raw, mapping), original)
        quoted_raw = raw.replace(b'synthetic-0', b'"comma,\xf0\x9f\x90\xb8"')
        quoted_map = mapping.replace(b'synthetic-0', b'"comma,\xf0\x9f\x90\xb8"')
        self.assertEqual(ci.review(quoted_raw, quoted_map)['candidates'], a['candidates'])

    def test_singletons_and_agreement(self):
        raw = ci.encoded(['a','b'], ['x','y'], [(1,1,1),(0,0,0)])
        result = ci.review(raw, b'case,cluster\nx,X\ny,Y\n')
        self.assertEqual(result['clusters_changing_decision_or_direction'], 0)
        self.assertTrue(all(c['minimum_effect'] == ci.rational(Fraction(0)) for c in result['candidates']))

    def test_limits(self):
        for n in (1, 2001):
            raw = ci.encoded(['a','b'], [str(i) for i in range(n)], [(0,1,1)]*n)
            with self.assertRaises(ValueError):
                ci.review(raw, b'case,cluster\n')
        raw = ci.encoded(['a','b'], [str(i) for i in range(129)], [(0,1,1)]*129)
        mapping = ('case,cluster\n'+''.join(f'{i},{i}\n' for i in range(129))).encode()
        with self.assertRaises(ValueError):
            ci.review(raw, mapping)

    def test_portable_cli_pins_and_early_errors(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            folder = Path(temp)
            for name in ('cluster_influence.py','ladder_engine.py'):
                shutil.copyfile(Path(__file__).with_name(name), folder/name)
            script = str(folder/'cluster_influence.py')
            raw, mapping = ci.demo_inputs()
            (folder/'cases.csv').write_bytes(raw)
            (folder/'mapping.csv').write_bytes(mapping)
            args = ['--input',str(folder/'cases.csv'),'--mapping',str(folder/'mapping.csv'),
                    '--expected-input-sha256',ci.digest(raw),'--expected-mapping-sha256',ci.digest(mapping)]
            run = lambda options: subprocess.run([sys.executable,'-B',script,*options],capture_output=True)
            good = run(args)
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertEqual(json.loads(good.stdout)['clusters_checked'],3)
            for options in (args[:-1]+['bad'], ['--demo','--input','x'], ['--demo','--max-details','129'], []):
                bad = run(options)
                self.assertEqual(bad.returncode,2)
                self.assertEqual(bad.stdout,b'')
            self.assertEqual(run(['--demo']).returncode,0)

    def test_snapshot(self):
        folder = Path(__file__).parent
        provenance = json.loads((folder/'provenance.json').read_text())
        self.assertEqual(ci.digest((folder/'ladder_engine.py').read_bytes()), provenance['sha256'])


if __name__ == '__main__':
    unittest.main()
