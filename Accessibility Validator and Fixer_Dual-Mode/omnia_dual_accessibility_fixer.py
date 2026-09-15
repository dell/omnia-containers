#!/usr/bin/env python3
"""
Omnia Dual-Mode Accessibility Fixer
Fixes accessibility issues in both RST/Sphinx and Markdown/mkdocs documentation
Automatically detects file format and applies appropriate fixing logic
Enhanced for Omnia Documentation Process (GitHub, ReadTheDocs/mkdocs, Windsurf/Devin)
Based on Validator methodology from CET Knowledge Base
"""

import os
import re
import sys
import json
import argparse
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DocumentFormat(Enum):
    """Document format types"""
    RST = "rst"
    MARKDOWN = "md"
    UNKNOWN = "unknown"


class OmniaDualAccessibilityFixer:
    """Dual-mode fixer that handles both RST and Markdown formats"""
    
    def __init__(self, report_file: str, backup_dir: str = None):
        self.report_file = report_file
        self.backup_dir = backup_dir
        self.fix_templates = self._load_fix_templates()
        self.report_data = self._load_report()
        self.fixed_count = 0
        self.skipped_count = 0
        self.error_count = 0
    
    def _load_fix_templates(self) -> Dict:
        """Load fix templates for common issues"""
        return {
            "EMPTY_IMAGE_ALT": {
                "rst": "Add :alt: directive with descriptive text",
                "md": "Add descriptive alt text in ![alt](url)"
            },
            "NON_DESCRIPTIVE_LINK": {
                "rst": "Replace with descriptive link text",
                "md": "Replace with descriptive link text"
            },
            "BARE_URL": {
                "rst": "Format as `Link text <URL>`_",
                "md": "Format as [Link text](URL)"
            }
        }
    
    def _load_report(self) -> Dict:
        """Load accessibility report"""
        try:
            with open(self.report_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading report: {e}")
            sys.exit(1)
    
    def _detect_format(self, file_path: str) -> DocumentFormat:
        """Detect document format based on file extension"""
        ext = Path(file_path).suffix.lower()
        if ext == '.rst':
            return DocumentFormat.RST
        elif ext == '.md':
            return DocumentFormat.MARKDOWN
        else:
            return DocumentFormat.UNKNOWN
    
    def _create_backup(self, file_path: str):
        """Create backup of file before fixing"""
        if self.backup_dir:
            os.makedirs(self.backup_dir, exist_ok=True)
            backup_path = os.path.join(self.backup_dir, os.path.basename(file_path))
            shutil.copy2(file_path, backup_path)
            print(f"Backup created: {backup_path}")
    
    def fix_file(self, file_path: str, auto_only: bool = False, interactive: bool = False) -> bool:
        """Fix issues in a single file (auto-detects format)"""
        format_type = self._detect_format(file_path)
        
        if format_type == DocumentFormat.UNKNOWN:
            print(f"Skipping unknown format: {file_path}")
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines(keepends=True)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return False
        
        print(f"Fixing {file_path} as {format_type.value.upper()}")
        
        # Get issues for this file
        file_issues = []
        if "files" in self.report_data:
            if file_path in self.report_data["files"]:
                file_issues = self.report_data["files"][file_path]["issues"]
        
        if not file_issues:
            print(f"No issues found for {file_path}")
            return True
        
        # Create backup before fixing
        self._create_backup(file_path)
        
        # Apply fixes based on format
        if format_type == DocumentFormat.RST:
            fixed_lines = self._fix_rst_file(lines, file_issues, auto_only, interactive)
        elif format_type == DocumentFormat.MARKDOWN:
            fixed_lines = self._fix_md_file(lines, file_issues, auto_only, interactive)
        
        # Write fixed content
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            print(f"Successfully fixed {file_path}")
            return True
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            return False
    
    def _fix_rst_file(self, lines: List[str], issues: List[Dict], auto_only: bool, interactive: bool) -> List[str]:
        """Fix RST file using RST-specific logic"""
        fixed_lines = lines.copy()
        
        for issue in issues:
            line_num = issue["line"] - 1  # Convert to 0-indexed
            if line_num >= len(fixed_lines):
                continue
            
            issue_type = issue["type"]
            original_line = fixed_lines[line_num]
            
            if issue_type == "EMPTY_IMAGE_ALT":
                fixed_lines[line_num] = self._fix_rst_empty_image_alt(original_line, interactive)
            elif issue_type == "BARE_URL":
                fixed_lines[line_num] = self._fix_rst_bare_url(original_line, interactive)
            elif issue_type == "NON_DESCRIPTIVE_LINK":
                if interactive:
                    fixed_lines[line_num] = self._fix_rst_non_descriptive_link(original_line, interactive)
            else:
                if interactive:
                    print(f"Manual fix needed for {issue_type} at line {line_num + 1}")
                    print(f"  Current: {original_line.strip()}")
                    new_line = input(f"  Enter fix (or press Enter to skip): ")
                    if new_line:
                        fixed_lines[line_num] = new_line + '\n'
                        self.fixed_count += 1
                    else:
                        self.skipped_count += 1
                else:
                    self.skipped_count += 1
        
        return fixed_lines
    
    def _fix_md_file(self, lines: List[str], issues: List[Dict], auto_only: bool, interactive: bool) -> List[str]:
        """Fix Markdown file using Markdown-specific logic"""
        fixed_lines = lines.copy()
        
        for issue in issues:
            line_num = issue["line"] - 1  # Convert to 0-indexed
            if line_num >= len(fixed_lines):
                continue
            
            issue_type = issue["type"]
            original_line = fixed_lines[line_num]
            
            if issue_type == "EMPTY_IMAGE_ALT":
                fixed_lines[line_num] = self._fix_md_empty_image_alt(original_line, interactive)
            elif issue_type == "BARE_URL":
                fixed_lines[line_num] = self._fix_md_bare_url(original_line, interactive)
            elif issue_type == "NON_DESCRIPTIVE_LINK":
                if interactive:
                    fixed_lines[line_num] = self._fix_md_non_descriptive_link(original_line, interactive)
            else:
                if interactive:
                    print(f"Manual fix needed for {issue_type} at line {line_num + 1}")
                    print(f"  Current: {original_line.strip()}")
                    new_line = input(f"  Enter fix (or press Enter to skip): ")
                    if new_line:
                        fixed_lines[line_num] = new_line + '\n'
                        self.fixed_count += 1
                    else:
                        self.skipped_count += 1
                else:
                    self.skipped_count += 1
        
        return fixed_lines
    
    def _fix_rst_empty_image_alt(self, line: str, interactive: bool) -> str:
        """Fix empty image alt text in RST"""
        if interactive:
            print(f"Fixing empty image alt in RST")
            print(f"  Current: {line.strip()}")
            alt_text = input("  Enter alt text: ")
            if alt_text:
                return line.strip() + f"\n   :alt: {alt_text}\n"
        else:
            # Auto-fix with placeholder
            return line.strip() + "\n   :alt: Descriptive text\n"
        return line
    
    def _fix_md_empty_image_alt(self, line: str, interactive: bool) -> str:
        """Fix empty image alt text in Markdown"""
        if interactive:
            print(f"Fixing empty image alt in Markdown")
            print(f"  Current: {line.strip()}")
            alt_text = input("  Enter alt text: ")
            if alt_text:
                # Replace empty alt with descriptive text
                return re.sub(r'!\[\]\(', f'![{alt_text}](', line)
        else:
            # Auto-fix with placeholder
            return re.sub(r'!\[\]\(', '![Descriptive text](', line)
        return line
    
    def _fix_rst_bare_url(self, line: str, interactive: bool) -> str:
        """Fix bare URL in RST"""
        urls = re.findall(r'https?://[^\s\)]+', line)
        if not urls:
            return line
        
        if interactive:
            print(f"Fixing bare URL in RST")
            print(f"  Current: {line.strip()}")
            for url in urls:
                link_text = input(f"  Enter link text for {url}: ")
                if link_text:
                    line = line.replace(url, f'`{link_text} <{url}>`_')
        else:
            # Auto-fix with generic text
            for url in urls:
                line = line.replace(url, f'`link <{url}>`_')
        return line
    
    def _fix_md_bare_url(self, line: str, interactive: bool) -> str:
        """Fix bare URL in Markdown"""
        urls = re.findall(r'https?://[^\s\)]+', line)
        if not urls:
            return line
        
        if interactive:
            print(f"Fixing bare URL in Markdown")
            print(f"  Current: {line.strip()}")
            for url in urls:
                link_text = input(f"  Enter link text for {url}: ")
                if link_text:
                    line = line.replace(url, f'[{link_text}]({url})')
        else:
            # Auto-fix with generic text
            for url in urls:
                line = line.replace(url, f'[link]({url})')
        return line
    
    def _fix_rst_non_descriptive_link(self, line: str, interactive: bool) -> str:
        """Fix non-descriptive link in RST"""
        if interactive:
            print(f"Fixing non-descriptive link in RST")
            print(f"  Current: {line.strip()}")
            new_text = input("  Enter descriptive link text: ")
            if new_text:
                # Replace the non-descriptive text
                return re.sub(r'`[^`]+`_', f'`{new_text}`_', line)
        return line
    
    def _fix_md_non_descriptive_link(self, line: str, interactive: bool) -> str:
        """Fix non-descriptive link in Markdown"""
        if interactive:
            print(f"Fixing non-descriptive link in Markdown")
            print(f"  Current: {line.strip()}")
            new_text = input("  Enter descriptive link text: ")
            if new_text:
                # Replace the non-descriptive text
                return re.sub(r'\[[^\]]+\]', f'[{new_text}]', line)
        return line
    
    def fix_all_files(self, auto_only: bool = False, interactive: bool = False):
        """Fix all files mentioned in the report"""
        if "files" not in self.report_data:
            print("No files found in report")
            return
        
        total_files = len(self.report_data["files"])
        print(f"Found {total_files} files to fix")
        
        for file_path in self.report_data["files"]:
            if self.fix_file(file_path, auto_only, interactive):
                self.fixed_count += 1
            else:
                self.error_count += 1
        
        print(f"\nFixing complete:")
        print(f"  Files fixed: {self.fixed_count}")
        print(f"  Issues skipped: {self.skipped_count}")
        print(f"  Errors: {self.error_count}")


def main():
    parser = argparse.ArgumentParser(
        description="Omnia Dual-Mode Accessibility Fixer - Fixes both RST/Sphinx and Markdown/mkdocs documentation"
    )
    parser.add_argument(
        "report",
        help="Path to accessibility report JSON file"
    )
    parser.add_argument(
        "--auto-only",
        action="store_true",
        help="Apply automatic fixes only"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run interactive fixing session"
    )
    parser.add_argument(
        "--no-auto-fix",
        action="store_true",
        help="Disable automatic fixes (interactive only)"
    )
    parser.add_argument(
        "--backup-dir",
        help="Directory to store backup files"
    )
    parser.add_argument(
        "--diff-only",
        action="store_true",
        help="Generate pure file diff comparison (doesn't require accessibility report)"
    )
    parser.add_argument(
        "--comparison-report",
        help="Path to write comparison report"
    )
    
    args = parser.parse_args()
    
    fixer = OmniaDualAccessibilityFixer(args.report, args.backup_dir)
    
    if args.interactive:
        fixer.fix_all_files(auto_only=not args.no_auto_fix, interactive=True)
    else:
        fixer.fix_all_files(auto_only=True, interactive=False)


if __name__ == "__main__":
    main()
