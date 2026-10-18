#!/usr/bin/env python3
"""Exercise cluster diagnostics on the predecessor's actual fixed JSON policies."""
from pathlib import Path
import sys

import cluster_influence as ci


def main():
    folder = Path(__file__).resolve().parent
    source = folder.parent / 'policy-benchmark'
    if not source.is_relative_to(Path.cwd().resolve()):
        raise ValueError('policy sources must be inside workspace')
    sys.path.insert(0, str(source))
    import policy_benchmark as policy
    # Existing demo seals, executes all policies, replays and freshly reexecutes.
    measured = policy.demo()
    observations = measured['observations']
    names = list(policy.policies.NAMES[1:])
    ids = [r['case'] for r in observations]
    rows = [tuple(r['passed'][n] for n in policy.policies.NAMES) for r in observations]
    raw = ci.encoded(names, ids, rows)
    mapping = ci.workspace_bytes(folder / 'policy-groups.csv')
    result = ci.review(raw, mapping, max_details=128)
    result['data_kind'] = 'measured_local_execution_on_curated_cases'
    result['policy_receipt_sha256'] = measured['receipt_sha256']
    result['grouping_note'] = 'Post hoc illustrative case categories, not registered independent clusters.'
    result['paired_csv'] = raw.decode()
    result['group_mapping_csv'] = mapping.decode()
    print(ci.canonical(result).decode())


if __name__ == '__main__':
    main()
