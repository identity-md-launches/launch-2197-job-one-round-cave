#!/usr/bin/env python3
"""Compare decoded member names across explicitly selected JSON documents."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unicodedata


ENGINE = Path(__file__).resolve().parents[1] / 'json-citations' / 'json_citations.py'
spec = importlib.util.spec_from_file_location('crosscheck_json_citations', ENGINE)
citations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(citations)
parser_engine = citations.lantern
lantern = parser_engine.lantern

MAX_FILES = 32
MAX_TOTAL_BYTES = 8 * 1024 * 1024
MAX_KEYS = 100000
MAX_KEY_CHARS = 4096
MAX_OUTPUT = 4 * 1024 * 1024
PREVIEW_CHARS = 40
PREVIEW_BYTES = 64


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class Number:
    """Do not convert numbers to floats/ints or confuse them with JSON strings."""
    def __init__(self, spelling):
        pass


def decoded_keys(raw):
    """Validate a complete document before yielding (key, structural path, span).

    Duplicate member names remain separate pairs. Values are validated but never
    compared. The inherited byte tokenizer is used only after JSON validation.
    """
    text = raw.decode('utf-8', errors='strict')
    parser_engine.check_depth(text)
    tree = json.loads(text, object_pairs_hook=parser_engine.Pairs,
                      parse_int=Number, parse_float=Number,
                      parse_constant=parser_engine.reject_constant)
    pending, keys, nodes = [(tree, ())], [], 0
    while pending:
        value, path = pending.pop()
        nodes += 1
        if nodes > parser_engine.MAX_NODES:
            raise ValueError('JSON value count exceeds 20000')
        if isinstance(value, parser_engine.Pairs):
            children = []
            for index, (key, child) in enumerate(value):
                if len(key) > MAX_KEY_CHARS:
                    raise ValueError('decoded member name exceeds 4096 characters')
                key.encode('utf-8', errors='strict')
                keys.append((key, path + (('key', index),)))
                children.append((child, path + (('value', index),)))
            pending.extend(reversed(children))
        elif isinstance(value, list):
            pending.extend((child, path + (('index', index),))
                           for index, child in reversed(list(enumerate(value))))
        elif isinstance(value, str):
            # Reject lone surrogate escapes even in values, not just in keys.
            value.encode('utf-8', errors='strict')
    spans = citations.string_tokens(raw)
    # Original lexical order, independent of the object-first validation walk.
    keys.sort(key=lambda item: spans[item[1]][0])
    return [(key, path, spans[path]) for key, path in keys]


def witness(raw, source_index, key, path, span):
    start, end = span
    encoded = key.encode('utf-8')
    return dict(source_index=source_index, location=[list(part) for part in path],
                byte_start=start, byte_end=end, token_sha256=digest(raw[start:end]),
                preview_hex=raw[start:min(end, start + PREVIEW_BYTES)].hex(),
                omitted_token_bytes=max(0, end - start - PREVIEW_BYTES),
                decoded_sha256=digest(encoded), decoded_characters=len(key),
                decoded_preview=lantern.escaped(key[:PREVIEW_CHARS]),
                omitted_decoded_characters=max(0, len(key) - PREVIEW_CHARS))


def review(documents, max_findings=100):
    """Review ordered (unique label, original bytes) pairs without opening inputs."""
    if type(documents) not in (list, tuple) or not 2 <= len(documents) <= MAX_FILES:
        raise ValueError('provide between 2 and 32 documents')
    if type(max_findings) is not int or not 1 <= max_findings <= 1000:
        raise ValueError('max_findings must be an integer between 1 and 1000')
    total_bytes, labels = 0, set()
    for document in documents:
        if type(document) not in (list, tuple) or len(document) != 2:
            raise ValueError('each document must be a label and bytes pair')
        label, raw = document
        if not isinstance(label, str) or not 1 <= len(label) <= 1024:
            raise ValueError('label must contain 1 to 1024 characters')
        if label in labels:
            raise ValueError('document labels must be unique')
        labels.add(label)
        if not isinstance(raw, bytes) or len(raw) > lantern.MAX_BYTES:
            raise ValueError('each document must be at most 2 MiB of UTF-8 bytes')
        total_bytes += len(raw)
    if total_bytes > MAX_TOTAL_BYTES:
        raise ValueError('documents exceed 8 MiB total byte budget')

    prior, findings, sources = {}, [], []
    key_count, finding_count = 0, 0
    for source_index, (label, raw) in enumerate(documents):
        keys = decoded_keys(raw)
        key_count += len(keys)
        if key_count > MAX_KEYS:
            raise ValueError('documents exceed 100000 member name budget')
        sources.append(dict(index=source_index, label=lantern.escaped(label),
                            sha256=digest(raw), bytes=len(raw), member_names=len(keys)))
        pending = {}
        for key, path, span in keys:
            skeleton = unicodedata.normalize('NFKC', key).translate(lantern.LOOKALIKES)
            earlier = prior.get(skeleton, [])
            first = next((entry for entry in earlier if entry[0] != key), None)
            if first is not None:
                finding_count += 1
                if len(findings) < max_findings:
                    findings.append(dict(rule='cross-file-decoded-key-collision',
                                         skeleton_sha256=digest(skeleton.encode('utf-8')),
                                         earlier=first[1],
                                         later=witness(raw, source_index, key, path, span)))
            # Two earliest distinct spellings suffice to find the earliest
            # unequal witness for any later spelling. Merge only after EOF.
            candidates = pending.setdefault(skeleton, list(earlier))
            if len(candidates) < 2 and all(entry[0] != key for entry in candidates):
                candidates.append((key, witness(raw, source_index, key, path, span)))
        prior.update(pending)

    return dict(tool='json-crosscheck/1', unicode_version=unicodedata.unidata_version,
                engine_sha256={p.parent.name: digest(p.read_bytes()) for p in
                               (ENGINE, citations.DEPENDENCY, parser_engine.SCANNER)},
                sources=sources, total_bytes=total_bytes, member_names=key_count,
                distinct_skeletons=len(prior), finding_count=finding_count,
                retained_findings=len(findings), omitted_findings=finding_count-len(findings),
                truncated=finding_count > len(findings), findings=findings,
                assessment='review-required' if finding_count else 'no-covered-key-collisions-found',
                limitations=[
                    'Heuristic triage, not proof of deception or safety; not full UTS #39.',
                    'Whole decoded JSON member names, NFKC then limited case-sensitive Lantern map.',
                    'Only across supplied files, at any object depth; values are not compared.',
                    'Unrelated object paths can collide; this is not a schema compatibility verdict.',
                    'Equivalent encodings of the same decoded name are not collisions.',
                    'Each later key occurrence with a different earlier-file spelling counts once.',
                    'File order affects counts; witnesses use file order then original byte order.',
                    'Witnesses are earliest unequal spellings, not all pairs. Duplicate keys remain distinct.',
                    'Ranges are zero-based half-open original bytes, including both string quotes.',
                    'Locations use zero-based object-pair indexes with key/value roles and array indexes.',
                    'Previews are inert ASCII, capped at 64 raw bytes and 40 decoded code points.',
                    'Evidence is not redacted; digests identify bytes, not source authenticity.',
                    'UTF-8 JSON only, depth at most 64, no BOM, NaN, infinity or lone surrogates.',
                    'Does not detect every dangerous character; use JSON Lantern for other patterns.'])


def render(report):
    output = json.dumps(report, ensure_ascii=True, allow_nan=False, indent=2) + '\n'
    if len(output) > MAX_OUTPUT:
        raise ValueError('report exceeds 4 MiB; reduce max_findings')
    return output


def read_documents(values):
    if not 2 <= len(values) <= MAX_FILES:
        raise ValueError('provide between 2 and 32 files')
    root = Path.cwd().resolve()
    paths, documents, total = set(), [], 0
    for value in values:
        path = lantern.workspace_file(value)
        if path in paths:
            raise ValueError('the same resolved file was selected twice')
        paths.add(path)
        with path.open('rb') as handle:
            raw = handle.read(lantern.MAX_BYTES + 1)
        total += len(raw)
        if len(raw) > lantern.MAX_BYTES or total > MAX_TOTAL_BYTES:
            raise ValueError('selected files exceed byte budget')
        documents.append((str(path.relative_to(root)), raw))
    return documents


DEMO = [('synthetic/approved.json', br'{"owner":1,"nested":{"pay-owner":2}}'),
        ('synthetic/received.json', br'{"\u043ewner":3,"nested":[{"pay-\uff4fwner":4}]}'),
        ('synthetic/equivalent.json', br'{"\u006fwner":5}')]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--demo', action='store_true')
    group.add_argument('--files', nargs='+', metavar='PATH')
    parser.add_argument('--max-findings', type=int, default=100)
    args = parser.parse_args(argv)
    try:
        documents = DEMO if args.demo else read_documents(args.files)
        report = review(documents, args.max_findings)
        sys.stdout.write(render(report))
        return 0 if args.demo or not report['finding_count'] else 1
    except (OSError, ValueError, RecursionError, OverflowError) as error:
        sys.stderr.write(json.dumps({'error': str(error)}, ensure_ascii=True) + '\n')
        return 2


if __name__ == '__main__':
    sys.exit(main())
