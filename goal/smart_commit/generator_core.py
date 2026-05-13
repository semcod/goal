"""Smart commit generator — staged-file analysis pipeline."""

import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

from goal.smart_commit.abstraction import CodeAbstraction


class SmartCommitGeneratorCore:
    """Generates smart commit messages using code abstraction."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize with goal.yaml configuration."""
        self.config = config
        self.abstraction = CodeAbstraction(config)
        self._deep_analyzer = None

    @property
    def deep_analyzer(self):
        """Lazy-load deep analyzer to avoid circular imports."""
        if self._deep_analyzer is None:
            try:
                from goal.deep_analyzer import CodeChangeAnalyzer

                self._deep_analyzer = CodeChangeAnalyzer()
            except ImportError:
                self._deep_analyzer = False  # Mark as unavailable
        return self._deep_analyzer if self._deep_analyzer else None

    def _analyze_file_diffs(
        self, staged_files: List[str], analysis: Dict[str, Any]
    ) -> List[str]:
        """Populate analysis with per-file domain/diff info. Returns all extracted entities."""
        domain_counter: Counter = Counter()
        all_entities: List[str] = []

        for filepath in staged_files:
            domain = self.abstraction.get_domain(filepath)
            domain_counter[domain] += 1
            analysis["domains"][domain].append(filepath)

            diff = self._get_file_diff(filepath)
            if not diff:
                continue
            for line in diff.split("\n"):
                if line.startswith("+") and not line.startswith("+++"):
                    analysis["added"] += 1
                elif line.startswith("-") and not line.startswith("---"):
                    analysis["deleted"] += 1

            if filepath.endswith(".md"):
                all_entities.extend(self.abstraction.extract_markdown_topics(diff))
            else:
                all_entities.extend(self.abstraction.extract_entities(filepath, diff))

        if domain_counter:
            analysis["primary_domain"] = domain_counter.most_common(1)[0][0]

        return list(dict.fromkeys(all_entities))[:10]

    def _merge_deep_analysis(
        self, analysis: Dict[str, Any], staged_files: List[str]
    ) -> None:
        """Run the deep analyzer and merge its results into *analysis*."""
        if not self.deep_analyzer:
            return
        try:
            deep = self.deep_analyzer.generate_functional_summary(staged_files)
            analysis["deep_analysis"] = deep

            if deep.get("functional_value"):
                analysis["benefit"] = deep["functional_value"]

            agg = deep.get("aggregated") or {}
            added_names = [e["name"] for e in agg.get("added_entities", [])]
            if added_names:
                analysis["entities"] = list(
                    dict.fromkeys(added_names[:5] + analysis["entities"][:5])
                )[:10]
            if not analysis["features"] and agg.get("functional_areas"):
                analysis["features"] = agg["functional_areas"]

            if deep.get("relations"):
                analysis["relations"] = deep["relations"]
        except Exception:
            pass

    def analyze_changes(self, staged_files: List[str] = None) -> Dict[str, Any]:
        """Analyze staged changes and extract abstractions."""
        if staged_files is None:
            staged_files = self._get_staged_files()

        analysis = {
            "files": staged_files,
            "file_count": len(staged_files),
            "domains": defaultdict(list),
            "entities": [],
            "features": [],
            "added": 0,
            "deleted": 0,
            "primary_domain": "core",
            "commit_type": "feat",
            "benefit": "",
            "summary": "",
        }

        if not staged_files:
            return analysis

        analysis["entities"] = self._analyze_file_diffs(staged_files, analysis)
        analysis["features"] = self.abstraction.detect_features(
            staged_files, analysis["entities"]
        )
        analysis["commit_type"] = self._infer_commit_type(analysis)

        self._merge_deep_analysis(analysis, staged_files)

        if not analysis.get("benefit"):
            analysis["benefit"] = self.abstraction.infer_benefit(
                analysis["entities"],
                analysis["primary_domain"],
                analysis["commit_type"],
                files=staged_files,
                features=analysis["features"],
            )

        analysis["summary"] = self._generate_functional_summary(analysis)
        return analysis

    @staticmethod
    def _summarize_features(features: List[str]) -> str:
        """Summarize detected high-level features."""
        if len(features) == 1:
            return f"Added {features[0]} support"
        if len(features) == 2:
            return f"Added {features[0]} and {features[1]} support"
        return (
            f"Added {features[0]}, {features[1]}, and {len(features) - 2} more features"
        )

    @staticmethod
    def _summarize_entities(entities: List[str]) -> str:
        """Summarize extracted code entities."""
        meaningful = [e for e in entities if len(e) > 2 and not e.startswith("test_")]
        if not meaningful:
            return ""
        if len(meaningful) <= 3:
            return f"Implemented {', '.join(meaningful)}"
        return f"Implemented {meaningful[0]}, {meaningful[1]}, and {len(meaningful) - 2} more functions"

    @staticmethod
    def _summarize_documentation(files: List[str]) -> str:
        doc_files = [f for f in files if f.endswith((".md", ".rst", ".txt"))]
        if doc_files and len(doc_files) > len(files) // 2:
            doc_names = [Path(f).stem.upper() for f in doc_files[:3]]
            return f"Updated documentation ({', '.join(doc_names)})"
        return ""

    @staticmethod
    def _summarize_test_files(files: List[str], parts: List[str]) -> str:
        test_files = [f for f in files if "test" in f.lower()]
        if test_files and not parts:
            return f"Added/updated {len(test_files)} test files"
        return ""

    @staticmethod
    def _fallback_functional_summary(files: List[str], added: int, deleted: int) -> str:
        if added > deleted * 2:
            return f"Added new functionality ({added} lines)"
        if deleted > added:
            return f"Refactored code ({deleted} lines removed)"
        return f"Updated {len(files)} files"

    def _generate_functional_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate a human-readable functional summary of changes."""
        parts: List[str] = []
        features = analysis.get("features", [])
        entities = analysis.get("entities", [])
        files = analysis.get("files", [])
        added = analysis.get("added", 0)
        deleted = analysis.get("deleted", 0)

        if features:
            parts.append(self._summarize_features(features))
        elif entities:
            s = self._summarize_entities(entities)
            if s:
                parts.append(s)

        doc_summary = self._summarize_documentation(files)
        if doc_summary:
            parts.append(doc_summary)

        test_summary = self._summarize_test_files(files, parts)
        if test_summary:
            parts.append(test_summary)

        if not parts:
            parts.append(self._fallback_functional_summary(files, added, deleted))

        return "; ".join(parts)

    def _get_staged_files(self) -> List[str]:
        """Get list of staged files."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=True,
            )
            return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
        except subprocess.CalledProcessError:
            return []

    def _get_file_diff(self, filepath: str) -> str:
        """Get diff content for a specific file."""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--", filepath],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""

    def _infer_commit_type(self, analysis: Dict[str, Any]) -> str:
        """Infer commit type from analysis."""
        domain = analysis.get("primary_domain", "core")
        entities = analysis.get("entities", [])
        added = analysis.get("added", 0)
        deleted = analysis.get("deleted", 0)

        # Map domain to commit type
        domain_type_map = {
            "docs": "docs",
            "test": "test",
            "ci": "build",
            "build": "build",
            "config": "chore",
        }

        if domain in domain_type_map:
            return domain_type_map[domain]

        # Analyze entities for type hints
        entity_str = " ".join(entities).lower()
        if "fix" in entity_str or "bug" in entity_str:
            return "fix"
        if "refactor" in entity_str or "extract" in entity_str:
            return "refactor"
        if "test" in entity_str:
            return "test"

        # Analyze add/delete ratio
        if deleted > added * 2:
            return "refactor"
        if added > 0 and deleted == 0:
            return "feat"
        if deleted > added:
            return "fix"

        return "feat"
