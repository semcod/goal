from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


class GovernanceBaseSelectionTests(unittest.TestCase):
    def test_pull_requests_keep_candidate_base_and_pushes_use_integrated_head(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        expected = (
            "WELLMANIFEST_BASE_SHA: ${{ github.event_name == 'pull_request' "
            "&& github.event.pull_request.base.sha || github.sha }}"
        )
        self.assertIn(expected, workflow)

    def test_workflow_does_not_use_event_before_as_governance_base(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("github.event.before", workflow)


if __name__ == "__main__":
    unittest.main()
