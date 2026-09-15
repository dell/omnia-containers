#!/usr/bin/env python3
"""
Excel/CSV Report Generator for Markdown Accessibility
Generates CSV report with structured data for Excel visualizations
"""

import json
import sys
import csv
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class ExcelReporterMD:
    """Generates CSV reports suitable for Excel import"""
    
    def __init__(self, baseline_path, after_path, output_path):
        self.baseline_path = Path(baseline_path)
        self.after_path = Path(after_path)
        self.output_path = Path(output_path)
        self.baseline_data = None
        self.after_data = None
        
    def load_reports(self):
        """Load both baseline and current status reports"""
        with open(self.baseline_path, 'r') as f:
            self.baseline_data = json.load(f)
        print(f"Loaded baseline report: {self.baseline_data['summary']['total_issues']} issues")
        
        with open(self.after_path, 'r') as f:
            self.after_data = json.load(f)
        print(f"Loaded current status report: {self.after_data['summary']['total_issues']} issues")
    
    def generate_csv_report(self):
        """Generate CSV report with structured data for Excel"""
        with open(self.output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write summary section
            writer.writerow(['OMNIA MARKDOWN ACCESSIBILITY EXCEL REPORT'])
            writer.writerow(['Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])
            
            # Summary statistics
            writer.writerow(['SUMMARY STATISTICS'])
            writer.writerow(['Metric', 'Baseline', 'Current', 'Change'])
            writer.writerow(['Total Issues', self.baseline_data['summary']['total_issues'], 
                           self.after_data['summary']['total_issues'],
                           self.baseline_data['summary']['total_issues'] - self.after_data['summary']['total_issues']])
            writer.writerow(['Errors', self.baseline_data['summary']['by_severity']['ERROR'], 
                           self.after_data['summary']['by_severity']['ERROR'],
                           self.baseline_data['summary']['by_severity']['ERROR'] - self.after_data['summary']['by_severity']['ERROR']])
            writer.writerow(['Warnings', self.baseline_data['summary']['by_severity']['WARNING'], 
                           self.after_data['summary']['by_severity']['WARNING'],
                           self.baseline_data['summary']['by_severity']['WARNING'] - self.after_data['summary']['by_severity']['WARNING']])
            writer.writerow(['Suggestions', self.baseline_data['summary']['by_severity']['SUGGESTION'], 
                           self.after_data['summary']['by_severity']['SUGGESTION'],
                           self.baseline_data['summary']['by_severity']['SUGGESTION'] - self.after_data['summary']['by_severity']['SUGGESTION']])
            writer.writerow([])
            
            # Issue type breakdown
            writer.writerow(['ISSUE TYPE BREAKDOWN'])
            writer.writerow(['Issue Type', 'Baseline Count', 'Current Count', 'Fixed', 'Priority'])
            
            priority_mapping = {
                'MISSING_IMAGE_ALT': 'HIGH',
                'EMPTY_SECTION_TITLE': 'HIGH',
                'MISSING_DIRECTIVE_OPTION': 'MEDIUM',
                'NON_DESCRIPTIVE_LINK': 'MEDIUM',
                'INVALID_CODE_LANGUAGE': 'LOW',
                'INSECURE_EXTERNAL_LINK': 'LOW',
                'BARE_URL': 'OPTIONAL',
                'BARE_REF': 'OPTIONAL'
            }
            
            baseline_by_type = defaultdict(int)
            after_by_type = defaultdict(int)
            
            for file_data in self.baseline_data.get('files', {}).values():
                for issue in file_data.get('issues', []):
                    baseline_by_type[issue['type']] += 1
            
            for file_data in self.after_data.get('files', {}).values():
                for issue in file_data.get('issues', []):
                    after_by_type[issue['type']] += 1
            
            for issue_type in sorted(set(baseline_by_type.keys()) | set(after_by_type.keys())):
                baseline_count = baseline_by_type.get(issue_type, 0)
                after_count = after_by_type.get(issue_type, 0)
                fixed = baseline_count - after_count
                priority = priority_mapping.get(issue_type, 'UNKNOWN')
                writer.writerow([issue_type, baseline_count, after_count, fixed, priority])
            
            writer.writerow([])
            
            # File-level statistics
            writer.writerow(['FILE-LEVEL STATISTICS'])
            writer.writerow(['File Path', 'Baseline Issues', 'Current Issues', 'Fixed', 'Percentage Fixed'])
            
            file_stats = []
            for file_path in set(self.baseline_data.get('files', {}).keys()) | set(self.after_data.get('files', {}).keys()):
                baseline_count = len(self.baseline_data.get('files', {}).get(file_path, {}).get('issues', []))
                after_count = len(self.after_data.get('files', {}).get(file_path, {}).get('issues', []))
                fixed = baseline_count - after_count
                percent_fixed = (fixed / baseline_count * 100) if baseline_count > 0 else 0
                file_stats.append({
                    'file': file_path,
                    'baseline': baseline_count,
                    'current': after_count,
                    'fixed': fixed,
                    'percent': percent_fixed
                })
            
            # Sort by baseline count
            file_stats.sort(key=lambda x: x['baseline'], reverse=True)
            for file_stat in file_stats:
                writer.writerow([file_stat['file'], file_stat['baseline'], 
                               file_stat['current'], file_stat['fixed'], 
                               f"{file_stat['percent']:.1f}%"])
            
            writer.writerow([])
            
            # Detailed issue data for pivot tables
            writer.writerow(['DETAILED ISSUE DATA'])
            writer.writerow(['File', 'Line', 'Issue Type', 'Severity', 'Message', 'Status', 'Priority'])
            
            for file_path, file_data in self.after_data.get('files', {}).items():
                for issue in file_data.get('issues', []):
                    priority = priority_mapping.get(issue['type'], 'UNKNOWN')
                    writer.writerow([file_path, issue['line'], issue['type'], 
                                   issue['severity'], issue['message'], 'Remaining', priority])
            
            writer.writerow([])
            
            # Severity breakdown for charts
            writer.writerow(['SEVERITY BREAKDOWN FOR CHARTS'])
            writer.writerow(['Severity', 'Baseline', 'Current', 'Change'])
            writer.writerow(['ERROR', self.baseline_data['summary']['by_severity']['ERROR'], 
                           self.after_data['summary']['by_severity']['ERROR'],
                           self.baseline_data['summary']['by_severity']['ERROR'] - self.after_data['summary']['by_severity']['ERROR']])
            writer.writerow(['WARNING', self.baseline_data['summary']['by_severity']['WARNING'], 
                           self.after_data['summary']['by_severity']['WARNING'],
                           self.baseline_data['summary']['by_severity']['WARNING'] - self.after_data['summary']['by_severity']['WARNING']])
            writer.writerow(['SUGGESTION', self.baseline_data['summary']['by_severity']['SUGGESTION'], 
                           self.after_data['summary']['by_severity']['SUGGESTION'],
                           self.baseline_data['summary']['by_severity']['SUGGESTION'] - self.after_data['summary']['by_severity']['SUGGESTION']])
            
            writer.writerow([])
            writer.writerow(['END OF REPORT'])
        
        print(f"CSV report generated: {self.output_path}")

def main():
    if len(sys.argv) != 4:
        print("Usage: python generate_excel_report_md.py <baseline_json> <after_json> <output_csv>")
        sys.exit(1)
    
    baseline_path = sys.argv[1]
    after_path = sys.argv[2]
    output_path = sys.argv[3]
    
    reporter = ExcelReporterMD(baseline_path, after_path, output_path)
    reporter.load_reports()
    reporter.generate_csv_report()

if __name__ == "__main__":
    main()
