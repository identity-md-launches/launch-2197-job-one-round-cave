"""Offline behavioral checks; no network, environment or external fixtures."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('json_crosscheck', HERE / 'json_crosscheck.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)
ROOT = HERE.parents[2]
SCRATCH = ROOT / 'test' / 'scratch'


class CrosscheckTests(unittest.TestCase):
    def report(self, first, second, cap=100):
        return tool.review([('first', first), ('second', second)], cap)

    def check_citation(self, documents, cite, expected):
        raw = documents[cite['source_index']][1]
        token = raw[cite['byte_start']:cite['byte_end']]
        self.assertEqual(json.loads(token), expected)
        self.assertEqual(hashlib.sha256(token).hexdigest(), cite['token_sha256'])
        self.assertEqual(hashlib.sha256(expected.encode()).hexdigest(), cite['decoded_sha256'])
        self.assertEqual(token[:64].hex(), cite['preview_hex'])
        self.assertEqual(max(0, len(token)-64), cite['omitted_token_bytes'])

    def test_escaped_demo_and_exact_ranges(self):
        report = tool.review(tool.DEMO)
        self.assertEqual(report['finding_count'], 3)
        expected = [('owner', '\u043ewner'), ('pay-owner', 'pay-\uff4fwner'), ('\u043ewner', 'owner')]
        for finding, (a, b) in zip(report['findings'], expected):
            self.check_citation(tool.DEMO, finding['earlier'], a)
            self.check_citation(tool.DEMO, finding['later'], b)
        self.assertEqual(report['findings'][1]['later']['location'],
                         [['value', 1], ['index', 0], ['key', 0]])

    def test_equivalent_encodings_are_identical(self):
        report = self.report(b'{"owner":1}', br'{"\u006fwner":2}')
        self.assertEqual(report['finding_count'], 0)
        self.assertEqual(report['member_names'], 2)

    def test_same_document_and_values_excluded(self):
        a = '{"owner":1,"\u043ewner":2,"value":"\uff4fwner"}'.encode()
        report = self.report(a, br'["owner","\u043ewner",{}]')
        self.assertEqual(report['finding_count'], 0)
        self.assertEqual(report['member_names'], 3)

    def test_duplicates_and_two_witnesses(self):
        docs = [('a', '{"owner":0,"\u043ewner":0,"owner":1}'.encode()),
                ('b', b'{"owner":0,"owner":1}'),
                ('c', '{"\uff4fwner":0}'.encode())]
        report = tool.review(docs)
        self.assertEqual(report['finding_count'], 3)
        self.check_citation(docs, report['findings'][0]['earlier'], '\u043ewner')
        self.check_citation(docs, report['findings'][2]['earlier'], 'owner')
        self.assertEqual(report['sources'][0]['member_names'], 3)

    def test_multibyte_prefix_quotes_backslashes_and_surrogate_pair(self):
        docs = [('a', '{"é":"🐸", "a/\\\"\\\\🐸":0}'.encode()),
                ('b', br'{"\uff41/\"\\\ud83d\udc38":1}')]
        report = tool.review(docs)
        self.assertEqual(report['finding_count'], 1)
        finding = report['findings'][0]
        self.check_citation(docs, finding['earlier'], 'a/"\\🐸')
        self.check_citation(docs, finding['later'], '\uff41/"\\🐸')

    def test_key_order_is_original_byte_order(self):
        # The nested key comes before the root's second key in the source.
        docs = [('a', '{"nested":{"\u043ewner":1},"owner":2}'.encode()),
                ('b', '{"\uff4fwner":0}'.encode())]
        report = tool.review(docs)
        self.check_citation(docs, report['findings'][0]['earlier'], '\u043ewner')

    def test_full_member_names_not_identifier_fragments(self):
        report = self.report(b'{"prefix-owner":1}', '{"prefix-\u043ewner":2}'.encode())
        self.assertEqual(report['finding_count'], 1)
        report = self.report(b'{"prefix-owner":1}', '{"suffix-\u043ewner":2}'.encode())
        self.assertEqual(report['finding_count'], 0)

    def test_cap_exact_count_and_still_validates_late_input(self):
        docs = tool.DEMO + [('late', b'not json')]
        with self.assertRaises(ValueError):
            tool.review(docs, 1)
        report = tool.review(tool.DEMO, 1)
        self.assertEqual((report['finding_count'], report['retained_findings'],
                          report['omitted_findings'], report['truncated']), (3, 1, 2, True))

    def test_malformed_and_non_json_inputs(self):
        invalid = [b'', b'\xff', b'\xef\xbb\xbf{}', b'{} trailing', b'{"a":1,}',
                   b'{"a":NaN}', b'Infinity', b'-Infinity', br'{"\ud800":1}',
                   br'{"x":"\udfff"}', br'{"x":"\ud800a"}', b'"unterminated',
                   b'{"a":01}', b'{"a":"\x00"}']
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.report(b'{}', raw)

    def test_opaque_big_numbers_and_primitive_documents(self):
        raw = b'{"x":' + b'9'*5000 + b',"y":1e9999999999}'
        report = self.report(raw, b'[null,true,false,"word",0]')
        self.assertEqual(report['member_names'], 2)
        self.assertEqual(report['finding_count'], 0)
        self.assertEqual(self.report(b'null', b'false')['member_names'], 0)

    def test_depth_node_key_and_total_budgets(self):
        self.report(b'[]', b'['*64 + b'0' + b']'*64)
        with self.assertRaises(ValueError):
            self.report(b'{}', b'['*65 + b'0' + b']'*65)
        with mock.patch.object(tool.parser_engine, 'MAX_NODES', 3):
            with self.assertRaises(ValueError):
                self.report(b'{}', b'[0,1,2]')
        with mock.patch.object(tool, 'MAX_KEYS', 1):
            with self.assertRaises(ValueError):
                self.report(b'{"a":1}', b'{"b":2}')
        with self.assertRaises(ValueError):
            self.report(b'{}', json.dumps({'a'*4097: 0}).encode())
        self.report(b'{}', json.dumps({'a'*4096: 0}).encode())
        with mock.patch.object(tool, 'MAX_TOTAL_BYTES', 3):
            with self.assertRaises(ValueError):
                self.report(b'{}', b'{}')
        with self.assertRaises(ValueError):
            self.report(b'{}', b' '*(tool.lantern.MAX_BYTES+1))

    def test_invalid_api_arguments(self):
        for docs in [None, [], [('a', b'{}')], [('a', b'{}')]*33,
                     [('same', b'{}'), ('same', b'{}')],
                     [('a', '{}'), ('b', b'{}')], [('a', b'{}'), ('', b'{}')],
                     [('a', b'{}'), ('b',)], [('a', b'{}'), (1, b'{}')]]:
            with self.subTest(docs=docs), self.assertRaises(ValueError):
                tool.review(docs)
        for cap in [0, 1001, True, 1.0, '1']:
            with self.subTest(cap=cap), self.assertRaises(ValueError):
                tool.review(tool.DEMO, cap)

    def test_escaped_output_labels_and_previews(self):
        docs = [('label\x1b[31m\u202e', b'{"x":1}'),
                ('second', '{"ｘ":2}'.encode())]
        report = tool.review(docs)
        self.assertTrue(report['sources'][0]['label'].isascii())
        self.assertNotIn('\x1b', report['sources'][0]['label'])
        self.assertNotIn('\u202e', report['sources'][0]['label'])
        self.assertTrue(report['findings'][0]['later']['decoded_preview'].isascii())
        output = tool.render(report)
        self.assertTrue(output.isascii())
        self.assertEqual(json.loads(output), report)

    def test_long_key_previews_are_explicitly_truncated(self):
        docs = [('a', json.dumps({'owner'+'x'*100:0}).encode()),
                ('b', json.dumps({'\u043ewner'+'x'*100:0}).encode())]
        report = tool.review(docs)
        cite = report['findings'][0]['later']
        self.assertEqual(cite['omitted_decoded_characters'], 65)
        self.assertEqual(cite['omitted_token_bytes'], 48)
        self.check_citation(docs, cite, '\u043ewner'+'x'*100)

    def test_exhaustive_reference_on_seeded_generated_documents(self):
        rng = random.Random(73729)
        names = ['owner', '\u043ewner', '\uff4fwner', 'path/owner', 'path/\u043ewner',
                 'a', '\u0430', 'é', 'e\u0301', '', 'OWNER', '🐸', 'name\u200b']
        for _ in range(100):
            docs, decoded = [], []
            for index in range(rng.randint(2, 5)):
                chosen = [rng.choice(names) for _ in range(rng.randint(0, 12))]
                raw = ('{' + ','.join(json.dumps(k, ensure_ascii=rng.choice([True, False]))+':0'
                                      for k in chosen) + '}').encode()
                docs.append((str(index), raw))
                decoded.append(chosen)
            expected = []
            for index, keys in enumerate(decoded):
                for key in keys:
                    # Independent brute-force pair search, intentionally quadratic.
                    match = next(((prior, old) for prior in range(index) for old in decoded[prior]
                                  if old != key and
                                  tool.unicodedata.normalize('NFKC', old).translate(tool.lantern.LOOKALIKES)
                                  == tool.unicodedata.normalize('NFKC', key).translate(tool.lantern.LOOKALIKES)), None)
                    if match is not None:
                        expected.append((match[0], match[1], index, key))
            cap = rng.randint(1, 7)
            report = tool.review(docs, cap)
            self.assertEqual(report['finding_count'], len(expected))
            self.assertEqual(report['omitted_findings'], max(0, len(expected)-cap))
            self.assertEqual(report['member_names'], sum(map(len, decoded)))
            for finding, (prior, old, current, key) in zip(report['findings'], expected):
                self.assertEqual(finding['earlier']['source_index'], prior)
                self.assertEqual(finding['later']['source_index'], current)
                self.check_citation(docs, finding['earlier'], old)
                self.check_citation(docs, finding['later'], key)

    def test_cli_demo_status_and_invalid_late_file_no_partial_output(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(tool.main(['--demo', '--max-findings', '1']), 0)
        self.assertEqual(json.loads(out.getvalue())['omitted_findings'], 2)
        self.assertEqual(err.getvalue(), '')
        with mock.patch.object(tool, 'read_documents', return_value=tool.DEMO):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(tool.main(['--files', 'a', 'b']), 1)
        with mock.patch.object(tool, 'read_documents', return_value=tool.DEMO+[('bad', b'{')]):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(tool.main(['--files', 'a', 'b']), 2)
            self.assertEqual(out.getvalue(), '')
            self.assertIn('error', json.loads(err.getvalue()))

    def test_output_budget_no_partial_result(self):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(tool, 'MAX_OUTPUT', 1):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(tool.main(['--demo']), 2)
        self.assertEqual(out.getvalue(), '')
        self.assertIn('4 MiB', err.getvalue())

    def test_cli_workspace_containment_and_duplicate_path(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as directory:
            base = Path(directory)
            (base/'a.json').write_bytes(b'{"owner":1}')
            (base/'b.json').write_bytes(br'{"\u043ewner":2}')
            (base/'alias.json').symlink_to('a.json')
            relative = base.relative_to(ROOT)
            paths = [str(relative/'a.json'), str(relative/'b.json')]
            self.assertEqual(len(tool.read_documents(paths)), 2)
            with self.assertRaises(ValueError):
                tool.read_documents([paths[0], str(relative/'alias.json')])
            with self.assertRaises(ValueError):
                tool.read_documents([paths[0], '../outside.json'])
            (base/'outside.json').symlink_to(ROOT.parent/'outside.json')
            with self.assertRaises(ValueError):
                tool.read_documents([paths[0], str(relative/'outside.json')])
            result = subprocess.run([sys.executable, '-B', str(HERE/'json_crosscheck.py'),
                                     '--files', *paths], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)['finding_count'], 1)

    def test_portable_four_folder_copy(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as directory:
            base = Path(directory)
            for name in ['json-crosscheck', 'json-citations', 'json-lantern', 'unicode-lantern']:
                target = base/'tools'/name
                target.mkdir(parents=True)
                for path in (HERE.parent/name).glob('*.py'):
                    if not path.name.startswith('test_'):
                        shutil.copyfile(path, target/path.name)
            result = subprocess.run([sys.executable, '-B', 'tools/json-crosscheck/json_crosscheck.py',
                                     '--demo'], cwd=base, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['finding_count'], 3)


if __name__ == '__main__':
    unittest.main()
