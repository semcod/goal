#!/usr/bin/env python3
"""Read-only verification of Goal's declared and active main protection."""

import argparse
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def required_contexts(root):
    declaration = json.loads((root / '.governance/required-checks.json').read_text())
    names = set()
    for item in declaration['requiredChecks']:
        if item == {'name': 'test', 'workflowFile': '.github/workflows/ci.yml'}:
            workflow = (root / item['workflowFile']).read_text()
            matrix = re.findall(r'^\s*python-version:\s*(\[[^\n]+\])\s*$', workflow, re.M)
            require(len(matrix) == 1, 'Expected one explicit Python CI matrix')
            versions = json.loads(matrix[0])
            require(versions and all(isinstance(v, str) for v in versions), 'Invalid Python matrix')
            names.update(f'test ({version})' for version in versions)
        else:
            names.add(item['name'])
    return names


def validate_policy(policy, contexts):
    require(policy['schema'] == 'goal.main-protection/v1', 'Unknown policy schema')
    require(policy['repository'] == 'semcod/goal', 'Unexpected repository')
    rows = policy['rulesets']
    require(len(rows) == 2, 'Expected independent gate and publisher rulesets')
    by_name = {row['name']: row for row in rows}
    require(set(by_name) == {'goal-main-required-gates', 'goal-main-trusted-publisher'}, 'Unexpected ruleset names')
    for row in rows:
        require(row['target'] == 'branch' and row['enforcement'] == 'active', 'Rules must be active')
        require(row['conditions'] == {'ref_name': {'include': ['refs/heads/main'], 'exclude': []}}, 'Rules must cover exactly main')
    gates = by_name['goal-main-required-gates']
    require(gates['bypass_actors'] == [], 'Required gates must have no bypass')
    rules = {rule['type']: rule for rule in gates['rules']}
    require(len(gates['rules']) == 4 and set(rules) == {'deletion', 'non_fast_forward', 'pull_request', 'required_status_checks'}, 'Missing or duplicate gate')
    review = rules['pull_request']['parameters']
    require(review['required_approving_review_count'] >= 1, 'Independent review is required')
    require(review['dismiss_stale_reviews_on_push'] and review['require_last_push_approval'], 'Approval must cover the latest push')
    require(review['required_review_thread_resolution'], 'Review threads must be resolved')
    checks = rules['required_status_checks']['parameters']
    require(checks['strict_required_status_checks_policy'] and not checks['do_not_enforce_on_create'], 'Checks must cover the current base')
    entries = checks['required_status_checks']
    require({entry['context'] for entry in entries} == contexts and len(entries) == len(contexts), 'Required check names differ from the workflow declaration/matrix')
    require(all(entry['integration_id'] == 15368 for entry in entries), 'Checks must come from GitHub Actions')
    publisher = by_name['goal-main-trusted-publisher']
    require(publisher['bypass_actors'] == [{'actor_id': 4344831, 'actor_type': 'Integration', 'bypass_mode': 'always'}], 'Only the protected Validator App may publish')
    require(publisher['rules'] == [{'type': 'update', 'parameters': {'update_allows_fetch_and_merge': False}}], 'Publisher exception must apply only to the update restriction')


def projected(actual, expected):
    """Ignore response metadata, but retain every expected security field."""
    if isinstance(expected, dict):
        require(isinstance(actual, dict), 'Expected an object from GitHub')
        return {key: projected(actual[key], value) for key, value in expected.items()}
    if isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), 'GitHub list differs from policy')
        if expected and isinstance(expected[0], dict):
            key = next((key for key in ('type', 'context', 'actor_id') if key in expected[0]), None)
            if key:
                actual = sorted(actual, key=lambda item: item[key])
                expected = sorted(expected, key=lambda item: item[key])
        return [projected(a, e) for a, e in zip(actual, expected)]
    return actual


def gh(endpoint):
    return json.loads(subprocess.check_output(['gh', 'api', endpoint], text=True))


def verify_live(policy, api=gh, *, public_only=False):
    repository = policy['repository']
    base = f'repos/{repository}'
    listed = api(base + '/rulesets?includes_parents=true&per_page=100')
    require(len(listed) < 100, 'Ruleset inventory requires pagination; refusing an incomplete audit')
    active = api(base + '/rules/branches/main?per_page=100')
    require(len(active) < 100, 'Active rule inventory requires pagination')
    ids = []
    for expected in policy['rulesets']:
        matches = [row for row in listed if row['name'] == expected['name'] and row['source'] == repository]
        require(len(matches) == 1, 'Missing or duplicate repository ruleset: ' + expected['name'])
        rule_id = matches[0]['id']
        actual = api(base + '/rulesets/' + str(rule_id))
        # GitHub serializes the ordinary update restriction without parameters
        # when the optional upstream-fetch exception is disabled.
        for rule in actual['rules']:
            if rule['type'] == 'update' and 'parameters' not in rule:
                rule['parameters'] = {'update_allows_fetch_and_merge': False}
        # GitHub hides bypass actors from callers without ruleset write access.
        # CI deliberately checks public fields; deployment must run full mode.
        compared = {key: value for key, value in expected.items() if not (public_only and key == 'bypass_actors')}
        require(projected(actual, compared) == projected(compared, compared), 'Live ruleset drift: ' + expected['name'])
        applied = {row['type'] for row in active if row['ruleset_id'] == rule_id}
        require(applied == {rule['type'] for rule in expected['rules']}, 'Ruleset is not fully active on main')
        ids.append(rule_id)
    return ids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    live = parser.add_mutually_exclusive_group()
    live.add_argument('--live', action='store_true', help='Verify all GitHub settings, including bypass actors (requires ruleset write visibility; makes no writes)')
    live.add_argument('--public-live', action='store_true', help='Verify public GitHub settings only; bypass actors are not observable with CI read permissions')
    args = parser.parse_args()
    try:
        policy = json.loads((ROOT / '.github/main-protection.json').read_text())
        validate_policy(policy, required_contexts(ROOT))
        ids = verify_live(policy, public_only=args.public_live) if args.live or args.public_live else []
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'MAIN-PROTECTION-FAIL: {error}\n')
    mode = 'live' if args.live else 'public-live' if args.public_live else 'declared'
    print(json.dumps({'status': 'pass', 'mode': mode, 'bypassActorsVerifiedLive': args.live, 'rulesetIds': ids, 'mutated': False}))


if __name__ == '__main__':
    main()
