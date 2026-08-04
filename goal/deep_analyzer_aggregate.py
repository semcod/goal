"""Deep analysis — aggregation and summary helpers."""

import subprocess
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple


class CodeChangeAggregatorMixin:
    def aggregate_changes(self, file_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate analysis results across multiple files."""
        all_added = []
        all_modified = []
        all_removed = []
        all_areas = set()
        total_complexity_change = 0
        all_value_indicators = []

        for analysis in file_analyses:
            all_added.extend(analysis.get("added_entities", []))
            all_modified.extend(analysis.get("modified_entities", []))
            all_removed.extend(analysis.get("removed_entities", []))
            all_areas.update(analysis.get("functional_areas", []))
            total_complexity_change += analysis.get("complexity_change", 0)
            all_value_indicators.extend(analysis.get("value_indicators", []))

        # Count indicators
        indicator_counts = Counter(all_value_indicators)
        primary_indicator = (
            indicator_counts.most_common(1)[0][0] if indicator_counts else None
        )

        return {
            "added_entities": all_added,
            "modified_entities": all_modified,
            "removed_entities": all_removed,
            "functional_areas": list(all_areas),
            "complexity_change": total_complexity_change,
            "primary_indicator": primary_indicator,
            "indicator_counts": dict(indicator_counts),
        }

    def _detect_file_patterns(self, files: List[str]) -> Dict[str, bool]:
        """Detect specific patterns in file paths."""
        return {
            "analyzer": any("analyzer" in f.lower() for f in files),
            "deep": any("deep" in f.lower() for f in files),
            "smart": any("smart" in f.lower() for f in files),
            "config": any("config" in f.lower() for f in files),
            "cli": any("cli" in f.lower() for f in files),
        }

    def _check_analyzer_value(
        self, file_patterns: Dict[str, bool], added: List[Dict]
    ) -> Optional[str]:
        """Check for analyzer/deep pattern values."""
        if file_patterns["analyzer"] or file_patterns["deep"]:
            if len(added) > 0:
                return "enhanced code analysis capabilities"
            return "improved code analysis"
        return None

    def _check_cli_value(self, areas: List[str], added: List[Dict]) -> Optional[str]:
        """Check for CLI-related value."""
        if "cli" in areas and added:
            cli_entities = [
                e
                for e in added
                if any(d in str(e.get("decorators", [])) for d in ["click", "command"])
            ]
            if cli_entities:
                return f"new CLI commands: {', '.join(e['name'] for e in cli_entities[:CONSTANT_3])}"
        return None

    def _check_area_values(self, areas: List[str], added: List[Dict]) -> Optional[str]:
        """Check area-based values (configuration, api, auth, testing, formatting)."""
        if "configuration" in areas:
            config_entities = [
                e for e in added if "config" in e.get("name", "").lower()
            ]
            if config_entities:
                return "improved configuration management"

        if "api" in areas:
            return "new API capabilities"

        if "auth" in areas:
            return "security enhancements"

        if "testing" in areas:
            test_count = len(
                [e for e in added if e.get("name", "").startswith("test_")]
            )
            if test_count > 0:
                return f"added {test_count} tests for better coverage"
            return "improved test coverage"

        if "formatting" in areas:
            return "improved output formatting"

        return None

    def _check_complexity_value(self, complexity: int) -> Optional[str]:
        """Check complexity-based value."""
        if complexity < -CONSTANT_5:
            return "simplified code structure"
        if complexity > 10:
            return "new functionality"
        return None

    def _check_architecture_value(self, added: List[Dict]) -> Optional[str]:
        """Check for architecture improvement values."""
        if len(added) >= 2 and any(
            "analyzer" in e.get("name", "").lower() for e in added
        ):
            return "enhanced architecture with deep analysis"
        return None

    def _build_entity_fallback(self, added: List[Dict], modified: List[Dict]) -> str:
        """Build fallback value based on added/modified entities."""
        if len(added) >= CONSTANT_3:
            names = [e["name"] for e in added[:CONSTANT_3]]
            return f"added {', '.join(names)}"

        if len(modified) >= 2:
            names = [e["name"] for e in modified[:2]]
            return f"enhanced {', '.join(names)}"

        if added:
            return f"added {added[0]['name']}"

        if modified:
            return f"updated {modified[0]['name']}"

        return "code improvements"

    def infer_functional_value(
        self, aggregated: Dict[str, Any], files: List[str]
    ) -> str:
        """Infer the functional value/impact of the changes."""
        areas = aggregated.get("functional_areas", [])
        added = aggregated.get("added_entities", [])
        modified = aggregated.get("modified_entities", [])
        complexity = aggregated.get("complexity_change", 0)

        file_patterns = self._detect_file_patterns(files)

        # Priority-based value inference
        value = self._check_analyzer_value(file_patterns, added)
        if value:
            return value

        value = self._check_cli_value(areas, added)
        if value:
            return value

        value = self._check_area_values(areas, added)
        if value:
            return value

        value = self._check_complexity_value(complexity)
        if value:
            return value

        value = self._check_architecture_value(added)
        if value:
            return value

        return self._build_entity_fallback(added, modified)
        return "code improvements"

    def detect_relations(
        self, file_analyses: List[Dict[str, Any]]
    ) -> List[Tuple[str, str, str]]:
        """Detect relations between changed modules."""
        relations = []

        # Group by domain
        domains = defaultdict(list)
        for analysis in file_analyses:
            filepath = analysis.get("filepath", "")
            for area in analysis.get("functional_areas", []):
                domains[area].append(filepath)

        # Check for known relation patterns
        domain_set = set(domains.keys())
        for (d1, d2), relation in self.RELATION_PATTERNS.items():
            if d1 in domain_set and d2 in domain_set:
                relations.append((d1, d2, relation))

        return relations

    def generate_functional_summary(self, files: List[str]) -> Dict[str, Any]:
        """Generate a complete functional summary of changes."""
        file_analyses = []

        for filepath in files:
            try:
                # Get old content from git
                old_result = subprocess.run(
                    ["git", "show", f"HEAD:{filepath}"], capture_output=True, text=True
                )
                old_content = old_result.stdout if old_result.returncode == 0 else ""

                # Get new content
                try:
                    with open(filepath, "r") as f:
                        new_content = f.read()
                except FileNotFoundError:
                    new_content = ""

                analysis = self.analyze_file_diff(filepath, old_content, new_content)
                file_analyses.append(analysis)
            except Exception:
                continue

        aggregated = self.aggregate_changes(file_analyses)
        value = self.infer_functional_value(aggregated, files)
        relations = self.detect_relations(file_analyses)

        return {
            "file_analyses": file_analyses,
            "aggregated": aggregated,
            "functional_value": value,
            "relations": relations,
            "summary": self._build_summary(aggregated, value, relations),
        }

    @staticmethod
    def _format_entity_names(items: List[Dict], limit: int) -> List[str]:
        return [e["name"] for e in items[:limit]]

    @staticmethod
    def _format_relations(relations: List) -> str:
        rel_strs = [f"{r[0]}→{r[1]}: {r[2]}" for r in relations]
        return f"Relations: {'; '.join(rel_strs)}"

    @staticmethod
    def _format_complexity_change(complexity: int) -> str:
        sign = "+" if complexity > 0 else ""
        return f"Complexity: {sign}{complexity}"

    @staticmethod
    def _format_areas(areas: List[str]) -> str:
        return f"Areas: {', '.join(areas)}"

    def _build_summary(self, aggregated: Dict, value: str, relations: List) -> str:
        """Build human-readable summary."""
        parts = []

        added = aggregated.get("added_entities", [])
        modified = aggregated.get("modified_entities", [])
        areas = aggregated.get("functional_areas", [])
        complexity = aggregated.get("complexity_change", 0)

        if added:
            funcs = self._format_entity_names(
                [e for e in added if e.get("type") == "function"], CONSTANT_4
            )
            classes = self._format_entity_names(
                [e for e in added if e.get("type") == "class"], 2
            )
            if classes:
                parts.append(f"New classes: {', '.join(classes)}")
            if funcs:
                parts.append(f"New functions: {', '.join(funcs)}")

        if modified:
            names = self._format_entity_names(modified, CONSTANT_3)
            parts.append(f"Modified: {', '.join(names)}")

        if relations:
            parts.append(self._format_relations(relations))

        if complexity != 0:
            parts.append(self._format_complexity_change(complexity))

        if areas:
            parts.append(self._format_areas(areas))

        return "\n".join(parts) if parts else value
