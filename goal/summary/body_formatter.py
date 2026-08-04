"""Body formatting for enhanced commit summaries."""

from pathlib import Path
from typing import Dict, List

from goal.summary.quality_filter import SummaryQualityFilter


class CommitBodyFormatter:
    """Format enhanced commit body sections."""

    def __init__(self, quality_filter: SummaryQualityFilter):
        self.quality_filter = quality_filter

    @staticmethod
    def _format_entity_list(label: str, entities: List[Dict], limit: int = 6) -> str:
        """Format a list of entities as a YAML-like line, e.g. 'added: [a, b]'."""
        names = [e["name"] for e in entities[:limit]]
        suffix = f", +{len(entities) - limit} more" if len(entities) > limit else ""
        return f"    {label}: [{', '.join(names)}{suffix}]"

    @staticmethod
    def _split_added_entities(added_ents: List[Dict]) -> tuple:
        """Split entities into tests and non-tests."""
        names = [e["name"] for e in added_ents]
        tests = [name for name in names if name.startswith("test_")]
        non_tests = [name for name in names if not name.startswith("test_")]
        return non_tests, tests

    def _append_file_header(self, change_lines: List[str], f: str, area: str) -> None:
        """Append file header to change lines."""
        change_lines.append(f"  - file: {Path(f).name}")
        change_lines.append(f"    area: {area}")

    def _append_added_entities(
        self,
        change_lines: List[str],
        added_ents: List[Dict],
        test_scenarios: List[str],
    ) -> None:
        """Append added entities section."""
        non_tests, tests = self._split_added_entities(added_ents)
        test_scenarios.extend(tests)
        if non_tests:
            change_lines.append(
                self._format_entity_list("added", [{"name": n} for n in non_tests])
            )
        if tests:
            change_lines.append(f"    new_tests: {len(tests)}")

    def _append_entity_change(
        self, change_lines: List[str], label: str, entities: List[Dict]
    ) -> None:
        """Append entity change section."""
        if entities:
            change_lines.append(self._format_entity_list(label, entities))

    def _format_file_change(
        self,
        f: str,
        fa: Dict,
        categorized: Dict,
        change_lines: List[str],
        test_scenarios: List[str],
    ) -> bool:
        """Append change lines for a single file. Returns True if any entities found."""
        added_ents = fa.get("added_entities", [])
        modified_ents = fa.get("modified_entities", [])
        removed_ents = fa.get("removed_entities", [])

        if not added_ents and not modified_ents and not removed_ents:
            return False

        area = next(
            (cat for cat, cat_files in categorized.items() if f in cat_files), "core"
        )
        self._append_file_header(change_lines, f, area)

        if added_ents:
            self._append_added_entities(change_lines, added_ents, test_scenarios)

        self._append_entity_change(change_lines, "modified", modified_ents)
        self._append_entity_change(change_lines, "removed", removed_ents)
        return True

    def format_changes_section(
        self, files: List[str], file_analyses: List[Dict]
    ) -> tuple:
        """Format the CHANGES section with per-file breakdown.

        Returns:
            Tuple of (section_text, test_scenarios, has_changes)
        """
        categorized = self.quality_filter.categorize_files(files)
        analysis_map = {}
        for fa in file_analyses:
            fp = fa.get("filepath", "")
            analysis_map[fp] = fa
            analysis_map[Path(fp).name] = fa

        change_lines = ["changes:"]
        test_scenarios: List[str] = []
        has_changes = False

        for f in files:
            fa = analysis_map.get(f) or analysis_map.get(Path(f).name) or {}
            if self._format_file_change(
                f, fa, categorized, change_lines, test_scenarios
            ):
                has_changes = True

        if has_changes:
            return "\n".join(change_lines), test_scenarios, True
        return "", [], False

    def format_testing_section(self, test_scenarios: List[str]) -> str:
        """Format the TESTING section with concrete test scenarios."""
        if not test_scenarios:
            return ""

        test_lines = ["testing:"]
        test_lines.append(f"  new_tests: {len(test_scenarios)}")
        test_lines.append("  scenarios:")
        for t in test_scenarios[:10]:
            # Strip test_ prefix for readability
            readable = t[5:] if t.startswith("test_") else t
            test_lines.append(f"    - {readable}")
        if len(test_scenarios) > 10:
            test_lines.append(f"    # +{len(test_scenarios) - 10} more")
        return "\n".join(test_lines)

    def format_dependencies_section(self, relations: Dict) -> str:
        """Format the DEPENDENCIES section with import flow."""
        if not relations.get("relations"):
            return ""

        dep_lines = ["dependencies:"]
        chain = relations.get("chain", "")
        if chain:
            dep_lines.append(f'  flow: "{chain}"')
        for r in relations.get("relations", [])[:8]:
            dep_lines.append(f"  - {r.get('from')}.py -> {r.get('to')}.py")
        return "\n".join(dep_lines)

    def format_stats_section(self, metrics: Dict, files: List[str]) -> str:
        """Format the STATS section with concise metrics."""
        if not metrics:
            return ""

        stat_lines = ["stats:"]
        added = metrics.get("lines_added", 0)
        deleted = metrics.get("lines_deleted", 0)
        if added or deleted:
            net = added - deleted
            sign = "+" if net >= 0 else ""
            stat_lines.append(f'  lines: "+{added}/-{deleted} (net {sign}{net})"')
        stat_lines.append(f"  files: {len(files)}")

        # Complexity change (human-readable interpretation)
        old_cc = metrics.get("old_complexity", 1)
        new_cc = metrics.get("new_complexity", old_cc)
        if old_cc and old_cc > 0:
            emoji, desc = self.quality_filter.format_complexity_delta(old_cc, new_cc)
            stat_lines.append(f'  complexity: "{desc}"')

        return "\n".join(stat_lines)

    def format_body(
        self,
        capabilities: List[Dict],
        roles: List[Dict],
        relations: Dict,
        metrics: Dict,
        files: List[str],
        aggregated: Dict,
        file_analyses: List[Dict] = None,
    ) -> str:
        """Format the enhanced commit body.

        Produces a YAML structure optimised for git log / GitHub readers:
        - changes:      per-file concrete additions/modifications/removals
        - testing:      new test scenarios (only when tests are present)
        - dependencies: import flow between changed files (only when present)
        - stats:        concise line/complexity metrics
        """
        file_analyses = file_analyses or []
        sections = []

        # ── CHANGES section: per-file breakdown of what was touched ──
        changes_section, test_scenarios, has_changes = self.format_changes_section(
            files, file_analyses
        )
        if has_changes:
            sections.append(changes_section)

        # ── TESTING section: concrete test scenarios added ──
        testing_section = self.format_testing_section(test_scenarios)
        if testing_section:
            sections.append(testing_section)

        # ── DEPENDENCIES section: import flow (only when non-trivial) ──
        deps_section = self.format_dependencies_section(relations)
        if deps_section:
            sections.append(deps_section)

        # ── STATS section: concise metrics ──
        stats_section = self.format_stats_section(metrics, files)
        if stats_section:
            sections.append(stats_section)

        return "\n\n".join(sections)


__all__ = ["CommitBodyFormatter"]
