#!/usr/bin/env python3
"""
Structured Markdown Accessibility Reporting System
Creates categorized reports with clear next steps and fix recommendations for Markdown/mkdocs
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class StructuredReporterMD:
    """Creates structured, categorized accessibility reports for Markdown"""
    
    def __init__(self, report_path, output_dir):
        self.report_path = Path(report_path)
        self.output_dir = Path(output_dir)
        self.data = None
        self.issues_by_category = defaultdict(list)
        
    def load_data(self):
        """Load accessibility report data"""
        with open(self.report_path, 'r') as f:
            self.data = json.load(f)
        print(f"Loaded report with {self.data['summary']['total_issues']} issues")
    
    def categorize_issues(self):
        """Categorize issues by type and effort level"""
        category_mapping = {
            'HIGH_PRIORITY': ['MISSING_IMAGE_ALT', 'EMPTY_SECTION_TITLE'],
            'MEDIUM_PRIORITY': ['MISSING_DIRECTIVE_OPTION', 'NON_DESCRIPTIVE_LINK'],
            'LOW_PRIORITY': ['INVALID_CODE_LANGUAGE', 'INSECURE_EXTERNAL_LINK'],
            'OPTIONAL': ['BARE_URL', 'BARE_REF']
        }
        
        for file_path, file_data in self.data.get('files', {}).items():
            for issue in file_data.get('issues', []):
                for category, issue_types in category_mapping.items():
                    if issue['type'] in issue_types:
                        self.issues_by_category[category].append({
                            'file_path': file_path,
                            'relative_path': file_data.get('relative_path', file_path),
                            'line': issue['line'],
                            'type': issue['type'],
                            'severity': issue['severity'],
                            'message': issue['message'],
                            'suggestion': issue['suggestion'],
                            'context': issue.get('context', '')
                        })
                        break
    
    def generate_index(self):
        """Generate main index file"""
        content = f"""
================================================================================
OMNIA MARKDOWN ACCESSIBILITY VALIDATION REPORT - INDEX
================================================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Issues: {self.data['summary']['total_issues']}
Errors: {self.data['summary']['by_severity']['ERROR']}
Warnings: {self.data['summary']['by_severity']['WARNING']}
Suggestions: {self.data['summary']['by_severity']['SUGGESTION']}

AVAILABLE REPORTS
================================================================================
1. EXECUTIVE_SUMMARY.txt - High-level overview and quick statistics
2. ISSUES_BY_CATEGORY.txt - Detailed breakdown by issue type and priority
3. FIX_RECOMMENDATIONS.txt - Specific guidance for each issue type
4. WORKFLOW_GUIDE.txt - Step-by-step instructions for systematic fixing

QUICK START
================================================================================
1. Read EXECUTIVE_SUMMARY.txt for overall assessment
2. Check ISSUES_BY_CATEGORY.txt for detailed breakdown
3. Follow FIX_RECOMMENDATIONS.txt for specific guidance
4. Use WORKFLOW_GUIDE.txt for systematic fixing approach

NEXT STEPS
================================================================================
- Review high-priority issues first (missing alt text, empty sections)
- Address medium-priority issues (non-descriptive links, directive options)
- Consider low-priority improvements (code languages, secure links)
- Re-validate after fixes to track progress
================================================================================
"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(self.output_dir / 'INDEX.txt', 'w') as f:
            f.write(content)
        print("Generated: INDEX.txt")
    
    def generate_executive_summary(self):
        """Generate executive summary report"""
        content = f"""
================================================================================
EXECUTIVE SUMMARY - OMNIA MARKDOWN ACCESSIBILITY VALIDATION
================================================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW
--------------------------------------------------------------------------------
Total Issues Found: {self.data['summary']['total_issues']}
- Critical (ERROR): {self.data['summary']['by_severity']['ERROR']}
- Important (WARNING): {self.data['summary']['by_severity']['WARNING']}
- Optional (SUGGESTION): {self.data['summary']['by_severity']['SUGGESTION']}

Files Analyzed: {len(self.data.get('files', {}))}

PRIORITY BREAKDOWN
--------------------------------------------------------------------------------
"""
        category_counts = {cat: len(issues) for cat, issues in self.issues_by_category.items()}
        for category in ['HIGH_PRIORITY', 'MEDIUM_PRIORITY', 'LOW_PRIORITY', 'OPTIONAL']:
            count = category_counts.get(category, 0)
            content += f"{category.replace('_', ' ')}: {count} issues\n"
        
        content += f"""
KEY FINDINGS
--------------------------------------------------------------------------------
- Image accessibility issues require immediate attention
- Link descriptions need improvement for screen reader compatibility
- Code block language specification needs verification
- External links should use HTTPS for security

RECOMMENDATIONS
================================================================================
1. Address HIGH_PRIORITY issues first (alt text, section titles)
2. Fix MEDIUM_PRIORITY issues for better accessibility (links, directives)
3. Review LOW_PRIORITY improvements when time permits
4. Re-validate after fixes to measure improvement

ESTIMATED EFFORT
--------------------------------------------------------------------------------
Total Issues: {self.data['summary']['total_issues']}
Estimated Time: {self.data['summary']['total_issues'] * 2} minutes (assuming 2 min per issue)
Recommended Sessions: 3-4 focused sessions of 1-2 hours each
================================================================================
"""
        with open(self.output_dir / 'EXECUTIVE_SUMMARY.txt', 'w') as f:
            f.write(content)
        print("Generated: EXECUTIVE_SUMMARY.txt")
    
    def generate_issues_by_category(self):
        """Generate detailed issues breakdown by category"""
        content = """
================================================================================
ISSUES BY CATEGORY - OMNIA MARKDOWN ACCESSIBILITY VALIDATION
================================================================================
"""
        
        for category in ['HIGH_PRIORITY', 'MEDIUM_PRIORITY', 'LOW_PRIORITY', 'OPTIONAL']:
            issues = self.issues_by_category.get(category, [])
            content += f"\n{category.replace('_', ' ')} ({len(issues)} issues)\n"
            content += "-" * 80 + "\n"
            
            if not issues:
                content += "No issues in this category.\n"
                continue
            
            for issue in issues[:10]:  # Show first 10 issues per category
                content += f"File: {issue['relative_path']}\n"
                content += f"Line: {issue['line']}\n"
                content += f"Type: {issue['type']}\n"
                content += f"Message: {issue['message']}\n"
                content += f"Suggestion: {issue['suggestion']}\n"
                content += "\n"
            
            if len(issues) > 10:
                content += f"... and {len(issues) - 10} more issues in this category\n"
        
        content += "\n================================================================================\n"
        with open(self.output_dir / 'ISSUES_BY_CATEGORY.txt', 'w') as f:
            f.write(content)
        print("Generated: ISSUES_BY_CATEGORY.txt")
    
    def generate_fix_recommendations(self):
        """Generate specific fix recommendations"""
        content = """
================================================================================
FIX RECOMMENDATIONS - OMNIA MARKDOWN ACCESSIBILITY VALIDATION
================================================================================
MISSING IMAGE ALT TEXT
--------------------------------------------------------------------------------
Issue: Images missing alt attribute or empty alt text
Impact: Screen readers cannot describe images to users
Fix: Add descriptive alt text to all images
Markdown: ![Descriptive text](image-url)
HTML: <img src="image-url" alt="Descriptive text">
Priority: HIGH

EMPTY SECTION TITLES
--------------------------------------------------------------------------------
Issue: Markdown headers with no content after # symbols
Impact: Navigation breaks for screen readers
Fix: Add meaningful text after header symbols
Markdown: ## Section Title (not just ##)
Priority: HIGH

NON-DESCRIPTIVE LINKS
--------------------------------------------------------------------------------
Issue: Links with unclear text like "click here" or "read more"
Impact: Screen reader users don't know link destination
Fix: Use descriptive link text
Markdown: [Download the guide](link.html) (not [click here](link.html))
Priority: MEDIUM

INVALID CODE LANGUAGES
--------------------------------------------------------------------------------
Issue: Code blocks with unsupported language specification
Impact: No syntax highlighting, poor rendering
Fix: Use supported languages: python, bash, shell, json, yaml, etc.
Markdown: ```python (not ```bash title="Run on K8s")
Priority: LOW

INSECURE EXTERNAL LINKS
--------------------------------------------------------------------------------
Issue: External links using http:// instead of https://
Impact: Security warning in modern browsers
Fix: Use https:// for external links
Priority: LOW

BARE URLS
--------------------------------------------------------------------------------
Issue: URLs not formatted as links
Impact: Poor readability and accessibility
Fix: Format URLs as Markdown links
Markdown: [Link text](URL) (not just https://example.com)
Priority: OPTIONAL
================================================================================
"""
        with open(self.output_dir / 'FIX_RECOMMENDATIONS.txt', 'w') as f:
            f.write(content)
        print("Generated: FIX_RECOMMENDATIONS.txt")
    
    def generate_workflow_guide(self):
        """Generate step-by-step workflow guide"""
        content = """
================================================================================
WORKFLOW GUIDE - OMNIA MARKDOWN ACCESSIBILITY VALIDATION
================================================================================
PHASE 1: ASSESSMENT (COMPLETED)
--------------------------------------------------------------------------------
[OK] Initial validation completed
[OK] Issues identified and categorized
[OK] Reports generated

PHASE 2: AUTOMATIC FIXES
--------------------------------------------------------------------------------
1. Run the automatic fixer:
   python omnia_md_accessibility_fixer.py reports/baseline_validation/accessibility_report.json --auto-fix --auto-only

2. Review automatic fixes in Windsurf/Devin IDE
3. Commit automatic fixes

PHASE 3: MANUAL FIXES - HIGH PRIORITY
--------------------------------------------------------------------------------
1. Start with MISSING_IMAGE_ALT issues
   - Add descriptive alt text to images
   - Focus on key images first (diagrams, screenshots)

2. Fix EMPTY_SECTION_TITLE issues
   - Add meaningful text to empty headers
   - Ensure proper document structure

3. Address NON_DESCRIPTIVE_LINK issues
   - Rewrite link text to be descriptive
   - Use action-oriented language

PHASE 4: MANUAL FIXES - MEDIUM PRIORITY
--------------------------------------------------------------------------------
1. Fix MISSING_DIRECTIVE_OPTION issues
   - Add required options to Markdown elements
   - Ensure proper HTML attributes if applicable

2. Review code block language specifications
   - Use supported languages
   - Remove complex attributes from code blocks

PHASE 5: VALIDATION AND TRACKING
--------------------------------------------------------------------------------
1. Re-validate after manual fixes:
   python omnia_md_accessibility_validator.py ../docs -r -o json -f reports/current_status/accessibility_report_after.json

2. Generate comparison report to track progress

3. Review remaining issues in current status

4. Continue iterative fixing until acceptable level

PHASE 6: FINAL VALIDATION
--------------------------------------------------------------------------------
1. Final validation with all fixes applied
2. Generate comprehensive reports
3. Review with team for approval
4. Update documentation standards if needed

TIPS FOR EFFICIENT FIXING
--------------------------------------------------------------------------------
- Fix issues file by file to track progress
- Use IDE search/replace for similar issues
- Test changes in mkdocs preview
- Commit frequently to avoid losing work
- Use fixer for repetitive patterns
================================================================================
"""
        with open(self.output_dir / 'WORKFLOW_GUIDE.txt', 'w') as f:
            f.write(content)
        print("Generated: WORKFLOW_GUIDE.txt")
    
    def generate_all_reports(self):
        """Generate all structured reports"""
        self.load_data()
        self.categorize_issues()
        self.generate_index()
        self.generate_executive_summary()
        self.generate_issues_by_category()
        self.generate_fix_recommendations()
        self.generate_workflow_guide()
        print(f"\nAll reports generated in: {self.output_dir}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python structured_reporting_md.py <input_json> <output_directory>")
        sys.exit(1)
    
    report_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    reporter = StructuredReporterMD(report_path, output_dir)
    reporter.generate_all_reports()

if __name__ == "__main__":
    main()
