# Quick Start Guide - Omnia Markdown Accessibility Skill

## 5-Minute Quick Start

### Option 1: Full Automated Workflow (Recommended)

```bash
# Run complete 9-step workflow with automatic fixes
python run_omnia_accessibility.py ..\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs
```

This will:
1. Validate all Markdown files
2. Generate structured baseline reports
3. Apply automatic fixes
4. Re-validate after fixes
5. Generate current status reports
6. Generate comparison report
7. Create HTML visual report with charts
8. Generate Excel/CSV report
9. Create unfixed issues report

### Option 2: Validation Only

```bash
# Validate without automatic fixes
python run_omnia_accessibility.py ..\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs --skip-fixes
```

### Option 3: Validation Without Backup

```bash
# Skip backup creation (useful for testing)
python run_omnia_accessibility.py ..\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs --no-backup
```

### Option 4: Checkpoint Mode (Review Before Fixing, Then Preview Before Publishing)

```bash
# Phase 1: Validation + baseline reports
python run_omnia_accessibility.py ..\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs --checkpoint-mode phase1

# Phase 2: Fixer + all reports (after reviewing baseline)
python run_omnia_accessibility.py ..\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs --checkpoint-mode phase2

# Phase 3: Render + preview (manual steps)
cd ..\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs && mkdocs build
# The HTML report uses file:// URLs and works directly from the built site
# When satisfied, publish to ReadTheDocs: https://your-project.readthedocs.io/
```

This allows you to review the baseline validation report before applying fixes, then review rendered output before publishing.

## Understanding the Reports

### Where Reports Are Generated

All reports are generated in the `reports/` directory:

```
reports/
├── baseline_validation/          # Initial validation report
│   ├── accessibility_report.json
│   ├── INDEX.txt
│   ├── EXECUTIVE_SUMMARY.txt
│   ├── ISSUES_BY_CATEGORY.txt
│   ├── FIX_RECOMMENDATIONS.txt
│   └── WORKFLOW_GUIDE.txt
├── current_status/                # Post-fix validation reports
│   ├── accessibility_report_after.json
│   ├── INDEX.txt
│   ├── EXECUTIVE_SUMMARY.txt
│   ├── ISSUES_BY_CATEGORY.txt
│   ├── FIX_RECOMMENDATIONS.txt
│   └── WORKFLOW_GUIDE.txt
├── comparison_report.txt         # Before/after comparison
├── visual_comparison_with_charts.html  # Interactive visual report
├── excel_report.csv              # Excel-compatible data
└── unfixed_issues_report.txt     # Manual fixes needed
```

### What Each Report Tells You

**baseline_validation/INDEX.txt**: Overview of initial accessibility assessment

**baseline_validation/EXECUTIVE_SUMMARY.txt**: High-level statistics and key findings

**baseline_validation/ISSUES_BY_CATEGORY.txt**: Issues grouped by category (Images, Links, Code, Structure, Tables)

**baseline_validation/FIX_RECOMMENDATIONS.txt**: Specific guidance for each issue type

**baseline_validation/WORKFLOW_GUIDE.txt**: Step-by-step fixing instructions

**comparison_report.txt**: Before/after comparison showing what was fixed

**visual_comparison_with_charts.html**: Interactive HTML report with CSS-based charts (pie charts, bar charts, data tables)

**excel_report.csv**: Excel-compatible data for custom analysis and pivot tables

**unfixed_issues_report.txt**: Detailed report of issues requiring manual intervention

## Using the Batch Files (Windows)

### Validate Documentation

```cmd
run_omnia_md_validator.bat ..\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs/docs
```

### Fix Issues

```cmd
run_omnia_md_fixer.bat reports/baseline_validation/accessibility_report.json auto
```

## Common Use Cases

### First-Time Accessibility Assessment

```bash
python run_omnia_accessibility.py ..\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs
```

### Regular Accessibility Checks

```bash
python run_omnia_accessibility.py ..\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs --skip-fixes
```

### Before Committing Changes

```bash
python run_omnia_accessibility.py ..\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs --no-backup
```

### After Making Manual Fixes

```bash
# Re-validate to check remaining issues
python omnia_md_accessibility_validator.py ..\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs\docs -r -o json -f reports/current_status/accessibility_report_after.json

# Generate new structured reports
python structured_reporting_md.py reports/current_status/accessibility_report_after.json reports/current_status
```

## Understanding Issue Types

### HIGH PRIORITY (Must Fix)
- **MISSING_IMAGE_ALT**: Images without descriptive alt text
- **EMPTY_SECTION_TITLE**: Headers with no content

### MEDIUM PRIORITY (Should Fix)
- **NON_DESCRIPTIVE_LINK**: Links like "click here" or "read more" - **Auto-fixable via config**
- **MISSING_DIRECTIVE_OPTION**: Missing required Markdown elements

### LOW PRIORITY (Nice to Fix)
- **INVALID_CODE_LANGUAGE**: Code blocks with unsupported languages - **Auto-fixable**
- **INSECURE_EXTERNAL_LINK**: HTTP links instead of HTTPS - **Auto-fixable**

### DISABLED (Not Applicable to Omnia)
- **MISSING_FIGURE_CAPTION**: Disabled - Omnia uses inline image descriptions
- **EMPTY_CODE_BLOCK**: Disabled - Empty code blocks valid in Omnia templates
- **NON_SEMANTIC_MARKUP**: Disabled - HTML tags acceptable in Omnia docs
- **BARE_URL**: Disabled - Bare URLs acceptable in Omnia context

## Backup Information

The skill automatically creates backups of your documentation files:

**Location**: `docs/.omnia_backup_TIMESTAMP/`
**Contents**: All Markdown files from your docs directory
**Metadata**: `backup_metadata.json` with timestamp and file count

To disable backups: Use `--no-backup` flag

## Troubleshooting

### "Python not available"
Ensure Python 3.6+ is installed and in your PATH.

### "Report file not found"
Make sure validation completed successfully before running the fixer.

### "Permission denied"
Ensure you have write permissions to the documentation directory.

### "Module not found"
The skill uses only Python standard library - no external dependencies needed.

## Next Steps

1. **Review INDEX.txt** in `reports/baseline_validation/` for overview
2. **Check EXECUTIVE_SUMMARY.txt** for high-level statistics
3. **Follow FIX_RECOMMENDATIONS.txt** for specific guidance
4. **Use WORKFLOW_GUIDE.txt** for systematic fixing approach
5. **Open visual_comparison_with_charts.html** for visual analysis
6. **Review unfixed_issues_report.txt** for manual fixes needed
7. **Import excel_report.csv** into Excel for custom analysis

## Integration with Omnia Workflow

The Markdown accessibility skill is designed for the Omnia documentation workflow:

- **GitHub Integration**: Validate before commits and PRs
- **mkdocs Compatibility**: Ensures proper rendering on mkdocs platform
- **CI/CD Integration**: Can be automated in GitHub Actions
- **Staging Validation**: Check content before staging builds

## Getting Help

For detailed instructions, see:
- `IDE_TERMINAL_GUIDE_MD.txt` - Complete terminal execution guide
- `README.md` - Comprehensive documentation
- `WORKFLOW_GUIDE.txt` (generated in reports) - Step-by-step fixing instructions

## Advanced Usage

### Custom Configuration

Edit `omnia_md_config.json` to customize:
- Include/exclude patterns
- Enable/disable specific checks
- Configure backup behavior
- Adjust fixer settings

### Individual Step Execution

For granular control, execute each step individually as described in `IDE_TERMINAL_GUIDE_MD.txt`.

### Interactive Fixing

```bash
python omnia_md_accessibility_fixer.py reports/baseline_validation/accessibility_report.json --interactive
```

This guides you through fixing issues that require manual intervention.
