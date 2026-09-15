#!/usr/bin/env python3
"""
Generate structured comparison report between before-fix and after-fix accessibility reports
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def generate_comparison_report(before_report_path, after_report_path, output_path):
    """Generate comparison report between before and after accessibility reports"""
    
    # Load both reports
    with open(before_report_path, 'r') as f:
        before_data = json.load(f)
    
    with open(after_report_path, 'r') as f:
        after_data = json.load(f)
    
    # Create comparison report
    report = []
    report.append("=" * 80)
    report.append("ACCESSIBILITY COMPARISON REPORT")
    report.append("BEFORE FIXES vs AFTER FIXES")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Executive Summary
    before_summary = before_data['summary']
    after_summary = after_data['summary']
    
    report.append("EXECUTIVE SUMMARY")
    report.append("-" * 80)
    report.append(f"Before Fixes:")
    report.append(f"  Total Issues: {before_summary['total_issues']}")
    report.append(f"  Files with Issues: {before_summary['files_with_issues']}")
    report.append("")
    report.append(f"After Fixes:")
    report.append(f"  Total Issues: {after_summary['total_issues']}")
    report.append(f"  Files with Issues: {after_summary['files_with_issues']}")
    report.append("")
    
    # Calculate changes
    issue_change = after_summary['total_issues'] - before_summary['total_issues']
    file_change = after_summary['files_with_issues'] - before_summary['files_with_issues']
    
    report.append("CHANGES")
    report.append("-" * 80)
    report.append(f"Total Issues: {issue_change:+d} ({'increase' if issue_change > 0 else 'decrease' if issue_change < 0 else 'no change'})")
    report.append(f"Files Affected: {file_change:+d} ({'increase' if file_change > 0 else 'decrease' if file_change < 0 else 'no change'})")
    report.append("")
    
    # Severity comparison
    report.append("SEVERITY COMPARISON")
    report.append("-" * 80)
    report.append(f"{'Severity':<20} {'Before':<10} {'After':<10} {'Change':<10}")
    report.append("-" * 50)
    
    for severity in ['ERROR', 'WARNING', 'SUGGESTION']:
        before_count = before_summary['by_severity'].get(severity, 0)
        after_count = after_summary['by_severity'].get(severity, 0)
        change = after_count - before_count
        report.append(f"{severity:<20} {before_count:<10} {after_count:<10} {change:+10}")
    
    report.append("")
    
    # Issue type comparison
    report.append("ISSUE TYPE COMPARISON")
    report.append("-" * 80)
    
    all_types = set(before_summary['by_issue_type'].keys()) | set(after_summary['by_issue_type'].keys())
    
    report.append(f"{'Issue Type':<30} {'Before':<10} {'After':<10} {'Change':<10}")
    report.append("-" * 60)
    
    for issue_type in sorted(all_types):
        before_count = before_summary['by_issue_type'].get(issue_type, 0)
        after_count = after_summary['by_issue_type'].get(issue_type, 0)
        change = after_count - before_count
        if change != 0:  # Only show types that changed
            report.append(f"{issue_type:<30} {before_count:<10} {after_count:<10} {change:+10}")
    
    report.append("")
    
    # Fixer Results
    report.append("FIXER RESULTS")
    report.append("-" * 80)
    report.append("The automatic fixer was run with the following results:")
    report.append("  - Issues Fixed: 0")
    report.append("  - Issues Skipped: 1,116")
    report.append("  - Files Modified: 0")
    report.append("")
    report.append("Note: Most accessibility issues require manual intervention:")
    report.append("  - Missing alt text needs descriptive content")
    report.append("  - Empty section titles need meaningful text")
    report.append("  - Non-descriptive links need rewriting")
    report.append("  - Missing directive options need specific values")
    report.append("")
    
    # Recommendations
    report.append("RECOMMENDATIONS")
    report.append("-" * 80)
    report.append("1. Review the FIX_RECOMMENDATIONS.txt in the before_fix folder")
    report.append("2. Address issues in priority order (HIGH -> MEDIUM -> LOW)")
    report.append("3. Use the specific guidance and templates provided")
    report.append("4. Make changes systematically file by file")
    report.append("5. Re-run validation after manual fixes to track progress")
    report.append("")
    
    # File-specific changes
    report.append("FILE-SPECIFIC ANALYSIS")
    report.append("-" * 80)
    
    # Get files that changed
    before_files = set(before_data['files'].keys())
    after_files = set(after_data['files'].keys())
    
    new_files = after_files - before_files
    removed_files = before_files - after_files
    common_files = before_files & after_files
    
    report.append(f"Files with changes: {len(common_files)}")
    report.append(f"New files added: {len(new_files)}")
    report.append(f"Files removed: {len(removed_files)}")
    report.append("")
    
    # Show top files with most changes
    file_changes = []
    for file_path in common_files:
        before_issues = len(before_data['files'][file_path]['issues'])
        after_issues = len(after_data['files'][file_path]['issues'])
        change = after_issues - before_issues
        if change != 0:
            file_changes.append((file_path, before_issues, after_issues, change))
    
    # Sort by absolute change
    file_changes.sort(key=lambda x: abs(x[3]), reverse=True)
    
    if file_changes:
        report.append("Top 10 Files with Most Changes:")
        report.append("-" * 80)
        for i, (file_path, before, after, change) in enumerate(file_changes[:10]):
            relative_path = before_data['files'][file_path].get('relative_path', file_path)
            report.append(f"{i+1}. {relative_path}")
            report.append(f"   Before: {before} issues, After: {after} issues, Change: {change:+d}")
    else:
        report.append("No significant changes in individual files")
    
    report.append("")
    report.append("=" * 80)
    report.append("END OF COMPARISON REPORT")
    report.append("=" * 80)
    
    # Write comparison report
    with open(output_path, 'w') as f:
        f.write('\n'.join(report))
    
    print(f"Comparison report saved to: {output_path}")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python generate_comparison.py <before_report.json> <after_report.json> <output.txt>")
        sys.exit(1)
    
    before_report = sys.argv[1]
    after_report = sys.argv[2]
    output_file = sys.argv[3]
    
    generate_comparison_report(before_report, after_report, output_file)
