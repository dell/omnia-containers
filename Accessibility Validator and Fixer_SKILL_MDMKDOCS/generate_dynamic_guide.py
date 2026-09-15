#!/usr/bin/env python3
"""
Dynamic IDE Guide Generator
Generates IDE_TERMINAL_GUIDE_MD.txt with paths adapted to current skill location
"""

import os
import sys
from pathlib import Path
from datetime import datetime


def get_relative_path(from_path, to_path):
    """Get relative path from from_path to to_path"""
    try:
        return os.path.relpath(to_path, from_path)
    except ValueError:
        # On Windows, can't get relative path between different drives
        return str(to_path)


def update_file_with_dynamic_path(file_path, old_pattern, new_path):
    """Update a file by replacing path patterns with dynamic paths"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the old pattern with the new path
        updated_content = content.replace(old_pattern, new_path)
        
        if updated_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"  Updated: {file_path.name}")
            return True
        return False
    except Exception as e:
        print(f"  Error updating {file_path.name}: {e}")
        return False


def generate_dynamic_guide(skill_dir, port):
    """Generate dynamic IDE guide based on current skill location"""
    skill_path = Path(skill_dir).resolve()
    
    # Try to find common documentation directories
    possible_docs_locations = [
        skill_path.parent / "docs",
        skill_path / "docs",
        skill_path.parent.parent / "docs",
        Path("../docs"),
        Path("../../docs"),
    ]
    
    docs_path = None
    for location in possible_docs_locations:
        if location.exists():
            docs_path = location
            break
    
    # If no docs found, use relative path as fallback
    if docs_path is None:
        docs_path = skill_path.parent / "docs"  # Default assumption
    
    # Get relative path from skill to docs
    docs_relative = get_relative_path(skill_path, docs_path)
    
    print(f"Updating guide files with dynamic paths...")
    print(f"  Documentation path: {docs_relative}")
    
    # Update various guide files that contain hardcoded paths
    files_to_update = [
        ("QUICK_START_GUIDE_MD.md", "..", docs_relative),
        ("QUICK_START_GUIDE_MD.md", "../docs", docs_relative),
        ("QUICK_START_GUIDE_MD.md", "..\\docs", docs_relative),
        ("README.md", "../docs", docs_relative),
        ("README.md", "..\\docs", docs_relative),
        ("LLM_AUTOMATION_GUIDE.md", "../docs", docs_relative),
        ("LLM_AUTOMATION_GUIDE.md", "..\\docs", docs_relative),
        ("LLM_FIXING_STEP_BY_STEP_GUIDE.md", "../docs", docs_relative),
        ("LLM_FIXING_STEP_BY_STEP_GUIDE.md", "..\\docs", docs_relative),
        ("WORKFLOW_ROADMAP.md", "../docs", docs_relative),
        ("WORKFLOW_ROADMAP.md", "..\\docs", docs_relative),
        ("IDE_TERMINAL_GUIDE.txt", "../docs", docs_relative),
        ("IDE_TERMINAL_GUIDE.txt", "..\\docs", docs_relative),
        ("quick_run_commands.txt", "../docs", docs_relative),
        ("quick_run_commands.txt", "..\\docs", docs_relative),
    ]
    
    updated_count = 0
    for filename, old_pattern, new_path in files_to_update:
        file_path = skill_path / filename
        if file_path.exists():
            if update_file_with_dynamic_path(file_path, old_pattern, new_path):
                updated_count += 1
    
    # Generate the guide content
    guide_content = f"""================================================================================
IDE TERMINAL EXECUTION GUIDE - MARKDOWN ACCESSIBILITY SKILL
================================================================================
How to run the Omnia Markdown Accessibility Skill directly from Windsurf Terminal
Instead of using the Cascade chat interface

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Skill Location: {skill_path}
Documentation Path: {docs_path.absolute()}
Server Port: {port}
Skill: Omnia Markdown Accessibility Validator & Fixer
Last Updated: Enhanced with full reporting infrastructure and dynamic path support

OVERVIEW
--------------------------------------------------------------------------------
This guide explains how to execute the Markdown accessibility skill directly from
the Windsurf IDE terminal window, providing faster execution and better
control over the validation and fixing process for Markdown/mkdocs documentation.

DYNAMIC PATH CONFIGURATION
--------------------------------------------------------------------------------
This guide is automatically generated based on the current skill location:
- Skill Directory: {skill_path}
- Documentation Directory: {docs_path.absolute()}
- Relative Path to Docs: {docs_relative}
- Server Port: {port}

When you move this skill to a different location, regenerate this guide by running:
python generate_dynamic_guide.py

ADVANTAGES OF TERMINAL EXECUTION
--------------------------------------------------------------------------------
- Faster execution than chat interface
- Direct command control and feedback
- Better error handling and debugging
- Scriptable and automatable
- No waiting for chat responses
- Full access to all command-line options
- Complete workflow automation

GETTING STARTED
--------------------------------------------------------------------------------
1. Open Windsurf IDE
2. Navigate to the skill folder:
   cd "{skill_path.name}"
3. Open the terminal panel (View -> Terminal)
4. Ensure Python is available in your environment

QUICK START - AUTOMATED WORKFLOW
--------------------------------------------------------------------------------
OPTION 1: Checkpoint Mode (Three-Phase Execution)

Phase 1 Command:
python run_omnia_accessibility.py "{docs_relative}" --checkpoint-mode phase1

What it does:
- Validates all Markdown files in the docs directory recursively
- Checks for accessibility issues (alt text, links, code blocks, etc.)
- Generates baseline validation report
- Saves checkpoint state for resuming later
- Exits for manual review of baseline reports

Phase 2 Command:
python run_omnia_accessibility.py "{docs_relative}" --checkpoint-mode phase2

What it does:
- Loads checkpoint state from Phase 1
- Applies automatic fixes to fixable issues
- Re-validates documentation after fixes
- Generates all comparison reports
- Generates HTML visual report
- Generates Excel/CSV report
- Generates unfixed issues report
- Saves checkpoint state for Phase 3

Phase 3 Command:
python run_omnia_accessibility.py "{docs_relative}" --checkpoint-mode phase3

What it does:
- Loads checkpoint state from Phase 2
- Provides step-by-step instructions for rendering and preview
- Displays local preview URL: http://127.0.0.1:{port}
- Displays production ReadTheDocs URL: https://your-project.readthedocs.io/
- Cleans up checkpoint state
- Finalizes workflow for publishing

When to use checkpoint mode:
- When you want to review baseline reports before applying fixes
- For large documentation sets requiring careful review
- In team workflows where validation and fixing are separate steps
- When you need to pause between validation and fixing phases

OPTION 2: Step-by-Step Workflow (For granular control)
--------------------------------------------------------------------------------
Use this approach when you need to:
- Review results between each step
- Customize individual step parameters
- Debug specific workflow stages
- Understand each step in detail

STEP 1: INITIAL VALIDATION
--------------------------------------------------------------------------------
Command:
python omnia_md_accessibility_validator.py "{docs_relative}" -r -o json -f reports/baseline_validation/accessibility_report.json

What it does:
- Scans all Markdown files in the docs directory recursively
- Checks for accessibility issues (alt text, links, code blocks, etc.)
- Generates a JSON report with all findings
- Creates backups of files before validation (if enabled)
- Automatically creates output directories if they don't exist

Expected output:
- Progress messages showing files being scanned
- Summary of issues found
- Confirmation of report generation
- Backup location (if created)

STEP 2: GENERATE STRUCTURED REPORTS
--------------------------------------------------------------------------------
Command:
python structured_reporting_md.py reports/baseline_validation/accessibility_report.json reports/baseline_validation

What it does:
- Creates user-friendly reports from the JSON data
- Generates categorized reports by priority
- Provides specific fix recommendations
- Creates workflow guides for systematic fixing
- Generates INDEX.txt, EXECUTIVE_SUMMARY.txt, ISSUES_BY_CATEGORY.txt, FIX_RECOMMENDATIONS.txt, WORKFLOW_GUIDE.txt

Expected output:
- Confirmation of report generation
- List of generated files
- Quick start instructions

STEP 3: RUN AUTOMATIC FIXER
--------------------------------------------------------------------------------
Command:
python omnia_md_accessibility_fixer.py reports/baseline_validation/accessibility_report.json --auto-fix --auto-only

What it does:
- Applies automatic fixes to issues that can be resolved programmatically
- Fixes insecure links (http to https)
- Fixes invalid code languages
- Skips issues requiring manual intervention
- Generates comparison report

Expected output:
- Progress messages for files being fixed
- Summary of fixes applied
- List of skipped issues

STEP 4: POST-FIX VALIDATION
--------------------------------------------------------------------------------
Command:
python omnia_md_accessibility_validator.py "{docs_relative}" -r -o json -f reports/current_status/accessibility_report_after.json

What it does:
- Re-validates documentation after fixes
- Generates new report showing current status
- Allows comparison with baseline
- Automatically creates output directories if they don't exist

Expected output:
- Progress messages showing files being scanned
- Summary of remaining issues
- Confirmation of report generation

STEP 5: GENERATE CURRENT STATUS REPORTS
--------------------------------------------------------------------------------
Command:
python structured_reporting_md.py reports/current_status/accessibility_report_after.json reports/current_status

What it does:
- Creates user-friendly reports for current status
- Shows remaining issues after fixes
- Provides updated fix recommendations
- Generates current workflow guide

Expected output:
- Confirmation of report generation
- List of generated files
- Updated statistics

STEP 6: GENERATE COMPARISON REPORT
--------------------------------------------------------------------------------
Command:
python generate_comparison_md.py reports/baseline_validation/accessibility_report.json reports/current_status/accessibility_report_after.json reports/comparison_report.txt

What it does:
- Compares baseline and current status
- Shows what was fixed
- Identifies remaining issues
- Provides recommendations

Expected output:
- Confirmation of comparison generation
- Summary of changes
- File location of comparison report

STEP 7: GENERATE HTML VISUAL REPORT
--------------------------------------------------------------------------------
Command:
python generate_visual_report_md.py reports/baseline_validation/accessibility_report.json reports/current_status/accessibility_report_after.json reports/visual_report.html

What it does:
- Generates interactive HTML report with CSS-based visual charts
- Creates pie charts for severity and priority distribution
- Creates bar charts for issue types and top files
- Provides detailed data tables with color-coded priorities
- No external dependencies - uses only standard library

Expected output:
- Confirmation of HTML report generation
- Path to generated HTML file
- Instructions to open in web browser

STEP 8: GENERATE EXCEL/CSV REPORT
--------------------------------------------------------------------------------
Command:
python generate_excel_report_md.py reports/baseline_validation/accessibility_report.json reports/current_status/accessibility_report_after.json reports/excel_report.csv

What it does:
- Generates CSV report with structured data for Excel visualizations
- Creates data tables for baseline vs after comparison
- Provides severity breakdown, issue type analysis, and file statistics
- Suitable for importing into Excel for custom charts and pivot tables

Expected output:
- Confirmation of CSV report generation
- Path to generated CSV file
- Instructions for Excel import

STEP 9: GENERATE UNFIXED ISSUES REPORT
--------------------------------------------------------------------------------
Command:
python generate_unfixed_report_md.py reports/current_status/accessibility_report_after.json reports/unfixed_issues_report.txt

What it does:
- Generates detailed report of unfixed issues
- Lists all issues requiring manual intervention
- Provides specific guidance for each issue type
- Includes effort estimates and prioritized fixing approach

Expected output:
- Confirmation of unfixed issues report generation
- Summary of remaining manual fixes needed
- File location of unfixed issues report

STEP 10: GENERATE HTML REPORT WITH CLICKABLE LINKS
--------------------------------------------------------------------------------
Command:
python generate_fixed_issues_html_report.py reports/baseline_validation/accessibility_report.json reports/current_status/accessibility_report_after.json reports/fixed_issues_with_links.html "{docs_relative}" {port}

What it does:
- Generates HTML report with clickable links to view fixed issues in rendered documentation
- Links point to http://127.0.0.1:{port}
- Includes server status checking to prevent connection errors
- Provides clear instructions when server is not running

Expected output:
- Confirmation of HTML report generation
- Path to generated HTML file
- Instructions to start mkdocs server on port {port}

STEP 11: RENDER DOCUMENTATION (Manual Step)
--------------------------------------------------------------------------------
Command:
cd "{docs_relative}" && mkdocs build

What it does:
- Renders the fixed Markdown documentation in ReadTheDocs format
- Generates HTML output in site/ directory
- Allows preview of how fixes will appear in production

Expected output:
- Confirmation of successful build
- Path to generated HTML files
- Any rendering errors or warnings

STEP 12: PREVIEW RENDERED OUTPUT (Manual Step)
--------------------------------------------------------------------------------
Command:
cd "{docs_relative}" && mkdocs serve -a 127.0.0.1:{port}

What it does:
- Starts local web server for preview
- Opens browser at http://127.0.0.1:{port}
- Allows review of rendered documentation
- Verify both accessibility fixes and visual rendering

Expected output:
- Server startup confirmation
- URL for local preview: http://127.0.0.1:{port}
- Live reload on file changes

ALTERNATIVE: Unified One-Command Workflow (Last Resort)
--------------------------------------------------------------------------------
OPTION 3: Run validation with automatic report generation (One-Command Workflow)

Command:
python run_omnia_accessibility.py "{docs_relative}"

What it does:
- Validates all Markdown files in the docs directory recursively
- Checks for accessibility issues (alt text, links, code blocks, etc.)
- Generates baseline validation report
- Automatically generates comparison reports when baseline exists
- Automatically generates HTML visual report
- Automatically generates category-wise report
- Creates automatic backups of documentation files

Options:
  --skip-fixes: Run validation only, skip automatic fixes
  --checkpoint-mode phase1: Run validation + baseline reports, then pause for review
  --checkpoint-mode phase2: Resume from checkpoint, apply fixes, generate all reports
  --no-backup: Disable automatic backup of files

Expected output:
- Progress messages for validation
- Summary of issues found
- Confirmation of report generation
- Automatic comparison reports (if baseline exists)
- Backup location (if created)

When to use:
- First-time accessibility assessment
- Regular accessibility checks
- When you want complete automation
- When you need before/after comparison
- When you want to apply fixes immediately after validation

Note: This is a last resort option. The recommended approaches are Option 1 (Checkpoint Mode) and Option 2 (Step-by-Step Workflow), which provide better control and review capabilities.

BATCH FILE LAUNCHERS
--------------------------------------------------------------------------------
For Windows users, batch file launchers are available for convenience:

run_omnia_md_validator.bat "{docs_relative}"
  - Launches the Markdown accessibility validator
  - Accepts optional --no-backup and --no-recursive flags

run_omnia_md_fixer.bat reports/baseline_validation/accessibility_report.json auto
  - Launches the Markdown accessibility fixer
  - Accepts fix mode: auto (for automatic fixes)

CONFIGURATION
--------------------------------------------------------------------------------
The Markdown accessibility skill uses omnia_md_config.json for configuration:

Key configuration options:
- include_patterns: File patterns to include in validation
- exclude_patterns: Directories and files to exclude from validation
- checks: Enable/disable specific accessibility checks
- non_descriptive_link_patterns: Patterns for identifying non-descriptive links
- supported_code_languages: List of supported code block languages
- backup_settings: Configure backup behavior
- report_settings: Configure report generation options
- fixer_settings: Configure automatic fixer behavior

REPORT STRUCTURE
--------------------------------------------------------------------------------
Generated reports are organized in the reports/ directory:

reports/
├── baseline_validation/
│   ├── accessibility_report_TIMESTAMP.json
│   ├── INDEX.txt
│   ├── EXECUTIVE_SUMMARY.txt
│   ├── ISSUES_BY_CATEGORY.txt
│   ├── FIX_RECOMMENDATIONS.txt
│   └── WORKFLOW_GUIDE.txt
├── current_status/
│   ├── accessibility_report_after_TIMESTAMP.json
│   ├── INDEX.txt
│   ├── EXECUTIVE_SUMMARY.txt
│   ├── ISSUES_BY_CATEGORY.txt
│   ├── FIX_RECOMMENDATIONS.txt
│   └── WORKFLOW_GUIDE.txt
├── comparison_report_TIMESTAMP.txt
├── visual_report_TIMESTAMP.html
├── excel_report_TIMESTAMP.csv
├── unfixed_issues_report_TIMESTAMP.txt
└── fixed_issues_with_links.html

BACKUP FUNCTIONALITY
--------------------------------------------------------------------------------
The Markdown accessibility skill automatically creates backups of documentation
files before validation when enabled:

Backup location: {docs_relative}/.omnia_backup_TIMESTAMP/
Backup contents: All Markdown files from the docs directory
Backup metadata: backup_metadata.json with timestamp and file count

To disable backups: Use --no-backup flag with validator or workflow

TROUBLESHOOTING
--------------------------------------------------------------------------------
Issue: "Python is not available"
Solution: Ensure Python 3.6+ is installed and in your PATH

Issue: "Report file not found"
Solution: Ensure the validation step completed successfully before running fixer

Issue: "Backup directory already exists"
Solution: This is normal - each validation creates a new timestamped backup

Issue: "Permission denied when writing files"
Solution: Ensure you have write permissions to the documentation directory

Issue: "Module not found" errors
Solution: The skill uses only Python standard library - no external dependencies needed

Issue: "Path not found" errors
Solution: Regenerate this guide by running: python generate_dynamic_guide.py

INTEGRATION WITH OMNIA WORKFLOW
--------------------------------------------------------------------------------
The Markdown accessibility skill is designed to integrate seamlessly with the
Omnia documentation workflow:

1. Pre-commit validation: Check accessibility before committing changes
2. Staging validation: Validate content before staging builds
3. PR validation: Ensure accessibility standards in pull requests
4. Continuous monitoring: Regular accessibility checks for documentation
5. mkdocs compatibility: Ensures proper rendering on mkdocs platform

The skill works with GitHub Actions, CI/CD pipelines, and can be integrated
into automated documentation workflows.

SERVER CONFIGURATION
--------------------------------------------------------------------------------
This skill is configured to use port {port} for documentation preview:
- Start server: cd "{docs_relative}" && mkdocs serve -a 127.0.0.1:{port}
- Preview URL: http://127.0.0.1:{port}
- HTML report links are configured for this port

================================================================================
END OF GUIDE
================================================================================
"""

    # Write the guide to file
    guide_file = skill_path / "IDE_TERMINAL_GUIDE_MD.txt"
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print(f"Dynamic IDE guide generated: {guide_file}")
    print(f"Skill location: {skill_path}")
    print(f"Documentation path: {docs_path.absolute()}")
    print(f"Relative path to docs: {docs_relative}")
    print(f"Server port: {port}")
    print(f"Updated {updated_count} additional guide files with dynamic paths")
    
    return guide_file


def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.resolve()
    
    # Port is no longer required - file:// URLs are used instead
    port = None
    
    print(f"Generating dynamic IDE guide for skill at: {script_dir}")
    print(f"Using port: {port}")
    
    # Generate the guide
    generate_dynamic_guide(script_dir, port)


if __name__ == "__main__":
    main()
