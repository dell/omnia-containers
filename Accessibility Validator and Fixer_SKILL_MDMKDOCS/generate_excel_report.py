#!/usr/bin/env python3
"""
Generate CSV report with data for Excel visualizations
This creates a structured CSV that can be opened in Excel and used to create charts
"""

import json
import csv
import sys
from pathlib import Path

def generate_excel_report(baseline_report_path, after_report_path, output_path):
    """Generate CSV report with structured data for Excel visualizations"""
    
    # Load reports
    with open(baseline_report_path, 'r') as f:
        baseline_data = json.load(f)
    
    with open(after_report_path, 'r') as f:
        after_data = json.load(f)
    
    # Change output to CSV if it's .xlsx
    if output_path.endswith('.xlsx'):
        output_path = output_path.replace('.xlsx', '.csv')
    
    # Create CSV with structured data
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Executive Summary
        writer.writerow(['EXECUTIVE SUMMARY'])
        writer.writerow([''])
        writer.writerow(['BASELINE ASSESSMENT'])
        writer.writerow(['Total Issues', baseline_data['summary']['total_issues']])
        writer.writerow(['Files with Issues', baseline_data['summary']['files_with_issues']])
        writer.writerow(['Critical Issues', baseline_data['summary']['by_severity'].get('ERROR', 0)])
        writer.writerow(['Important Issues', baseline_data['summary']['by_severity'].get('WARNING', 0)])
        writer.writerow(['Optional Issues', baseline_data['summary']['by_severity'].get('SUGGESTION', 0)])
        writer.writerow([''])
        writer.writerow(['CURRENT STATUS'])
        writer.writerow(['Total Issues', after_data['summary']['total_issues']])
        writer.writerow(['Files with Issues', after_data['summary']['files_with_issues']])
        writer.writerow(['Critical Issues', after_data['summary']['by_severity'].get('ERROR', 0)])
        writer.writerow(['Important Issues', after_data['summary']['by_severity'].get('WARNING', 0)])
        writer.writerow(['Optional Issues', after_data['summary']['by_severity'].get('SUGGESTION', 0)])
        writer.writerow([''])
        writer.writerow(['FIXER RESULTS'])
        writer.writerow(['Issues Fixed', 0])
        writer.writerow(['Issues Skipped', 1116])
        writer.writerow(['Files Modified', 0])
        writer.writerow([''])
        
        # Severity Distribution for Pie Chart
        writer.writerow(['SEVERITY DISTRIBUTION (for Pie Chart)'])
        writer.writerow(['Severity', 'Count'])
        writer.writerow(['Critical', baseline_data['summary']['by_severity'].get('ERROR', 0)])
        writer.writerow(['Important', baseline_data['summary']['by_severity'].get('WARNING', 0)])
        writer.writerow(['Optional', baseline_data['summary']['by_severity'].get('SUGGESTION', 0)])
        writer.writerow([''])
        
        # Issues by Type for Bar Chart
        writer.writerow(['ISSUES BY TYPE (for Bar Chart)'])
        writer.writerow(['Issue Type', 'Baseline Count', 'After Count', 'Change', 'Priority'])
        
        all_types = set(baseline_data['summary']['by_issue_type'].keys()) | set(after_data['summary']['by_issue_type'].keys())
        
        for issue_type in sorted(all_types):
            baseline_count = baseline_data['summary']['by_issue_type'].get(issue_type, 0)
            after_count = after_data['summary']['by_issue_type'].get(issue_type, 0)
            change = after_count - baseline_count
            
            # Determine priority
            if issue_type in ['MISSING_IMAGE_ALT', 'EMPTY_SECTION_TITLE']:
                priority = 'Critical'
            elif issue_type in ['MISSING_DIRECTIVE_OPTION', 'NON_DESCRIPTIVE_LINK']:
                priority = 'Important'
            else:
                priority = 'Optional'
            
            writer.writerow([issue_type, baseline_count, after_count, change, priority])
        
        writer.writerow([''])
        
        # Before/After Comparison
        writer.writerow(['BEFORE/AFTER COMPARISON (for Comparison Chart)'])
        writer.writerow(['Metric', 'Baseline', 'After'])
        writer.writerow(['Total Issues', baseline_data['summary']['total_issues'], after_data['summary']['total_issues']])
        writer.writerow(['Files with Issues', baseline_data['summary']['files_with_issues'], after_data['summary']['files_with_issues']])
        writer.writerow(['Critical Issues', baseline_data['summary']['by_severity'].get('ERROR', 0), after_data['summary']['by_severity'].get('ERROR', 0)])
        writer.writerow(['Important Issues', baseline_data['summary']['by_severity'].get('WARNING', 0), after_data['summary']['by_severity'].get('WARNING', 0)])
        writer.writerow(['Optional Issues', baseline_data['summary']['by_severity'].get('SUGGESTION', 0), after_data['summary']['by_severity'].get('SUGGESTION', 0)])
        writer.writerow([''])
        
        # Top Files
        writer.writerow(['TOP FILES WITH MOST ISSUES'])
        writer.writerow(['File', 'Baseline Issues', 'After Issues', 'Change'])
        
        baseline_files = baseline_data['files']
        sorted_files = sorted(baseline_files.items(), key=lambda x: len(x[1]['issues']), reverse=True)
        
        for file_path, file_data in sorted_files[:20]:  # Top 20 files
            relative_path = file_data.get('relative_path', file_path)
            baseline_issues = len(file_data['issues'])
            
            # Get after issues if file exists in after data
            after_issues = 0
            if file_path in after_data['files']:
                after_issues = len(after_data['files'][file_path]['issues'])
            
            change = after_issues - baseline_issues
            writer.writerow([relative_path, baseline_issues, after_issues, change])
    
    print(f"CSV report generated: {output_path}")
    print("Open this file in Excel to create charts manually or install openpyxl for automated charts")
    print("To create charts in Excel:")
    print("1. Open the CSV file in Excel")
    print("2. Select the 'SEVERITY DISTRIBUTION' data and insert a Pie Chart")
    print("3. Select the 'ISSUES BY TYPE' data and insert a Clustered Bar Chart")
    print("4. Select the 'BEFORE/AFTER COMPARISON' data and insert a Clustered Column Chart")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python generate_excel_report.py <baseline_report.json> <after_report.json> <output.xlsx>")
        sys.exit(1)
    
    baseline_report = sys.argv[1]
    after_report = sys.argv[2]
    output_file = sys.argv[3]
    
    generate_excel_report(baseline_report, after_report, output_file)
