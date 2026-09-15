# Omnia Markdown Accessibility Validator & Fixer - Visual Workflow Roadmap

## Overview
This roadmap visualizes the complete workflow of the Accessibility Validator and Fixer skill, showing all checkpoints, decision points, and available paths.

---

## Main Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    START: Documentation Authoring                            │
│                   (Windsurf/Devin IDE or Local Editor)                        │
└──────────────────────────────┬────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKPOINT 1: Initial Setup                                                  │
│  ─────────────────────────                                                      │
│  ✓ Verify Python 3.6+ installed                                               │
│  ✓ Navigate to skill directory                                                 │
│  ✓ Review omnia_config.json (optional customization)                          │
└──────────────────────────────┬────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKPOINT 2: Choose Execution Method                                         │
│  ──────────────────────────────────                                           │
│                                                                              │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌──────────────────┐ │
│  │ Full 10-Step Workflow│   │ Manual Validator    │    │ Checkpoint Mode  │ │
│  │ (Recommended)       │    │ (Advanced Users)    │    │ (Review First)   │ │
│  └──────────┬──────────┘    └──────────┬──────────┘    └────────┬─────────┘ │
│             │                          │                         │           │
│             ▼                          ▼                         ▼           │
│  run_omnia_            omnia_md_               run_omnia_              │
│  accessibility.py      accessibility_           accessibility.py       │
│                       validator.py              --checkpoint-mode       │
│                                                 phase1/phase2          │
└──────────────────────────────┬────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKPOINT 3: Validation Phase                                               │
│  ─────────────────────────────                                               │
│                                                                              │
│  Input: Markdown file or directory path                                     │
│  Options:                                                                    │
│    • Recursive scan (-r)                                                     │
│    • Custom config (-c)                                                      │
│    • Project root (-p)                                                        │
│    • Output format: text/json (-o)                                           │
│    • Output file (-f)                                                         │
└──────────────────────────────┬────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKPOINT 4: Validation Results                                             │
│  ──────────────────────────────                                             │
│                                                                              │
│  Report Generated: accessibility_report.json                                 │
│                                                                              │
│  Summary:                                                                    │
│    • Total Issues Found                                                      │
│    • By Severity: ERROR | WARNING | SUGGESTION                              │
│    • By Issue Type (e.g., MISSING_IMAGE_ALT, BARE_URL)                       │
│    • Files with Issues                                                       │
│                                                                              │
│  Decision Point:                                                             │
│    ┌──────────────────────────────────────────────────────────────────────┐  │
│    │ Issues Found?                                                        │  │
│    └──────────────────────────┬───────────────────────────────────────────┘  │
│                               │                                               │
│              ┌────────────────┴────────────────┐                              │
│              │                                 │                              │
│              ▼ NO                             ▼ YES                           │
│    ┌──────────────────┐              ┌──────────────────┐                    │
│    │ END - No Issues │              │ Proceed to Fixer │                    │
│    │ Documentation   │              │ Phase            │                    │
│    │ is Accessible    │              └────────┬─────────┘                    │
│    └──────────────────┘                       │                               │
└──────────────────────────────────────────────┼───────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKPOINT 5: Choose Fix Mode                                                 │
│  ──────────────────────────────                                             │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                                │
│  │ Full Workflow    │  │ Validate Only    │                                │
│  │ (Default)        │  │ --skip-fixes     │                                │
│  │                  │  │                  │                                │
│  │ All 9 steps      │  │ Steps 1-2 only    │                                │
│  │ Auto fixes       │  │ No fixes applied  │                                │
│  └────────┬─────────┘  └────────┬─────────┘                                │
│           │                      │                                           │
│           ▼                      ▼                                           │
│    ┌──────────────┐      ┌──────────────┐                                  │
│    │ Complete     │      │ Manual Review│                                  │
│    │ Automation   │      │ & Manual Fix │                                  │
│    └──────────────┘      └──────────────┘                                  │
└──────────────────────────────┬────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKPOINT 6: Fixer Execution                                                 │
│  ──────────────────────────                                                   │
│                                                                              │
│  Original Report Preserved:                                                  │
│    accessibility_report_original_YYYYMMDD_HHMMSS.json                        │
│                                                                              │
│  Backup Created (unless --no-backup):                                        │
│    .omnia_backup/ directory with timestamped files                            │
│                                                                              │
│  Fixer Options:                                                              │
│    • --auto-fix: Apply automatic fixes (default)                             │
│    • --no-auto-fix: Disable automatic fixes                                  │
│    • --auto-fix-suggestions: Also fix SUGGESTION level                       │
│    • --interactive: Run interactive session                                  │
│    • --auto-only: Only automatic, skip interactive                           │
│    • --no-backup: Disable backup creation                                    │
└──────────────────────────────┬────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKPOINT 7: Fix Results                                                    │
│  ────────────────────────                                                    │
│                                                                              │
│  Summary Generated:                                                           │
│    • Issues Fixed Automatically                                             │
│    • Issues Fixed Interactively                                              │
│    • Issues Requiring Manual Review                                          │
│    • Files Modified                                                          │
│    • New Issues Created (if any)                                            │
│                                                                              │
│  Comparison Report Generated:                                                 │
│    comparison_report_corrected.txt                                          │
│    - Shows before/after by issue type                                       │
│    - Shows before/after by severity                                         │
│    - Lists fixed issues with line changes                                   │
│    - Groups remaining issues by type                                        │
└──────────────────────────────┬────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKPOINT 8: Comprehensive Reports Generation                              │
│  ────────────────────────────────────────────                                 │
│                                                                              │
│  Reports Directory Structure:                                                │
│    reports/                                                                  │
│    ├── baseline_validation/                                                 │
│    │   ├── accessibility_report.json                                        │
│    │   ├── INDEX.txt                                                         │
│    │   ├── EXECUTIVE_SUMMARY.txt                                             │
│    │   ├── ISSUES_BY_CATEGORY.txt                                           │
│    │   ├── FIX_RECOMMENDATIONS.txt                                           │
│    │   └── WORKFLOW_GUIDE.txt                                               │
│    ├── current_status/                                                       │
│    │   ├── accessibility_report_after.json                                   │
│    │   ├── INDEX.txt                                                         │
│    │   ├── EXECUTIVE_SUMMARY.txt                                             │
│    │   ├── ISSUES_BY_CATEGORY.txt                                           │
│    │   ├── FIX_RECOMMENDATIONS.txt                                           │
│    │   └── WORKFLOW_GUIDE.txt                                               │
│    ├── comparison_report.txt                                                 │
│    ├── visual_comparison_with_charts.html                                   │
│    ├── excel_report.csv                                                      │
│    └── unfixed_issues_report.txt                                             │
│                                                                              │
│  Report Types:                                                               │
│    • baseline_validation/INDEX.txt - Initial assessment overview             │
│    • baseline_validation/EXECUTIVE_SUMMARY.txt - High-level statistics       │
│    • baseline_validation/ISSUES_BY_CATEGORY.txt - Issues by category         │
│    • baseline_validation/FIX_RECOMMENDATIONS.txt - Specific guidance          │
│    • baseline_validation/WORKFLOW_GUIDE.txt - Step-by-step instructions       │
│    • comparison_report.txt - Before/after comparison                          │
│    • visual_comparison_with_charts.html - Interactive CSS charts              │
│    • excel_report.csv - Excel-compatible data                                 │
│    • unfixed_issues_report.txt - Manual fixes needed                         │
└──────────────────────────────┬────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKPOINT 9: Manual Review (if needed)                                     │
│  ────────────────────────────────────                                       │
│                                                                              │
│  For Issues Requiring Manual Intervention:                                   │
│    • Missing Image Alt Text - Add descriptive :alt: directive                │
│    • Empty Section Titles - Add meaningful content                           │
│    • Non-Descriptive Links - Rewrite with descriptive text                  │
│    • Missing Directive Options - Add required options                       │
│                                                                              │
│  Priority Order:                                                             │
│    1. ERROR level issues (Critical)                                         │
│    2. WARNING level issues (Important)                                      │
│    3. SUGGESTION level issues (Optional)                                     │
└──────────────────────────────┬────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKPOINT 10: Re-validation (After Manual Fixes)                            │
│  ──────────────────────────────────────────────                              │
│                                                                              │
│  Run Validator Again:                                                        │
│    python omnia_rst_accessibility_validator.py path/to/docs -r -o json      │
│    -f reports/current_status/accessibility_report_manual_fixes.json         │
│                                                                              │
│  Generate Updated Reports:                                                    │
│    python structured_reporting.py reports/current_status/accessibility_     │
│    report_manual_fixes.json reports/current_status                           │
│                                                                              │
│  Compare with Baseline:                                                      │
│    python generate_excel_report.py reports/baseline_validation/             │
│    accessibility_report.json reports/current_status/                         │
│    accessibility_report_manual_fixes.json reports/                           │
│    accessibility_report.csv                                                  │
└──────────────────────────────┬────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKPOINT 11: Final Review & Commit                                         │
│  ────────────────────────────────────                                       │
│                                                                              │
│  Review Changes in IDE:                                                      │
│    • Check modified files                                                   │
│    • Verify fixes are correct                                               │
│    • Ensure no new issues introduced                                        │
│                                                                              │
│  Commit to Git:                                                              │
│    git add .                                                                 │
│    git commit -m "Fix accessibility issues"                                 │
│    git push                                                                  │
└──────────────────────────────┬────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKPOINT 12: CI/CD Integration (Optional)                                  │
│  ────────────────────────────────────────                                   │
│                                                                              │
│  GitHub Actions:                                                             │
│    • Automatic validation on push/PR                                        │
│    • Upload accessibility report as artifact                                 │
│    • Block merge if critical issues remain                                   │
│                                                                              │
│  ReadTheDocs Build:                                                          │
│    • Validation runs as part of build process                               │
│    • Production docs published only if validation passes                    │
└──────────────────────────────┬────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         END: Complete                                         │
│              Accessible Documentation Ready for Publication                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Checkpoint Descriptions

### CHECKPOINT 1: Initial Setup
**Purpose**: Prepare environment for accessibility validation

**Actions**:
- Verify Python 3.6+ is installed: `python --version`
- Navigate to skill directory: `cd "Accessibility Validator and Fixer_SKILL_MDMKDOCS"`
- Review `omnia_config.json` for customization (optional)
- Ensure RST documentation files are accessible

**Configuration Options**:
- Enable/disable specific checks
- Customize severity levels
- Add internal domains
- Specify supported code languages
- Set exclude/include patterns

---

### CHECKPOINT 2: Choose Execution Method
**Purpose**: Select the appropriate entry point for your workflow

**Option A: Full 10-Step Workflow Script (Recommended)**
```bash
python run_omnia_accessibility.py path/to/docs
```
**Benefits**:
- One-command execution of complete workflow
- Automatic validation and fixing
- Comprehensive report generation
- Visual HTML report with charts
- Excel-compatible CSV export
- HTML report with clickable links (file:// URLs)
- Streamlined for Windsurf/Devin IDE

**Option B: Manual Validator**
```bash
python omnia_md_accessibility_validator.py path/to/docs -r -o json -f report.json
```
**Benefits**:
- Fine-grained control
- Advanced options
- Suitable for scripting

**Option C: Checkpoint Mode (Three-Phase Execution)**
```bash
# Phase 1: Validation + baseline reports
python run_omnia_accessibility.py path/to/docs --checkpoint-mode phase1

# Phase 2: Fixer + all reports (after review)
python run_omnia_accessibility.py path/to/docs --checkpoint-mode phase2

# Phase 3: Render + preview (manual steps)
cd path/to/docs && mkdocs build
# The HTML report uses file:// URLs and works directly from the built site
# When satisfied, publish to ReadTheDocs: https://your-project.readthedocs.io/
```
**Benefits**:
- Review baseline reports before applying fixes
- Review rendered output before publishing
- Pause between validation, fixing, and rendering phases
- Same flow and reports as full workflow
- Automatic state persistence between phases
- Useful for large documentation sets requiring review

**Option D: Windows Batch Scripts**
```bash
run_omnia_accessibility.bat path/to/docs
```
**Benefits**:
- Windows-friendly
- No Python path needed
- Quick execution

---

### CHECKPOINT 3: Validation Phase
**Purpose**: Scan Markdown files for accessibility issues

**Input Parameters**:
- `path`: Markdown file or directory (required)
- `-r, --recursive`: Scan directories recursively
- `-c CONFIG`: Custom configuration file
- `-p PROJECT_ROOT`: Project root for Omnia-specific checks
- `-o {text,json}`: Output format
- `-f OUTPUT_FILE`: Save report to file

**Validation Checks Performed**:
1. **Core Accessibility Checks**:
   - Empty Section Titles
   - Missing Image Alt Text
   - Non-Descriptive Links
   - Empty Table Headers
   - Missing Figure Captions
   - Empty Code Blocks
   - Non-Semantic Markup
   - Insecure External Links

2. **Omnia-Specific Checks**:
   - Document Title Validation
   - Bare URL Detection
   - Code Block Language Support
   - Directive Option Validation
   - Internal Reference Formatting

---

### CHECKPOINT 4: Validation Results
**Purpose**: Review findings and decide next steps

**Report Contents**:
- **Metadata**: Generation time, validator version, project root
- **Summary**: Total issues, by severity, by type, files affected
- **File Details**: Issues per file with line numbers, context, suggestions

**Severity Levels**:
- **ERROR**: Critical issues that must be fixed (e.g., missing alt text)
- **WARNING**: Issues that should be addressed (e.g., insecure links)
- **SUGGESTION**: Optional improvements (e.g., bare URLs)

**Decision Point**:
- **No issues found**: Documentation is accessible - proceed to commit
- **Issues found**: Proceed to fixer phase

---

### CHECKPOINT 5: Choose Fix Mode
**Purpose**: Select how to address identified issues

**Mode A: Full 10-Step Workflow (Default)**
```bash
python run_omnia_accessibility.py path/to/docs
```
- Complete automation of all 10 steps
- Automatic fixes for ERROR and WARNING issues
- Generates all reports including visual HTML
- Creates Excel-compatible CSV
- Provides unfixed issues guidance
- Generates HTML report with clickable links (file:// URLs)

**Mode B: Checkpoint Mode (Review First)**
```bash
# Phase 1: Validation + baseline reports
python run_omnia_accessibility.py path/to/docs --checkpoint-mode phase1

# Phase 2: Fixer + all reports (after reviewing baseline)
python run_omnia_accessibility.py path/to/docs --checkpoint-mode phase2
```
- Review baseline reports before applying fixes
- Pause between validation and fixing phases
- Same flow and reports as full workflow
- Automatic state persistence between phases

**Mode C: Validate Only**
```bash
python run_omnia_accessibility.py path/to/docs --skip-fixes
```
- Skip fixing phase (Steps 1-2 only)
- Review report manually
- Apply fixes manually in IDE

---

### CHECKPOINT 6: Fixer Execution
**Purpose**: Apply fixes to identified issues

**Safety Features**:
- **Original Report Preservation**: Timestamped copy saved before fixes
- **Backup Creation**: `.omnia_backup/` directory with original files
- **Rollback Capability**: Restore from backup if needed

**Fixer Options**:
- `--no-backup`: Disable backup creation (not recommended)
- `--auto-fix`: Apply automatic fixes (default: True)
- `--no-auto-fix`: Disable automatic fixes
- `--auto-fix-suggestions`: Also fix SUGGESTION level
- `--interactive`: Run interactive session
- `--auto-only`: Only automatic, skip interactive
- `--backup-dir`: Custom backup directory for comparison
- `--original-report`: Original report for accurate comparison
- `--comparison-report`: Path for comparison report
- `--diff-only`: Pure file diff comparison

---

### CHECKPOINT 7: Fix Results
**Purpose**: Review what was fixed and what remains

**Summary Information**:
- Issues fixed automatically
- Issues fixed interactively
- Issues requiring manual review
- Files modified
- New issues created (if any)

**Comparison Report Contents**:
- **Summary Tables**: Issues by type and severity before/after
- **Fixed Issues**: Line-by-line before/after comparison
- **Not Fixed Issues**: Grouped by type with examples
- **File Analysis**: Files changed, added, removed

---

### CHECKPOINT 8: Comprehensive Reports Generation
**Purpose**: Generate multiple report formats for different stakeholders

**Report Types**:

1. **COMPREHENSIVE_ACCESSIBILITY_REPORT.txt**
   - Executive summary
   - Fix recommendations with examples
   - Next steps and workflow guidance
   - Commands for execution
   - Estimated time commitment

2. **accessibility_visual_report.html**
   - Interactive CSS-based charts
   - Pie charts for severity distribution
   - Bar charts for issue categories
   - Top files analysis
   - Color-coded priority indicators
   - Responsive design

3. **accessibility_report.csv**
   - Excel-compatible data
   - Structured data for custom charts
   - Severity distribution data
   - Issue type distribution data
   - Top files data

4. **comparison_report_corrected.txt**
   - Before/after comparison
   - Summary by issue type
   - Summary by severity
   - Fixed issues with line changes
   - Remaining issues grouped by type

---

### CHECKPOINT 9: Manual Review (if needed)
**Purpose**: Address issues requiring manual intervention

**Common Manual Fixes**:

1. **Missing Image Alt Text**
   ```text
   # Before:
   .. image:: screenshot.png
   
   # After:
   .. image:: screenshot.png
      :alt: Screenshot showing the configuration panel with highlighted settings
   ```

2. **Empty Section Titles**
   ```text
   # Before:
   ==
   
   # After:
   Configuration
   ==
   ```

3. **Non-Descriptive Links**
   ```text
   # Before:
   `click here <https://example.com>`_
   
   # After:
   `View the configuration guide <https://example.com/config>`_
   ```

4. **Missing Directive Options**
   ```text
   # Before:
   .. code-block:: python
   
   # After:
   .. code-block:: python
      :linenos:
   ```

**Priority Order**:
1. **ERROR level**: Critical for accessibility compliance
2. **WARNING level**: Important for user experience
3. **SUGGESTION level**: Optional improvements

---

### CHECKPOINT 10: Re-validation (After Manual Fixes)
**Purpose**: Measure improvement and ensure no regressions

**Commands**:
```bash
# Re-validate after manual fixes
python omnia_md_accessibility_validator.py path/to/docs -r -o json \
  -f reports/current_status/accessibility_report_after.json

# Generate updated reports
python structured_reporting_md.py reports/current_status/accessibility_report_after.json \
  reports/current_status

# Generate comparison report
python generate_comparison_md.py reports/baseline_validation/accessibility_report.json \
  reports/current_status/accessibility_report_after.json \
  reports/comparison_report.txt

# Generate visual report
python generate_visual_report_md.py reports/baseline_validation/accessibility_report.json \
  reports/current_status/accessibility_report_after.json \
  reports/visual_comparison_with_charts.html
```

**Progress Tracking**:
- Compare total issues before/after
- Track reduction by severity
- Monitor files still with issues
- Identify recurring patterns

---

### CHECKPOINT 11: Final Review & Commit
**Purpose**: Ensure quality before committing changes

**Review Checklist**:
- [ ] All ERROR level issues addressed
- [ ] Most WARNING level issues addressed
- [ ] No new issues introduced
- [ ] Fixes are correct and appropriate
- [ ] Documentation still renders correctly
- [ ] Links are valid and functional

**Git Commands**:
```bash
git add .
git commit -m "Fix accessibility issues in documentation"
git push
```

---

### CHECKPOINT 12: CI/CD Integration (Optional)
**Purpose**: Automate validation in build pipeline

**GitHub Actions Example**:
```yaml
name: Omnia Accessibility Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Run Omnia Accessibility Validator
        run: |
          python Accessibility\ Validator\ and\ Fixer_SKILL/omnia_rst_accessibility_validator.py \
            docs/source -r -o json -f accessibility_report.json
      - name: Upload Report
        uses: actions/upload-artifact@v2
        with:
          name: accessibility-report
          path: accessibility_report.json
```

**ReadTheDocs Integration**:
- Add validation to Sphinx build process
- Block builds if critical issues remain
- Publish reports as build artifacts

---

## Quick Reference Command Summary

### Recommended Workflow (IDE Integration)
```bash
# Validate and fix in one command
python run_omnia_accessibility.py path/to/docs --fix-mode auto

# Validate only
python run_omnia_accessibility.py path/to/docs --validate-only

# Interactive fixing
python run_omnia_accessibility.py path/to/docs --fix-mode interactive

# Both automatic and interactive
python run_omnia_accessibility.py path/to/docs --fix-mode both
```

### Manual Workflow
```bash
# Step 1: Validate
python omnia_rst_accessibility_validator.py path/to/docs -r -o json -f report.json

# Step 2: Auto fix
python omnia_rst_accessibility_fixer.py report.json --auto-fix --auto-only

# Step 3: Interactive fix
python omnia_rst_accessibility_fixer.py report.json --interactive

# Step 4: Generate comparison
python omnia_rst_accessibility_fixer.py report.json \
  --original-report report_original.json \
  --comparison-report comparison.txt
```

### Report Generation
```bash
# Generate comprehensive reports
python run_omnia_accessibility.py path/to/docs --validate-only

# Generate Excel report
python generate_excel_report.py baseline.json current.json report.csv

# Generate visual HTML report
python generate_visual_report.py baseline.json current.json report.html
```

---

## Troubleshooting Flow

```
Issue: Python not found
  │
  ├─ Check: python --version
  ├─ Fix: Install Python 3.6+ from python.org
  └─ Verify: Add to PATH

Issue: Permission denied
  │
  ├─ Check: File permissions
  ├─ Fix: chmod +x script.py (Linux/Mac)
  └─ Fix: Run as administrator (Windows)

Issue: File not found
  │
  ├─ Check: Path is correct
  ├─ Fix: Use absolute path
  └─ Fix: Check working directory

Issue: No issues found but expected
  │
  ├─ Check: Configuration enabled
  ├─ Check: File patterns (*.rst)
  ├─ Check: Exclude patterns
  └─ Fix: Update omnia_config.json

Issue: Fixer not working
  │
  ├─ Check: Report file exists
  ├─ Check: Report is valid JSON
  ├─ Check: Backup directory permissions
  └─ Fix: Use --no-backup if permissions issue
```

---

## Best Practices

1. **Always use backup**: Don't use `--no-backup` unless necessary
2. **Start with auto mode**: Let automatic fixes run first
3. **Review changes**: Always review fixes in IDE before committing
4. **Iterative approach**: Fix in phases, re-validate after each phase
5. **Track progress**: Use comparison reports to measure improvement
6. **Integrate early**: Add to CI/CD pipeline to catch issues early
7. **Document exceptions**: Keep track of issues that can't be auto-fixed
8. **Regular validation**: Run validation periodically, not just before commits

---

## File Structure Reference

```
Accessibility Validator and Fixer_SKILL/
├── README.md                          # Main documentation
├── omnia_config.json                  # Configuration file
├── omnia_rst_accessibility_validator.py  # Core validator
├── omnia_rst_accessibility_fixer.py      # Core fixer
├── run_omnia_accessibility.py         # IDE integration script
├── run_omnia_accessibility.bat        # Windows batch script
├── run_omnia_fixer.bat                # Fixer batch script
├── run_omnia_validator.bat            # Validator batch script
├── generate_comparison.py             # Comparison report generator
├── generate_excel_report.py           # Excel/CSV report generator
├── generate_unfixed_report.py         # Unfixed issues report
├── generate_visual_report.py          # HTML visual report generator
├── quick_fix_auto.py                  # Quick auto-fix script
├── quick_fix_interactive.py           # Quick interactive fix
├── run_full_workflow.py               # Full workflow runner
├── structured_reporting.py            # Structured report generator
├── IDE_TERMINAL_GUIDE.txt             # Terminal execution guide
└── reports/                           # Generated reports (auto-created)
    ├── COMPREHENSIVE_ACCESSIBILITY_REPORT.txt
    ├── README.txt
    ├── accessibility_visual_report.html
    ├── accessibility_report.csv
    ├── baseline_validation/
    │   ├── accessibility_report.json
    │   ├── accessibility_report_original_*.json
    │   └── comparison_report.txt
    └── current_status/
        └── (for future reports)
```

---

## Severity Level Reference

| Severity | Description | Examples | Action Required |
|----------|-------------|----------|-----------------|
| **ERROR** | Critical accessibility issues | Missing alt text, empty sections, non-descriptive links | Must fix before publication |
| **WARNING** | Important issues affecting UX | Insecure links, invalid code languages, missing directive options | Should fix for best practices |
| **SUGGESTION** | Optional improvements | Bare URLs, bare references | Fix if time permits |

---

## Issue Type Reference

| Issue Type | Severity | Description | Auto-Fixable |
|------------|----------|-------------|--------------|
| EMPTY_SECTION_TITLE | ERROR | Section header with no content | No |
| MISSING_IMAGE_ALT | ERROR | Image without :alt: directive | No |
| EMPTY_IMAGE_ALT | ERROR | Image with empty :alt: | No |
| NON_DESCRIPTIVE_LINK | ERROR | Link text like "click here" | No |
| EMPTY_TABLE_HEADER | ERROR | Empty table header cell | No |
| MISSING_FIGURE_CAPTION | ERROR | Figure without caption | No |
| EMPTY_CODE_BLOCK | WARNING | Code block with no content | No |
| NON_SEMANTIC_MARKUP | WARNING | Non-semantic HTML tags | No |
| INSECURE_EXTERNAL_LINK | WARNING | http:// instead of https:// | Yes |
| INVALID_CODE_LANGUAGE | WARNING | Unsupported code language | No |
| BROKEN_INTERNAL_LINK | ERROR | Invalid :ref: target | No |
| MISSING_DIRECTIVE_OPTION | WARNING | Missing required directive option | No |
| MISSING_DOCUMENT_TITLE | WARNING | Document lacks title | No |
| BARE_URL | SUGGESTION | URL not formatted as RST link | Yes |
| BARE_REF | SUGGESTION :ref: not formatted as link | Yes |

---

## End of Roadmap

For questions or issues, refer to:
- README.md for detailed documentation
- IDE_TERMINAL_GUIDE.txt for terminal execution
- omnia_config.json for configuration options
