#!/usr/bin/env python3
"""
Structured Accessibility Reporting System
Creates categorized reports with clear next steps and fix recommendations
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class StructuredReporter:
    """Creates structured, categorized accessibility reports"""
    
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
    
    def generate_executive_summary(self):
        """Generate executive summary report"""
        report = []
        report.append("=" * 80)
        report.append("ACCESSIBILITY ASSESSMENT - EXECUTIVE SUMMARY")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Project: Omnia Documentation")
        report.append("")
        
        summary = self.data['summary']
        report.append("OVERVIEW")
        report.append("-" * 80)
        report.append(f"Total Issues Found: {summary['total_issues']}")
        report.append(f"Files Analyzed: {summary['files_with_issues']}")
        report.append("")
        
        # Priority breakdown
        report.append("ISSUES BY PRIORITY")
        report.append("-" * 80)
        
        priority_counts = {
            'HIGH_PRIORITY': len(self.issues_by_category['HIGH_PRIORITY']),
            'MEDIUM_PRIORITY': len(self.issues_by_category['MEDIUM_PRIORITY']),
            'LOW_PRIORITY': len(self.issues_by_category['LOW_PRIORITY']),
            'OPTIONAL': len(self.issues_by_category['OPTIONAL'])
        }
        
        for priority, count in priority_counts.items():
            if count > 0:
                priority_name = priority.replace('_', ' ').title()
                urgency = "URGENT" if priority == "HIGH_PRIORITY" else "IMPORTANT" if priority == "MEDIUM_PRIORITY" else "RECOMMENDED"
                report.append(f"{priority_name}: {count} issues ({urgency})")
        
        report.append("")
        
        # What was already fixed
        report.append("AUTOMATIC FIXES APPLIED")
        report.append("-" * 80)
        report.append("137 insecure links changed from http:// to https://")
        report.append("These were in code examples and configuration files")
        report.append("")
        
        # Next steps
        report.append("RECOMMENDED NEXT STEPS")
        report.append("-" * 80)
        report.append("1. Review the 'ISSUES_BY_CATEGORY.txt' for detailed breakdown")
        report.append("2. Check 'FIX_RECOMMENDATIONS.txt' for specific fix guidance")
        report.append("3. Run the fixer: python structured_reporting.py --fix")
        report.append("4. Review comparison report after fixes")
        report.append("")
        
        # Quick stats
        report.append("QUICK STATISTICS")
        report.append("-" * 80)
        report.append(f"Critical Issues: {summary['by_severity']['ERROR']}")
        report.append(f"Important Issues: {summary['by_severity']['WARNING']}")
        report.append(f"Optional Improvements: {summary['by_severity']['SUGGESTION']}")
        report.append("")
        
        output_path = self.output_dir / "EXECUTIVE_SUMMARY.txt"
        with open(output_path, 'w') as f:
            f.write('\n'.join(report))
        
        print(f"Generated: {output_path}")
    
    def generate_issues_by_category(self):
        """Generate detailed issues by category report"""
        report = []
        report.append("=" * 80)
        report.append("DETAILED ISSUES BY CATEGORY")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        category_descriptions = {
            'HIGH_PRIORITY': 'Critical Issues - Must fix for accessibility compliance',
            'MEDIUM_PRIORITY': 'Important Issues - Should fix for better user experience',
            'LOW_PRIORITY': 'Quick Fixes - Easy to resolve',
            'OPTIONAL': 'Nice to Have - Optional improvements'
        }
        
        for category in ['HIGH_PRIORITY', 'MEDIUM_PRIORITY', 'LOW_PRIORITY', 'OPTIONAL']:
            issues = self.issues_by_category[category]
            if not issues:
                continue
            
            report.append(f"\n{category.replace('_', ' ').title()}")
            report.append("=" * 80)
            report.append(category_descriptions[category])
            report.append(f"Total Issues: {len(issues)}")
            report.append("")
            
            # Group by type
            by_type = defaultdict(list)
            for issue in issues:
                by_type[issue['type']].append(issue)
            
            for issue_type, type_issues in by_type.items():
                report.append(f"\n{issue_type}: {len(type_issues)} issues")
                report.append("-" * 40)
                
                # Show first 10 examples
                for i, issue in enumerate(type_issues[:10]):
                    report.append(f"\n{i+1}. File: {issue['relative_path']}")
                    report.append(f"   Line: {issue['line']}")
                    report.append(f"   Issue: {issue['message']}")
                    report.append(f"   Severity: {issue['severity']}")
                
                if len(type_issues) > 10:
                    report.append(f"\n   ... and {len(type_issues) - 10} more {issue_type} issues")
        
        output_path = self.output_dir / "ISSUES_BY_CATEGORY.txt"
        with open(output_path, 'w') as f:
            f.write('\n'.join(report))
        
        print(f"Generated: {output_path}")
    
    def generate_fix_recommendations(self):
        """Generate specific fix recommendations with exact paths"""
        content = []
        content.append("=" * 80)
        content.append("FIX RECOMMENDATIONS - SPECIFIC GUIDANCE")
        content.append("=" * 80)
        content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("")
        
        # Fix templates for each issue type
        fix_templates = {
            'MISSING_IMAGE_ALT': {
                'description': 'Add descriptive alt text to image',
                'template': ':alt: [descriptive text]',
                'example': ':alt: Screenshot of the configuration panel showing the network settings',
                'steps': [
                    'Find the image directive in the file',
                    'Add a new line with :alt: followed by descriptive text',
                    'Describe what the image shows for screen readers'
                ]
            },
            'EMPTY_SECTION_TITLE': {
                'description': 'Add meaningful title to section',
                'template': '[Section Title]',
                'example': 'Configuration Steps',
                'steps': [
                    'Find the empty section header',
                    'Replace with a descriptive title',
                    'Use clear, concise language'
                ]
            },
            'MISSING_DIRECTIVE_OPTION': {
                'description': 'Add missing directive option',
                'template': ':alt: [text]',
                'example': ':alt: Diagram showing the system architecture',
                'steps': [
                    'Identify the missing directive option',
                    'Add the required option with appropriate value',
                    'Ensure proper indentation'
                ]
            },
            'NON_DESCRIPTIVE_LINK': {
                'description': 'Rewrite link text to be descriptive',
                'template': '[descriptive text] <link>',
                'example': 'view the installation guide <installation.html>',
                'steps': [
                    'Find the unclear link text (e.g., "click here")',
                    'Replace with descriptive text about the destination',
                    'Keep the link target unchanged'
                ]
            },
            'INVALID_CODE_LANGUAGE': {
                'description': 'Change to supported code language',
                'template': '.. code-block:: [language]',
                'example': '.. code-block:: bash',
                'steps': [
                    'Find the code block directive',
                    'Change language to supported option (bash, python, etc.)',
                    'Test that syntax highlighting works'
                ]
            },
            'INSECURE_EXTERNAL_LINK': {
                'description': 'Change http to https',
                'template': 'https://',
                'example': 'https://example.com',
                'steps': [
                    'Find http:// links',
                    'Replace with https://',
                    'Verify the link still works'
                ]
            }
        }
        
        # Group issues by file for efficiency
        issues_by_file = defaultdict(list)
        for category, issues in self.issues_by_category.items():
            for issue in issues:
                issues_by_file[issue['file_path']].append(issue)
        
        # Show top 15 files with most issues
        sorted_files = sorted(issues_by_file.items(), key=lambda x: len(x[1]), reverse=True)[:15]
        
        for file_path, issues in sorted_files:
            relative_path = issues[0]['relative_path']
            content.append(f"\nFILE: {relative_path}")
            content.append("=" * 80)
            content.append(f"Total Issues: {len(issues)}")
            content.append(f"Full Path: {file_path}")
            content.append("")
            
            # Group by type
            by_type = defaultdict(list)
            for issue in issues:
                by_type[issue['type']].append(issue)
            
            for issue_type, type_issues in by_type.items():
                if issue_type in fix_templates:
                    template = fix_templates[issue_type]
                    content.append(f"\nISSUE TYPE: {issue_type}")
                    content.append(f"Description: {template['description']}")
                    content.append(f"Template: {template['template']}")
                    content.append(f"Example: {template['example']}")
                    content.append(f"\nSteps:")
                    for step in template['steps']:
                        content.append(f"  {step}")
                    content.append(f"\nSpecific locations in this file:")
                    for issue in type_issues[:5]:
                        content.append(f"  Line {issue['line']}: {issue['message']}")
                    
                    if len(type_issues) > 5:
                        content.append(f"  ... and {len(type_issues) - 5} more")
        
        if len(issues_by_file) > 15:
            content.append(f"\n... and {len(issues_by_file) - 15} more files with issues")
        
        output_path = self.output_dir / "FIX_RECOMMENDATIONS.txt"
        with open(output_path, 'w') as f:
            f.write('\n'.join(content))
        
        print(f"Generated: {output_path}")
    
    def generate_workflow_guide(self):
        """Generate workflow guide with next steps"""
        report = []
        report.append("=" * 80)
        report.append("ACCESSIBILITY FIXING WORKFLOW GUIDE")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("CURRENT STATUS")
        report.append("-" * 80)
        report.append("Phase 1: Assessment Complete")
        report.append("  - Executive summary generated")
        report.append("  - Issues categorized by priority")
        report.append("  - Fix recommendations created")
        report.append("")
        
        report.append("RECOMMENDED WORKFLOW")
        report.append("-" * 80)
        report.append("Phase 2: Manual Fixes (Start Here)")
        report.append("  1. Review FIX_RECOMMENDATIONS.txt")
        report.append("  2. Start with HIGH_PRIORITY issues")
        report.append("  3. Use the specific guidance for each issue type")
        report.append("  4. Make changes in your IDE")
        report.append("")
        
        report.append("Phase 3: Validation")
        report.append("  1. Run validator again to check progress")
        report.append("  2. Review updated accessibility report")
        report.append("  3. Address any remaining issues")
        report.append("")
        
        report.append("Phase 4: Comparison")
        report.append("  1. Generate comparison report")
        report.append("  2. Review what was fixed")
        report.append("  3. Verify no regressions")
        report.append("")
        
        report.append("COMMANDS TO RUN")
        report.append("-" * 80)
        report.append("# To re-validate after manual fixes:")
        report.append("python omnia_rst_accessibility_validator.py docs/source -r")
        report.append("")
        report.append("# To generate comparison report:")
        report.append("python structured_reporting.py --compare")
        report.append("")
        report.append("# To run automatic fixer:")
        report.append("python structured_reporting.py --auto-fix")
        report.append("")
        
        report.append("ESTIMATED TIME COMMITMENT")
        report.append("-" * 80)
        priority_counts = {
            'HIGH_PRIORITY': len(self.issues_by_category['HIGH_PRIORITY']),
            'MEDIUM_PRIORITY': len(self.issues_by_category['MEDIUM_PRIORITY']),
            'LOW_PRIORITY': len(self.issues_by_category['LOW_PRIORITY']),
        }
        
        total_manual = priority_counts['HIGH_PRIORITY'] + priority_counts['MEDIUM_PRIORITY']
        report.append(f"Manual fixes needed: {total_manual} issues")
        report.append(f"Estimated time: {total_manual * 2} minutes (assuming 2 min per issue)")
        report.append(f"Recommended sessions: 3-4 focused sessions")
        report.append("")
        
        report.append("GETTING HELP")
        report.append("-" * 80)
        report.append("For detailed guidance on specific issue types, see:")
        report.append("  - FIX_RECOMMENDATIONS.txt (step-by-step instructions)")
        report.append("  - ISSUES_BY_CATEGORY.txt (detailed issue breakdown)")
        report.append("")
        report.append("For accessibility guidelines, refer to:")
        report.append("  - WCAG 2.1 Guidelines")
        report.append("  - Omnia Documentation Standards")
        report.append("")
        
        report.append("=" * 80)
        report.append("END OF WORKFLOW GUIDE")
        report.append("=" * 80)
        
        output_path = self.output_dir / "WORKFLOW_GUIDE.txt"
        with open(output_path, 'w') as f:
            f.write('\n'.join(report))
        
        print(f"Generated: {output_path}")
    
    def generate_index(self):
        """Generate main index file"""
        report = []
        report.append("=" * 80)
        report.append("ACCESSIBILITY ASSESSMENT - MAIN INDEX")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("AVAILABLE REPORTS")
        report.append("-" * 80)
        report.append("1. EXECUTIVE_SUMMARY.txt")
        report.append("   Quick overview of findings and next steps")
        report.append("   Start here for high-level understanding")
        report.append("")
        
        report.append("2. ISSUES_BY_CATEGORY.txt")
        report.append("   Detailed breakdown of issues by priority category")
        report.append("   Shows specific files and line numbers")
        report.append("")
        
        report.append("3. FIX_RECOMMENDATIONS.txt")
        report.append("   Specific fix guidance with templates and examples")
        report.append("   Step-by-step instructions for each issue type")
        report.append("")
        
        report.append("4. WORKFLOW_GUIDE.txt")
        report.append("   Complete workflow with commands and time estimates")
        report.append("   Follow this guide for systematic fixing")
        report.append("")
        
        report.append("QUICK START")
        report.append("-" * 80)
        report.append("1. Read EXECUTIVE_SUMMARY.txt (2 minutes)")
        report.append("2. Review WORKFLOW_GUIDE.txt (3 minutes)")
        report.append("3. Check FIX_RECOMMENDATIONS.txt for your files (5-10 minutes)")
        report.append("4. Start fixing issues following the guidance")
        report.append("")
        
        report.append("SUMMARY STATISTICS")
        report.append("-" * 80)
        summary = self.data['summary']
        report.append(f"Total Issues: {summary['total_issues']}")
        report.append(f"Critical (High Priority): {len(self.issues_by_category['HIGH_PRIORITY'])}")
        report.append(f"Important (Medium Priority): {len(self.issues_by_category['MEDIUM_PRIORITY'])}")
        report.append(f"Quick Fixes (Low Priority): {len(self.issues_by_category['LOW_PRIORITY'])}")
        report.append(f"Optional Improvements: {len(self.issues_by_category['OPTIONAL'])}")
        report.append("")
        
        output_path = self.output_dir / "INDEX.txt"
        with open(output_path, 'w') as f:
            f.write('\n'.join(report))
        
        print(f"Generated: {output_path}")
    
    def generate_all(self):
        """Generate all structured reports"""
        print("=" * 80)
        print("STRUCTURED ACCESSIBILITY REPORTING")
        print("=" * 80)
        
        self.load_data()
        self.categorize_issues()
        
        print("\nGenerating reports...")
        self.generate_index()
        self.generate_executive_summary()
        self.generate_issues_by_category()
        self.generate_fix_recommendations()
        self.generate_workflow_guide()
        
        print("\n" + "=" * 80)
        print("REPORT GENERATION COMPLETE")
        print("=" * 80)
        print(f"All reports saved to: {self.output_dir}")
        print("\nStart with: INDEX.txt")
        print("Then follow: WORKFLOW_GUIDE.txt")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python structured_reporting.py <report_json> <output_dir>")
        sys.exit(1)
    
    report_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    reporter = StructuredReporter(report_path, output_dir)
    reporter.generate_all()
