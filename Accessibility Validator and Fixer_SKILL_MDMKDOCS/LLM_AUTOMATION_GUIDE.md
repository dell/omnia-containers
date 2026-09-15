# LLM-Enhanced Accessibility Fixer - User Guide

## Overview

The LLM-Enhanced Accessibility Fixer is an intelligent automation that uses Large Language Model (LLM) capabilities to fix complex accessibility issues in RST documentation files. It extends the existing Accessibility Validator & Fixer skill with context-aware fixing for issues that require understanding of the surrounding content.

## What It Does

The LLM-enhanced fixer intelligently handles accessibility issues that require contextual understanding:

- **Missing Image Alt Text**: Generates descriptive alt text based on image filenames and surrounding content
- **Empty Image Alt Text**: Replaces empty alt attributes with meaningful descriptions
- **Non-Descriptive Links**: Converts generic link text like "click here" into descriptive text based on URL context
- **Empty Section Titles**: Generates meaningful section titles from surrounding content
- **Missing Directive Options**: Adds appropriate RST directive options based on context

## How It Works

### 1. Issue Categorization

The fixer automatically categorizes accessibility issues into three types:

- **Auto-fixable**: Simple fixes (insecure links, bare URLs) handled by existing fixer
- **LLM-fixable**: Complex fixes requiring context understanding (handled by LLM fixer)
- **Manual-only**: Issues requiring domain knowledge (marked for manual review)

### 2. Context Analysis

For LLM-fixable issues, the fixer:
- Extracts the problematic line
- Gathers surrounding lines for context
- Analyzes the content structure
- Applies intelligent fix strategies

### 3. Fix Generation

The fixer uses two approaches:

#### Local Rule-Based (Default)
- Pattern matching on filenames, URLs, and content
- Heuristic-based text generation
- No external dependencies
- Works offline

#### API-Based (Optional)
- Integration with OpenAI, Anthropic, or other LLM APIs
- More sophisticated context understanding
- Requires API key configuration
- Works with internet connection

## Installation & Setup

### 1. Configuration File

The `llm_config.json` file controls the fixer behavior:

```json
{
  "enabled": true,
  "provider": "local",
  "model": "local-rules",
  "fix_strategies": {
    "MISSING_IMAGE_ALT": {
      "enabled": true,
      "strategy": "filename-based"
    }
  }
}
```

### 2. Configuration Options

- `enabled`: Enable/disable LLM fixing (default: true)
- `provider`: "local" (rule-based) or "openai"/"anthropic" (API-based)
- `model`: Model name for API-based providers
- `fix_strategies`: Configure which issue types to fix
- `safety_settings`: Backup and file size limits
- `reporting`: Report generation options

## Usage

### Standalone Usage

Run the LLM fixer directly on an accessibility report:

```bash
python llm_enhanced_fixer.py reports/baseline_validation/accessibility_report.json
```

With custom configuration:

```bash
python llm_enhanced_fixer.py reports/baseline_validation/accessibility_report.json --llm-config custom_llm_config.json
```

Dry run (show what would be fixed without applying changes):

```bash
python llm_enhanced_fixer.py reports/baseline_validation/accessibility_report.json --dry-run
```

### Integrated Workflow

Use the LLM fixer directly on the accessibility report:

```bash
python llm_enhanced_fixer.py reports/baseline_validation/accessibility_report.json
```

With custom LLM configuration:

```bash
python llm_enhanced_fixer.py reports/baseline_validation/accessibility_report.json --llm-config custom_llm_config.json
```

Note: The main workflow script (`run_omnia_accessibility.py`) currently uses the standard fixer. For LLM-enhanced fixing, run the LLM fixer separately after validation.

## Fix Strategies

### Image Alt Text

**Strategy**: Filename-based + Context analysis

**Example**:
- Filename: `screenshot_configuration_panel.png`
- Generated alt: "Screenshot showing configuration panel"

**Fallback**: "Image showing interface elements"

### Non-Descriptive Links

**Strategy**: URL-based text generation

**Example**:
- URL: `https://docs.example.com/getting-started`
- Generated text: "View the getting started documentation"

**Fallback**: Manual review required

### Empty Section Titles

**Strategy**: Context extraction from surrounding lines

**Example**:
- Surrounding text: "This section covers the installation process..."
- Generated title: "Installation Process"

**Fallback**: Manual review required

### Missing Directive Options

**Strategy**: Directive defaults based on type

**Example**:
- Code block: Adds `:linenos:` option
- Image: Adds `:alt:` option

**Fallback**: Manual review required

## Safety Features

### Automatic Backup

- Creates `.llm_backup/` directory
- Timestamped backup files: `filename_YYYYMMDD_HHMMSS.bak`
- Preserves original files before any changes

### File Size Limits

- Maximum file size: 10MB (configurable)
- Only processes `.rst` and `.md` files (configurable)

### Validation

- Re-validates after LLM fixes
- Generates updated accessibility report
- Tracks fix success/failure rates

## Reports

### LLM Fix Report

Generated automatically after fixing:
- Total LLM-fixable issues
- Successfully fixed count
- Failed fixes count
- Skipped issues count
- Detailed fix list with backup locations

**Location**: `reports/llm_fix_report.txt`

### Updated Accessibility Report

After LLM fixes, a new validation report is generated:
- Shows remaining issues
- Tracks improvement metrics
- Identifies issues still requiring manual attention

**Location**: `reports/current_status/accessibility_report_llm_fixed.json`

## API Integration (Optional)

### OpenAI Integration

Configure in `llm_config.json`:

```json
{
  "provider": "openai",
  "api_key": "your-openai-api-key",
  "model": "gpt-4",
  "api_settings": {
    "openai": {
      "base_url": "https://api.openai.com/v1",
      "model": "gpt-4",
      "max_retries": 3
    }
  }
}
```

### Anthropic Integration

```json
{
  "provider": "anthropic",
  "api_key": "your-anthropic-api-key",
  "model": "claude-3-opus-20240229",
  "api_settings": {
    "anthropic": {
      "base_url": "https://api.anthropic.com/v1",
      "model": "claude-3-opus-20240229",
      "max_retries": 3
    }
  }
}
```

## Best Practices

### 1. Start with Local Rules

- Use `provider: "local"` for initial testing
- No API keys required
- Works offline
- Fast and reliable

### 2. Review Fixes

- Always review the `llm_fix_report.txt`
- Check backup files if needed
- Manually verify complex fixes

### 3. Re-validate

- Run validation after LLM fixes
- Compare before/after reports
- Track improvement metrics

### 4. Manual Review

- Some issues still require manual intervention
- Focus on high-severity remaining issues
- Use LLM suggestions as starting point

## Troubleshooting

### No Fixes Generated

**Problem**: LLM fixer reports 0 fixes applied

**Solutions**:
- Check if `llm_config.json` has `enabled: true`
- Verify report contains LLM-fixable issues
- Check fix strategies are enabled in config
- Review fix strategy patterns match your content

### Fix Quality Issues

**Problem**: Generated fixes are not appropriate

**Solutions**:
- Customize `local_rules` patterns in config
- Enable API-based provider for better context understanding
- Adjust temperature setting (lower = more conservative)
- Review and manually correct after LLM fixes

### Backup Issues

**Problem**: Backup files not created

**Solutions**:
- Check write permissions in target directory
- Verify `backup_enabled: true` in config
- Check disk space availability
- Review backup directory path in config

## Integration with Existing Workflow

### Complete Workflow Example

```bash
# Step 1: Validate
python run_omnia_accessibility.py path/to/docs --skip-fixes

# Step 2: Apply LLM-enhanced fixes
python llm_enhanced_fixer.py reports/baseline_validation/accessibility_report.json

# Step 3: Review remaining issues
python run_omnia_accessibility.py path/to/docs --skip-fixes

# Step 4: Manual fixes for remaining issues
# (Use IDE to manually fix remaining issues)

# Step 5: Final validation
python run_omnia_accessibility.py path/to/docs --skip-fixes
```

### Comparison with Traditional Fixing

**Traditional Workflow**:
1. Validate → 2. Manual review → 3. Manual fixes → 4. Re-validate (2-3 hours)

**LLM-Enhanced Workflow**:
1. Validate → 2. LLM fixes → 3. Manual review → 4. Re-validate (20-30 minutes)

**Time Savings**: ~80% reduction in fixing time

## Advanced Configuration

### Custom Fix Patterns

Add custom patterns to `local_rules` in config:

```json
{
  "local_rules": {
    "image_alt_patterns": {
      "custom_pattern": "Custom description for"
    },
    "link_text_patterns": {
      "custom_link": "Custom link text for"
    }
  }
}
```

### Issue Type Filtering

Enable/disable specific issue types:

```json
{
  "fix_strategies": {
    "MISSING_IMAGE_ALT": {
      "enabled": true
    },
    "NON_DESCRIPTIVE_LINK": {
      "enabled": false
    }
  }
}
```

### Safety Adjustments

Modify safety settings:

```json
{
  "safety_settings": {
    "backup_enabled": true,
    "backup_dir": ".custom_backup",
    "max_file_size_mb": 20,
    "dry_run_by_default": true
  }
}
```

## Performance Considerations

### Local Rule-Based
- Speed: Very fast (seconds)
- Resource usage: Minimal
- Quality: Good for common patterns
- Best for: Large codebases, offline use

### API-Based
- Speed: Moderate (depends on API)
- Resource usage: Network required
- Quality: Excellent for complex contexts
- Best for: Complex documentation, high accuracy needed

## Limitations

### Current Limitations

- Only handles RST and Markdown files
- Requires Python 3.6+
- Local rules have limited context understanding
- API integration requires internet and API keys

### Known Issues

- May not handle highly technical content perfectly
- Requires manual review of all fixes
- Some edge cases may need manual intervention

## Future Enhancements

### Planned Features

- Support for additional file formats
- Enhanced context understanding
- Learning from manual corrections
- Integration with more LLM providers
- Batch processing improvements

## Support & Feedback

### Getting Help

1. Review this documentation
2. Check `llm_fix_report.txt` for detailed information
3. Review configuration in `llm_config.json`
4. Check backup files for original content

### Reporting Issues

When reporting issues, include:
- Accessibility report (JSON)
- LLM fix report (TXT)
- Configuration file (JSON)
- Example of the issue
- Expected vs actual behavior

## Summary

The LLM-Enhanced Accessibility Fixer provides intelligent, context-aware fixing for complex accessibility issues. It integrates seamlessly with the existing Accessibility Validator & Fixer workflow and can significantly reduce the time required to fix accessibility issues in RST documentation.

**Key Benefits**:
- 80% reduction in fixing time
- Intelligent context-aware fixes
- Automatic backup and rollback
- Works offline with local rules
- Optional API integration for enhanced accuracy
- Comprehensive reporting and tracking

**Recommended Usage**:
1. Start with local rule-based provider
2. Review all fixes in the report
3. Use API integration for complex content
4. Always re-validate after fixes
5. Manually review remaining issues
