#!/usr/bin/env python3
"""
Generate detailed report of unfixed accessibility issues
"""

import json
import sys
from datetime import datetime
from collections import defaultdict

def generate_unfixed_report(report_path, output_path):
    """Generate a detailed report of unfixed issues"""
    
    with open(report_path, 'r') as f:
        data = json.load(f)
    
    report = []
    report.append("=" * 80)
    report.append("DETAILED UNFIXED ACCESSIBILITY ISSUES REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Summary
    summary = data.get('summary', {})
    report.append("SUMMARY:")
    report.append("-" * 80)
    report.append(f"Total Issues: {summary.get('total_issues', 0)}")
    report.append(f"Files with Issues: {summary.get('files_with_issues', 0)}")
    report.append("")
    
    by_severity = summary.get('by_severity', {})
    report.append("By Severity:")
    for severity, count in by_severity.items():
        report.append(f"  {severity}: {count}")
    report.append("")
    
    by_type = summary.get('by_issue_type', {})
    report.append("By Issue Type:")
    for issue_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
        report.append(f"  {issue_type}: {count}")
    report.append("")
    
    # Group issues by type for detailed listing
    issues_by_type = defaultdict(list)
    
    for file_path, file_data in data.get('files', {}).items():
        for issue in file_data.get('issues', []):
            issues_by_type[issue['type']].append({
                'file': file_path,
                'relative_path': file_data.get('relative_path', file_path),
                'line': issue['line'],
                'severity': issue['severity'],
                'message': issue['message'],
                'suggestion': issue['suggestion'],
                'context': issue.get('context', '')
            })
    
    # Detailed issues by type (focusing on ERROR and WARNING first)
    report.append("=" * 80)
    report.append("DETAILED ISSUES BY TYPE (ERROR & WARNING)")
    report.append("=" * 80)
    report.append("")
    
    priority_order = ['ERROR', 'WARNING', 'SUGGESTION']
    
    for issue_type in sorted(issues_by_type.keys()):
        issues = issues_by_type[issue_type]
        
        # Filter by priority
        error_issues = [i for i in issues if i['severity'] == 'ERROR']
        warning_issues = [i for i in issues if i['severity'] == 'WARNING']
        suggestion_issues = [i for i in issues if i['severity'] == 'SUGGESTION']
        
        if error_issues or warning_issues:
            report.append(f"\n{issue_type} ({len(issues)} total issues)")
            report.append("-" * 80)
            
            if error_issues:
                report.append(f"\nERRORS ({len(error_issues)}):")
                for i, issue in enumerate(error_issues[:20]):  # Limit to first 20 per type
                    report.append(f"\n  {i+1}. File: {issue['relative_path']}")
                    report.append(f"     Line: {issue['line']}")
                    report.append(f"     Message: {issue['message']}")
                    report.append(f"     Suggestion: {issue['suggestion']}")
                    if issue['context']:
                        report.append(f"     Context: {issue['context'][:100]}...")
                
                if len(error_issues) > 20:
                    report.append(f"\n  ... and {len(error_issues) - 20} more ERROR issues")
            
            if warning_issues:
                report.append(f"\nWARNINGS ({len(warning_issues)}):")
                for i, issue in enumerate(warning_issues[:20]):  # Limit to first 20 per type
                    report.append(f"\n  {i+1}. File: {issue['relative_path']}")
                    report.append(f"     Line: {issue['line']}")
                    report.append(f"     Message: {issue['message']}")
                    report.append(f"     Suggestion: {issue['suggestion']}")
                    if issue['context']:
                        report.append(f"     Context: {issue['context'][:100]}...")
                
                if len(warning_issues) > 20:
                    report.append(f"\n  ... and {len(warning_issues) - 20} more WARNING issues")
    
    # Quick fix recommendations
    report.append("\n" + "=" * 80)
    report.append("QUICK FIX RECOMMENDATIONS")
    report.append("=" * 80)
    report.append("")
    
    quick_fixes = {
        'INVALID_CODE_LANGUAGE': {
            'effort': 'LOW',
            'description': 'Change unsupported code languages to supported ones',
            'example': 'Change "text" to "bash" or "python"'
        },
        'INSECURE_EXTERNAL_LINK': {
            'effort': 'LOW', 
            'description': 'Change http:// to https:// in URLs',
            'example': 'Already automated, but some may need manual review'
        },
        'NON_DESCRIPTIVE_LINK': {
            'effort': 'MEDIUM',
            'description': 'Rewrite link text to be descriptive',
            'example': 'Change "click here" to "view the installation guide"'
        },
        'MISSING_DIRECTIVE_OPTION': {
            'effort': 'MEDIUM',
            'description': 'Add missing directive options like :alt: for images',
            'example': 'Add :alt: Descriptive text to image directives'
        },
        'EMPTY_SECTION_TITLE': {
            'effort': 'HIGH',
            'description': 'Add descriptive titles to empty sections',
            'example': 'Replace empty title with meaningful section name'
        },
        'MISSING_IMAGE_ALT': {
            'effort': 'HIGH',
            'description': 'Add descriptive alt text to all images',
            'example': 'Add :alt: Screenshot of the configuration panel'
        }
    }
    
    for issue_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
        if issue_type in quick_fixes and count > 0:
            info = quick_fixes[issue_type]
            report.append(f"\n{issue_type} ({count} issues) - {info['effort']} EFFORT:")
            report.append(f"  {info['description']}")
            report.append(f"  Example: {info['example']}")
    
    report.append("\n" + "=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(report))
    
    print(f"Detailed unfixed issues report saved to: {output_path}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python generate_unfixed_report.py <input_json> <output_txt>")
        sys.exit(1)
    
    input_json = sys.argv[1]
    output_txt = sys.argv[2]
    generate_unfixed_report(input_json, output_txt)
