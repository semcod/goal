# Sample Enhanced Summary Output

Real-world output from `goal push --dry-run`:

---

## Markdown Output (Default)

```yaml
---
command: goal push
project_types: ["python"]
version_bump: 2.1.5 -> 2.1.6
file_count: 7
enhanced: true
value_score: 85
timestamp: 2026-01-29T12:37:28.647018
---
```

```markdown
# Goal Push Result

## Summary
**Files:** 7 (+1404/-16 lines)
**Version:** 2.1.5 → 2.1.6
**Commit:** `feat(goal): deep code analysis engine`

## New Capabilities
✅ **deep code analysis engine** - intelligent change detection
✅ **code relationship mapping** - architecture understanding
✅ **code quality metrics** - maintainability tracking
✅ **multi-language support** - universal code analysis
✅ **configuration management** - customizable workflows

## Functional Components
- **summary generator** (`generate_enhanced_summary`)
- **diff analysis engine** (`analyze_file_diff`)
- **complexity analyzer** (`_calculate_complexity`)
- **language-specific code analyzer** (`_analyze_generic_diff`)
- **dependency graph builder** (`detect_relations`)

## Impact Metrics
📉 Complexity: +549%
🔗 Relations: 0.1 density
⭐ Value score: 85/100

## Relations
**Chain:** `cli→commit_generator→smart_commit`
```
CHANGE PIPELINE:
cli.py ──┬──> commit_generator.py
         └──> formatter.py
```

---

*Generated at 2026-01-29T12:37:28.647018*
```

---

## Interactive Mode Output

```text
## GOAL Workflow Preview

- **Files:** 7 (+1404/-16 lines)
- **Version:** 2.1.5 → 2.1.6
- **Commit:** `feat(goal): deep code analysis engine`

### Commit Body
```
NEW CAPABILITIES:
├── deep code analysis engine: intelligent change detection
├── code relationship mapping: architecture understanding
├── code quality metrics: maintainability tracking
├── multi-language support: universal code analysis
└── configuration management: customizable workflows

FUNCTIONAL COMPONENTS:
✅ summary generator (generate_enhanced_summary)
✅ diff analysis engine (analyze_file_diff)
✅ complexity analyzer (_calculate_complexity)

IMPACT:
📊 Complexity: +549%
🔗 Relations: 0.1 density
⭐ Value score: 85/100

RELATIONS:
Chain: cli→formatter

Files: analysis: deep_analyzer.py; cli: cli.py; config: config.py; 
       core: commit_generator.py, enhanced_summary.py, smart_commit.py; 
       output: formatter.py
```

Run tests? [Y/n]
```

---

## JSON Output (for CI/CD)

```json
{
  "title": "feat(goal): deep code analysis engine",
  "body": "NEW CAPABILITIES:\n├── deep code analysis engine...",
  "enhanced": true,
  "capabilities": [
    {
      "id": "ast_analysis",
      "capability": "deep code analysis engine",
      "impact": "intelligent change detection"
    },
    {
      "id": "dependency_graph",
      "capability": "code relationship mapping",
      "impact": "architecture understanding"
    }
  ],
  "roles": [
    {
      "name": "generate_enhanced_summary",
      "role": "summary generator",
      "type": "function"
    },
    {
      "name": "analyze_file_diff",
      "role": "diff analysis engine",
      "type": "function"
    }
  ],
  "relations": {
    "chain": "cli→commit_generator→smart_commit",
    "relations": [
      {"from": "cli", "to": "commit_generator", "type": "imports"},
      {"from": "commit_generator", "to": "smart_commit", "type": "imports"}
    ]
  },
  "metrics": {
    "functional_coverage": 72,
    "relation_density": 0.1,
    "complexity_delta": 549,
    "test_impact": 0,
    "value_score": 85
  }
}
```

---

## Comparison: Different Abstraction Levels

### High (Business Value Focus)
```
feat(goal): enterprise-grade commit intelligence engine
```

### Medium (Balanced)
```
feat(goal): add DeepAnalyzer, EnhancedSummary, RelationMapper
```

### Low (Statistical)
```
feat(goal): update 7 files (+1404/-16)
```

### Legacy (Traditional)
```
refactor(core): add testing, logging, validation
```
