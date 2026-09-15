#!/usr/bin/env python3
"""
Comparison Report Generator for Markdown Accessibility
Compares baseline and current status accessibility reports
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class ComparisonReporterMD:
    """Generates comparison reports between baseline and current status"""
    
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
    
    def generate_comparison(self):
        """Generate comparison report"""
        baseline_total = self.baseline_data['summary']['total_issues']
        after_total = self.after_data['summary']['total_issues']
        fixed_count = baseline_total - after_total
        improvement_percent = (fixed_count / baseline_total * 100) if baseline_total > 0 else 0
        
        content = f"""
================================================================================
OMNIA MARKDOWN ACCESSIBILITY COMPARISON REPORT
================================================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW
--------------------------------------------------------------------------------
Baseline Issues: {baseline_total}
Current Issues: {after_total}
Issues Fixed: {fixed_count}
Improvement: {improvement_percent:.1f}%

SEVERITY COMPARISON
--------------------------------------------------------------------------------
                      Baseline    Current    Change
Errors:               {self.baseline_data['summary']['by_severity']['ERROR']:>8}    {self.after_data['summary']['by_severity']['ERROR']:>8}    {self.baseline_data['summary']['by_severity']['ERROR'] - self.after_data['summary']['by_severity']['ERROR']:>6}
Warnings:             {self.baseline_data['summary']['by_severity']['WARNING']:>8}    {self.after_data['summary']['by_severity']['WARNING']:>8}    {self.baseline_data['summary']['by_severity']['WARNING'] - self.after_data['summary']['by_severity']['WARNING']:>6}
Suggestions:          {self.baseline_data['summary']['by_severity']['SUGGESTION']:>8}    {self.after_data['summary']['by_severity']['SUGGESTION']:>8}    {self.baseline_data['summary']['by_severity']['SUGGESTION'] - self.after_data['summary']['by_severity']['SUGGESTION']:>6}

ISSUES FIXED BY TYPE
--------------------------------------------------------------------------------
"""
        
        # Calculate issues fixed by type
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
            if fixed > 0:
                content += f"{issue_type}: {fixed} fixed (from {baseline_count} to {after_count})\n"
        
        content += """
REMAINING ISSUES BY PRIORITY
--------------------------------------------------------------------------------
"""
        
        # Calculate remaining issues by priority
        category_mapping = {
            'HIGH_PRIORITY': ['MISSING_IMAGE_ALT', 'EMPTY_SECTION_TITLE'],
            'MEDIUM_PRIORITY': ['MISSING_DIRECTIVE_OPTION', 'NON_DESCRIPTIVE_LINK'],
            'LOW_PRIORITY': ['INVALID_CODE_LANGUAGE', 'INSECURE_EXTERNAL_LINK'],
            'OPTIONAL': ['BARE_URL', 'BARE_REF']
        }
        
        remaining_by_priority = defaultdict(int)
        for file_data in self.after_data.get('files', {}).values():
            for issue in file_data.get('issues', []):
                for category, issue_types in category_mapping.items():
                    if issue['type'] in issue_types:
                        remaining_by_priority[category] += 1
                        break
        
        for priority in ['HIGH_PRIORITY', 'MEDIUM_PRIORITY', 'LOW_PRIORITY', 'OPTIONAL']:
            count = remaining_by_priority.get(priority, 0)
            content += f"{priority.replace('_', ' ')}: {count} remaining issues\n"
        
        content += """
RECOMMENDATIONS
--------------------------------------------------------------------------------
"""
        if after_total > 0:
            content += f"- {after_total} issues still need to be addressed\n"
            content += "- Focus on HIGH_PRIORITY issues first\n"
            content += "- Continue iterative fixing process\n"
            content += "- Re-validate after manual fixes\n"
        else:
            content += "- All accessibility issues have been resolved!\n"
            content += "- Documentation is now fully accessible\n"
            content += "- Consider running periodic checks\n"
        
        content += """
FIXER EFFECTIVENESS ANALYSIS
--------------------------------------------------------------------------------
"""
        if fixed_count > 0:
            content += f"- Successfully fixed {fixed_count} issues automatically\n"
            content += f"- {improvement_percent:.1f}% improvement in accessibility score\n"
            content += "- Automatic fixer is working effectively\n"
        else:
            content += "- No automatic fixes were applied\n"
            content += "- Manual fixing required for remaining issues\n"
        
        content += "\n================================================================================\n"
        
        with open(self.output_path, 'w') as f:
            f.write(content)
        print(f"Comparison report generated: {self.output_path}")

def main():
    if len(sys.argv) != 4:
        print("Usage: python generate_comparison_md.py <baseline_json> <after_json> <output_txt>")
        sys.exit(1)
    
    baseline_path = sys.argv[1]
    after_path = sys.argv[2]
    output_path = sys.argv[3]
    
    reporter = ComparisonReporterMD(baseline_path, after_path, output_path)
    reporter.load_reports()
    reporter.generate_comparison()

if __name__ == "__main__":
    main()
