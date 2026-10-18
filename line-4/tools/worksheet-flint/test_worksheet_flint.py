import copy
from fractions import Fraction
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest

import worksheet_flint as w


def doc(*steps):
    return {'schema': w.SCHEMA, 'steps': list(steps)}


def step(name, expression, **extra):
    return dict(name=name, expression=expression, **extra)


class WorksheetTests(unittest.TestCase):
    def test_demo_flags_actual_failed_budget(self):
        result = w.evaluate(w.demo_document())
        self.assertFalse(result['passes'])
        total = result['steps'][-1]
        self.assertEqual(total['value'], '64')
        self.assertTrue(total['checks']['expect']['passes'])
        self.assertFalse(total['checks']['at_most']['passes'])
        self.assertEqual(total['dependencies'], ['overhead', 'transfer'])

    def test_conversion_does_not_round_or_change_reference_units(self):
        result = w.evaluate(doc(step('x', '1 m / 3 s', to='km/h'),
                                step('y', '$x * 3 s', to='cm', expect='1 m')))
        self.assertTrue(result['passes'])
        self.assertEqual(result['steps'][0]['base_value'], '1/3')
        self.assertEqual(result['steps'][0]['value'], '1.2')
        self.assertEqual(result['steps'][1]['value'], '100')

    def test_reference_check_uses_previous_quantity(self):
        result = w.evaluate(doc(step('min', '3 s'), step('max', '4 s'),
                                step('actual', '3500 ms', at_least='$min', at_most='$max')))
        self.assertTrue(result['passes'])
        self.assertEqual(result['steps'][-1]['dependencies'], ['max', 'min'])

    def test_failed_claim_keeps_computed_value_and_continues(self):
        result = w.evaluate(doc(step('x', '2 m', expect='3 m'),
                                step('y', '$x * 2', expect='4 m')))
        self.assertFalse(result['passes'])
        self.assertTrue(result['steps'][-1]['passes'])
        self.assertEqual(result['steps'][-1]['base_value'], '4')

    def test_dimension_mismatches_zero_included(self):
        for expr, options in [('$x + 0 s', {}), ('$x', {'expect': '0 s'}),
                              ('$x', {'at_most': '0 s'}), ('$x', {'to': 's'})]:
            with self.subTest(expr=expr, options=options), self.assertRaises(w.WorksheetError):
                w.evaluate(doc(step('x', '0 m'), step('y', expr, **options)))

    def test_references_cannot_redefine_units_or_inject_code(self):
        result = w.evaluate(doc(step('m', '2 s'), step('x', '3 m'),
                                step('y', '$m * 3', expect='6 s')))
        self.assertEqual(result['steps'][1]['base_unit'], 'm')
        for expr in ('$missing', '$later', '$x', '__import__(1)', '$' + 'a'*33,
                     '$a.__class__', '$a[0]', '$a;1', '$a_b', '$a$a', '2 $a'):
            with self.subTest(expr=expr), self.assertRaises(w.WorksheetError):
                w.evaluate(doc(step('a', '1 m'), step('x', expr), step('later', '1')))

    def test_order_duplicate_name_cycles_and_no_global_state(self):
        invalid = [doc(step('a', '$a')), doc(step('a', '$b'), step('b', '$a')),
                   doc(step('a', '1'), step('a', '2'))]
        for document in invalid:
            with self.assertRaises(w.WorksheetError):
                w.evaluate(document)
        w.evaluate(doc(step('a', '1')))
        with self.assertRaises(w.WorksheetError):
            w.evaluate(doc(step('b', '$a')))

    def test_zero_division_and_powers(self):
        result = w.evaluate(doc(step('a', '2 m'), step('b', '$a^2', expect='4 * m^2'),
                                step('c', '(-$a)^2 / $a', expect='2 m')))
        self.assertTrue(result['passes'])
        for expr in ('$a / 0', '$a^13', '$a^(1/2)', '$a^$a'):
            with self.subTest(expr=expr), self.assertRaises(w.WorksheetError):
                w.evaluate(doc(step('a', '2 m'), step('b', expr)))

    def test_schema_types_unknown_fields_and_bounds(self):
        invalid = [None, [], {}, doc(), doc(*[step('a'+str(i), '1') for i in range(33)]),
                   doc(step('a', '1', to=None)), doc(step('a', '1', to='0')),
                   doc(step('a', '1', to='-1')), doc(step('a', '1', extra='1')),
                   doc(step('a', '1', at_least='2', at_most='1')),
                   doc(step('a', '1', expression2='x')), doc(step('bad-name', '1')),
                   doc(step(True, '1')), doc(step('a', True)), doc(step('a', '')),
                   doc(step('a', '1'*4097)), doc(step('a', '1', to='$a'))]
        for document in invalid:
            with self.subTest(document=str(document)[:150]), self.assertRaises(w.WorksheetError):
                w.evaluate(document)

    def test_json_bounds_duplicates_and_non_numbers(self):
        for data in (b'{}x', b'\xff', b'{"schema":1}', b'NaN', b'1.0', b'1e999999',
                     b'{' + b'"x":{},"x":{}' + b'}', b'['*9+b']'*9,
                     b' '*(w.MAX_BYTES+1)):
            with self.subTest(data=data[:50]), self.assertRaises(w.WorksheetError):
                w.decode(data)
        self.assertEqual(w.decode(b'{"a":"\\\"[[["}'), {'a': '"[[['})
        self.assertEqual(w.decode(b' '*(w.MAX_BYTES-2)+b'{}'), {})

    def test_reference_numeric_and_dimension_budgets(self):
        for expression in ('$x^12', '(' * 40 + '$x' + ')' * 40, '+'.join(['$x']*130)):
            source = '1e100' if expression == '$x^12' else '1'
            with self.subTest(expression=expression), self.assertRaises(w.WorksheetError):
                w.evaluate(doc(step('x', source), step('y', expression)))
        steps = [step('x0', 'm^12')]
        steps += [step('x'+str(i), '$x'+str(i-1)+'^12') for i in range(1, 4)]
        with self.assertRaises(w.WorksheetError):
            w.evaluate(doc(*steps))

    def test_independent_seeded_fraction_chains_and_immutability(self):
        rng = random.Random(29)
        for _ in range(300):
            distance, duration, overhead = rng.randint(-10000,10000), rng.randint(1,1000), rng.randint(-100,100)
            document = doc(step('distance', f'{distance} cm'), step('duration', f'{duration} ms'),
                           step('speed', '$distance / $duration', to='km/h'),
                           step('shifted', '($speed * $duration) + '+str(overhead)+' mm', to='cm'))
            original = copy.deepcopy(document)
            result = w.evaluate(document)
            self.assertEqual(document, original)
            speed = Fraction(distance,100) / Fraction(duration,1000)
            self.assertEqual(Fraction(result['steps'][2]['base_value']), speed)
            self.assertEqual(Fraction(result['steps'][2]['value']), speed*Fraction(18,5))
            self.assertEqual(Fraction(result['steps'][3]['value']), Fraction(distance)+Fraction(overhead,10))

    def test_stable_output_and_complete_cli_validation(self):
        script = str(Path(__file__).with_name('worksheet_flint.py'))
        for document, status in [(w.demo_document(),1), (doc(step('a','1 m',expect='100 cm')),0),
                                 (doc(step('a','1',expect='2'),step('b','0/0')),2)]:
            data = json.dumps(document).encode()
            result = subprocess.run([sys.executable,'-B',script,'check'],input=data,
                                    capture_output=True,timeout=5)
            self.assertEqual(result.returncode,status,result.stderr)
            if status == 2:
                self.assertEqual(result.stdout,b'')
                self.assertIn(b'step 2',result.stderr)
            else:
                self.assertEqual(json.loads(result.stdout), w.evaluate(document))
        self.assertEqual(w.evaluate(w.demo_document()), w.evaluate(w.demo_document()))


if __name__ == '__main__':
    unittest.main()
