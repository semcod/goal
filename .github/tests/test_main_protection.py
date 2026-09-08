import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('main_protection', ROOT / '.github/scripts/check_main_protection.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ProtectionTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / '.github/main-protection.json').read_text())
        self.contexts = checker.required_contexts(ROOT)

    def validate(self):
        checker.validate_policy(self.policy, self.contexts)

    def test_declared_policy_matches_real_matrix(self):
        self.validate()
        self.assertIn('test (3.12)', self.contexts)
        self.assertIn('test (3.13)', self.contexts)
        self.assertNotIn('test', self.contexts)

    def test_gate_bypass_rejected(self):
        self.policy['rulesets'][0]['bypass_actors'] = self.policy['rulesets'][1]['bypass_actors']
        with self.assertRaises(ValueError):
            self.validate()

    def test_untrusted_publisher_rejected(self):
        self.policy['rulesets'][1]['bypass_actors'][0]['actor_id'] = 1
        with self.assertRaises(ValueError):
            self.validate()

    def test_disabled_or_excluded_main_rejected(self):
        for field, value in [('enforcement', 'disabled'), ('conditions', {'ref_name': {'include': ['refs/heads/main'], 'exclude': ['refs/heads/main']}})]:
            with self.subTest(field=field):
                candidate = copy.deepcopy(self.policy)
                candidate['rulesets'][0][field] = value
                with self.assertRaises(ValueError):
                    checker.validate_policy(candidate, self.contexts)

    def test_missing_matrix_check_rejected(self):
        self.policy['rulesets'][0]['rules'][-1]['parameters']['required_status_checks'].pop(0)
        with self.assertRaises(ValueError):
            self.validate()

    def test_stale_review_rejected(self):
        self.policy['rulesets'][0]['rules'][2]['parameters']['dismiss_stale_reviews_on_push'] = False
        with self.assertRaises(ValueError):
            self.validate()

    def fake_api(self, drift=None, omit_active=False):
        rows = copy.deepcopy(self.policy['rulesets'])
        for number, row in enumerate(rows, 1):
            row.update(id=number, source='semcod/goal', created_at='metadata ignored')
        if drift:
            drift(rows)
        def read(endpoint):
            if '/rulesets?' in endpoint:
                return rows
            if '/rules/branches/main?' in endpoint:
                return [] if omit_active else [{'ruleset_id': row['id'], 'type': rule['type']} for row in rows for rule in row['rules']]
            return rows[int(endpoint.rsplit('/', 1)[1]) - 1]
        return read

    def test_live_readback_handles_order_and_metadata(self):
        api = self.fake_api(lambda rows: rows[0]['rules'].reverse())
        self.assertEqual(checker.verify_live(self.policy, api), [1, 2])

    def test_live_extra_bypass_is_drift(self):
        api = self.fake_api(lambda rows: rows[0]['bypass_actors'].append({'actor_id': 1}))
        with self.assertRaises(ValueError):
            checker.verify_live(self.policy, api)

    def test_declared_but_inactive_rules_rejected(self):
        with self.assertRaises(ValueError):
            checker.verify_live(self.policy, self.fake_api(omit_active=True))

    def test_incomplete_inventory_rejected(self):
        with self.assertRaises(ValueError):
            checker.verify_live(self.policy, lambda endpoint: [{}] * 100)

    def test_api_failure_propagates(self):
        def unavailable(endpoint):
            raise OSError('GitHub unavailable')
        with self.assertRaises(OSError):
            checker.verify_live(self.policy, unavailable)

    def test_hidden_bypass_requires_explicit_public_scope(self):
        api = self.fake_api(lambda rows: [row.pop('bypass_actors') for row in rows])
        with self.assertRaises(KeyError):
            checker.verify_live(self.policy, api)
        self.assertEqual(checker.verify_live(self.policy, api, public_only=True), [1, 2])

    def test_github_omits_disabled_upstream_fetch_exception(self):
        api = self.fake_api(lambda rows: rows[1]['rules'][0].pop('parameters'))
        self.assertEqual(checker.verify_live(self.policy, api), [1, 2])

    def test_enabled_upstream_fetch_exception_is_drift(self):
        def drift(rows):
            rows[1]['rules'][0]['parameters']['update_allows_fetch_and_merge'] = True
        with self.assertRaises(ValueError):
            checker.verify_live(self.policy, self.fake_api(drift))


if __name__ == '__main__':
    unittest.main()
