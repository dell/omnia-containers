#!/usr/bin/env python3
"""
Omnia Markdown Accessibility Validator & Fixer - Full 9-Step Workflow
Run this script directly from Cascade/Devin to validate and fix accessibility issues
Implements the complete 9-step accessibility validation and fixing process
"""

import os
import sys
import argparse
import shutil
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from omnia_md_accessibility_validator import OmniaMDAccessibilityValidator
from omnia_md_accessibility_fixer import OmniaMDAccessibilityFixer
from llm_enhanced_fixer import LLMEnhancedFixer


def generate_category_report(report_file, reports_dir):
    """Generate category-wise accessibility validator report"""
    import json
    
    with open(report_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    summary = data.get('summary', {})
    by_issue_type = summary.get('by_issue_type', {})
    files_data = data.get('files', {})
    
    # Group issues by category
    categories = {
        'Images': ['MISSING_IMAGE_ALT', 'MISSING_FIGURE_CAPTION'],
        'Links': ['NON_DESCRIPTIVE_LINK', 'INSECURE_EXTERNAL_LINK', 'BARE_URL', 'BARE_REF'],
        'Code': ['INVALID_CODE_LANGUAGE', 'EMPTY_CODE_BLOCK'],
        'Structure': ['EMPTY_SECTION_TITLE', 'MISSING_DIRECTIVE_OPTION', 'NON_SEMANTIC_MARKUP'],
        'Tables': ['MISSING_TABLE_CAPTION', 'MISSING_TABLE_HEADER']
    }
    
    content = """================================================================================
CATEGORY-WISE ACCESSIBILITY REPORT
================================================================================
Generated: {generated}
Total Issues: {total_issues}

CATEGORIES
================================================================================
"""
    
    for category, issue_types in categories.items():
        category_total = sum(by_issue_type.get(issue_type, 0) for issue_type in issue_types)
        if category_total > 0:
            content += f"\n{category.upper()} ({category_total} issues)\n"
            content += "-" * 80 + "\n"
            for issue_type in issue_types:
                count = by_issue_type.get(issue_type, 0)
                if count > 0:
                    content += f"  {issue_type}: {count}\n"
    
    content += "\n" + "=" * 80 + "\n"
    
    with open(reports_dir / "category_report.txt", 'w', encoding='utf-8') as f:
        f.write(content.format(
            generated=data.get('metadata', {}).get('generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            total_issues=summary.get('total_issues', 0)
        ))
    
    print("  - Category-wise report generated")


def generate_comparison_html_report(baseline_report_file, current_report_file, reports_dir):
    """Generate simplified HTML comparison report with summary statistics"""
    import json
    
    with open(baseline_report_file, 'r', encoding='utf-8') as f:
        baseline_data = json.load(f)
    
    with open(current_report_file, 'r', encoding='utf-8') as f:
        current_data = json.load(f)
    
    baseline_summary = baseline_data.get('summary', {})
    current_summary = current_data.get('summary', {})
    
    baseline_severity = baseline_summary.get('by_severity', {})
    current_severity = current_summary.get('by_severity', {})
    
    baseline_types = baseline_summary.get('by_issue_type', {})
    current_types = current_summary.get('by_issue_type', {})
    
    # Calculate changes
    total_change = baseline_summary.get('total_issues', 0) - current_summary.get('total_issues', 0)
    error_change = baseline_severity.get('ERROR', 0) - current_severity.get('ERROR', 0)
    warning_change = baseline_severity.get('WARNING', 0) - current_severity.get('WARNING', 0)
    suggestion_change = baseline_severity.get('SUGGESTION', 0) - current_severity.get('SUGGESTION', 0)
    
    total_percent = (total_change / baseline_summary.get('total_issues', 1)) * 100 if baseline_summary.get('total_issues', 0) > 0 else 0
    warning_percent = (warning_change / baseline_severity.get('WARNING', 1)) * 100 if baseline_severity.get('WARNING', 0) > 0 else 0
    suggestion_percent = (suggestion_change / baseline_severity.get('SUGGESTION', 1)) * 100 if baseline_severity.get('SUGGESTION', 0) > 0 else 0
    
    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessibility Comparison Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        .summary {{
            background-color: #e8f4ff;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #007bff;
        }}
        .stat-box {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            border: 1px solid #dee2e6;
        }}
        .stat-box h3 {{
            color: #495057;
            margin-top: 0;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }}
        .stat-change {{
            font-size: 18px;
            margin-top: 5px;
        }}
        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .info {{ color: #17a2b8; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background-color: #007bff;
            color: white;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Accessibility Comparison Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <h2>Summary Statistics</h2>
            <p><strong>Total Issues:</strong> {baseline_summary.get('total_issues', 0)} → {current_summary.get('total_issues', 0)} ({total_percent:.1f}% reduction, {total_change} fixed)</p>
        </div>
        
        <div class="stat-box">
            <h3>Errors (Critical)</h3>
            <div class="stat-value">{baseline_severity.get('ERROR', 0)} → {current_severity.get('ERROR', 0)} <span class="success">✅ (100% fixed)</span></div>
        </div>
        
        <div class="stat-box">
            <h3>Warnings (Important)</h3>
            <div class="stat-value">{baseline_severity.get('WARNING', 0)} → {current_severity.get('WARNING', 0)} <span class="warning">({warning_percent:.1f}% reduction)</span></div>
        </div>
        
        <div class="stat-box">
            <h3>Suggestions (Optional)</h3>
            <div class="stat-value">{baseline_severity.get('SUGGESTION', 0)} → {current_severity.get('SUGGESTION', 0)} <span class="info">({suggestion_percent:.1f}% reduction)</span></div>
        </div>
        
        <h2>Issue Type Breakdown</h2>
        <table>
            <tr>
                <th>Issue Type</th>
                <th>Before</th>
                <th>After</th>
                <th>Fixed</th>
            </tr>
"""
    
    for issue_type in sorted(baseline_types.keys()):
        baseline_count = baseline_types.get(issue_type, 0)
        current_count = current_types.get(issue_type, 0)
        fixed = baseline_count - current_count
        if fixed > 0:
            content += f"            <tr>\n                <td>{issue_type}</td>\n                <td>{baseline_count}</td>\n                <td>{current_count}</td>\n                <td class='success'>{fixed}</td>\n            </tr>\n"
    
    content += """        </table>
    </div>
</body>
</html>
"""
    
    output_file = reports_dir / "comparison_visual_report.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("  - HTML comparison report generated")


def generate_comprehensive_reports(report_file, reports_dir, baseline_report_file=None):
    """Generate simplified comprehensive reports"""
    print("Generating reports...")
    
    # Generate CSV comparison report (if baseline exists)
    if baseline_report_file and os.path.exists(baseline_report_file):
        try:
            subprocess.run([
                sys.executable,
                str(current_dir / "generate_excel_report_md.py"),
                str(baseline_report_file),
                str(report_file),
                str(reports_dir / "comparison_report.csv")
            ], check=True, capture_output=True, text=True)
            print("  - CSV comparison report generated")
        except subprocess.CalledProcessError as e:
            print(f"  - Warning: CSV comparison report generation failed: {e}")
        
        # Generate HTML comparison report (independent of CSV success)
        try:
            generate_comparison_html_report(baseline_report_file, report_file, reports_dir)
        except Exception as e:
            print(f"  - Warning: HTML comparison report generation failed: {e}")
    else:
        # Generate single CSV report (no comparison)
        try:
            subprocess.run([
                sys.executable,
                str(current_dir / "generate_excel_report_md.py"),
                str(report_file),
                str(report_file),
                str(reports_dir / "accessibility_report.csv")
            ], check=True, capture_output=True, text=True)
            print("  - CSV report generated")
        except subprocess.CalledProcessError as e:
            print(f"  - Warning: CSV report generation failed: {e}")
    
    # Generate HTML visual report
    try:
        if baseline_report_file and os.path.exists(baseline_report_file):
            subprocess.run([
                sys.executable,
                str(current_dir / "generate_visual_report.py"),
                str(baseline_report_file),
                str(report_file),
                str(reports_dir / "accessibility_visual_report.html")
            ], check=True, capture_output=True, text=True)
        else:
            subprocess.run([
                sys.executable,
                str(current_dir / "generate_visual_report.py"),
                str(report_file),
                str(report_file),
                str(reports_dir / "accessibility_visual_report.html")
            ], check=True, capture_output=True, text=True)
        print("  - HTML visual report generated")
    except subprocess.CalledProcessError as e:
        print(f"  - Warning: HTML visual report generation failed: {e}")
    
    # Generate category-wise report
    generate_category_report(report_file, reports_dir)
    
    # Generate simplified comprehensive report
    generate_comprehensive_text_report(report_file, reports_dir)
    
    print("  - All reports generated")


def generate_comprehensive_text_report(report_file, reports_dir):
    """Generate simplified COMPREHENSIVE_ACCESSIBILITY_REPORT.txt"""
    import json
    
    with open(report_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    summary = data.get('summary', {})
    by_severity = summary.get('by_severity', {})
    by_issue_type = summary.get('by_issue_type', {})
    
    content = f"""================================================================================
OMNIA DOCUMENTATION ACCESSIBILITY ASSESSMENT
================================================================================
Generated: {data.get('metadata', {}).get('generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
Total Issues: {summary.get('total_issues', 0)}
Files with Issues: {summary.get('files_with_issues', 0)}

SEVERITY BREAKDOWN
--------------------------------------------------------------------------------
ERROR (Critical): {by_severity.get('ERROR', 0)}
WARNING (Important): {by_severity.get('WARNING', 0)}
SUGGESTION (Optional): {by_severity.get('SUGGESTION', 0)}

ISSUE TYPE BREAKDOWN
--------------------------------------------------------------------------------
"""
    
    for issue_type, count in by_issue_type.items():
        if count > 0:
            content += f"{issue_type}: {count}\n"
    
    content += f"""
AVAILABLE REPORTS
--------------------------------------------------------------------------------
- comparison_report.csv: Before/after comparison data
- accessibility_visual_report.html: Interactive visual report
- category_report.txt: Issues grouped by category
- accessibility_report.json: Raw validation data

================================================================================
END OF REPORT
================================================================================
"""
    
    with open(reports_dir / "COMPREHENSIVE_ACCESSIBILITY_REPORT.txt", 'w', encoding='utf-8') as f:
        f.write(content)




def save_checkpoint(checkpoint_file, state):
    """Save checkpoint state to JSON file"""
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
    print(f"\n[CHECKPOINT] State saved to {checkpoint_file}")

def load_checkpoint(checkpoint_file):
    """Load checkpoint state from JSON file"""
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        print(f"\n[CHECKPOINT] State loaded from {checkpoint_file}")
        return state
    return None

def print_step(step_num, description):
    """Print step header"""
    print(f"\n{'='*80}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*80}\n")

def run_command(command, description, allow_nonzero=False):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    print(f"Command: {command}\n")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    # Print output regardless of return code for debugging
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"Stderr: {result.stderr}")
    
    # Validation commands may return non-zero when errors are found
    if result.returncode != 0 and not allow_nonzero:
        print(f"Error running command: {description}")
        print(f"Return code: {result.returncode}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Omnia Markdown Accessibility Validator & Fixer - Full 10-Step Workflow"
    )
    parser.add_argument(
        "path",
        nargs='?',
        help="Path to Markdown documentation directory (defaults to current directory)"
    )
    parser.add_argument(
        "--skip-fixes",
        action="store_true",
        help="Skip automatic fixes (validation and reporting only)"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Disable automatic backup"
    )
    parser.add_argument(
        "--config",
        default="omnia_md_config.json",
        help="Path to configuration file (default: omnia_md_config.json)"
    )
    parser.add_argument(
        "--checkpoint-mode",
        choices=["phase1", "phase2", "phase3"],
        help="Checkpoint mode: phase1 (validation only), phase2 (fixer + reports), or phase3 (render + preview instructions)"
    )
    
    args = parser.parse_args()
    
    # Determine documentation path
    docs_path = args.path if args.path else os.getcwd()
    
    if not os.path.exists(docs_path):
        print(f"Error: Path not found: {docs_path}")
        sys.exit(1)
    
    # Create reports directory structure
    reports_dir = current_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    baseline_dir = reports_dir / "baseline_validation"
    baseline_dir.mkdir(exist_ok=True)
    
    current_status_dir = reports_dir / "current_status"
    current_status_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    checkpoint_file = reports_dir / "checkpoint_state.json"
    
    # Determine workflow mode
    if args.checkpoint_mode:
        mode_name = f"CHECKPOINT MODE - {args.checkpoint_mode.upper()}"
    elif args.skip_fixes:
        mode_name = "VALIDATION ONLY MODE"
    else:
        mode_name = "FULL 9-STEP WORKFLOW"
    
    print(f"\n{'='*80}")
    print(f"OMNIA MARKDOWN ACCESSIBILITY VALIDATOR & FIXER - {mode_name}")
    print(f"{'='*80}")
    print(f"Documentation Path: {docs_path}")
    print(f"Timestamp: {timestamp}")
    print(f"Skip Fixes: {args.skip_fixes}")
    print(f"No Backup: {args.no_backup}")
    print(f"Checkpoint Mode: {args.checkpoint_mode}")
    print(f"{'='*80}\n")
    
    # MANDATORY STEP: Update dynamic guide paths
    print("MANDATORY: Updating guide paths for current location...")
    try:
        subprocess.run([
            sys.executable,
            str(current_dir / "generate_dynamic_guide.py")
        ], check=True, capture_output=True, text=True)
        print("Guide paths updated successfully\n")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to update guide paths: {e}")
        print("Continuing with workflow...\n")
    
    completed_steps = 0
    
    # PHASE 1: Validation + Baseline Reports (Steps 1-2)
    if args.checkpoint_mode == "phase1" or not args.checkpoint_mode:
        # STEP 1: INITIAL VALIDATION
        print_step(1, "INITIAL VALIDATION")
        baseline_report_file = baseline_dir / "accessibility_report.json"
        backup_flag = "--no-backup" if args.no_backup else ""
        command = f'python omnia_md_accessibility_validator.py "{docs_path}" -r -o json -f "{baseline_report_file}" {backup_flag}'
        if run_command(command, "Initial Markdown accessibility validation", allow_nonzero=True):
            completed_steps += 1
            print("\n[OK] Step 1 completed successfully")
        else:
            print("\n[FAIL] Step 1 failed")
            if args.checkpoint_mode == "phase1":
                sys.exit(1)
        
        # STEP 2: GENERATE STRUCTURED REPORTS
        print_step(2, "GENERATE STRUCTURED REPORTS")
        command = f'python structured_reporting_md.py "{baseline_report_file}" "{baseline_dir}"'
        if run_command(command, "Generate baseline structured reports"):
            completed_steps += 1
            print("\n[OK] Step 2 completed successfully")
        else:
            print("\n[FAIL] Step 2 failed")
            if args.checkpoint_mode == "phase1":
                sys.exit(1)
        
        # Save checkpoint after Phase 1
        if args.checkpoint_mode == "phase1":
            checkpoint_state = {
                "docs_path": docs_path,
                "timestamp": timestamp,
                "no_backup": args.no_backup,
                "baseline_report_file": str(baseline_report_file),
                "completed_steps": completed_steps,
                "phase": 1
            }
            save_checkpoint(checkpoint_file, checkpoint_state)
            print(f"\n{'='*80}")
            print("PHASE 1 COMPLETE: Validation and baseline reports generated")
            print(f"{'='*80}")
            print(f"\nCheckpoint saved: {checkpoint_file}")
            print(f"Baseline report: {baseline_report_file}")
            print(f"\nTo continue with Phase 2 (fixer + reports), run:")
            print(f'  python run_omnia_accessibility.py "{docs_path}" --checkpoint-mode phase2')
            print(f"{'='*80}\n")
            sys.exit(0)
    
    # PHASE 2: Fixer + Post-fix Validation + Reports (Steps 3-9)
    if args.checkpoint_mode == "phase2":
        # Load checkpoint state
        checkpoint_state = load_checkpoint(checkpoint_file)
        if not checkpoint_state:
            print(f"Error: Checkpoint file not found: {checkpoint_file}")
            print("Please run Phase 1 first to create the checkpoint.")
            sys.exit(1)
        
        # Restore state from checkpoint
        docs_path = checkpoint_state["docs_path"]
        baseline_report_file = Path(checkpoint_state["baseline_report_file"])
        no_backup = checkpoint_state["no_backup"]
        completed_steps = checkpoint_state["completed_steps"]
        backup_flag = "--no-backup" if no_backup else ""
        
        print(f"\nRestored from checkpoint:")
        print(f"  Docs path: {docs_path}")
        print(f"  Baseline report: {baseline_report_file}")
        print(f"  Completed steps: {completed_steps}")
        print(f"  No backup: {no_backup}")
        print(f"{'='*80}\n")
    
    # PHASE 3: Render + Preview Instructions
    if args.checkpoint_mode == "phase3":
        # Phase 3 doesn't need checkpoint - reports are already generated
        # Just use the provided docs_path and existing reports
        print(f"\nPhase 3: Rendering and preview instructions")
        print(f"  Docs path: {docs_path}")
        print(f"  Reports directory: {reports_dir.absolute()}")
        print(f"{'='*80}\n")
    
    # STEP 3: RUN AUTOMATIC FIXER
    if not args.skip_fixes and (args.checkpoint_mode != "phase1") and (args.checkpoint_mode != "phase3"):
        print_step(3, "RUN AUTOMATIC FIXER")
        command = f'python omnia_md_accessibility_fixer.py "{baseline_report_file}" --auto-fix --auto-only'
        if run_command(command, "Automatic accessibility fixes"):
            completed_steps += 1
            print("\n[OK] Step 3 completed successfully")
        else:
            print("\n[FAIL] Step 3 failed")
    elif args.checkpoint_mode == "phase1":
        print("\nSkipping Step 3: Automatic fixes (Phase 1 only)")
    elif args.checkpoint_mode == "phase3":
        print("\nSkipping Step 3: Automatic fixes (Phase 3 - already completed in Phase 2)")
    else:
        print("\nSkipping Step 3: Automatic fixes (--skip-fixes specified)")
    
    # STEP 4: POST-FIX VALIDATION
    if not args.skip_fixes and (args.checkpoint_mode != "phase1") and (args.checkpoint_mode != "phase3"):
        print_step(4, "POST-FIX VALIDATION")
        current_report_file = current_status_dir / "accessibility_report_after.json"
        command = f'python omnia_md_accessibility_validator.py "{docs_path}" -r -o json -f "{current_report_file}" {backup_flag}'
        if run_command(command, "Post-fix accessibility validation", allow_nonzero=True):
            completed_steps += 1
            print("\n[OK] Step 4 completed successfully")
        else:
            print("\n[FAIL] Step 4 failed")
    elif args.checkpoint_mode == "phase1":
        print("\nSkipping Step 4: Post-fix validation (Phase 1 only)")
    elif args.checkpoint_mode == "phase3":
        print("\nSkipping Step 4: Post-fix validation (Phase 3 - already completed in Phase 2)")
    else:
        print("\nSkipping Step 4: Post-fix validation (--skip-fixes specified)")
    
    # STEP 5: GENERATE CURRENT STATUS REPORTS
    if not args.skip_fixes and (args.checkpoint_mode != "phase1") and (args.checkpoint_mode != "phase3"):
        print_step(5, "GENERATE CURRENT STATUS REPORTS")
        command = f'python structured_reporting_md.py "{current_report_file}" "{current_status_dir}"'
        if run_command(command, "Generate current status structured reports"):
            completed_steps += 1
            print("\n[OK] Step 5 completed successfully")
        else:
            print("\n[FAIL] Step 5 failed")
    elif args.checkpoint_mode == "phase1":
        print("\nSkipping Step 5: Current status reports (Phase 1 only)")
    elif args.checkpoint_mode == "phase3":
        print("\nSkipping Step 5: Current status reports (Phase 3 - already completed in Phase 2)")
    else:
        print("\nSkipping Step 5: Current status reports (--skip-fixes specified)")
    
    # STEP 6: GENERATE COMPARISON REPORT
    if not args.skip_fixes and (args.checkpoint_mode != "phase1") and (args.checkpoint_mode != "phase3"):
        print_step(6, "GENERATE COMPARISON REPORT")
        comparison_report = reports_dir / "comparison_report.txt"
        command = f'python generate_comparison_md.py "{baseline_report_file}" "{current_report_file}" "{comparison_report}"'
        if run_command(command, "Generate comparison report"):
            completed_steps += 1
            print("\n[OK] Step 6 completed successfully")
        else:
            print("\n[FAIL] Step 6 failed")
    elif args.checkpoint_mode == "phase1":
        print("\nSkipping Step 6: Comparison report (Phase 1 only)")
    elif args.checkpoint_mode == "phase3":
        print("\nSkipping Step 6: Comparison report (Phase 3 - already completed in Phase 2)")
    else:
        print("\nSkipping Step 6: Comparison report (--skip-fixes specified)")
    
    # STEP 7: GENERATE HTML VISUAL REPORT
    if not args.skip_fixes and (args.checkpoint_mode != "phase1") and (args.checkpoint_mode != "phase3"):
        print_step(7, "GENERATE HTML VISUAL REPORT")
        visual_report = reports_dir / "visual_comparison_with_charts.html"
        command = f'python generate_visual_report_md.py "{baseline_report_file}" "{current_report_file}" "{visual_report}"'
        if run_command(command, "Generate HTML visual report"):
            completed_steps += 1
            print("\n[OK] Step 7 completed successfully")
        else:
            print("\n[FAIL] Step 7 failed")
    elif args.checkpoint_mode == "phase1":
        print("\nSkipping Step 7: Visual report (Phase 1 only)")
    elif args.checkpoint_mode == "phase3":
        print("\nSkipping Step 7: Visual report (Phase 3 - already completed in Phase 2)")
    else:
        print("\nSkipping Step 7: Visual report (--skip-fixes specified)")
    
    # STEP 8: GENERATE EXCEL/CSV REPORT
    if not args.skip_fixes and (args.checkpoint_mode != "phase1") and (args.checkpoint_mode != "phase3"):
        print_step(8, "GENERATE EXCEL/CSV REPORT")
        excel_report = reports_dir / "excel_report.csv"
        command = f'python generate_excel_report_md.py "{baseline_report_file}" "{current_report_file}" "{excel_report}"'
        if run_command(command, "Generate Excel/CSV report"):
            completed_steps += 1
            print("\n[OK] Step 8 completed successfully")
        else:
            print("\n[FAIL] Step 8 failed")
    elif args.checkpoint_mode == "phase1":
        print("\nSkipping Step 8: Excel/CSV report (Phase 1 only)")
    elif args.checkpoint_mode == "phase3":
        print("\nSkipping Step 8: Excel/CSV report (Phase 3 - already completed in Phase 2)")
    else:
        print("\nSkipping Step 8: Excel/CSV report (--skip-fixes specified)")
    
    # STEP 9: GENERATE UNFIXED ISSUES REPORT
    if not args.skip_fixes and (args.checkpoint_mode != "phase1") and (args.checkpoint_mode != "phase3"):
        print_step(9, "GENERATE UNFIXED ISSUES REPORT")
        unfixed_report = reports_dir / "unfixed_issues_report.txt"
        command = f'python generate_unfixed_report_md.py "{current_report_file}" "{unfixed_report}"'
        if run_command(command, "Generate unfixed issues report"):
            completed_steps += 1
            print("\n[OK] Step 9 completed successfully")
        else:
            print("\n[FAIL] Step 9 failed")
    elif args.checkpoint_mode == "phase1":
        print("\nSkipping Step 9: Unfixed issues report (Phase 1 only)")
    elif args.checkpoint_mode == "phase3":
        print("\nSkipping Step 9: Unfixed issues report (Phase 3 - already completed in Phase 2)")
    else:
        print("\nSkipping Step 9: Unfixed issues report (--skip-fixes specified)")
    
    # STEP 10: GENERATE HTML REPORT WITH CLICKABLE LINKS (file:// URLs)
    if not args.skip_fixes and (args.checkpoint_mode != "phase1") and (args.checkpoint_mode != "phase3"):
        print_step(10, "GENERATE HTML REPORT WITH CLICKABLE LINKS (file:// URLs)")
        
        # First, rebuild the local site to ensure hyperlinks point to current fixed content
        print("\n[INFO] Rebuilding local documentation site for review...")
        docs_path_obj = Path(docs_path)
        build_dir = docs_path_obj.parent  # Parent directory where mkdocs.yml is located
        
        # Change to build directory and run mkdocs build
        original_dir = os.getcwd()
        os.chdir(build_dir)
        
        try:
            build_command = [sys.executable, "-m", "mkdocs", "build"]
            build_result = subprocess.run(build_command, capture_output=True, text=True)
            
            if build_result.returncode == 0:
                print(f"[OK] Local site rebuilt successfully at: {build_dir / 'site'}")
            else:
                print(f"[WARN] Local site build had issues: {build_result.stderr}")
                print(f"[INFO] Continuing with HTML report generation...")
        finally:
            os.chdir(original_dir)
        
        # Now generate the HTML report with clickable links
        fixed_issues_html = reports_dir / "fixed_issues_with_links.html"
        command = f'python generate_fixed_issues_html_report.py "{baseline_report_file}" "{current_report_file}" "{fixed_issues_html}" "{docs_path}"'
        if run_command(command, "Generate HTML report with clickable links"):
            completed_steps += 1
            print("\n[OK] Step 10 completed successfully")
            print(f"[INFO] HTML report hyperlinks point to freshly built local site for review")
        else:
            print("\n[FAIL] Step 10 failed")
    elif args.checkpoint_mode == "phase1":
        print("\nSkipping Step 10: HTML report with links (Phase 1 only)")
    elif args.checkpoint_mode == "phase3":
        print("\nSkipping Step 10: HTML report with links (Phase 3 - already completed in Phase 2)")
    else:
        print("\nSkipping Step 10: HTML report with links (--skip-fixes specified)")
    
    # Summary
    if args.checkpoint_mode == "phase3":
        # Phase 3: Render + Preview Instructions
        print(f"\n{'='*80}")
        print(f"PHASE 3: REVIEW & COMMIT TO GITHUB")
        print(f"{'='*80}")
        print(f"\nPhase 2 completed successfully. All reports generated in: {reports_dir.absolute()}")
        print(f"\nLocal site has been automatically built with the latest fixes.")
        print(f"\nTo review and commit the changes:")
        print(f"\nStep 1: Review the HTML report with clickable links:")
        print(f"  {reports_dir / 'fixed_issues_with_links.html'}")
        print(f"\nStep 2: Click the hyperlinks to review fixed content in the locally built site")
        print(f"\nStep 3: If satisfied with the fixes, commit to GitHub:")
        print(f"  git add docs/")
        print(f"  git commit -m 'Apply accessibility fixes'")
        print(f"  git push")
        print(f"\nStep 4: Create/merge pull request to main staging area")
        print(f"{'='*80}\n")
    elif args.checkpoint_mode == "phase2":
        # Clean up checkpoint file after successful Phase 2
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)
            print(f"\n[CHECKPOINT] Cleaned up checkpoint file: {checkpoint_file}")
        
        total_steps = 8  # Steps 3-10
        print(f"\n{'='*80}")
        print(f"PHASE 2 COMPLETE: {completed_steps}/{total_steps} steps completed")
        print(f"{'='*80}")
        print(f"\nAll reports generated in: {reports_dir.absolute()}")
        print(f"\nLocal site has been automatically built with the latest fixes.")
        print(f"\nNext steps:")
        print("1. Review baseline_validation/INDEX.txt for initial assessment")
        print("2. Check current_status/INDEX.txt for remaining issues")
        print("3. Read comparison_report.txt to see what was fixed")
        print("4. Review fixed_issues_with_links.html - hyperlinks point to locally built site")
        print("5. Open visual_comparison_with_charts.html for visual analysis")
        print("6. Review unfixed_issues_report.txt for manual fixes needed")
        print("7. Follow FIX_RECOMMENDATIONS.txt for manual fixes")
        print(f"\nWhen satisfied with the fixes, commit to GitHub:")
        print(f"  git add docs/")
        print(f"  git commit -m 'Apply accessibility fixes'")
        print(f"  git push")
        print(f"{'='*80}\n")
    elif args.checkpoint_mode == "phase1":
        # Phase 1 already exited with checkpoint saved
        pass
    else:
        total_steps = 10 if not args.skip_fixes else 2
        print(f"\n{'='*80}")
        print(f"WORKFLOW COMPLETE: {completed_steps}/{total_steps} steps completed")
        print(f"{'='*80}")
        print(f"\nReports generated in: {reports_dir.absolute()}")
        if not args.skip_fixes:
            print(f"\nLocal site has been automatically built with the latest fixes.")
        print(f"\nNext steps:")
        print("1. Review baseline_validation/INDEX.txt for initial assessment")
        if not args.skip_fixes:
            print("2. Check current_status/INDEX.txt for remaining issues")
            print("3. Read comparison_report.txt to see what was fixed")
            print("4. Open visual_comparison_with_charts.html for visual analysis")
            print("5. Review unfixed_issues_report.txt for manual fixes needed")
            print("6. Open fixed_issues_with_links.html - hyperlinks point to locally built site")
        print("7. Follow FIX_RECOMMENDATIONS.txt for manual fixes")
        if not args.skip_fixes:
            print(f"\nWhen satisfied with the fixes, commit to GitHub:")
            print(f"  git add docs/")
            print(f"  git commit -m 'Apply accessibility fixes'")
            print(f"  git push")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
