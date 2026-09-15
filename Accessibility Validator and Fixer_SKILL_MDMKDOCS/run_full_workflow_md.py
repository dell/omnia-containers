#!/usr/bin/env python3
"""
Full Workflow Automation for Markdown Accessibility
Automates the complete 9-step accessibility validation and fixing process
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

class MarkdownAccessibilityWorkflow:
    """Automates the complete accessibility workflow for Markdown"""
    
    def __init__(self, docs_path, skip_fixes=False, no_backup=False):
        self.docs_path = Path(docs_path).absolute()
        self.skip_fixes = skip_fixes
        self.no_backup = no_backup
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.reports_dir = Path("reports")
        
    def print_step(self, step_num, description):
        """Print step header"""
        print(f"\n{'='*80}")
        print(f"STEP {step_num}: {description}")
        print(f"{'='*80}\n")
    
    def run_command(self, command, description, allow_nonzero=False):
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
    
    def step1_initial_validation(self):
        """Step 1: Initial validation with backup"""
        self.print_step(1, "Initial Validation with Backup")
        
        # Create reports directory
        baseline_dir = self.reports_dir / "baseline_validation"
        baseline_dir.mkdir(parents=True, exist_ok=True)
        
        backup_flag = "--no-backup" if self.no_backup else ""
        output_file = baseline_dir / f"accessibility_report_{self.timestamp}.json"
        
        command = f'python omnia_md_accessibility_validator.py "{self.docs_path}" -r -o json -f "{output_file}" {backup_flag}'
        return self.run_command(command, "Initial Markdown accessibility validation", allow_nonzero=True)
    
    def step2_generate_baseline_reports(self):
        """Step 2: Generate structured baseline reports"""
        self.print_step(2, "Generate Baseline Structured Reports")
        
        baseline_dir = self.reports_dir / "baseline_validation"
        # Find the most recent baseline report
        json_files = list(baseline_dir.glob("accessibility_report_*.json"))
        if json_files:
            latest_report = max(json_files, key=os.path.getctime)
        else:
            latest_report = baseline_dir / "accessibility_report.json"
        
        command = f'python structured_reporting_md.py "{latest_report}" "{baseline_dir}"'
        return self.run_command(command, "Generate baseline structured reports")
    
    def step3_automatic_fixer(self):
        """Step 3: Run automatic fixer"""
        if self.skip_fixes:
            print("Skipping automatic fixes (--skip-fixes specified)")
            return True
            
        self.print_step(3, "Run Automatic Fixer")
        
        baseline_dir = self.reports_dir / "baseline_validation"
        json_files = list(baseline_dir.glob("accessibility_report_*.json"))
        if json_files:
            latest_report = max(json_files, key=os.path.getctime)
        else:
            latest_report = baseline_dir / "accessibility_report.json"
        
        command = f'python omnia_md_accessibility_fixer.py "{latest_report}" --auto-fix --auto-only'
        return self.run_command(command, "Automatic accessibility fixes")
    
    def step4_post_fix_validation(self):
        """Step 4: Post-fix validation"""
        if self.skip_fixes:
            print("Skipping post-fix validation (--skip-fixes specified)")
            return True
            
        self.print_step(4, "Post-Fix Validation")
        
        current_dir = self.reports_dir / "current_status"
        current_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = current_dir / f"accessibility_report_after_{self.timestamp}.json"
        backup_flag = "--no-backup" if self.no_backup else ""
        
        command = f'python omnia_md_accessibility_validator.py "{self.docs_path}" -r -o json -f "{output_file}" {backup_flag}'
        return self.run_command(command, "Post-fix accessibility validation", allow_nonzero=True)
    
    def step5_generate_current_reports(self):
        """Step 5: Generate current status reports"""
        if self.skip_fixes:
            print("Skipping current status reports (--skip-fixes specified)")
            return True
            
        self.print_step(5, "Generate Current Status Reports")
        
        current_dir = self.reports_dir / "current_status"
        json_files = list(current_dir.glob("accessibility_report_after_*.json"))
        if json_files:
            latest_report = max(json_files, key=os.path.getctime)
        else:
            latest_report = current_dir / "accessibility_report_after.json"
        
        command = f'python structured_reporting_md.py "{latest_report}" "{current_dir}"'
        return self.run_command(command, "Generate current status structured reports")
    
    def step6_comparison_report(self):
        """Step 6: Generate comparison report"""
        if self.skip_fixes:
            print("Skipping comparison report (--skip-fixes specified)")
            return True
            
        self.print_step(6, "Generate Comparison Report")
        
        baseline_dir = self.reports_dir / "baseline_validation"
        current_dir = self.reports_dir / "current_status"
        
        baseline_files = list(baseline_dir.glob("accessibility_report_*.json"))
        current_files = list(current_dir.glob("accessibility_report_after_*.json"))
        
        if baseline_files and current_files:
            baseline_report = max(baseline_files, key=os.path.getctime)
            current_report = max(current_files, key=os.path.getctime)
        else:
            baseline_report = baseline_dir / "accessibility_report.json"
            current_report = current_dir / "accessibility_report_after.json"
        
        output_file = self.reports_dir / f"comparison_report_{self.timestamp}.txt"
        command = f'python generate_comparison_md.py "{baseline_report}" "{current_report}" "{output_file}"'
        return self.run_command(command, "Generate comparison report")
    
    def step7_visual_report(self):
        """Step 7: Generate HTML visual report"""
        if self.skip_fixes:
            print("Skipping visual report (--skip-fixes specified)")
            return True
            
        self.print_step(7, "Generate HTML Visual Report")
        
        baseline_dir = self.reports_dir / "baseline_validation"
        current_dir = self.reports_dir / "current_status"
        
        baseline_files = list(baseline_dir.glob("accessibility_report_*.json"))
        current_files = list(current_dir.glob("accessibility_report_after_*.json"))
        
        if baseline_files and current_files:
            baseline_report = max(baseline_files, key=os.path.getctime)
            current_report = max(current_files, key=os.path.getctime)
        else:
            baseline_report = baseline_dir / "accessibility_report.json"
            current_report = current_dir / "accessibility_report_after.json"
        
        output_file = self.reports_dir / f"visual_report_{self.timestamp}.html"
        command = f'python generate_visual_report_md.py "{baseline_report}" "{current_report}" "{output_file}"'
        return self.run_command(command, "Generate HTML visual report")
    
    def step8_excel_report(self):
        """Step 8: Generate Excel/CSV report"""
        if self.skip_fixes:
            print("Skipping Excel/CSV report (--skip-fixes specified)")
            return True
            
        self.print_step(8, "Generate Excel/CSV Report")
        
        baseline_dir = self.reports_dir / "baseline_validation"
        current_dir = self.reports_dir / "current_status"
        
        baseline_files = list(baseline_dir.glob("accessibility_report_*.json"))
        current_files = list(current_dir.glob("accessibility_report_after_*.json"))
        
        if baseline_files and current_files:
            baseline_report = max(baseline_files, key=os.path.getctime)
            current_report = max(current_files, key=os.path.getctime)
        else:
            baseline_report = baseline_dir / "accessibility_report.json"
            current_report = current_dir / "accessibility_report_after.json"
        
        output_file = self.reports_dir / f"excel_report_{self.timestamp}.csv"
        command = f'python generate_excel_report_md.py "{baseline_report}" "{current_report}" "{output_file}"'
        return self.run_command(command, "Generate Excel/CSV report")
    
    def step9_unfixed_report(self):
        """Step 9: Generate unfixed issues report"""
        if self.skip_fixes:
            print("Skipping unfixed issues report (--skip-fixes specified)")
            return True
            
        self.print_step(9, "Generate Unfixed Issues Report")
        
        current_dir = self.reports_dir / "current_status"
        json_files = list(current_dir.glob("accessibility_report_after_*.json"))
        
        if json_files:
            latest_report = max(json_files, key=os.path.getctime)
        else:
            latest_report = current_dir / "accessibility_report_after.json"
        
        output_file = self.reports_dir / f"unfixed_issues_report_{self.timestamp}.txt"
        command = f'python generate_unfixed_report_md.py "{latest_report}" "{output_file}"'
        return self.run_command(command, "Generate unfixed issues report")
    
    def run_workflow(self):
        """Run the complete workflow"""
        print(f"\n{'='*80}")
        print("OMNIA MARKDOWN ACCESSIBILITY FULL WORKFLOW")
        print(f"{'='*80}")
        print(f"Documentation Path: {self.docs_path}")
        print(f"Timestamp: {self.timestamp}")
        print(f"Skip Fixes: {self.skip_fixes}")
        print(f"No Backup: {self.no_backup}")
        print(f"{'='*80}\n")
        
        steps = [
            ("Initial Validation with Backup", self.step1_initial_validation),
            ("Generate Baseline Structured Reports", self.step2_generate_baseline_reports),
            ("Run Automatic Fixer", self.step3_automatic_fixer),
            ("Post-Fix Validation", self.step4_post_fix_validation),
            ("Generate Current Status Reports", self.step5_generate_current_reports),
            ("Generate Comparison Report", self.step6_comparison_report),
            ("Generate HTML Visual Report", self.step7_visual_report),
            ("Generate Excel/CSV Report", self.step8_excel_report),
            ("Generate Unfixed Issues Report", self.step9_unfixed_report)
        ]
        
        completed_steps = 0
        for step_num, (description, step_func) in enumerate(steps, 1):
            try:
                if step_func():
                    completed_steps += 1
                    print(f"\n[OK] Step {step_num} completed successfully")
                else:
                    print(f"\n[FAIL] Step {step_num} failed")
            except Exception as e:
                print(f"\n[ERROR] Step {step_num} failed with error: {e}")
        
        print(f"\n{'='*80}")
        print(f"WORKFLOW COMPLETE: {completed_steps}/{len(steps)} steps completed")
        print(f"{'='*80}")
        print(f"\nReports generated in: {self.reports_dir.absolute()}")
        print(f"\nNext steps:")
        print("1. Review baseline_validation/INDEX.txt for initial assessment")
        if not self.skip_fixes:
            print("2. Check current_status/INDEX.txt for remaining issues")
            print("3. Read comparison report to see what was fixed")
            print("4. Open visual_report.html for visual analysis")
            print("5. Review unfixed_issues_report.txt for manual fixes needed")
        print("6. Follow FIX_RECOMMENDATIONS.txt for manual fixes")
        print(f"{'='*80}\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_full_workflow_md.py <docs_path> [--skip-fixes] [--no-backup]")
        print("Example: python run_full_workflow_md.py ../docs")
        print("Example: python run_full_workflow_md.py ../docs --skip-fixes")
        print("Example: python run_full_workflow_md.py ../docs --no-backup")
        sys.exit(1)
    
    docs_path = sys.argv[1]
    skip_fixes = "--skip-fixes" in sys.argv
    no_backup = "--no-backup" in sys.argv
    
    workflow = MarkdownAccessibilityWorkflow(docs_path, skip_fixes, no_backup)
    workflow.run_workflow()

if __name__ == "__main__":
    main()
