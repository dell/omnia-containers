#!/usr/bin/env python3
"""
Omnia RST Accessibility Validator & Fixer - Full Workflow Automation
Runs all 9 steps of the accessibility workflow with a single command
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


def run_command(cmd, description, ignore_validator_errors=False):
    """Run a command and display progress"""
    print(f"\n{'='*80}")
    print(f"{description}")
    print(f"{'='*80}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.returncode != 0:
        # Validator exits with 1 when errors are found, which is expected
        if ignore_validator_errors and "validator" in ' '.join(cmd):
            print(f"Note: Validator found accessibility issues (expected behavior)")
            return True
        print(f"Error: {result.stderr}")
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Omnia RST Accessibility Validator & Fixer - Full Workflow Automation"
    )
    parser.add_argument(
        "path",
        nargs='?',
        default="../docs",
        help="Path to RST documentation directory (default: ../docs)"
    )
    parser.add_argument(
        "--skip-fixes",
        action="store_true",
        help="Skip automatic fixes (validation only)"
    )
    parser.add_argument(
        "--fix-mode",
        choices=["auto", "interactive", "both"],
        default="auto",
        help="Fix mode: auto, interactive, or both (default: auto)"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Disable automatic backup"
    )
    
    args = parser.parse_args()
    
    docs_path = args.path
    reports_dir = current_dir / "reports"
    baseline_dir = reports_dir / "baseline_validation"
    current_status_dir = reports_dir / "current_status"
    
    # Create directories
    reports_dir.mkdir(exist_ok=True)
    baseline_dir.mkdir(exist_ok=True)
    current_status_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("="*80)
    print("OMNIA RST ACCESSIBILITY VALIDATOR & FIXER - FULL WORKFLOW")
    print("="*80)
    print(f"Documentation path: {docs_path}")
    print(f"Timestamp: {timestamp}")
    print()
    
    # STEP 1: INITIAL VALIDATION
    step1_cmd = [
        sys.executable,
        str(current_dir / "omnia_rst_accessibility_validator.py"),
        docs_path,
        "-r",
        "-o", "json",
        "-f", str(baseline_dir / "accessibility_report.json")
    ]
    
    if not run_command(step1_cmd, "STEP 1: INITIAL VALIDATION", ignore_validator_errors=True):
        print("Step 1 failed. Exiting.")
        sys.exit(1)
    
    # STEP 2: GENERATE STRUCTURED REPORTS
    step2_cmd = [
        sys.executable,
        str(current_dir / "structured_reporting.py"),
        str(baseline_dir / "accessibility_report.json"),
        str(baseline_dir)
    ]
    
    if not run_command(step2_cmd, "STEP 2: GENERATE STRUCTURED REPORTS"):
        print("Step 2 failed. Continuing...")
    
    # STEP 3: RUN AUTOMATIC FIXER
    if not args.skip_fixes:
        step3_cmd = [
            sys.executable,
            str(current_dir / "omnia_rst_accessibility_fixer.py"),
            str(baseline_dir / "accessibility_report.json"),
            "--auto-fix",
            "--auto-only"
        ]
        
        if not run_command(step3_cmd, "STEP 3: RUN AUTOMATIC FIXER"):
            print("Step 3 failed. Continuing...")
    else:
        print("\n" + "="*80)
        print("STEP 3: RUN AUTOMATIC FIXER")
        print("="*80)
        print("Skipped (--skip-fixes flag used)")
    
    # STEP 4: POST-FIX VALIDATION
    step4_cmd = [
        sys.executable,
        str(current_dir / "omnia_rst_accessibility_validator.py"),
        docs_path,
        "-r",
        "-o", "json",
        "-f", str(current_status_dir / f"accessibility_report_after_{timestamp}.json")
    ]
    
    if not run_command(step4_cmd, "STEP 4: POST-FIX VALIDATION", ignore_validator_errors=True):
        print("Step 4 failed. Exiting.")
        sys.exit(1)
    
    # STEP 5: GENERATE CURRENT STATUS REPORTS
    step5_cmd = [
        sys.executable,
        str(current_dir / "structured_reporting.py"),
        str(current_status_dir / f"accessibility_report_after_{timestamp}.json"),
        str(current_status_dir)
    ]
    
    if not run_command(step5_cmd, "STEP 5: GENERATE CURRENT STATUS REPORTS"):
        print("Step 5 failed. Continuing...")
    
    # STEP 6: GENERATE COMPARISON REPORT
    step6_cmd = [
        sys.executable,
        str(current_dir / "generate_comparison.py"),
        str(baseline_dir / "accessibility_report.json"),
        str(current_status_dir / f"accessibility_report_after_{timestamp}.json"),
        str(reports_dir / f"comparison_report_{timestamp}.txt")
    ]
    
    if not run_command(step6_cmd, "STEP 6: GENERATE COMPARISON REPORT"):
        print("Step 6 failed. Continuing...")
    
    # STEP 7: GENERATE HTML VISUAL REPORT
    step7_cmd = [
        sys.executable,
        str(current_dir / "generate_visual_report.py"),
        str(baseline_dir / "accessibility_report.json"),
        str(current_status_dir / f"accessibility_report_after_{timestamp}.json"),
        str(reports_dir / f"visual_report_{timestamp}.html")
    ]
    
    if not run_command(step7_cmd, "STEP 7: GENERATE HTML VISUAL REPORT"):
        print("Step 7 failed. Continuing...")
    
    # STEP 8: GENERATE EXCEL/CSV REPORT
    step8_cmd = [
        sys.executable,
        str(current_dir / "generate_excel_report.py"),
        str(baseline_dir / "accessibility_report.json"),
        str(current_status_dir / f"accessibility_report_after_{timestamp}.json"),
        str(reports_dir / f"excel_report_{timestamp}.csv")
    ]
    
    if not run_command(step8_cmd, "STEP 8: GENERATE EXCEL/CSV REPORT"):
        print("Step 8 failed. Continuing...")
    
    # STEP 9: GENERATE UNFIXED ISSUES REPORT
    step9_cmd = [
        sys.executable,
        str(current_dir / "generate_unfixed_report.py"),
        str(current_status_dir / f"accessibility_report_after_{timestamp}.json"),
        str(reports_dir / f"unfixed_issues_report_{timestamp}.txt")
    ]
    
    if not run_command(step9_cmd, "STEP 9: GENERATE UNFIXED ISSUES REPORT"):
        print("Step 9 failed. Continuing...")
    
    # FINAL SUMMARY
    print("\n" + "="*80)
    print("FULL WORKFLOW COMPLETED")
    print("="*80)
    print(f"Timestamp: {timestamp}")
    print()
    print("Generated Reports:")
    print(f"  - Baseline validation: {baseline_dir / 'accessibility_report.json'}")
    print(f"  - Current status: {current_status_dir / f'accessibility_report_after_{timestamp}.json'}")
    print(f"  - Comparison report: {reports_dir / f'comparison_report_{timestamp}.txt'}")
    print(f"  - Visual report: {reports_dir / f'visual_report_{timestamp}.html'}")
    print(f"  - Excel report: {reports_dir / f'excel_report_{timestamp}.csv'}")
    print(f"  - Unfixed issues: {reports_dir / f'unfixed_issues_report_{timestamp}.txt'}")
    print()
    print("Next Steps:")
    print("  1. Review the visual report: visual_report_{timestamp}.html")
    print("  2. Check unfixed issues: unfixed_issues_report_{timestamp}.txt")
    print("  3. Apply manual fixes as needed")
    print("  4. Re-run this workflow to track progress")
    print("="*80)


if __name__ == "__main__":
    main()
