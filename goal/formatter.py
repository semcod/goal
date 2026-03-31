"""Markdown output formatter for Goal."""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class MarkdownFormatter:
    """Formats Goal output as structured markdown for LLM consumption."""
    
    def __init__(self):
        self.sections = []
        self.metadata = {}
    
    def add_header(self, title: str, level: int = 1):
        """Add markdown header."""
        self.sections.append(f"{'#' * level} {title}\n")
    
    def add_metadata(self, **kwargs):
        """Add metadata section."""
        self.metadata.update(kwargs)
    
    def add_section(self, title: str, content: str, code_block: bool = False, language: str = ""):
        """Add a section with optional code block."""
        self.sections.append(f"\n## {title}\n")
        if code_block:
            self.sections.append(f"```{language}\n{content}\n```\n")
        else:
            self.sections.append(f"{content}\n")
    
    def add_list(self, title: str, items: List[str], ordered: bool = False):
        """Add a bulleted or numbered list."""
        self.sections.append(f"\n## {title}\n")
        for i, item in enumerate(items, 1):
            prefix = f"{i}." if ordered else "-"
            self.sections.append(f"{prefix} {item}\n")
    
    def add_command_output(self, command: str, output: str, exit_code: int = 0):
        """Add command execution result."""
        status = "✅ Success" if exit_code == 0 else "❌ Failed"
        self.sections.append(f"\n### Command: `{command}`\n")
        self.sections.append(f"**Status:** {status} (exit code: {exit_code})\n")
        self.sections.append("**Output:**\n")
        self.sections.append(f"```\n{output}\n```\n")
    
    def add_summary(self, actions_taken: List[str], next_steps: List[str]):
        """Add summary of actions and next steps."""
        self.sections.append("\n## Summary\n")
        self.sections.append("**Actions Taken:**\n")
        for action in actions_taken:
            self.sections.append(f"- ✅ {action}\n")
        
        if next_steps:
            self.sections.append("\n**Next Steps:**\n")
            for step in next_steps:
                self.sections.append(f"- ➡️ {step}\n")
    
    def render(self) -> str:
        """Render the complete markdown output."""
        output = []
        
        # Add metadata as front matter if present
        if self.metadata:
            output.append("---\n")
            for key, value in self.metadata.items():
                if isinstance(value, (list, dict)):
                    value = json.dumps(value, indent=2)
                output.append(f"{key}: {value}\n")
            output.append("---\n")
        
        output.extend(self.sections)
        output.append(f"\n---\n*Generated at {datetime.now().isoformat()}*\n")
        
        return "".join(output)


def _build_functional_overview(
    features: List[str],
    summary: str,
    entities: List[str],
    files: List[str],
    stats: Dict[str, tuple],
    current_version: str,
    new_version: str,
    commit_msg: str,
    project_types: List[str]
) -> tuple:
    """Build the functional overview section and key entities.
    
    Returns:
        Tuple of (section_title, section_content, key_entities_list)
    """
    total_adds = sum(s[0] for s in stats.values())
    total_dels = sum(s[1] for s in stats.values())
    
    if features or summary:
        functional_overview = f"**What Changed:** "
        if features:
            if len(features) == 1:
                functional_overview += f"Added {features[0]} support"
            elif len(features) == 2:
                functional_overview += f"Added {features[0]} and {features[1]} support"
            else:
                functional_overview += f"Added {features[0]}, {features[1]}, and {len(features)-2} more features"
        elif summary:
            functional_overview += summary
        else:
            functional_overview += f"Updated {len(files)} files"
        
        functional_overview += f"\n**Scope:** {len(files)} files (+{total_adds}/-{total_dels} lines)"
        functional_overview += f"\n**Version:** {current_version} → {new_version}"
        functional_overview += f"\n**Commit:** `{commit_msg}`"
        
        # Key changes (entities)
        meaningful = []
        if entities:
            meaningful = [e for e in entities if len(e) > 2][:6]
        
        return "Summary", functional_overview, meaningful
    else:
        # Fallback to traditional overview
        overview = f"""**Project Type:** {', '.join(project_types)}
**Files Changed:** {len(files)} (+{total_adds}/-{total_dels} lines)
**Version:** {current_version} → {new_version}
**Commit Message:** `{commit_msg}`""".strip()
        
        return "Overview", overview, []


def _build_files_section(
    formatter,
    files: List[str],
    stats: Dict[str, tuple],
    analysis: Optional[Dict[str, Any]]
) -> None:
    """Build the files/domains section."""
    # Group files by domain if analysis available
    if analysis and analysis.get('domains'):
        domains = analysis['domains']
        domain_summary = []
        for domain, domain_files in domains.items():
            if domain_files:
                domain_summary.append(f"**{domain.title()}:** {len(domain_files)} files")
        if domain_summary:
            formatter.add_list("Changes by Area", domain_summary)
    else:
        # Files list (fallback)
        file_details = []
        for f in files[:10]:  # Limit to 10 files
            adds, dels = stats.get(f, (0, 0))
            file_details.append(f"{f} (+{adds}/-{dels})")
        
        if len(files) > 10:
            file_details.append(f"... and {len(files) - 10} more files")
        
        formatter.add_list("Changed Files", file_details)


def _determine_next_steps(error: Optional[str], test_exit_code: int, new_version: str) -> List[str]:
    """Determine appropriate next steps based on outcome."""
    if not error and test_exit_code == 0:
        return [
            "Changes committed successfully",
            f"Version updated to {new_version}",
            "Run `goal push --yes` to retry without prompts",
            "Run `goal --all` for full automation including publish"
        ]
    elif test_exit_code != 0:
        return [
            "Fix failing tests",
            "Run tests manually: pytest",
            "Retry with: goal push",
            "Or skip tests: goal push --yes -m 'chore: skip tests'"
        ]
    else:
        return [
            "Review the error above",
            "Check git status: goal status",
            "Retry when ready"
        ]


def format_push_result(
    project_types: List[str],
    files: List[str],
    stats: Dict[str, tuple],
    current_version: str,
    new_version: str,
    commit_msg: str,
    commit_body: Optional[str] = None,
    test_result: Optional[str] = None,
    test_exit_code: int = 0,
    actions: List[str] = None,
    error: Optional[str] = None,
    analysis: Optional[Dict[str, Any]] = None
) -> str:
    """Format push command result as markdown."""
    
    formatter = MarkdownFormatter()
    
    # Extract features and summary from analysis if available
    features = analysis.get('features', []) if analysis else []
    summary = analysis.get('summary', '') if analysis else ''
    entities = analysis.get('entities', []) if analysis else []
    
    # Add metadata
    formatter.add_metadata(
        command="goal push",
        project_types=project_types,
        version_bump=f"{current_version} -> {new_version}",
        file_count=len(files),
        features=features if features else None,
        timestamp=datetime.now().isoformat()
    )
    
    # Header
    formatter.add_header("Goal Push Result", 1)
    
    # Functional Summary
    section_title, section_content, key_entities = _build_functional_overview(
        features, summary, entities, files, stats,
        current_version, new_version, commit_msg, project_types
    )
    formatter.add_section(section_title, section_content)
    
    # Add key entities if present
    if key_entities:
        formatter.sections.append("\n**Key Functions/Classes:**\n")
        for e in key_entities:
            formatter.sections.append(f"- `{e}`\n")
    
    if commit_body:
        formatter.add_section("Commit Body", commit_body, code_block=True)
    
    # Files/domains section
    _build_files_section(formatter, files, stats, analysis)
    
    # Test results if available
    if test_result is not None:
        formatter.add_command_output(
            "pytest" if "python" in project_types else "test",
            test_result,
            test_exit_code
        )
    
    # Actions taken
    if actions:
        formatter.add_list("Actions Performed", actions, ordered=True)
    
    # Error if present
    if error:
        formatter.add_section("Error", error, code_block=True)
    
    # Next steps
    next_steps = _determine_next_steps(error, test_exit_code, new_version)
    
    formatter.add_summary(
        actions_taken=actions or [],
        next_steps=next_steps
    )
    
    return formatter.render()


def _format_complexity_metric(metrics: Dict[str, Any]) -> Optional[str]:
    """Format complexity change as a single metric line, or None."""
    old_cc = metrics.get('old_complexity', 1)
    new_cc = metrics.get('new_complexity', old_cc)
    if old_cc == new_cc or old_cc <= 0:
        return None
    delta_pct = ((new_cc - old_cc) / old_cc) * 100
    if delta_pct < -10:
        return f"📉 -{abs(delta_pct):.0f}% complexity (refactor win)"
    if delta_pct > 50:
        return f"⚠️ +{delta_pct:.0f}% complexity (monitor)"
    if delta_pct > 0:
        return f"📊 +{delta_pct:.0f}% complexity (new features)"
    return "➡️ Stable complexity"


def _format_metrics_section(metrics: Dict[str, Any], relations: Dict[str, Any] = None) -> str:
    """Build the Impact Metrics section content."""
    lines: List[str] = []
    cc_line = _format_complexity_metric(metrics)
    if cc_line:
        lines.append(cc_line)
    if metrics.get('test_impact', 0) > 0:
        lines.append(f"🧪 Test coverage: +{metrics['test_impact']}%")
    rel_count = len(relations.get('relations', [])) if relations else 0
    if rel_count > 0:
        lines.append(f"🔗 Relations: {rel_count} dependencies detected")
    lines.append(f"⭐ Value score: {metrics['value_score']}/100")
    return '\n'.join(lines)


def _format_relations_section(relations: Dict[str, Any]) -> Optional[str]:
    """Build the Relations section content, or None if empty."""
    if not relations or not relations.get('chain'):
        return None
    content = f"**Chain:** `{relations['chain']}`"
    if relations.get('ascii'):
        content += f"\n```\n{relations['ascii']}\n```"
    return content


def format_enhanced_summary(
    commit_title: str,
    commit_body: str,
    capabilities: List[Dict[str, str]] = None,
    roles: List[Dict[str, str]] = None,
    relations: Dict[str, Any] = None,
    metrics: Dict[str, Any] = None,
    files: List[str] = None,
    stats: Dict[str, tuple] = None,
    current_version: str = "",
    new_version: str = ""
) -> str:
    """Format enhanced business-value summary as markdown."""
    
    formatter = MarkdownFormatter()
    
    # Metadata
    formatter.add_metadata(
        command="goal push",
        enhanced=True,
        version_bump=f"{current_version} -> {new_version}" if current_version else None,
        value_score=metrics.get('value_score') if metrics else None,
        timestamp=datetime.now().isoformat()
    )
    
    formatter.add_header("Goal Push Result", 1)
    
    # Calculate totals
    total_adds = sum(s[0] for s in (stats or {}).values())
    total_dels = sum(s[1] for s in (stats or {}).values())
    
    # Main summary with business value
    summary_parts = [
        f"**Files:** {len(files or [])} (+{total_adds}/-{total_dels} lines)",
        f"**Version:** {current_version} → {new_version}" if current_version else None,
        f"**Commit:** `{commit_title}`"
    ]
    formatter.add_section("Summary", '\n'.join(p for p in summary_parts if p))
    
    # NEW CAPABILITIES section
    if capabilities:
        cap_lines = [f"✅ **{cap['capability']}** - {cap['impact']}" for cap in capabilities[:5]]
        formatter.add_section("New Capabilities", '\n'.join(cap_lines))
    
    # FUNCTIONAL COMPONENTS section (roles)
    if roles:
        role_lines = [f"- **{role['role']}** (`{role['name']}`)" for role in roles[:5]]
        formatter.add_section("Functional Components", '\n'.join(role_lines))
    
    # IMPACT METRICS section
    if metrics:
        formatter.add_section("Impact Metrics", _format_metrics_section(metrics, relations))
    
    # RELATIONS section
    rel_content = _format_relations_section(relations)
    if rel_content:
        formatter.add_section("Relations", rel_content)
    
    # Commit body (if different from capabilities display)
    if commit_body and not capabilities:
        formatter.add_section("Details", commit_body, code_block=True)
    
    return formatter.render()


def format_status_output(
    version: str,
    branch: str,
    staged_files: List[str],
    unstaged_files: List[str]
) -> str:
    """Format status command output as markdown."""
    
    formatter = MarkdownFormatter()
    
    formatter.add_header("Goal Status", 1)
    
    # Current state
    state_info = f"""
**Version:** {version}
**Branch:** {branch}
**Staged Files:** {len(staged_files)}
**Unstaged Files:** {len(unstaged_files)}
    """.strip()
    
    formatter.add_section("Current State", state_info)
    
    # Files
    if staged_files:
        formatter.add_list("Staged Files", staged_files)
    
    if unstaged_files:
        formatter.add_list("Unstaged/Untracked Files", unstaged_files[:20])
        if len(unstaged_files) > 20:
            formatter.add_section("", f"... and {len(unstaged_files) - 20} more files")
    
    # Quick actions
    actions = [
        "Commit staged files: `goal push`",
        "Stage all changes: `git add . && goal push`",
        "Check version: `goal version`",
        "Dry run: `goal push --dry-run`"
    ]
    
    formatter.add_list("Quick Actions", actions)
    
    return formatter.render()
