# Omnia Markdown Accessibility Validator & Fixer

**Enhanced for Omnia Documentation Process (GitHub, mkdocs, Windsurf/Devin)**

This tool validates and fixes Markdown documentation for accessibility compliance, specifically tailored for the Omnia documentation workflow involving GitHub, mkdocs, and Windsurf/Devin IDE.

## Overview

The Omnia Markdown Accessibility Validator checks Markdown files for common accessibility issues that can prevent users with disabilities from accessing content effectively. It implements checks based on the Validator methodology from CET Knowledge Base, adapted for Markdown/mkdocs documentation with Omnia-specific enhancements.

**Companion Tool**: See `omnia_md_accessibility_fixer.py` for the automated fixing tool.

## Omnia-Specific Features

### Enhanced Workflow Integration
- **GitHub Integration**: Validates files before commits and PRs
- **mkdocs Compatibility**: Ensures proper rendering on mkdocs platform
- **Windsurf/Devin IDE Support**: Optimized for doc-as-code workflow
- **Staging Area Validation**: Validates content before staging builds

### Additional Checks Beyond Standard Validator
- **Omnia Structure Validation**: Checks for proper document structure
- **Documentation Link Formatting**: Ensures proper Markdown link syntax
- **Code Block Language Validation**: Verifies supported languages for syntax highlighting
- **Markdown Element Validation**: Checks for proper Markdown usage and required attributes
- **Internal Reference Formatting**: Validates proper reference syntax for cross-linking

## Features

### Core Accessibility Checks (Based on Validator Methodology)

- **Empty Section Titles**: Detects section headers with no content
- **Missing Image Alt Text**: Ensures all images have descriptive alt text
- **Non-Descriptive Links**: Identifies links with unclear text (e.g., "click here") - **Auto-fixable via config**
- **Empty Table Headers**: Checks for empty table header cells
- **Missing Figure Captions**: Enhanced detection for non-descriptive alt text - **Auto-fixable via config** (93+ mappings)
- **Insecure External Links**: Warns about http:// links (should use https://) - **Auto-fixable**
- **Invalid Code Language**: Validates code block languages against supported list - **Auto-fixable**

### Enhanced MISSING_FIGURE_CAPTION Detection
The validator now detects non-descriptive alt text more comprehensively:
- **Empty alt text**: `![]()` 
- **Generic words**: "image", "img", "picture", "screenshot", "diagram", "chart", "figure"
- **Filename matching**: Alt text that is just the image filename (case-insensitive)
- **Too short**: Alt text less than 10 characters
- **Technical terms**: Alt text with only underscores and technical terms without context

### Disabled Checks (Not Applicable to Omnia)

The following checks are disabled as they are not applicable to Omnia documentation standards:
- **Empty Code Blocks**: Disabled - Empty code blocks are valid in Omnia templates
- **Non-Semantic Markup**: Disabled - HTML tags are acceptable in Omnia docs
- **Bare URL Detection**: Disabled - Bare URLs are acceptable in Omnia context

### Omnia-Specific Checks

- **Document Title Validation**: Ensures documents have proper titles for mkdocs navigation
- **Bare URL Detection**: Identifies URLs that should be formatted as Markdown links
- **Code Block Language Support**: Validates code block languages against Pygments support
- **Markdown Element Validation**: Checks for proper Markdown element usage and required attributes
- **Internal Reference Formatting**: Validates Markdown internal reference usage

### Error Severity Levels

- **ERROR**: Critical accessibility issues that must be fixed
- **WARNING**: Issues that should be addressed for best practices
- **SUGGESTION**: Optional improvements for better accessibility

## Installation

### Prerequisites

- Python 3.6 or higher
- No external dependencies required (uses Python standard library)

### Setup

1. Clone or download this tool to your local system
2. No installation required - it's a standalone Python script

### Folder Structure

```
Accessibility Validator and Fixer_SKILL_MDMKDOCS/
├── README.md                           # This file
├── omnia_config.json                   # Configuration file
├── omnia_md_accessibility_validator.py # Core validation tool
├── omnia_md_accessibility_fixer.py     # Core fixing tool
├── run_omnia_accessibility.py          # IDE integration script
├── run_omnia_accessibility.bat         # Windows batch script
├── run_omnia_fixer.bat                 # Windows batch script for fixer
├── run_omnia_validator.bat             # Windows batch script for validator
└── reports/                            # Generated reports (auto-created)
    ├── baseline_validation/              # Initial validation report
    │   └── accessibility_report.json
    ├── current_status/                    # Post-fix validation reports (timestamped)
    │   └── accessibility_report_TIMESTAMP.json
    ├── COMPREHENSIVE_ACCESSIBILITY_REPORT.txt  # Simplified summary
    ├── category_report.txt               # Issues grouped by category
    ├── comparison_report.csv           # Before/after comparison data
    ├── comparison_visual_report.html   # HTML comparison with summary statistics
    └── accessibility_visual_report.html  # Interactive visual report
```

**Note:** All generated reports are automatically saved to the `reports/` folder to keep the skill folder clean and portable.

## Usage

### Option 1: Full 10-Step Workflow Script (Recommended)

The easiest way to use the accessibility validator and fixer is through the `run_omnia_accessibility.py` script, which implements the complete 10-step workflow:

```bash
# Run complete 10-step workflow with automatic fixes (recommended)
python run_omnia_accessibility.py path/to/docs

# Validate only (skip automatic fixes)
python run_omnia_accessibility.py path/to/docs --skip-fixes

# Run without backup (useful for testing)
python run_omnia_accessibility.py path/to/docs --no-backup
```

**The 10-step workflow includes:**
1. Initial validation with backup
2. Generate structured baseline reports
3. Run automatic fixer
4. Post-fix validation
5. Generate current status reports
6. Generate comparison report
7. Generate HTML visual report with charts
8. Generate Excel/CSV report
9. Generate unfixed issues report
10. **Automatic local site rebuild + Generate HTML report with clickable links (file:// URLs)**

**Benefits of using the full workflow script:**
- One-command execution of complete validation and fixing process
- Automatically generates all reports including visual_comparison_with_charts.html
- Structured reports in baseline_validation/ and current_status/ directories
- Comparison reports showing before/after analysis
- Excel-compatible CSV for custom analysis
- Unfixed issues report for manual intervention guidance
- **Automatic local site rebuild** - Ensures HTML report hyperlinks point to current fixed content
- HTML report with clickable links to view fixed issues in rendered documentation (file:// URLs)
- **Ready-to-review workflow** - Local site is automatically built for immediate review before GitHub commit

### Option 2: Validate Only (Skip Fixes)

For users who want to validate without applying automatic fixes:

```bash
python run_omnia_accessibility.py path/to/docs --skip-fixes
```

This runs the validation and generates baseline reports only, without modifying any files.

### Option 3: Checkpoint Mode (Three-Phase Execution)

For users who want to review the initial validation report before proceeding with fixes, and then review rendered output before publishing, use the checkpoint mode to split the workflow into three separate commands:

```bash
# PHASE 1: Validation + Baseline Reports (Steps 1-2)
python run_omnia_accessibility.py path/to/docs --checkpoint-mode phase1

# PHASE 2: Fixer + Post-fix Validation + All Reports (Steps 3-10)
python run_omnia_accessibility.py path/to/docs --checkpoint-mode phase2

# PHASE 3: Review + Commit to GitHub (Manual Steps)
# The HTML report uses file:// URLs and works directly from the automatically built site
# When satisfied, commit to GitHub:
#   git add docs/
#   git commit -m 'Apply accessibility fixes'
#   git push
```

**Phase 1 (Steps 1-2):**
- Initial validation with backup
- Generate structured baseline reports
- Saves checkpoint state to `reports/checkpoint_state.json`
- Exits after generating baseline reports for review

**Phase 2 (Steps 3-10):**
- Loads checkpoint state from Phase 1
- Runs automatic fixer
- Post-fix validation
- Generate current status reports
- Generate comparison report
- Generate HTML visual report with charts
- Generate Excel/CSV report
- Generate unfixed issues report
- **Automatic local site rebuild + Generate HTML report with clickable links (file:// URLs)**
- Cleans up checkpoint file after completion

**Benefits of checkpoint mode:**
- Review baseline validation report before applying fixes
- Pause between validation and fixing phases
- Same flow and reports as the full 10-step workflow
- **Automatic local site rebuild** in Phase 2 for immediate review
- Automatic state persistence between phases
- Useful for large documentation sets requiring review

**When to use checkpoint mode:**
- When you need to review the initial accessibility assessment before fixing
- For large documentation sets where you want to verify the scope of issues
- When working in teams where validation and fixing are done by different people
- For debugging or testing the validation process before committing to fixes

### Basic Usage (Manual)

```bash
# Validate a single Markdown file
python omnia_md_accessibility_validator.py path/to/file.md

# Validate all Markdown files in a directory (non-recursive)
python omnia_md_accessibility_validator.py path/to/directory

# Validate all Markdown files recursively
python omnia_md_accessibility_validator.py path/to/directory -r
```

### Advanced Usage

```bash
# Use custom configuration
python omnia_md_accessibility_validator.py path/to/directory -r -c omnia_config.json

# Specify project root for Omnia-specific checks
python omnia_md_accessibility_validator.py path/to/directory -r -p "C:/path/to/omnia-project"

# Generate JSON output (new structured format)
python omnia_md_accessibility_validator.py path/to/directory -r -o json

# Save report to file
python omnia_md_accessibility_validator.py path/to/directory -r -f omnia_accessibility_report.txt

# Combine options
python omnia_md_accessibility_validator.py path/to/directory -r -c omnia_config.json -o json -f accessibility_report.json
```

### Command Line Options

```
positional arguments:
  path                  Path to Markdown file or directory to validate

optional arguments:
  -h, --help            show this help message and exit
  -r, --recursive       Recursively validate all Markdown files in directory
  -c CONFIG, --config CONFIG
                        Path to configuration JSON file
  -p PROJECT_ROOT, --project-root PROJECT_ROOT
                        Project root directory for Omnia-specific checks
  -o {text,json}, --output {text,json}
                        Output format (default: text)
  -f OUTPUT_FILE, --output-file OUTPUT_FILE
                        Write report to file instead of stdout
```

## Configuration

The tool uses a JSON configuration file to customize validation rules. The current configuration is optimized for Omnia documentation with disabled checks that are not applicable:

```json
{
  "check_empty_section_titles": true,
  "check_missing_image_alt": true,
  "check_non_descriptive_links": true,
  "check_empty_table_headers": true,
  "check_missing_figure_captions": true,
  "check_empty_code_blocks": false,
  "check_semantic_markup": false,
  "check_empty_paragraphs": false,
  "check_external_links": true,
  "check_omnia_structure": true,
  "check_documentation_links": false,
  "check_code_block_languages": true,
  "check_rst_directives": true,
  "check_internal_references": true,
  "valid_code_block_patterns": [
    "^```bash title=\"[^\"]+\"$",
    "^```bash title='[^']+'$",
    "^```bash title=[^\\s]+$"
  ],
  "auto_fix_descriptive_links": {
    "https://github.com/dell/omnia": "Omnia GitHub Repository",
    "https://github.com/dell/omnia/tree/pub/build_stream/examples/catalog": "BuildStreaM catalog examples"
  },
  "auto_fix_image_captions": {
    "omnia-branch-structure.png": "Diagram showing Omnia Git branch structure with main branch and feature branches for contribution workflow",
    "Architecture.png": "High-level architecture diagram showing Omnia components including OIM, cluster nodes, and external services",
    "omnia_telemetry_architecture.png": "Telemetry architecture diagram showing data flow from cluster nodes through telemetry stack to monitoring systems"
  },
  "supported_code_languages": [
    "python", "bash", "shell", "json", "yaml", "xml",
    "javascript", "java", "c", "cpp", "go", "rust",
    "powershell", "sql", "html", "css", "typescript",
    "ruby", "php", "text", "csv", "ini", "toml", "ldif"
  ]
}
```

### Configuration Options

**Disabled Checks (Omnia-specific):**
- `check_empty_code_blocks: false` - Empty code blocks valid in Omnia templates
- `check_semantic_markup: false` - HTML tags acceptable in Omnia docs
- `check_documentation_links: false` - Bare URLs acceptable in Omnia context

**New Features:**
- `valid_code_block_patterns` - Supports Omnia's `bash title="Run on"` template
- `auto_fix_descriptive_links` - Automatic fix mappings for common URLs
- `auto_fix_image_captions` - Automatic caption mappings for key images
- Extended `supported_code_languages` - Includes csv, ini, toml, ldif for Omnia configs
- `check_missing_figure_captions: true` - Now enabled with auto-fix capability

## Using with Omnia Documentation

### Validate Omnia Documentation

```bash
# Navigate to the accessibility_validator directory
cd "C:/Users/Joned_David/OneDrive - Dell Technologies/Documents/OMNIA_Workfiles/Test/CreatedModified Skill for Accessibility Validation"

# Validate Omnia documentation
python omnia_md_accessibility_validator.py "../../../2.2.0.0-rc1/omnia-artifactory/docs" -r -f omnia_accessibility_report.txt
```

### Integrate with Build Process

Add to your mkdocs build process by modifying your build script:

```text
validate:
	python ../CreatedModified\ Skill\ for\ Accessibility\ Validation/omnia_md_accessibility_validator.py . -r -f validation_report.txt

build: validate
	mkdocs build
```

### Integration with GitHub Actions

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
          python CreatedModified\ Skill\ for\ Accessibility\ Validation/omnia_md_accessibility_validator.py docs -r -o json -f accessibility_report.json
      - name: Upload Report
        uses: actions/upload-artifact@v2
        with:
          name: accessibility-report
          path: accessibility_report.json
```

## Fixing Issues

### Using the Full Workflow Script

The recommended way to use the accessibility validator and fixer is through the `run_omnia_accessibility.py` script, which implements the complete 10-step workflow:

```bash
# Run complete 10-step workflow (recommended)
python run_omnia_accessibility.py path/to/docs

# Validate only (skip fixes)
python run_omnia_accessibility.py path/to/docs --skip-fixes

# Run without backup
python run_omnia_accessibility.py path/to/docs --no-backup
```

### Automatic Fixes

The fixer now includes enhanced automatic fix capabilities for Omnia:

```bash
# Apply automatic fixes only
python omnia_md_accessibility_fixer.py accessibility_report.json --auto-only

# Apply automatic fixes including suggestions
python omnia_md_accessibility_fixer.py accessibility_report.json --auto-fix-suggestions
```

**Auto-fixable Issues:**
- **Non-Descriptive Links**: Automatically fixes using `auto_fix_descriptive_links` config mappings
- **Missing Figure Captions**: Automatically adds captions using `auto_fix_image_captions` config mappings  
- **Insecure External Links**: Changes http:// to https:// (excluding localhost)
- **Invalid Code Languages**: Maps unsupported languages to supported alternatives
- **Bare URLs**: Formats as Markdown links

**Configuration-Based Auto-Fixing:**
Add URL-to-text mappings in `omnia_config.json`:
```json
"auto_fix_descriptive_links": {
  "https://github.com/dell/omnia": "Omnia GitHub Repository",
  "https://github.com/dell/omnia/tree/pub/build_stream/examples/catalog": "BuildStreaM catalog examples"
}
```

Add image caption mappings in `omnia_config.json`:
```json
"auto_fix_image_captions": {
  "omnia-branch-structure.png": "Diagram showing Omnia Git branch structure with main branch and feature branches for contribution workflow"
}
```

### Interactive Fixes

```bash
# Run interactive fixing session
python omnia_md_accessibility_fixer.py accessibility_report.json --interactive

# Apply both automatic and interactive fixes
python omnia_md_accessibility_fixer.py accessibility_report.json --interactive
```

### Comparison Report with Original Report

For accurate before/after comparison, use the original report that was automatically preserved:

```bash
# Generate comparison report using original report
python omnia_md_accessibility_fixer.py accessibility_report.json --original-report accessibility_report_original_20260703_120000.json --comparison-report comparison_report.txt
```

### Pure File Diff Comparison

Generate a file diff comparison without needing an accessibility report:

```bash
# Generate pure file diff between backup and current files
python omnia_md_accessibility_fixer.py dummy.json --diff-only --backup-dir path/to/backup --comparison-report file_diff_report.txt
```

### Fixer Options

```
positional arguments:
  report                Path to accessibility report JSON file

optional arguments:
  -h, --help            show this help message and exit
  --no-backup           Don't create backup files
  --auto-fix            Apply automatic fixes (default: True)
  --no-auto-fix         Disable automatic fixes
  --auto-fix-suggestions
                        Also auto-fix SUGGESTION level issues
  --interactive         Run interactive fixing session
  --auto-only           Only apply automatic fixes, skip interactive
  -p PROJECT_ROOT, --project-root PROJECT_ROOT
                        Project root directory for Omnia-specific context
  --backup-dir BACKUP_DIR
                        Backup directory to compare against (for before/after comparison)
  --original-report ORIGINAL_REPORT
                        Original accessibility report from before fixes (for accurate comparison)
  --comparison-report COMPARISON_REPORT
                        Path to write comparison report (before/after fixes)
  --diff-only           Generate pure file diff comparison (doesn't require accessibility report)
```

## Output Formats

### Text Format (Default)

```
================================================================================
OMNIA MARKDOWN ACCESSIBILITY VALIDATION REPORT
================================================================================
Generated: 2026-07-03 10:41:00
Total Issues Found: 15

Errors: 8
Warnings: 5
Suggestions: 2

--------------------------------------------------------------------------------
File: path/to/file.md
--------------------------------------------------------------------------------
[ERROR] Line 45: Image is missing alt text
  Suggestion: Add :alt: directive with descriptive text
  Context: Omnia: Required for screen reader compatibility

[ERROR] Line 67: Link text is not descriptive: 'click here'
  Suggestion: Use descriptive link text that describes the destination
  Context: Omnia: Non-descriptive links fail WCAG 2.4.4

[WARN] Line 23: External link uses http instead of https: https://example.com
  Suggestion: Use https:// for external links (unless linking to mailto or ftp)
  Context: Omnia: HTTPS required for security compliance
```

### JSON Format (New Structured Format)

The JSON output now uses a structured format that's more readable for large datasets:

```json
{
  "metadata": {
    "generated": "2026-07-03 14:00:01",
    "validator_version": "1.1",
    "project_root": "/path/to/project"
  },
  "summary": {
    "total_issues": 54091,
    "by_severity": {
      "ERROR": 1472,
      "WARNING": 957,
      "SUGGESTION": 51662
    },
    "by_issue_type": {
      "BARE_REF": 182,
      "BARE_URL": 1896
    },
    "files_with_issues": 1331
  },
  "files": {
    "path/to/file.md": {
      "relative_path": "docs/file.md",
      "total_issues": 8,
      "summary": {
        "ERROR": 0,
        "WARNING": 0,
        "SUGGESTION": 8
      },
      "issues": [
        {
          "line": 45,
          "type": "MISSING_IMAGE_ALT",
          "severity": "ERROR",
          "message": "Image is missing alt text",
          "suggestion": "Add :alt: directive with descriptive text",
          "context": "Omnia: Required for screen reader compatibility"
        }
      ],
      "suggestion_summary": {
        "count": 8,
        "example_types": ["BARE_URL"]
      }
    }
  }
}
```

**Benefits of the new format:**
- **Summary section**: Quick overview of total issues by severity and type
- **Grouped by file**: Easier to navigate when dealing with thousands of issues
- **Suggestion summaries**: Suggestions are summarized to reduce file size
- **Metadata**: Includes generation time and version information

## Comparison Report Format (New Table Format)

The comparison report now uses a table format for better readability:

```
================================================================================
OMNIA ACCESSIBILITY FIXER COMPARISON REPORT
================================================================================
Generated: 2026-07-03 14:00:02
Original issues (before fixes): 4356
Current issues (after fixes): 4356
Issues fixed: 0

SUMMARY BY ISSUE TYPE:
--------------------------------------------------------------------------------
Issue Type                          Total      Fixed  Not Fixed
--------------------------------------------------------------
EMPTY_SECTION_TITLE                   502          0        502
INVALID_CODE_LANGUAGE                 332          0        332
MISSING_DIRECTIVE_OPTION             1382          0       1382

SUMMARY BY SEVERITY:
--------------------------------------------------------------------------------
Severity             Total      Fixed  Remaining
-----------------------------------------------
ERROR                 2642          0       2642
WARNING               1714          0       1714

FIXED ISSUES (Before -> After):
--------------------------------------------------------------------------------
File: docs/file.md
--------------------------------------------------------------------------------
Line   Type                 Before                                After
----------------------------------------------------------------------------------------------
45     MISSING_IMAGE_ALT     .. image:: img.png                   .. image:: img.png
                                                                  :alt: Descriptive text

NOT FIXED ISSUES (Requires Manual Review):
--------------------------------------------------------------------------------

EMPTY_SECTION_TITLE (502 issues):
  Example: Section title is empty
  Suggestion: Add a descriptive title for this section
  Files affected: 366
```

**Benefits of the new format:**
- **Summary tables**: Quick overview of issues by type and severity
- **Before/after comparison**: Shows exact changes made to fixed lines
- **Grouped by file**: Easier to navigate through fixes
- **Not fixed summary**: Groups remaining issues by type with examples

## Windows Batch Scripts

For Windows users, the IDE integration script is recommended:

```text
# Run validate and fix (recommended)
python run_omnia_accessibility.py path/to/docs --fix-mode auto

# Run validation only
python run_omnia_accessibility.py path/to/docs --validate-only
```

## Omnia Workflow Integration

### Local Authoring (Windsurf/Devin IDE)

The recommended workflow using the full workflow script:

1. **Author Markdown content** in Windsurf/Devin IDE
2. **Run complete 10-step workflow**: `python run_omnia_accessibility.py path/to/docs`
3. **Review reports** in `reports/` directory:
   - `baseline_validation/INDEX.txt` for initial assessment
   - `comparison_report.txt` to see what was fixed
   - `visual_comparison_with_charts.html` for visual analysis
   - `unfixed_issues_report.txt` for manual fixes needed
   - `fixed_issues_with_links.html` for clickable links to view fixed issues with before/after comparison
4. **Review changes** in IDE
5. **Commit and push** to GitHub fork

**Note**: The full workflow script automatically:
- Creates backups of original files
- Generates all structured reports
- Creates visual HTML report with charts
- Generates Excel-compatible CSV
- Provides unfixed issues guidance
- Generates HTML report with clickable links (file:// URLs) for viewing fixed issues

### Alternative Manual Workflow

1. **Author Markdown content** in Windsurf/Devin IDE
2. **Run validator** before committing: `python omnia_md_accessibility_validator.py . -r`
3. **Fix issues** using fixer: `python omnia_md_accessibility_fixer.py report.json --auto-fix --auto-only`
4. **Re-validate** after fixes: `python omnia_md_accessibility_validator.py . -r -o json -f reports/current_status/accessibility_report_after.json`
5. **Generate reports**: `python structured_reporting_md.py reports/current_status/accessibility_report_after.json reports/current_status`
6. **Review changes** in IDE
7. **Commit and push** to GitHub fork

### Staging & Review (GitHub PR)

1. **Create PR** from fork to upstream
2. **GitHub Actions** automatically runs accessibility validation
3. **Review report** in PR artifacts
4. **Fix issues** and push updates
5. **ReadTheDocs** builds staging preview

### Production (ReadTheDocs)

1. **Merge PR** to main branch
2. **Webhook triggers** ReadTheDocs build
3. **Accessibility validation** runs as part of build
4. **Production docs** published if validation passes

## Mapping to Validator Checks

| Validator (DITA) | Omnia Markdown Validator | Description |
|------------------|---------------------|-------------|
| Section Title element is empty | Empty Section Titles | Checks for empty section headers |
| Image is missing alt element | Missing Image Alt Text | Ensures images have alt text |
| Link text is not descriptive | Non-Descriptive Links | Identifies unclear link text |
| Table is missing thead element | Empty Table Headers | Checks for empty table headers |
| Figure is missing title element | Missing Figure Captions | Ensures figures have captions |
| Steps element is empty | Empty Code Blocks | Detects empty code blocks |
| Do not use typographic markup <b> | Non-Semantic Markup | Identifies non-semantic HTML |
| Ensure URL begins with https | Insecure External Links | Warns about http links |
| N/A | Document Title Validation | Ensures proper document titles |
| N/A | Bare URL Detection | Formats URLs as Markdown links |
| N/A | Code Block Language Validation | Validates syntax highlighting |
| N/A | Directive Option Validation | Checks required options |

## Troubleshooting

### Python Not Found

Ensure Python 3.6+ is installed and in your PATH:
```bash
python --version
```

### Permission Denied

On Linux/Mac, make the script executable:
```bash
chmod +x omnia_md_accessibility_validator.py
```

### File Not Found

Ensure the path to Markdown files is correct. Use absolute paths if relative paths don't work.

## Extensibility for Other Dell Projects

This Omnia-specific skill can be adapted for other Dell documentation projects:

### OME (OpenManage Enterprise)
- Update `omnia_internal_domains` in config
- Adjust project-specific patterns
- Customize exclusion patterns

### Other Dell Documentation Projects
- Copy the skill to project directory
- Update configuration for project-specific requirements
- Integrate with project's CI/CD pipeline
- Customize validation rules as needed

## Contributing

To add new validation rules:

1. Add a new check method to the `OmniaMDAccessibilityValidator` class
2. Enable the check in the configuration
3. Update the documentation
4. Add corresponding fix method to fixer if applicable

## License

This tool is based on Validator methodology from Dell's CET Knowledge Base and is adapted for Markdown/mkdocs documentation validation with Omnia-specific enhancements.

## Support

For issues or questions related to Omnia Documentation, contact: omnia.readme@dell.com

## Version History

- **v1.5** (2026-07-29): HTML report with clickable links (file:// URLs)
  - Added Step 10: Generate HTML report with clickable links (file:// URLs)
  - New script: generate_fixed_issues_html_report.py
  - Creates interactive HTML report with direct links to view each fixed issue in rendered documentation
  - Links use file:// URLs to work directly from built site directory (no server required)
  - Updated workflow from 9-step to 10-step process
  - Integrated into run_omnia_accessibility.py as mandatory step
  - Updated all documentation to reflect new 10-step workflow
  - Enhanced report organization in reports/ directory

- **v1.4** (2026-07-27): Checkpoint mode implementation
  - Added --checkpoint-mode argument for three-phase execution
  - Phase 1: Validation + baseline reports (Steps 1-2)
  - Phase 2: Fixer + post-fix validation + all reports (Steps 3-9)
  - Phase 3: Render + preview instructions (manual mkdocs build/serve)
  - Automatic state persistence via checkpoint_state.json
  - Enables review of baseline reports before applying fixes
  - Enables review of rendered output before publishing
  - Same flow and reports as full 9-step workflow
  - Documentation updated with Option 3 usage instructions

- **v1.3** (2026-07-27): False positive fixes and validation improvements
  - Disabled empty paragraph check due to false positives (blank lines required in Markdown)
  - Updated fixer to skip empty paragraph issues
  - Configuration already reflected disabled state
  - Documentation accuracy improved

- **v1.2** (2026-07-21): Full 9-step workflow implementation
  - Implemented complete 9-step automated workflow in run_omnia_accessibility.py
  - Added visual_comparison_with_charts.html generation (Step 7)
  - Added structured reports in baseline_validation/ and current_status/ directories
  - Added Excel/CSV report generation (Step 8)
  - Added unfixed issues report generation (Step 9)
  - Simplified command-line arguments (--skip-fixes, --no-backup)
  - Updated all documentation guides to reflect new workflow

- **v1.1** (2026-07-03): Enhanced reporting and workflow improvements
  - Added structured JSON format for better readability with large datasets
  - Implemented table-format comparison report with before/after comparison
  - Added automatic original report preservation for accurate comparison
  - Added IDE integration script (run_omnia_accessibility.py) for streamlined workflow
  - Added pure file diff comparison feature (--diff-only)
  - Enhanced comparison report to show fixed vs remaining issues by type and severity
  - Updated load methods to handle both old and new JSON formats

- **v1.0** (2026-07-03): Initial Omnia-specific release
  - Enhanced with Omnia workflow integration
  - Added Omnia-specific validation checks
  - Improved GitHub Actions integration
  - Added ReadTheDocs compatibility checks
