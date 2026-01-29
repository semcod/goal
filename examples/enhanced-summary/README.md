# Enhanced Summary Examples

This directory contains sample outputs demonstrating the Enhanced Summary feature.

## Files

| File | Description |
|------|-------------|
| [before-after.md](before-after.md) | Comparison of traditional vs enhanced output |
| [sample-output.md](sample-output.md) | Real-world enhanced summary output |
| [config-example.yaml](config-example.yaml) | Quality configuration for enhanced summaries |

## Quick Demo

```bash
# Generate enhanced summary for current changes
goal commit --detailed

# Show in dry-run mode
goal push --dry-run

# Force legacy format for comparison
goal push --dry-run --abstraction legacy
```

## See Also

- [Enhanced Summary Documentation](../../docs/enhanced-summary.md)
- [Configuration Guide](../../docs/configuration.md)
