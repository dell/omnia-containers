#!/usr/bin/env python3
"""
Unfixed Issues Report Generator for Markdown Accessibility
Generates detailed report of unfixed accessibility issues requiring manual intervention
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class UnfixedIssuesReporterMD:
    """Generates detailed report of unfixed accessibility issues"""
    
    def __init__(self, after_path, output_path):
        self.after_path = Path(after_path)
        self.output_path = Path(output_path)
        self.after_data = None
        self.data = None  # For compatibility with report generation
        
    def load_report(self):
        """Load current status report"""
        with open(self.after_path, 'r') as f:
            self.after_data = json.load(f)
            self.data = self.after_data  # For compatibility with report generation
        print(f"Loaded current status report: {self.after_data['summary']['total_issues']} issues")
    
    def generate_unfixed_report(self):
        """Generate detailed unfixed issues report"""
        content = f"""
================================================================================
UNFIXED MARKDOWN ACCESSIBILITY ISSUES REPORT
================================================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Remaining Issues: {self.data['summary']['total_issues']}
- Errors: {self.data['summary']['by_severity']['ERROR']}
- Warnings: {self.data['summary']['by_severity']['WARNING']}
- Suggestions: {self.data['summary']['by_severity']['SUGGESTION']}

OVERVIEW
--------------------------------------------------------------------------------
This report details all accessibility issues that remain after automatic fixes.
These issues require manual intervention to resolve.

UNFIXED ISSUES BY SEVERITY
================================================================================

"""
        
        # Group issues by severity
        by_severity = defaultdict(list)
        for file_path, file_data in self.data.get('files', {}).items():
            for issue in file_data.get('issues', []):
                by_severity[issue['severity']].append({
                    'file_path': file_path,
                    'line': issue['line'],
                    'type': issue['type'],
                    'message': issue['message'],
                    'suggestion': issue['suggestion'],
                    'context': issue.get('context', '')
                })
        
        for severity in ['ERROR', 'WARNING', 'SUGGESTION']:
            issues = by_severity.get(severity, [])
            content += f"{severity} ({len(issues)} issues)\n"
            content += "-" * 80 + "\n"
            
            if not issues:
                content += "No issues in this severity level.\n"
                content += "\n"
                continue
            
            for issue in issues:
                content += f"File: {issue['file_path']}\n"
                content += f"Line: {issue['line']}\n"
                content += f"Type: {issue['type']}\n"
                content += f"Message: {issue['message']}\n"
                content += f"Suggestion: {issue['suggestion']}\n"
                if issue['context']:
                    content += f"Context: {issue['context']}\n"
                content += "\n"
        
        content += """
UNFIXED ISSUES BY TYPE
================================================================================
"""
        
        # Group issues by type
        by_type = defaultdict(list)
        for file_path, file_data in self.data.get('files', {}).items():
            for issue in file_data.get('issues', []):
                by_type[issue['type']].append({
                    'file_path': file_path,
                    'line': issue['line'],
                    'message': issue['message'],
                    'suggestion': issue['suggestion']
                })
        
        for issue_type in sorted(by_type.keys()):
            issues = by_type[issue_type]
            content += f"{issue_type} ({len(issues)} issues)\n"
            content += "-" * 80 + "\n"
            
            for issue in issues[:5]:  # Show first 5 examples
                content += f"  {issue['file_path']}:{issue['line']} - {issue['message']}\n"
            
            if len(issues) > 5:
                content += f"  ... and {len(issues) - 5} more\n"
            
            content += "\n"
        
        content += """
QUICK FIX RECOMMENDATIONS WITH EFFORT ESTIMATES
================================================================================

MISSING IMAGE ALT TEXT (HIGH PRIORITY)
--------------------------------------------------------------------------------
Effort: Medium (5-10 minutes per image)
Steps:
1. Identify each image in the file
2. Add descriptive alt text: ![Descriptive text](image-url)
3. For complex images, consider adding detailed descriptions
4. Test with screen reader to verify effectiveness

EMPTY SECTION TITLES (HIGH PRIORITY)
--------------------------------------------------------------------------------
Effort: Low (2-5 minutes per section)
Steps:
1. Find empty headers (just # symbols with no text)
2. Add meaningful section title
3. Ensure title describes the content below
4. Follow proper heading hierarchy

NON-DESCRIPTIVE LINKS (MEDIUM PRIORITY)
--------------------------------------------------------------------------------
Effort: Low (3-5 minutes per link)
Steps:
1. Find links with text like "click here" or "read more"
2. Rewrite link text to describe destination
3. Use action-oriented language
4. Keep link text concise (under 100 characters)

INVALID CODE LANGUAGES (LOW PRIORITY)
--------------------------------------------------------------------------------
Effort: Low (1-2 minutes per code block)
Steps:
1. Identify code blocks with unsupported languages
2. Use supported languages: python, bash, shell, json, yaml, etc.
3. Remove complex attributes from code blocks
4. Test syntax highlighting in mkdocs preview

INSECURE EXTERNAL LINKS (LOW PRIORITY)
--------------------------------------------------------------------------------
Effort: Low (1 minute per link)
Steps:
1. Find http:// links (non-localhost)
2. Change to https:// where possible
3. Verify the site supports HTTPS
4. Test link still works after change

BARE URLS (OPTIONAL)
--------------------------------------------------------------------------------
Effort: Low (2-3 minutes per URL)
Steps:
1. Find URLs not formatted as links
2. Format as Markdown links: [text](URL)
3. Use descriptive link text
4. Test link functionality

PRIORITIZED FIXING APPROACH
================================================================================
Phase 1 (Critical - First 2 hours):
- Fix all MISSING_IMAGE_ALT issues
- Fix all EMPTY_SECTION_TITLE issues

Phase 2 (Important - Next 2 hours):
- Fix all NON_DESCRIPTIVE_LINK issues
- Fix MISSING_DIRECTIVE_OPTION issues

Phase 3 (Improvements - Final 1-2 hours):
- Fix INVALID_CODE_LANGUAGE issues
- Fix INSECURE_EXTERNAL_LINK issues
- Consider BARE_URL improvements if time permits

TOTAL ESTIMATED EFFORT
--------------------------------------------------------------------------------
Total Issues: {self.data['summary']['total_issues']}
Estimated Time: {self.data['summary']['total_issues'] * 3} minutes (assuming 3 min per issue)
Recommended Sessions: 3-4 focused sessions of 1-2 hours each

NEXT STEPS
================================================================================
1. Start with HIGH_PRIORITY issues (alt text, section titles)
2. Work systematically through files to track progress
3. Test changes in mkdocs preview
4. Re-validate after manual fixes
5. Continue iterative fixing until acceptable level
================================================================================
"""
        
        with open(self.output_path, 'w') as f:
            f.write(content)
        print(f"Unfixed issues report generated: {self.output_path}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python generate_unfixed_report_md.py <after_json> <output_txt>")
        sys.exit(1)
    
    after_path = sys.argv[1]
    output_path = sys.argv[2]
    
    reporter = UnfixedIssuesReporterMD(after_path, output_path)
    reporter.load_report()
    reporter.generate_unfixed_report()

if __name__ == "__main__":
    main()
