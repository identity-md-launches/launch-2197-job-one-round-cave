#!/usr/bin/env python3
"""Find uncovered portions of a chosen window in fully replayed log evidence."""
import argparse
from datetime import datetime
import re
import sys

import replay

FORMAT = 'timeline-gaps/1'
HEX = re.compile(r'[0-9a-f]{64}\Z')


def instant(text):
    """Query endpoints are instants, never precision-expanded log timestamps."""
    if not isinstance(text, str) or replay.engine.ISO.fullmatch(text) is None:
        raise replay.ReplayError('endpoint needs offset-aware ISO text with at most 6 fractional digits')
    # Validate calendar, explicit offset range, and UTC conversion with the fixed
    # parser. Its precision-expanded end is deliberately not used for queries.
    # Do not use parse_stamp here: the maximum printable instant is a valid end.
    body, offset = replay.engine.ISO.fullmatch(text).groups()
    if offset != 'Z' and (int(offset[1:3]) > 23 or int(offset[4:]) > 59):
        raise replay.ReplayError('endpoint offset is outside ±23:59')
    dt = datetime.fromisoformat(body + ('+00:00' if offset == 'Z' else offset))
    return replay.engine.micros(dt)


def partition(intervals, start, end):
    """Exact union and complement; touching half-open coverage has no gap."""
    clipped = sorted((max(a, start), min(b, end)) for a, b in intervals
                     if a < end and b > start)
    union = []
    for a, b in clipped:
        if union and a <= union[-1][1]:
            union[-1][1] = max(union[-1][1], b)
        else:
            union.append([a, b])
    gaps, cursor = [], start
    for a, b in union:
        if cursor < a:
            gaps.append([cursor, a])
        cursor = b
    if cursor < end:
        gaps.append([cursor, end])
    return union, gaps


def analyze(pack, start_text, end_text, limit=50):
    if type(limit) is not int or not 0 <= limit <= 200:
        raise replay.ReplayError('limit must be an integer in 0..200')
    start, end = instant(start_text), instant(end_text)
    if start >= end:
        raise replay.ReplayError('window start must precede end')
    checked = replay.verify_pack(pack)  # Always verify all evidence before filtering.
    events = pack['timeline']['events']
    intervals = [(instant(e['start_utc']), instant(e['end_utc_exclusive'])) for e in events]
    covered, gaps = partition(intervals, start, end)
    duration = end - start
    uncovered = sum(b-a for a, b in gaps)
    def describe(pair):
        a, b = pair
        return {'start_utc_inclusive': replay.engine.utc_text(a),
                'end_utc_exclusive': replay.engine.utc_text(b), 'duration_us': b-a}
    return {
        'format': FORMAT, 'replay': checked,
        'window': describe([start, end]),
        'counts': {'timestamped_events': len(events),
                   'intersecting_events': sum(a < end and b > start for a, b in intervals),
                   'undated_lines': len(pack['timeline']['omitted']),
                   'covered_components': len(covered), 'gaps_total': len(gaps),
                   'gaps_shown': min(len(gaps), limit),
                   'gaps_not_shown': max(0, len(gaps)-limit)},
        'durations_us': {'window': duration, 'covered': duration-uncovered,
                         'uncovered': uncovered, 'longest_gap': max((b-a for a, b in gaps), default=0)},
        'gaps': [describe(pair) for pair in gaps[:limit]],
        'engine_sha256': pack['engine_sha256'], 'options': dict(pack['options']),
        'interpretation': (
            'Gaps are the complement of the union of dated-event uncertainty intervals '
            'within the requested half-open window. They are gaps in this evidence model, '
            'not proof of inactivity, downtime, missing collection, or causality. '
            'Timestamp precision is modeled as truncation; clock bounds are analyst assertions. '
            'Undated lines cannot be placed. Replay proves internal consistency, not '
            'authenticity or completeness. Messages and source bytes are not echoed.')}


def demo():
    pack = replay.make_pack([('worker.log',
        b'2026-10-18T10:00:01Z accepted\n'
        b'2026-10-18T10:00:02Z processing\n'
        b'untimestamped diagnostic\n'
        b'2026-10-18T10:00:04Z completed\n')], ignore_unmatched=True)
    result = analyze(pack, '2026-10-18T10:00:00Z', '2026-10-18T10:00:06Z')
    result['example'] = 'synthetic, not a real incident'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo')
    inspect = commands.add_parser('analyze')
    inspect.add_argument('pack')
    inspect.add_argument('--start', required=True, help='inclusive ISO instant')
    inspect.add_argument('--end', required=True, help='exclusive ISO instant')
    inspect.add_argument('--limit', type=int, default=50)
    inspect.add_argument('--expect-sha256', help='trusted lowercase digest of exact pack bytes')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        else:
            raw = replay.read_workspace(args.pack, replay.MAX_PACK_BYTES)
            digest = replay.digest(raw)
            if args.expect_sha256 is not None:
                if HEX.fullmatch(args.expect_sha256) is None:
                    raise replay.ReplayError('expected digest must be 64 lowercase hex digits')
                if digest != args.expect_sha256:
                    raise replay.ReplayError('pack does not match expected SHA-256')
            result = analyze(replay.load_pack(raw), args.start, args.end, args.limit)
            result['pack_sha256'] = digest
        sys.stdout.buffer.write(replay.canonical(result) + b'\n')
        return 0
    except (OSError, ValueError, OverflowError, RecursionError) as exc:
        print('timeline-gaps: ' + replay.engine.visible(str(exc)), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
