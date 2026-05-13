"""Smart commit generator — message and changelog formatting."""

import re
from pathlib import Path
from typing import Any, Dict, List


class SmartCommitGeneratorGenerateMixin:
    def generate_message(
        self, analysis: Dict[str, Any] = None, level: str = None
    ) -> str:
        """Generate commit message based on analysis."""
        if analysis is None:
            analysis = self.analyze_changes()

        if level is None:
            level = self.abstraction.determine_abstraction_level(analysis)

        files = analysis.get("files", [])
        is_docs_only = self._is_docs_only_change(files)

        # For docs-only changes, use simpler functional descriptions
        if is_docs_only:
            return self._generate_docs_message(analysis)

        # Route to appropriate abstraction level generator
        if level == "high":
            return self._generate_high_abstraction_message(analysis)
        if level == "medium":
            return self._generate_medium_abstraction_message(analysis)

        return self._generate_low_abstraction_message(analysis)

    def _is_docs_only_change(self, files: List[str]) -> bool:
        """Check if this is a documentation-only change."""
        if not files:
            return False
        return all(
            f.lower().endswith((".md", ".rst", ".txt"))
            or "readme" in f.lower()
            or f.startswith("docs/")
            for f in files
        )

    def _generate_docs_message(self, analysis: Dict[str, Any]) -> str:
        """Generate commit message for documentation-only changes."""
        commit_type = analysis.get("commit_type", "feat")
        domain = analysis.get("primary_domain", "core")
        files = analysis.get("files", [])
        file_count = analysis.get("file_count", 0)
        added = analysis.get("added", 0)

        if any("readme" in f.lower() for f in files):
            if added > 100:
                return f"docs({domain}): expand README with detailed examples"
            return f"docs({domain}): update README"
        if any("changelog" in f.lower() for f in files):
            return f"docs({domain}): update changelog"
        if file_count == 1:
            fname = Path(files[0]).stem.lower()
            return f"docs({domain}): update {fname} documentation"
        return f"docs({domain}): update documentation"

    def _generate_high_abstraction_message(self, analysis: Dict[str, Any]) -> str:
        """Generate message for high abstraction level."""
        commit_type = analysis.get("commit_type", "feat")
        domain = analysis.get("primary_domain", "core")
        features = analysis.get("features", [])
        benefit = analysis.get("benefit", "improved functionality")

        # Prefer features over entities for high abstraction
        if features:
            if len(features) == 1:
                return f"{commit_type}({domain}): add {features[0]} support"
            elif len(features) == 2:
                return f"{commit_type}({domain}): add {features[0]} and {features[1]} support"
            else:
                return f"{commit_type}({domain}): add {features[0]}, {features[1]} and more"

        return f"{commit_type}({domain}): {benefit}"

    def _generate_medium_abstraction_message(self, analysis: Dict[str, Any]) -> str:
        """Generate message for medium abstraction level."""
        commit_type = analysis.get("commit_type", "feat")
        domain = analysis.get("primary_domain", "core")
        entities = analysis.get("entities", [])
        features = analysis.get("features", [])
        benefit = analysis.get("benefit", "improved functionality")

        if features:
            feature_str = ", ".join(features[:3])
            return f"{commit_type}({domain}): add {feature_str}"

        if entities:
            meaningful = self._filter_meaningful_entities(entities)[:3]
            if meaningful:
                return f"{commit_type}({domain}): add {', '.join(meaningful)}"

        return f"{commit_type}({domain}): {benefit}"

    def _generate_low_abstraction_message(self, analysis: Dict[str, Any]) -> str:
        """Generate message for low abstraction level (fallback)."""
        commit_type = analysis.get("commit_type", "feat")
        domain = analysis.get("primary_domain", "core")
        entities = analysis.get("entities", [])
        files = analysis.get("files", [])
        benefit = analysis.get("benefit", "improved functionality")
        added = analysis.get("added", 0)
        deleted = analysis.get("deleted", 0)

        # Prefer benefit if meaningful
        if benefit and benefit != "improved functionality":
            return f"{commit_type}({domain}): {benefit}"

        # Try to create functional description from entities
        if entities:
            meaningful = [e for e in entities if len(e) > 2][:2]
            if meaningful:
                verb = self.abstraction.get_action_verb(commit_type)
                return f"{commit_type}({domain}): {verb} {', '.join(meaningful)}"

        # Infer from file patterns
        return self._infer_message_from_files(analysis)

    def _filter_meaningful_entities(self, entities: List[str]) -> List[str]:
        """Filter out noise from entity names."""
        return [
            e
            for e in entities
            if len(e) > 2
            and not e.startswith("test_")
            and not re.match(r"^\[.*\]$", e)  # Skip [version] patterns
            and not re.match(r"^\d", e)  # Skip entities starting with numbers
        ]

    def _infer_message_from_files(self, analysis: Dict[str, Any]) -> str:
        """Infer commit message from file patterns."""
        commit_type = analysis.get("commit_type", "feat")
        domain = analysis.get("primary_domain", "core")
        files = analysis.get("files", [])
        added = analysis.get("added", 0)
        deleted = analysis.get("deleted", 0)

        if not files:
            verb = self.abstraction.get_action_verb(commit_type)
            return f"{commit_type}({domain}): {verb} code structure"

        # Check for common patterns
        if any("cli" in f.lower() for f in files):
            return f"{commit_type}({domain}): improve CLI functionality"
        if any("config" in f.lower() for f in files):
            return f"{commit_type}({domain}): update configuration handling"
        if any("test" in f.lower() for f in files):
            return f"{commit_type}({domain}): improve test coverage"
        if any(f.endswith(".md") for f in files):
            return f"{commit_type}({domain}): update documentation"

        # Fallback based on stats
        verb = self.abstraction.get_action_verb(commit_type)
        if added > deleted * 2:
            return f"{commit_type}({domain}): {verb} new functionality"
        elif deleted > added:
            return f"{commit_type}({domain}): refactor and simplify code"
        else:
            return f"{commit_type}({domain}): {verb} code structure"

    def generate_functional_body(self, analysis: Dict[str, Any] = None) -> str:
        """Generate a functional, human-readable commit body."""
        if analysis is None:
            analysis = self.analyze_changes()

        parts = []
        features = analysis.get("features", [])
        entities = analysis.get("entities", [])
        files = analysis.get("files", [])
        added = analysis.get("added", 0)
        deleted = analysis.get("deleted", 0)
        summary = analysis.get("summary", "")

        # Main summary
        if summary:
            parts.append(f"## Summary\n{summary}\n")

        # Features added
        if features:
            parts.append("## Features Added")
            for f in features:
                parts.append(f"- {f}")
            parts.append("")

        # Key functions/classes
        if entities:
            meaningful = [e for e in entities if len(e) > 2][:8]
            if meaningful:
                parts.append("## Key Changes")
                for e in meaningful:
                    parts.append(f"- `{e}`")
                parts.append("")

        # File changes by domain
        domains = analysis.get("domains", {})
        if domains:
            parts.append("## Changes by Area")
            for domain, domain_files in domains.items():
                if domain_files:
                    parts.append(f"- **{domain.title()}**: {len(domain_files)} files")
            parts.append("")

        # Stats
        parts.append("## Statistics")
        parts.append(f"- Files: {len(files)}")
        parts.append(f"- Lines: +{added}/-{deleted}")

        return "\n".join(parts)

    def generate_changelog_entry(
        self, analysis: Dict[str, Any] = None, commit_hash: str = None
    ) -> Dict[str, Any]:
        """Generate structured changelog entry."""
        if analysis is None:
            analysis = self.analyze_changes()

        commit_type = analysis.get("commit_type", "feat")
        domain = analysis.get("primary_domain", "core")
        entities = analysis.get("entities", [])
        benefit = analysis.get("benefit", "improved functionality")

        # Map commit type to changelog section
        type_to_section = {
            "feat": "Added",
            "fix": "Fixed",
            "docs": "Changed",
            "refactor": "Changed",
            "perf": "Changed",
            "test": "Changed",
            "build": "Changed",
            "chore": "Changed",
            "style": "Changed",
        }

        section = type_to_section.get(commit_type, "Changed")

        # Build entry
        entry = {
            "section": section,
            "domain": domain,
            "type": commit_type,
            "message": f"{commit_type}({domain}): {benefit}",
            "entities": entities[:5],
            "commit_hash": commit_hash,
        }

        # Add entity details if configured
        changelog_config = self.config.get("git", {}).get("changelog", {})
        if changelog_config.get("include_entities", True) and entities:
            max_entities = changelog_config.get("max_entities_per_entry", 5)
            entry["entity_details"] = entities[:max_entities]

        return entry

    def format_changelog_entry(self, entry: Dict[str, Any]) -> str:
        """Format changelog entry as markdown."""
        message = entry.get("message", "")
        entities = entry.get("entity_details", [])
        commit_hash = entry.get("commit_hash", "")

        # Base entry
        if commit_hash:
            line = f"- {message} ([{commit_hash[:7]}](commit/{commit_hash}))"
        else:
            line = f"- {message}"

        # Add entity details
        if entities:
            entity_list = ", ".join(f"`{e}`" for e in entities)
            line += f"\n  - Added: {entity_list}"

        return line
