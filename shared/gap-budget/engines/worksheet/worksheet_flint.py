#!/usr/bin/env python3
"""Check an ordered worksheet with exact quantities and explicit dimensions."""
from __future__ import annotations

import argparse
import json
import re
import sys

import engine

SCHEMA = 'worksheet-flint/1'
MAX_BYTES = 65536
MAX_STEPS = 32
NAME = re.compile(r'[A-Za-z][A-Za-z0-9_]{0,31}\Z')
REFERENCE = re.compile(r'\$([A-Za-z][A-Za-z0-9_]{0,31})(?![A-Za-z0-9_])')
FIELDS = {'name', 'expression', 'to', 'expect', 'at_least', 'at_most'}


class WorksheetError(ValueError):
    pass


class Parser(engine.Parser):
    """Reference tokens carry quantities directly, never expanded source text."""
    def __init__(self, source, values):
        references = {}
        def placeholder(match):
            references[match.start()] = match.group(1)
            return '1' + ' ' * (len(match.group()) - 1)
        masked = REFERENCE.sub(placeholder, source)
        super().__init__(masked)
        self.source = source
        self.values = values
        self.dependencies = set()
        self.tokens = [engine.Token('reference', references[t.pos], t.pos)
                       if t.pos in references else t for t in self.tokens]

    def atom(self):
        token = self.here
        if self.take('reference'):
            if token.text not in self.values:
                raise engine.UnitError(f'unknown or forward reference ${token.text}', token.pos)
            self.dependencies.add(token.text)
            return self.values[token.text]
        return super().atom()


def text(value, field):
    if type(value) is not str or not value.strip() or len(value) > engine.MAX_SOURCE:
        raise WorksheetError(f'{field} must be a nonempty string of at most {engine.MAX_SOURCE} characters')


def evaluate(document):
    if type(document) is not dict or set(document) != {'schema', 'steps'} or document['schema'] != SCHEMA:
        raise WorksheetError('expected exactly schema=worksheet-flint/1 and steps')
    steps = document['steps']
    if type(steps) is not list or not 1 <= len(steps) <= MAX_STEPS:
        raise WorksheetError(f'steps must be a list of 1..{MAX_STEPS} steps')
    values, rows = {}, []
    all_pass = True
    for index, step in enumerate(steps, 1):
        label = f'step {index}'
        try:
            if type(step) is not dict or not {'name', 'expression'} <= set(step) or set(step) - FIELDS:
                raise WorksheetError('step needs name and expression, with only documented optional fields')
            name = step['name']
            if type(name) is not str or not NAME.fullmatch(name):
                raise WorksheetError('name must match [A-Za-z][A-Za-z0-9_]{0,31}')
            label += f' ({name})'
            if name in values:
                raise WorksheetError('duplicate step name')
            for key, value in step.items():
                if key != 'name':
                    text(value, key)
            dependencies = set()
            def parse(expression):
                parser = Parser(expression, values)
                quantity = engine.Parser.bounded(parser.parse(), 0)
                dependencies.update(parser.dependencies)
                return quantity
            result = parse(step['expression'])
            checks, bounds = {}, {}
            for field in ('expect', 'at_least', 'at_most'):
                if field not in step:
                    continue
                quantity = parse(step[field])
                if quantity.dims != result.dims:
                    raise WorksheetError(f'{field} has incompatible dimensions')
                bounds[field] = quantity
                passes = (result.value == quantity.value if field == 'expect' else
                          result.value >= quantity.value if field == 'at_least' else
                          result.value <= quantity.value)
                checks[field] = {'base_value': str(quantity.value), 'passes': passes}
            if 'at_least' in bounds and 'at_most' in bounds and bounds['at_least'].value > bounds['at_most'].value:
                raise WorksheetError('lower bound exceeds upper bound')
            if 'to' in step:
                target = engine.Parser(step['to'], target=True).parse()
                if target.value <= 0 or target.dims != result.dims:
                    raise WorksheetError('target needs a positive scale and matching dimensions')
                displayed = engine.Parser.bounded(engine.Quantity(result.value / target.value, result.dims), 0).value
                unit = step['to']
            else:
                displayed, unit = result.value, engine.dimensions(result.dims)
            passed = all(check['passes'] for check in checks.values())
            all_pass &= passed
            rows.append({'request': dict(step), 'dependencies': sorted(dependencies),
                         'base_value': str(result.value), 'base_unit': engine.dimensions(result.dims),
                         'dimensions': dict(zip(('length', 'mass', 'time', 'data'), result.dims)),
                         'value': engine.exact_decimal(displayed), 'unit': unit,
                         'checks': checks, 'passes': passed})
            # Failed claims do not overwrite an exact result with the claimed value.
            values[name] = result
        except (engine.UnitError, WorksheetError) as exc:
            raise WorksheetError(f'{label}: {exc}') from exc
    return {'schema': SCHEMA, 'steps': rows, 'passes': all_pass}


def decode(data):
    if len(data) > MAX_BYTES:
        raise WorksheetError(f'input exceeds {MAX_BYTES} bytes')
    try:
        source = data.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise WorksheetError('input must be UTF-8') from exc
    depth, quoted, escaped = 0, False, False
    for char in source:
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in '[{':
            depth += 1
            if depth > 8:
                raise WorksheetError('input exceeds 8 nesting levels')
        elif char in ']}':
            depth -= 1
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise WorksheetError(f'duplicate JSON key {key!r}')
            result[key] = value
        return result
    def forbidden(value):
        raise WorksheetError('JSON numeric values are not supported; quantities are expression strings')
    try:
        return json.loads(source, object_pairs_hook=pairs, parse_int=forbidden,
                          parse_float=forbidden, parse_constant=forbidden)
    except (ValueError, RecursionError) as exc:
        raise WorksheetError(f'invalid worksheet JSON: {exc}') from exc


def demo_document():
    return {'schema': SCHEMA, 'steps': [
        {'name': 'bytes', 'expression': '750 MiB'},
        {'name': 'rate', 'expression': '12 MiB/s'},
        {'name': 'transfer', 'expression': '$bytes / $rate', 'to': 's', 'expect': '62.5 s'},
        {'name': 'overhead', 'expression': '1500 ms'},
        {'name': 'total', 'expression': '$transfer + $overhead', 'to': 's',
         'expect': '64 s', 'at_most': '1 min'}]}


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('command', choices=('demo', 'check'))
    args = cli.parse_args(argv)
    try:
        document = demo_document() if args.command == 'demo' else decode(sys.stdin.buffer.read(MAX_BYTES + 1))
        result = evaluate(document)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0 if result['passes'] else 1
    except WorksheetError as exc:
        print(f'worksheet-flint: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
