#!/usr/bin/env python3
"""
LLM-Enhanced Accessibility Fixer
Uses LLM to intelligently fix complex accessibility issues in RST files
Enhanced for Omnia Documentation Process
"""

import os
import re
import json
import sys
import argparse
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class LLMFixRequest:
    """Request for LLM-based fix"""
    file_path: str
    line_number: int
    error_type: str
    context: str
    original_line: str
    suggestion: str
    surrounding_lines: List[str]


class LLMEnhancedFixer:
    """LLM-enhanced fixer for complex accessibility issues"""
    
    def __init__(self, report_path: str, llm_config_path: str = None, backup: bool = True):
        self.report_path = report_path
        self.llm_config_path = llm_config_path or "llm_config.json"
        self.backup = backup
        self.issues: List[Dict] = []
        self.fixes_applied: List[Dict] = []
        self.failed_fixes: List[Dict] = []
        self.llm_config = self._load_llm_config()
        
    def _load_llm_config(self) -> Dict:
        """Load LLM configuration"""
        config = {
            "enabled": False,
            "provider": "openai",  # openai, anthropic, local
            "model": "gpt-4",
            "api_key": "",
            "max_tokens": 500,
            "temperature": 0.3,
            "timeout": 30
        }
        
        if os.path.exists(self.llm_config_path):
            try:
                with open(self.llm_config_path, 'r') as f:
                    config.update(json.load(f))
            except Exception as e:
                print(f"Warning: Could not load LLM config: {e}")
        
        return config
    
    def load_report(self) -> bool:
        """Load accessibility report"""
        try:
            with open(self.report_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # Handle both flat and structured formats
            if isinstance(report_data, dict) and 'files' in report_data:
                # Structured format
                for file_path, file_data in report_data['files'].items():
                    for issue in file_data.get('issues', []):
                        self.issues.append({
                            'file_path': file_path,
                            'line_number': issue['line'],
                            'type': issue['type'],
                            'severity': issue['severity'],
                            'message': issue['message'],
                            'suggestion': issue['suggestion'],
                            'context': issue.get('context', '')
                        })
            else:
                # Flat format
                for issue in report_data:
                    self.issues.append({
                        'file_path': issue['file'],
                        'line_number': issue['line'],
                        'type': issue['type'],
                        'severity': issue['severity'],
                        'message': issue['message'],
                        'suggestion': issue['suggestion'],
                        'context': issue.get('context', '')
                    })
            
            print(f"Loaded {len(self.issues)} issues from report")
            return True
        except Exception as e:
            print(f"Error loading report: {e}")
            return False
    
    def get_surrounding_lines(self, file_path: str, line_number: int, context_lines: int = 3) -> List[str]:
        """Get surrounding lines for context"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start = max(0, line_number - context_lines - 1)
            end = min(len(lines), line_number + context_lines)
            
            return [line.rstrip() for line in lines[start:end]]
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return []
    
    def categorize_issues(self) -> Dict[str, List[Dict]]:
        """Categorize issues by fix complexity"""
        categories = {
            'auto_fixable': [],
            'llm_fixable': [],
            'manual_only': []
        }
        
        for issue in self.issues:
            issue_type = issue['type']
            
            # Auto-fixable issues (handled by existing fixer)
            if issue_type in ['INSECURE_EXTERNAL_LINK', 'BARE_URL', 'BARE_REFERENCE']:
                categories['auto_fixable'].append(issue)
            # LLM-fixable issues (require context understanding)
            elif issue_type in ['MISSING_IMAGE_ALT', 'EMPTY_IMAGE_ALT', 'NON_DESCRIPTIVE_LINK', 
                               'EMPTY_SECTION_TITLE', 'MISSING_DIRECTIVE_OPTION']:
                categories['llm_fixable'].append(issue)
            # Manual-only issues (require domain knowledge)
            else:
                categories['manual_only'].append(issue)
        
        return categories
    
    def generate_llm_fix(self, request: LLMFixRequest) -> Optional[str]:
        """Generate fix using LLM"""
        if not self.llm_config['enabled']:
            return None
        
        try:
            # Check if we should use local terminal-based approach or API
            if self.llm_config['provider'] == 'local':
                return self._generate_local_fix(request)
            else:
                return self._generate_api_fix(request)
        except Exception as e:
            print(f"Error generating LLM fix: {e}")
            return None
    
    def _generate_local_fix(self, request: LLMFixRequest) -> Optional[str]:
        """Generate fix using local rules and heuristics"""
        # Local rule-based fixes for common patterns
        if request.error_type == 'MISSING_IMAGE_ALT':
            # Extract image filename from context
            image_match = re.search(r'.. (?:image|figure):: ([^\s]+)', request.context)
            if image_match:
                filename = image_match.group(1)
                # Generate descriptive alt text from filename
                alt_text = self._filename_to_alt_text(filename)
                return f":alt: {alt_text}"
        
        elif request.error_type == 'EMPTY_SECTION_TITLE':
            # Use context from surrounding lines to generate title
            surrounding_text = ' '.join(request.surrounding_lines)
            if surrounding_text:
                # Extract key words for title
                words = re.findall(r'\b[A-Z][a-z]+\b', surrounding_text)
                if words:
                    return ' '.join(words[:3]).title()
        
        elif request.error_type == 'NON_DESCRIPTIVE_LINK':
            # Extract URL from context
            url_match = re.search(r'https?://[^\s\)]+', request.context)
            if url_match:
                url = url_match.group()
                # Generate descriptive text from URL
                return self._url_to_link_text(url)
        
        return None
    
    def _generate_api_fix(self, request: LLMFixRequest) -> Optional[str]:
        """Generate fix using LLM API (placeholder for actual API integration)"""
        # This would integrate with OpenAI, Anthropic, etc.
        # For now, fall back to local rules
        print("LLM API integration not configured, using local rules")
        return self._generate_local_fix(request)
    
    def _filename_to_alt_text(self, filename: str) -> str:
        """Convert filename to descriptive alt text"""
        # Remove extension and common prefixes
        name = filename.rsplit('.', 1)[0]
        name = re.sub(r'^(screenshot|image|pic|photo)_?', '', name, flags=re.IGNORECASE)
        
        # Convert underscores and hyphens to spaces
        name = re.sub(r'[_-]', ' ', name)
        
        # Capitalize words
        name = ' '.join(word.capitalize() for word in name.split())
        
        if not name:
            return "Image showing interface elements"
        
        return f"Screenshot showing {name.lower()}"
    
    def _url_to_link_text(self, url: str) -> str:
        """Generate descriptive link text from URL"""
        # Remove protocol and common prefixes
        clean_url = url.replace('https://', '').replace('http://', '')
        clean_url = re.sub(r'^(www\d?\.)?', '', clean_url)
        
        # Split by slashes and take meaningful parts
        parts = clean_url.split('/')
        if len(parts) > 1:
            # Use path segments for description
            meaningful_parts = [p for p in parts[1:] if p and not p.isdigit()]
            if meaningful_parts:
                text = ' '.join(meaningful_parts[:2])
                text = re.sub(r'[_-]', ' ', text)
                return f"View the {text.lower()}"
        
        return f"Visit {clean_url.split('/')[0]}"
    
    def apply_fix(self, file_path: str, line_number: int, fix: str) -> bool:
        """Apply fix to file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            idx = line_number - 1
            if idx < 0 or idx >= len(lines):
                print(f"Invalid line number {line_number} in {file_path}")
                return False
            
            # Determine if fix should replace line or be added
            if fix.startswith(':alt:') or fix.startswith(':'):
                # Add as new line after current line
                indent = len(lines[idx]) - len(lines[idx].lstrip())
                fix_line = ' ' * (indent + 3) + fix + '\n'
                lines.insert(idx + 1, fix_line)
            else:
                # Replace current line
                lines[idx] = fix + '\n'
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return True
        except Exception as e:
            print(f"Error applying fix to {file_path}: {e}")
            return False
    
    def create_backup(self, file_path: str) -> str:
        """Create backup of file"""
        if not self.backup:
            return None
        
        backup_dir = os.path.join(os.path.dirname(file_path), '.llm_backup')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f"{os.path.basename(file_path)}_{timestamp}.bak")
        
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def fix_llm_fixable_issues(self) -> Dict:
        """Fix issues that require LLM intervention"""
        categories = self.categorize_issues()
        llm_fixable = categories['llm_fixable']
        
        results = {
            'total_llm_fixable': len(llm_fixable),
            'fixed': 0,
            'failed': 0,
            'skipped': 0,
            'fixes': []
        }
        
        print(f"\nProcessing {len(llm_fixable)} LLM-fixable issues...")
        
        for issue in llm_fixable:
            file_path = issue['file_path']
            line_number = issue['line_number']
            error_type = issue['type']
            
            # Get context
            surrounding_lines = self.get_surrounding_lines(file_path, line_number)
            
            # Create fix request
            request = LLMFixRequest(
                file_path=file_path,
                line_number=line_number,
                error_type=error_type,
                context=issue.get('context', ''),
                original_line=issue.get('original_line', ''),
                suggestion=issue.get('suggestion', ''),
                surrounding_lines=surrounding_lines
            )
            
            # Generate fix
            fix = self.generate_llm_fix(request)
            
            if fix:
                # Create backup
                backup_path = self.create_backup(file_path)
                
                # Apply fix
                if self.apply_fix(file_path, line_number, fix):
                    results['fixed'] += 1
                    results['fixes'].append({
                        'file_path': file_path,
                        'line_number': line_number,
                        'error_type': error_type,
                        'fix': fix,
                        'backup': backup_path
                    })
                    print(f"[OK] Fixed {error_type} in {file_path}:{line_number}")
                else:
                    results['failed'] += 1
                    print(f"[FAIL] Failed to fix {error_type} in {file_path}:{line_number}")
            else:
                results['skipped'] += 1
                print(f"[SKIP] Skipped {error_type} in {file_path}:{line_number} (no fix generated)")
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """Generate report of LLM-enhanced fixing"""
        report = []
        report.append("=" * 80)
        report.append("LLM-ENHANCED ACCESSIBILITY FIXER REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Report: {self.report_path}")
        report.append(f"LLM Config: {self.llm_config_path}")
        report.append("")
        
        report.append("SUMMARY:")
        report.append(f"  Total LLM-fixable issues: {results['total_llm_fixable']}")
        report.append(f"  Successfully fixed: {results['fixed']}")
        report.append(f"  Failed: {results['failed']}")
        report.append(f"  Skipped: {results['skipped']}")
        report.append("")
        
        if results['fixes']:
            report.append("FIXES APPLIED:")
            report.append("-" * 80)
            for fix in results['fixes']:
                report.append(f"  File: {fix['file_path']}")
                report.append(f"  Line: {fix['line_number']}")
                report.append(f"  Type: {fix['error_type']}")
                report.append(f"  Fix: {fix['fix']}")
                if fix['backup']:
                    report.append(f"  Backup: {fix['backup']}")
                report.append("")
        
        report.append("=" * 80)
        return "\n".join(report)
    
    def run(self) -> Dict:
        """Run the LLM-enhanced fixing process"""
        print("LLM-Enhanced Accessibility Fixer")
        print("=" * 80)
        
        # Load report
        if not self.load_report():
            return {'error': 'Failed to load report'}
        
        # Categorize issues
        categories = self.categorize_issues()
        
        print(f"\nIssue Categories:")
        print(f"  Auto-fixable: {len(categories['auto_fixable'])}")
        print(f"  LLM-fixable: {len(categories['llm_fixable'])}")
        print(f"  Manual-only: {len(categories['manual_only'])}")
        
        if not categories['llm_fixable']:
            print("\nNo LLM-fixable issues found.")
            return {'total_llm_fixable': 0, 'fixed': 0, 'failed': 0, 'skipped': 0, 'fixes': []}
        
        # Fix LLM-fixable issues
        results = self.fix_llm_fixable_issues()
        
        # Generate report
        report_text = self.generate_report(results)
        
        # Save report
        report_path = os.path.join(
            os.path.dirname(self.report_path),
            'llm_fix_report.txt'
        )
        with open(report_path, 'w') as f:
            f.write(report_text)
        
        print(f"\nReport saved to: {report_path}")
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description='LLM-Enhanced Accessibility Fixer for RST files'
    )
    parser.add_argument('report', help='Path to accessibility report JSON file')
    parser.add_argument('--llm-config', default='llm_config.json',
                       help='Path to LLM configuration file')
    parser.add_argument('--no-backup', action='store_true',
                       help='Disable backup creation')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be fixed without applying changes')
    
    args = parser.parse_args()
    
    fixer = LLMEnhancedFixer(
        report_path=args.report,
        llm_config_path=args.llm_config,
        backup=not args.no_backup
    )
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be applied")
        fixer.load_report()
        categories = fixer.categorize_issues()
        print(f"\nWould fix {len(categories['llm_fixable'])} LLM-fixable issues")
    else:
        results = fixer.run()
        print(f"\nCompleted: {results['fixed']}/{results['total_llm_fixable']} issues fixed")


if __name__ == '__main__':
    main()
