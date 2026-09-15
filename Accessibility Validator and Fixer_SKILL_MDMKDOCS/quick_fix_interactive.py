#!/usr/bin/env python3
"""
Quick Interactive Fixer for High-Impact, Low-Effort Accessibility Issues
Focuses on issues that can be fixed quickly with minimal user input
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

class QuickFixer:
    """Targeted fixer for quick wins"""
    
    def __init__(self, report_path, docs_path):
        self.report_path = report_path
        self.docs_path = Path(docs_path)
        self.issues = []
        self.fixes_applied = []
        
    def load_report(self):
        """Load and filter issues for quick fixes"""
        with open(self.report_path, 'r') as f:
            data = json.load(f)
        
        # Focus on LOW and MEDIUM effort issues
        target_types = [
            'INVALID_CODE_LANGUAGE',  # LOW - 116 issues
            'INSECURE_EXTERNAL_LINK',  # LOW - 7 issues  
            'NON_DESCRIPTIVE_LINK'   # MEDIUM - 74 issues (sample)
        ]
        
        for file_path, file_data in data.get('files', {}).items():
            for issue in file_data.get('issues', []):
                if issue['type'] in target_types:
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
        
        # Sort by type and file for efficiency
        self.issues.sort(key=lambda x: (x['type'], x['file_path']))
        
        print(f"Loaded {len(self.issues)} quick-fix issues")
        print(f"  INVALID_CODE_LANGUAGE: {sum(1 for i in self.issues if i['type'] == 'INVALID_CODE_LANGUAGE')}")
        print(f"  INSECURE_EXTERNAL_LINK: {sum(1 for i in self.issues if i['type'] == 'INSECURE_EXTERNAL_LINK')}")
        print(f"  NON_DESCRIPTIVE_LINK: {sum(1 for i in self.issues if i['type'] == 'NON_DESCRIPTIVE_LINK')}")
    
    def fix_invalid_code_language(self):
        """Fix invalid code languages with batch replacement"""
        code_issues = [i for i in self.issues if i['type'] == 'INVALID_CODE_LANGUAGE']
        if not code_issues:
            return
        
        print(f"\n{'='*80}")
        print("FIXING INVALID CODE LANGUAGES (LOW EFFORT)")
        print(f"{'='*80}")
        print(f"Total issues: {len(code_issues)}")
        print("\nCommon replacements:")
        print("  'text' -> 'bash' (for command-line examples)")
        print("  'text' -> 'python' (for Python code)")
        print("  'csv' -> 'bash' (for data files)")
        print("\nRecommended: Replace all 'text' with 'bash' (most common)")
        
        choice = input("\nChoose option:\n1. Replace all 'text' with 'bash'\n2. Replace all 'text' with 'python'\n3. Manual review each\n4. Skip\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            replacement = 'bash'
            self._batch_replace_code_language(code_issues, 'text', replacement)
        elif choice == '2':
            replacement = 'python'
            self._batch_replace_code_language(code_issues, 'text', replacement)
        elif choice == '3':
            self._manual_fix_code_language(code_issues)
        else:
            print("Skipped INVALID_CODE_LANGUAGE fixes")
    
    def _batch_replace_code_language(self, issues, old_lang, new_lang):
        """Batch replace code language"""
        files_modified = set()
        
        for issue in issues:
            file_path = Path(issue['file_path'])
            if not file_path.exists():
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace code block language
                pattern = rf'(\.\. code-block::\s+){re.escape(old_lang)}(\s|$)'
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
                        'change': f"Changed '{old_lang}' to '{new_lang}'"
                    })
            except Exception as e:
                print(f"Error fixing {file_path}: {e}")
        
        print(f"Fixed {len(files_modified)} files")
    
    def _manual_fix_code_language(self, issues):
        """Manual review for code language fixes"""
        for i, issue in enumerate(issues[:10]):  # Limit to first 10 for manual review
            print(f"\n{i+1}/{min(10, len(issues))}: {issue['relative_path']} (line {issue['line']})")
            print(f"  Message: {issue['message']}")
            
            file_path = Path(issue['file_path'])
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    if issue['line'] <= len(lines):
                        print(f"  Current: {lines[issue['line']-1].strip()}")
                except:
                    pass
            
            new_lang = input("  Enter new language (bash/python/shell/json/yaml) or press Enter to skip: ").strip()
            if new_lang:
                self._fix_single_code_language(issue, new_lang)
        
        if len(issues) > 10:
            print(f"\n... and {len(issues) - 10} more issues (use batch option for remaining)")
    
    def _fix_single_code_language(self, issue, new_lang):
        """Fix single code language issue"""
        file_path = Path(issue['file_path'])
        if not file_path.exists():
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract current language from the issue message
            current_lang = 'text'  # Default assumption
            match = re.search(r"'(\w+)'", issue['message'])
            if match:
                current_lang = match.group(1)
            
            pattern = rf'(\.\. code-block::\s+){re.escape(current_lang)}(\s|$)'
            replacement = rf'\1{new_lang}\2'
            new_content = re.sub(pattern, replacement, content)
            
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                self.fixes_applied.append({
                    'file': issue['relative_path'],
                    'line': issue['line'],
                    'type': issue['type'],
                    'change': f"Changed '{current_lang}' to '{new_lang}'"
                })
                print(f"  ✓ Fixed")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    def fix_insecure_links(self):
        """Fix remaining insecure external links"""
        link_issues = [i for i in self.issues if i['type'] == 'INSECURE_EXTERNAL_LINK']
        if not link_issues:
            return
        
        print(f"\n{'='*80}")
        print("FIXING INSECURE EXTERNAL LINKS (LOW EFFORT)")
        print(f"{'='*80}")
        print(f"Total issues: {len(link_issues)}")
        print("\nThese are typically internal/local URLs that use http://")
        print("Recommended: Convert all to https://")
        
        choice = input("\nConvert all http:// to https://? (y/n): ").strip().lower()
        
        if choice == 'y':
            files_modified = set()
            for issue in link_issues:
                file_path = Path(issue['file_path'])
                if not file_path.exists():
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Replace http:// with https:// (but be careful with variables)
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
            
            print(f"Fixed {len(files_modified)} files")
        else:
            print("Skipped INSECURE_EXTERNAL_LINK fixes")
    
    def fix_non_descriptive_links_sample(self):
        """Fix sample of non-descriptive links (MEDIUM EFFORT)"""
        link_issues = [i for i in self.issues if i['type'] == 'NON_DESCRIPTIVE_LINK']
        if not link_issues:
            return
        
        print(f"\n{'='*80}")
        print("FIXING NON-DESCRIPTIVE LINKS (MEDIUM EFFORT - SAMPLE)")
        print(f"{'='*80}")
        print(f"Total issues: {len(link_issues)}")
        print("This requires manual review for each link")
        print("Showing first 5 issues as sample...")
        
        for i, issue in enumerate(link_issues[:5]):
            print(f"\n{i+1}/5: {issue['relative_path']} (line {issue['line']})")
            print(f"  Message: {issue['message']}")
            
            file_path = Path(issue['file_path'])
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    if issue['line'] <= len(lines):
                        print(f"  Current: {lines[issue['line']-1].strip()}")
                except:
                    pass
            
            new_text = input("  Enter descriptive link text or press Enter to skip: ").strip()
            if new_text:
                self._fix_single_link(issue, new_text)
        
        print(f"\n... {len(link_issues) - 5} more issues remaining")
        print("For full fix, consider using the main interactive fixer")
    
    def _fix_single_link(self, issue, new_text):
        """Fix single non-descriptive link"""
        file_path = Path(issue['file_path'])
        if not file_path.exists():
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if issue['line'] <= len(lines):
                old_line = lines[issue['line']-1]
                
                # Extract the URL from the link
                url_match = re.search(r'<([^>]+)>', old_line)
                if url_match:
                    url = url_match.group(1)
                    # Replace the link text
                    new_line = re.sub(r'^\s*[`*]*.*?[`*]*\s*<', f'{new_text} <', old_line)
                    lines[issue['line']-1] = new_line
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    
                    self.fixes_applied.append({
                        'file': issue['relative_path'],
                        'line': issue['line'],
                        'type': issue['type'],
                        'change': f"Changed link text to '{new_text}'"
                    })
                    print(f"  ✓ Fixed")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    def generate_report(self):
        """Generate quick fix report"""
        report_path = self.report_path.parent / 'quick_fix_report.txt'
        
        with open(report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("QUICK FIX REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total fixes applied: {len(self.fixes_applied)}\n\n")
            
            f.write("FIXES APPLIED:\n")
            f.write("-" * 80 + "\n")
            
            for fix in self.fixes_applied:
                f.write(f"File: {fix['file']}\n")
                f.write(f"  Line: {fix['line']}\n")
                f.write(f"  Type: {fix['type']}\n")
                f.write(f"  Change: {fix['change']}\n")
                f.write("\n")
        
        print(f"\nQuick fix report saved to: {report_path}")
    
    def run(self):
        """Run quick fixer"""
        print("=" * 80)
        print("QUICK INTERACTIVE FIXER")
        print("=" * 80)
        print("Focuses on high-impact, low-effort accessibility issues\n")
        
        self.load_report()
        
        if not self.issues:
            print("No quick-fix issues found")
            return
        
        print("\n" + "=" * 80)
        print("QUICK FIX STRATEGY")
        print("=" * 80)
        print("1. INVALID_CODE_LANGUAGE (116 issues) - LOW EFFORT")
        print("   - Batch replace unsupported code languages")
        print("2. INSECURE_EXTERNAL_LINK (7 issues) - LOW EFFORT") 
        print("   - Convert http:// to https://")
        print("3. NON_DESCRIPTIVE_LINK (74 issues) - MEDIUM EFFORT")
        print("   - Sample manual review (5 issues shown)")
        
        input("\nPress Enter to continue...")
        
        # Run fixes in order of effort
        self.fix_invalid_code_language()
        self.fix_insecure_links()
        self.fix_non_descriptive_links_sample()
        
        if self.fixes_applied:
            self.generate_report()
            print(f"\n✓ Total fixes applied: {len(self.fixes_applied)}")
        else:
            print("\nNo fixes applied")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python quick_fix_interactive.py <report_json> <docs_path>")
        sys.exit(1)
    
    report_path = sys.argv[1]
    docs_path = sys.argv[2]
    
    fixer = QuickFixer(report_path, docs_path)
    fixer.run()
