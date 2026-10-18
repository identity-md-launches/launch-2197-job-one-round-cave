#!/usr/bin/env python3
"""Replay timestamp coverage and check explicit duration budgets with exact units."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'engines/timeline'))
sys.path.insert(0, str(HERE / 'engines/worksheet'))
import timeline_gaps as gaps
import worksheet_flint as worksheet

SCHEMA = 'gap-budget/1'


def seconds(microseconds):
    if type(microseconds) is not int or microseconds < 0:
        raise ValueError('duration must be nonnegative integer microseconds')
    return f'({microseconds} / 1000000) * s'


def budget(expression):
    if not isinstance(expression, str) or not 1 <= len(expression) <= worksheet.engine.MAX_SOURCE:
        raise ValueError('budget must be a bounded time expression')
    quantity = worksheet.engine.Parser(expression).parse()
    if quantity.dims != (0, 0, 1, 0) or quantity.value < 0:
        raise ValueError('budget must have time dimensions and be nonnegative')
    return expression


def review(pack, start, end, max_uncovered, max_gap, limit=50):
    # These expressions are parsed as quantities, never as source code or refs.
    max_uncovered, max_gap = budget(max_uncovered), budget(max_gap)
    coverage = gaps.analyze(pack, start, end, limit)
    durations = coverage['durations_us']
    request = {'schema': worksheet.SCHEMA, 'steps': [
        {'name': 'window', 'expression': seconds(durations['window']), 'to': 's'},
        {'name': 'covered', 'expression': seconds(durations['covered']), 'to': 's'},
        {'name': 'uncovered', 'expression': seconds(durations['uncovered']),
         'to': 's', 'at_most': max_uncovered},
        {'name': 'longest_gap', 'expression': seconds(durations['longest_gap']),
         'to': 's', 'at_most': max_gap},
        {'name': 'accounted', 'expression': '$covered + $uncovered',
         'expect': '$window', 'to': 's'},
        {'name': 'uncovered_fraction', 'expression': '$uncovered / $window'}]}
    calculated = worksheet.evaluate(request)
    return {'schema': SCHEMA, 'coverage': coverage, 'worksheet_request': request,
            'worksheet_result': calculated, 'passes': calculated['passes'],
            'interpretation': [
                'Budgets are user-supplied policy on timestamp interval coverage only.',
                'Passing is not evidence of availability, complete logs, honest timestamps or clock accuracy.',
                'Gaps are not measured downtime; wider asserted uncertainty may remove them.',
                'Entire pack is replayed before selecting the window. Undated lines remain explicit.',
                'All totals precede the displayed-gap cap. Fraction uses the complete window.',
                'A trusted pack digest identifies bytes; replay establishes consistency, not authorship.'
            ]}


def demo():
    pack = gaps.replay.make_pack([('synthetic-worker.log',
        b'2026-10-18T10:00:01Z accepted\n'
        b'2026-10-18T10:00:02Z processing\n'
        b'undated diagnostic\n'
        b'2026-10-18T10:00:04Z completed\n')], ignore_unmatched=True)
    result = review(pack, '2026-10-18T10:00:00Z', '2026-10-18T10:00:06Z', '2500 ms', '1 s', 1)
    result['example'] = 'synthetic demonstration, not an observed incident or availability claim'
    result['pack_sha256'] = gaps.replay.digest(gaps.replay.canonical(pack) + b'\n')
    return result


def source_hashes():
    return {str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((HERE / 'engines').rglob('*.py'))}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo')
    check = commands.add_parser('check')
    check.add_argument('pack')
    check.add_argument('--expected-sha256', required=True,
                       help='independently retained digest of exact pack bytes')
    check.add_argument('--start', required=True)
    check.add_argument('--end', required=True)
    check.add_argument('--max-uncovered', required=True)
    check.add_argument('--max-gap', required=True)
    check.add_argument('--limit', type=int, default=50)
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        else:
            if not re.fullmatch(r'[0-9a-f]{64}', args.expected_sha256):
                raise ValueError('expected SHA-256 must be 64 lowercase hexadecimal characters')
            raw = gaps.replay.read_workspace(args.pack, gaps.replay.MAX_PACK_BYTES)
            digest = gaps.replay.digest(raw)
            if digest != args.expected_sha256:
                raise ValueError('pack differs from retained SHA-256')
            result = review(gaps.replay.load_pack(raw), args.start, args.end,
                            args.max_uncovered, args.max_gap, args.limit)
            result['pack_sha256'] = digest
        result['source_sha256'] = source_hashes()
        output = json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2) + '\n'
    except (OSError, ValueError, worksheet.engine.UnitError, OverflowError, RecursionError) as exc:
        print('gap-budget: ' + ascii(str(exc)), file=sys.stderr)
        return 2
    sys.stdout.write(output)
    return 0 if result['passes'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
