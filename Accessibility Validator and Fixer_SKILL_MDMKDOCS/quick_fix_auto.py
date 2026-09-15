#!/usr/bin/env python3
"""
Automatic Quick Fixer for High-Impact, Low-Effort Accessibility Issues
Runs automatically without user input - focuses on safe, batch fixes
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class AutoQuickFixer:
    """Automatic fixer for safe, batch fixes"""
    
    def __init__(self, report_path, docs_path):
        self.report_path = Path(report_path)
        self.docs_path = Path(docs_path)
        self.issues = []
        self.fixes_applied = []
        self.manual_review_items = []
        
    def load_report(self):
        """Load and categorize issues"""
        with open(self.report_path, 'r') as f:
            data = json.load(f)
        
        # Categorize issues
        for file_path, file_data in data.get('files', {}).items():
            for issue in file_data.get('issues', []):
                self.issues.append({
                    'file_path': file_path,
                    'relative_path': file_data.get('relative_path', file_path),
                    'line': issue['line'],
                    'type': issue['type'],
                    'severity': issue['severity'],
                    'message': issue['message'],
                    'suggestion': issue['suggestion'],
                    'context': issue.get('context', '')
                })
        
        print(f"Loaded {len(self.issues)} total issues from report")
    
    def apply_safe_fixes(self):
        """Apply safe automatic fixes"""
        
        # 1. Fix INVALID_CODE_LANGUAGE (safe batch fix)
        self._fix_code_languages()
        
        # 2. Fix INSECURE_EXTERNAL_LINK (safe batch fix)
        self._fix_insecure_links()
        
        # 3. Generate manual review list for NON_DESCRIPTIVE_LINK
        self._prepare_manual_review_list()
    
    def _fix_code_languages(self):
        """Batch fix invalid code languages"""
        code_issues = [i for i in self.issues if i['type'] == 'INVALID_CODE_LANGUAGE']
        if not code_issues:
            return
        
        print(f"\n{'='*80}")
        print("AUTO-FIXING INVALID CODE LANGUAGES")
        print(f"{'='*80}")
        print(f"Total issues: {len(code_issues)}")
        
        # Strategy: Replace 'text' with 'bash' (most common for command examples)
        # Replace 'csv' with 'bash' (for data files)
        replacements = {
            'text': 'bash',
            'csv': 'bash'
        }
        
        files_modified = set()
        
        for issue in code_issues:
            file_path = Path(issue['file_path'])
            if not file_path.exists():
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Determine current language
                current_lang = 'text'
                match = re.search(r"'(\w+)'", issue['message'])
                if match:
                    current_lang = match.group(1)
                
                if current_lang in replacements:
                    new_lang = replacements[current_lang]
                    pattern = rf'(\.\. code-block::\s+){re.escape(current_lang)}(\s|$)'
                    replacement = rf'\1{new_lang}\2'
                    new_content = re.sub(pattern, replacement, content)
                    
                    if new_content != content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        files_modified.add(str(file_path))
                        self.fixes_applied.append({
                            'file': issue['relative_path'],
                            'line': issue['line'],
                            'type': issue['type'],
                            'change': f"Changed '{current_lang}' to '{new_lang}'"
                        })
            except Exception as e:
                print(f"Error fixing {file_path}: {e}")
        
        print(f"[OK] Fixed {len(files_modified)} files")
        print(f"  Replacements made: {len([f for f in self.fixes_applied if f['type'] == 'INVALID_CODE_LANGUAGE'])}")
    
    def _fix_insecure_links(self):
        """Batch fix insecure external links"""
        link_issues = [i for i in self.issues if i['type'] == 'INSECURE_EXTERNAL_LINK']
        if not link_issues:
            return
        
        print(f"\n{'='*80}")
        print("AUTO-FIXING INSECURE EXTERNAL LINKS")
        print(f"{'='*80}")
        print(f"Total issues: {len(link_issues)}")
        
        files_modified = set()
        
        for issue in link_issues:
            file_path = Path(issue['file_path'])
            if not file_path.exists():
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace http:// with https://
                new_content = re.sub(r'http://', 'https://', content)
                
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    files_modified.add(str(file_path))
                    self.fixes_applied.append({
                        'file': issue['relative_path'],
                        'line': issue['line'],
                        'type': issue['type'],
                        'change': "Changed http:// to https://"
                    })
            except Exception as e:
                print(f"Error fixing {file_path}: {e}")
        
        print(f"[OK] Fixed {len(files_modified)} files")
        print(f"  Replacements made: {len([f for f in self.fixes_applied if f['type'] == 'INSECURE_EXTERNAL_LINK'])}")
    
    def _prepare_manual_review_list(self):
        """Prepare list of issues needing manual review"""
        manual_types = ['NON_DESCRIPTIVE_LINK', 'EMPTY_SECTION_TITLE', 'MISSING_IMAGE_ALT', 'MISSING_DIRECTIVE_OPTION']
        
        for issue in self.issues:
            if issue['type'] in manual_types:
                self.manual_review_items.append(issue)
        
        print(f"\n{'='*80}")
        print("ISSUES REQUIRING MANUAL REVIEW")
        print(f"{'='*80}")
        
        # Group by type
        by_type = defaultdict(list)
        for item in self.manual_review_items:
            by_type[item['type']].append(item)
        
        for issue_type, items in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"\n{issue_type}: {len(items)} issues")
            print(f"  Example: {items[0]['relative_path']} (line {items[0]['line']})")
            print(f"  Suggestion: {items[0]['suggestion']}")
    
    def generate_reports(self):
        """Generate comprehensive reports"""
        
        # 1. Auto-fix report
        auto_report_path = self.report_path.parent / 'auto_fix_report.txt'
        with open(auto_report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("AUTOMATIC QUICK FIX REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total fixes applied: {len(self.fixes_applied)}\n\n")
            
            # Summary by type
            by_type = defaultdict(list)
            for fix in self.fixes_applied:
                by_type[fix['type']].append(fix)
            
            f.write("SUMMARY BY TYPE:\n")
            f.write("-" * 80 + "\n")
            for fix_type, fixes in by_type.items():
                f.write(f"{fix_type}: {len(fixes)} fixes\n")
            f.write("\n")
            
            # Detailed fixes
            f.write("DETAILED FIXES:\n")
            f.write("-" * 80 + "\n")
            for fix in self.fixes_applied:
                f.write(f"File: {fix['file']}\n")
                f.write(f"  Line: {fix['line']}\n")
                f.write(f"  Type: {fix['type']}\n")
                f.write(f"  Change: {fix['change']}\n")
                f.write("\n")
        
        print(f"\n[OK] Auto-fix report saved to: {auto_report_path}")
        
        # 2. Manual review report
        manual_report_path = self.report_path.parent / 'manual_review_report.txt'
        with open(manual_report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("MANUAL REVIEW REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total issues requiring manual review: {len(self.manual_review_items)}\n\n")
            
            # Group by type
            by_type = defaultdict(list)
            for item in self.manual_review_items:
                by_type[item['type']].append(item)
            
            f.write("SUMMARY BY TYPE:\n")
            f.write("-" * 80 + "\n")
            for issue_type, items in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
                f.write(f"{issue_type}: {len(items)} issues\n")
            f.write("\n")
            
            # Detailed items (first 20 per type)
            f.write("SAMPLE ISSUES (first 20 per type):\n")
            f.write("-" * 80 + "\n")
            
            for issue_type, items in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
                f.write(f"\n{issue_type} ({len(items)} total):\n")
                f.write("-" * 80 + "\n")
                
                for i, item in enumerate(items[:20]):
                    f.write(f"\n{i+1}. File: {item['relative_path']}\n")
                    f.write(f"   Line: {item['line']}\n")
                    f.write(f"   Severity: {item['severity']}\n")
                    f.write(f"   Message: {item['message']}\n")
                    f.write(f"   Suggestion: {item['suggestion']}\n")
                
                if len(items) > 20:
                    f.write(f"\n... and {len(items) - 20} more {issue_type} issues\n")
        
        print(f"[OK] Manual review report saved to: {manual_report_path}")
        
        # 3. Summary report
        summary_report_path = self.report_path.parent / 'quick_fix_summary.txt'
        with open(summary_report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("QUICK FIX SUMMARY\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("AUTOMATIC FIXES APPLIED:\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total auto-fixed: {len(self.fixes_applied)}\n")
            for fix_type, count in [(t, len([f for f in self.fixes_applied if f['type'] == t])) for t in ['INVALID_CODE_LANGUAGE', 'INSECURE_EXTERNAL_LINK']]:
                if count > 0:
                    f.write(f"  {fix_type}: {count}\n")
            
            f.write("\nMANUAL REVIEW REQUIRED:\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total requiring manual review: {len(self.manual_review_items)}\n")
            
            by_type = defaultdict(list)
            for item in self.manual_review_items:
                by_type[item['type']].append(item)
            
            for issue_type, items in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
                effort = 'HIGH' if issue_type in ['EMPTY_SECTION_TITLE', 'MISSING_IMAGE_ALT'] else 'MEDIUM'
                f.write(f"  {issue_type}: {len(items)} ({effort} EFFORT)\n")
            
            f.write("\nRECOMMENDATIONS:\n")
            f.write("-" * 80 + "\n")
            f.write("1. Review auto-fix report to verify changes\n")
            f.write("2. Prioritize MEDIUM effort items (NON_DESCRIPTIVE_LINK, MISSING_DIRECTIVE_OPTION)\n")
            f.write("3. Address HIGH effort items (EMPTY_SECTION_TITLE, MISSING_IMAGE_ALT) in batches\n")
            f.write("4. Consider SUGGESTION-level items (BARE_URL, BARE_REF) as optional improvements\n")
        
        print(f"[OK] Summary report saved to: {summary_report_path}")
    
    def run(self):
        """Run automatic quick fixer"""
        print("=" * 80)
        print("AUTOMATIC QUICK FIXER")
        print("=" * 80)
        print("Applies safe, batch fixes without user interaction\n")
        
        self.load_report()
        
        if not self.issues:
            print("No issues found in report")
            return
        
        print("\nApplying automatic fixes...")
        self.apply_safe_fixes()
        
        print("\nGenerating reports...")
        self.generate_reports()
        
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}")
        print(f"[OK] Auto-fixed: {len(self.fixes_applied)} issues")
        print(f"[INFO] Manual review needed: {len(self.manual_review_items)} issues")
        print(f"\nReports generated in: {self.report_path.parent}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python quick_fix_auto.py <report_json> <docs_path>")
        sys.exit(1)
    
    report_path = sys.argv[1]
    docs_path = sys.argv[2]
    
    fixer = AutoQuickFixer(report_path, docs_path)
    fixer.run()
