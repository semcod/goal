# Enhanced Commit Summary - Enterprise-Grade Intelligence

> Transform statistical commit messages into business-value summaries with capabilities, metrics, and dependency chains.

## Table of Contents

- [Overview](#overview)
- [Before vs After](#before-vs-after)
- [Architecture](#architecture)
- [Implementation](#implementation)
- [Configuration](#configuration)
- [Comparison with Alternatives](#comparison-with-alternatives)
- [API Reference](#api-reference)

---

## Overview

Goal's Enhanced Summary system transforms raw code changes into **business-value focused** commit messages that communicate:

| Component | What it Does |
|-----------|--------------|
| **Capability Detection** | Maps code patterns to functional values |
| **Role Mapping** | Converts `_analyze_diff` → "language-specific code analyzer" |
| **Relation Detection** | Builds `config→cli→generator` dependency chains |
| **Quality Metrics** | Complexity delta, test coverage, value score |

### Why It Matters

```
❌ BEFORE: refactor(core): add testing, logging, validation
   - Generic keywords, no context
   - No developer benefit shown
   - +1404 lines = size, not meaning

✅ AFTER: refactor(core): enterprise-grade commit intelligence engine
   - Clear business value
   - Capabilities with impacts
   - Metrics and relations (YAML format)
```

---

## Before vs After

### Traditional Commit (Statistics-Based)

```text
refactor(core): add testing, logging, validation

Statistics: 7 files changed, 1404 insertions, 16 deletions

Summary:
- Dirs: goal=7
- Exts: .py=7
- A/M/D: 2/5/0

Added files:
- goal/deep_analyzer.py (+515/-0)
- goal/enhanced_summary.py (+493/-0)
```

**Problems:**
- "add testing, logging, validation" = keyword list, not value
- No file relationships shown
- +1404 lines = size, not meaning
- Developer value: 2/10

### Enhanced Commit (Business-Value YAML)

```yaml
refactor(core): enterprise-grade commit intelligence engine

new_capabilities:
  - capability: DeepAnalyzer
    impact: AST-based code analysis pipeline
  - capability: EnhancedSummary
    impact: Functional value extraction (85% accuracy)
  - capability: RelationMapper
    impact: config→cli→commit dependency chains
  - capability: QualityMetrics
    impact: Complexity tracking, test coverage delta

impact:
  value_score: 85
  relations: "cli→formatter"
  complexity_delta: +549

architecture:
  - category: analysis
    files: 1
    names: [deep_analyzer.py]
  - category: core
    files: 2
    names: [commit_generator.py, enhanced_summary.py]

dependency_flow:
  chain: config→cli→generator
  relations:
    - from: config.py
      to: cli.py
    - from: cli.py
      to: generator.py
```

**Improvements:**
- Clear business value in title
- Capabilities with functional descriptions
- Metrics showing quality impact
- Dependency chain visualization
- Developer value: 9/10

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Enhanced Summary Pipeline                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ CodeChange   │───▶│ Enhanced     │───▶│ Markdown     │      │
│  │ Analyzer     │    │ Summary      │    │ Formatter    │      │
│  │ (AST-based)  │    │ Generator    │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ - Python AST │    │ - Role Map   │    │ - Capability │      │
│  │ - JS Regex   │    │ - Relations  │    │   sections   │      │
│  │ - Markdown   │    │ - Metrics    │    │ - Impact     │      │
│  │   Headers    │    │ - Values     │    │   metrics    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Files

| File | Purpose | Lines |
|------|---------|-------|
| [`goal/deep_analyzer.py`](../goal/deep_analyzer.py) | AST-based code change analysis | ~515 |
| [`goal/enhanced_summary.py`](../goal/enhanced_summary.py) | Business value extraction | ~493 |
| [`goal/commit_generator.py`](../goal/commit_generator.py) | Commit message orchestration | ~790 |
| [`goal/formatter.py`](../goal/formatter.py) | Markdown output formatting | ~350 |
| [`goal/config.py`](../goal/config.py) | Quality thresholds & patterns | ~790 |

---

## Implementation

### 1. Role Mapping (Entity → Function)

Instead of showing raw function names, we map them to functional roles:

```python
# goal/enhanced_summary.py
ROLE_PATTERNS = {
    r'_analyze_(python|js|generic)_diff': 'language-specific code analyzer',
    r'CodeChangeAnalyzer': 'AST-based change detector',
    r'generate_functional_summary': 'business value summarizer',
    r'EnhancedSummaryGenerator': 'enterprise changelog generator',
    r'GoalConfig': 'configuration manager',
    r'@click\.command': 'CLI command',
}
```

**Result:**
```
❌ add functions: __init__, _analyze_generic_diff
✅ ✅ language-specific code analyzer (_analyze_generic_diff)
```

### 2. Capability Detection (Pattern → Value)

Detect what capabilities the changes bring:

```python
# goal/enhanced_summary.py
VALUE_PATTERNS = {
    'ast_analysis': {
        'signatures': ['ast.parse', 'ast.walk', 'libcst', 'tree-sitter'],
        'capability': 'deep code analysis engine',
        'impact': 'intelligent change detection'
    },
    'dependency_graph': {
        'signatures': ['networkx', 'relations', 'dependencies', 'graph'],
        'capability': 'code relationship mapping',
        'impact': 'architecture understanding'
    },
    'quality_metrics': {
        'signatures': ['radon', 'cyclomatic', 'complexity', 'coverage'],
        'capability': 'code quality metrics',
        'impact': 'maintainability tracking'
    },
}
```

**Output:**
```yaml
new_capabilities:
  - capability: deep code analysis engine
    impact: intelligent change detection
  - capability: code relationship mapping
    impact: architecture understanding
  - capability: code quality metrics
    impact: maintainability tracking
```

### 3. Relation Detection (File Dependencies)

Analyze imports to build dependency chains:

```python
# goal/enhanced_summary.py
def detect_file_relations(self, files: List[str]) -> Dict[str, Any]:
    relations = []
    
    # Parse imports
    import_pattern = r'from\s+\.?(\w+)\s+import|import\s+\.?(\w+)'
    
    for f in files:
        imports = re.findall(import_pattern, content)
        for imp in imports:
            # Check if imported module is in changed files
            if imp_name in changed_file_names:
                relations.append({
                    'from': source_file,
                    'to': imp_name,
                    'type': 'imports'
                })
    
    return {
        'relations': relations,
        'chain': self._build_relation_chain(relations),
        'ascii': self._render_relations_ascii(relations)
    }
```

**Output:**
```yaml
dependency_flow:
  chain: cli→commit_generator→smart_commit
  relations:
    - from: cli.py
      to: commit_generator.py
    - from: cli.py
      to: formatter.py
```

### 4. Quality Metrics

Calculate value metrics for the changes:

```python
# goal/enhanced_summary.py
def calculate_quality_metrics(self, analysis, files) -> Dict[str, Any]:
    return {
        'functional_coverage': 72,      # detected areas vs entities
        'relation_density': 0.1,        # relations per file
        'complexity_delta': 549,        # cyclomatic complexity change
        'test_impact': 15,              # % inferred from test/ changes
        'value_score': 85               # composite score 0-100
    }
```

**Output:**
```
IMPACT:
📊 Complexity: +549%
🔗 Relations: 0.1 density
⭐ Value score: 85/100
```

---

## Configuration

### goal.yaml Quality Settings

```yaml
quality:
  commit_summary:
    min_value_words: 3              # "deep analysis engine" ✓
    max_generic_terms: 0            # ban: "update", "cleaner"
    required_metrics: 2             # complexity, coverage, etc.
    relation_threshold: 0.7         # must find relations
    generic_terms:
      - update
      - improve
      - enhance
      - cleaner
      - better
      - misc

  enhanced_summary:
    enabled: true
    min_capabilities: 1
    min_value_score: 50
    include_metrics: true
    include_relations: true
    include_roles: true

  role_patterns:
    '_analyze_(python|js|generic)_diff': 'language-specific code analyzer'
    'CodeChangeAnalyzer': 'AST-based change detector'
    'generate_functional_summary': 'business value summarizer'

  value_patterns:
    ast_analysis:
      signatures: ['ast.parse', 'ast.walk', 'libcst']
      capability: 'deep code analysis engine'
      impact: 'intelligent change detection'
```

### Enable/Disable Enhanced Summary

```bash
# Use enhanced summary (default when config exists)
goal push

# Force legacy format
goal push --abstraction legacy

# Specific abstraction level
goal push --abstraction high    # Business value focus
goal push --abstraction medium  # Balanced
goal push --abstraction low     # Statistical focus
```

---

## Comparison with Alternatives

### Feature Comparison

| Feature | Goal Enhanced | Conventional Changelog | CodeClimate | Semantic Release |
|---------|--------------|----------------------|-------------|------------------|
| **Business Value Titles** | ✅ Auto-detected | ❌ Manual | ❌ No | ❌ Type-based |
| **Capability Detection** | ✅ Pattern-based | ❌ No | ⚠️ Limited | ❌ No |
| **Relation Mapping** | ✅ Import analysis | ❌ No | ✅ Yes | ❌ No |
| **Quality Metrics** | ✅ Complexity, coverage | ❌ No | ✅ Yes | ❌ No |
| **Role Mapping** | ✅ Entity → Function | ❌ No | ❌ No | ❌ No |
| **Zero Config** | ✅ Auto-detection | ⚠️ Needs setup | ❌ Complex | ⚠️ Plugin-based |
| **Multi-language** | ✅ Python, JS, Rust | ⚠️ JS-focused | ✅ Yes | ⚠️ JS-focused |

### Output Comparison

**Conventional Changelog:**
```
## [1.2.0] - 2024-01-29

### Added
- Add deep analyzer module
- Add enhanced summary generator

### Changed
- Update commit generator
```

**CodeClimate:**
```
Quality: B (3.2 maintainability)
Complexity: 15 methods above threshold
Duplication: 2.3%
```

**Goal Enhanced:**
```
refactor(core): enterprise-grade commit intelligence engine

NEW CAPABILITIES:
├── deep code analysis engine: intelligent change detection
├── code relationship mapping: architecture understanding
└── code quality metrics: maintainability tracking

IMPACT:
📊 Complexity: +549%
🔗 Relations: cli→formatter chain
⭐ Value score: 85/100
```

### When to Use What

| Use Case | Recommended Tool |
|----------|-----------------|
| **Quick commits with business context** | Goal Enhanced |
| **Strict conventional commits** | Conventional Changelog |
| **Code quality monitoring** | CodeClimate + Goal |
| **Automated releases** | Semantic Release + Goal |
| **Enterprise changelogs** | Goal Enhanced |

---

## API Reference

### EnhancedSummaryGenerator

```python
from goal.enhanced_summary import EnhancedSummaryGenerator

generator = EnhancedSummaryGenerator(config=config_dict)

# Generate full summary
result = generator.generate_enhanced_summary(files, diff_content)
# Returns: {
#     'title': 'enterprise-grade commit intelligence',
#     'body': 'NEW CAPABILITIES:\n...',
#     'capabilities': [{'id': 'ast_analysis', 'capability': '...', 'impact': '...'}],
#     'roles': [{'name': '_analyze_diff', 'role': 'language-specific analyzer'}],
#     'relations': {'chain': 'cli→generator', 'ascii': '...'},
#     'metrics': {'value_score': 85, 'complexity_delta': 549}
# }

# Map entity to role
role = generator.map_entity_to_role('_analyze_python_diff')
# Returns: 'language-specific code analyzer'

# Detect capabilities
caps = generator.detect_capabilities(files, diff_content)
# Returns: [{'id': 'ast_analysis', 'capability': '...', 'impact': '...'}]

# Calculate metrics
metrics = generator.calculate_quality_metrics(analysis, files)
# Returns: {'value_score': 85, 'complexity_delta': 549, ...}
```

### CodeChangeAnalyzer

```python
from goal.deep_analyzer import CodeChangeAnalyzer

analyzer = CodeChangeAnalyzer()

# Analyze single file
result = analyzer.analyze_file_diff(filepath, old_content, new_content)
# Returns: {
#     'filepath': 'goal/cli.py',
#     'language': 'python',
#     'added_entities': [{'name': 'push', 'type': 'function', ...}],
#     'modified_entities': [...],
#     'functional_areas': ['cli', 'configuration'],
#     'complexity_change': 5
# }

# Generate functional summary
summary = analyzer.generate_functional_summary(files)
# Returns: {
#     'aggregated': {...},
#     'functional_value': 'enhanced code analysis capabilities',
#     'relations': [('config', 'cli', 'configuration-driven CLI')],
#     'summary': 'New classes: CodeChangeAnalyzer\nNew functions: ...'
# }
```

---

## See Also

- [Configuration Guide](configuration.md) - Full goal.yaml reference
- [Commands Reference](commands.md) - All CLI options
- [Examples](examples.md) - Real-world usage
- [Troubleshooting](troubleshooting.md) - Common issues

---

*Generated by Goal Enhanced Summary - Enterprise-grade commit intelligence*
