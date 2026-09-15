#!/usr/bin/env python3
"""
Omnia Markdown Accessibility Fixer
Automatically fixes and interactively prompts for accessibility issues in Markdown files
Enhanced for Omnia Documentation Process (GitHub, mkdocs, Windsurf/Devin)
Based on accessibility validation results
"""

import os
import re
import sys
import json
import argparse
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class FixAction(Enum):
    """Types of fix actions"""
    AUTO = "AUTO"           # Can be automatically fixed
    INTERACTIVE = "INTERACTIVE"  # Requires user input
    SKIP = "SKIP"           # Should be skipped (requires manual review)


@dataclass
class AccessibilityIssue:
    """Represents a single accessibility issue"""
    file_path: str
    line_number: int
    error_type: str
    severity: str
    message: str
    suggestion: str
    context: str = ""
    original_line: str = ""
    fixed: bool = False
    fix_description: str = ""


class OmniaMDAccessibilityFixer:
    """Fixes accessibility issues in Markdown files - Omnia-specific implementation"""
    
    def __init__(self, report_path: str, backup: bool = True, project_root: str = None, backup_dir: str = None, original_report_path: str = None):
        self.report_path = report_path
        self.backup = backup
        self.project_root = project_root or os.getcwd()
        self.backup_dir = backup_dir  # Directory containing backup files for comparison
        self.original_report_path = original_report_path  # Original report before fixes
        self.issues: List[AccessibilityIssue] = []
        self.original_issues: List[AccessibilityIssue] = []  # Issues from original report
        self.fixes_applied: Dict[str, int] = {}
        self.files_modified: List[str] = []
        self.omnia_fix_templates = self._load_omnia_fix_templates()
        self.comparison_data = []  # Store before/after comparison data
        self.config = self._load_config()  # Load configuration for fix operations
        
    def _load_omnia_fix_templates(self) -> Dict:
        """Load Omnia-specific fix templates for Markdown"""
        return {
            "MISSING_IMAGE_ALT": {
                "template": "![{alt_text}]({url})",
                "indent": 0
            },
            "EMPTY_IMAGE_ALT": {
                "template": "![{alt_text}]({url})",
                "indent": 0
            },
            "NON_DESCRIPTIVE_LINK": {
                "patterns": {
                    "click here": "see {context}",
                    "read more": "learn more about {context}",
                    "learn more": "learn more about {context}",
                    "here": "this {context}",
                    "this link": "this {context}"
                }
            },
            "INSECURE_EXTERNAL_LINK": {
                "replacement": "https://"
            }
        }
    
    def _load_config(self) -> Dict:
        """Load configuration from omnia_config.json"""
        config_path = Path(__file__).parent / "omnia_config.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            return {}
    
    def generate_file_diff_report(self, backup_dir: str) -> str:
        """Generate a pure file diff comparison report without needing accessibility report"""
        if not backup_dir or not os.path.exists(backup_dir):
            return "Error: Backup directory not found"
        
        report = []
        report.append("=" * 80)
        report.append("OMNIA FILE DIFF COMPARISON REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Backup directory: {backup_dir}")
        report.append(f"Current directory: {self.project_root}")
        report.append("")
        
        all_changes = []
        files_compared = 0
        files_with_changes = 0
        
        # Walk through backup directory
        for root, dirs, files in os.walk(backup_dir):
            # Skip nested backup directories
            dirs[:] = [d for d in dirs if not d.startswith('.omnia_backup')]
            
            for file in files:
                if not file.endswith('.md'):
                    continue
                
                backup_file = os.path.join(root, file)
                rel_path = Path(backup_file).relative_to(backup_dir)
                
                # Try to find the corresponding current file
                # First try relative to project_root
                current_file = os.path.join(self.project_root, rel_path)
                
                # If not found, try the parent directory of backup_dir
                if not os.path.exists(current_file):
                    backup_parent = str(Path(backup_dir).parent)
                    current_file = os.path.join(backup_parent, rel_path)
                
                if not os.path.exists(current_file):
                    continue
                
                files_compared += 1
                
                # Compare files
                try:
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        backup_lines = f.readlines()
                except:
                    continue
                
                try:
                    with open(current_file, 'r', encoding='utf-8') as f:
                        current_lines = f.readlines()
                except:
                    continue
                
                # Find differences
                file_changes = []
                for i, (backup_line, current_line) in enumerate(zip(backup_lines, current_lines)):
                    if backup_line.rstrip() != current_line.rstrip():
                        file_changes.append({
                            'line': i + 1,
                            'before': backup_line.rstrip(),
                            'after': current_line.rstrip()
                        })
                
                if file_changes:
                    files_with_changes += 1
                    all_changes.append({
                        'file': str(rel_path),
                        'changes': file_changes
                    })
        
        report.append(f"Files compared: {files_compared}")
        report.append(f"Files with changes: {files_with_changes}")
        report.append(f"Total line changes: {sum(len(f['changes']) for f in all_changes)}")
        report.append("")
        
        if not all_changes:
            report.append("No changes found between backup and current files.")
        else:
            report.append("FILES WITH CHANGES:")
            report.append("-" * 80)
            
            for file_info in sorted(all_changes, key=lambda x: x['file']):
                report.append(f"\nFile: {file_info['file']}")
                report.append(f"Changes: {len(file_info['changes'])} lines")
                report.append("-" * 80)
                
                # Table header
                table = []
                table.append(f"{'Line':<6} {'Before':<40} {'After':<40}")
                table.append("-" * 86)
                
                for change in file_info['changes'][:20]:  # Limit to first 20 changes per file
                    before = change['before'][:37] + "..." if len(change['before']) > 40 else change['before']
                    after = change['after'][:37] + "..." if len(change['after']) > 40 else change['after']
                    table.append(f"{change['line']:<6} {before:<40} {after:<40}")
                
                if len(file_info['changes']) > 20:
                    table.append(f"... and {len(file_info['changes']) - 20} more changes")
                
                report.extend(table)
        
        report.append("\n" + "=" * 80)
        return "\n".join(report)
    
    def compare_with_backup(self) -> None:
        """Compare current files with backup to determine what was actually fixed"""
        if not self.backup_dir or not os.path.exists(self.backup_dir):
            print(f"Warning: Backup directory not found: {self.backup_dir}")
            print("Comparison will be based on current run fixes only.")
            return
        
        # Also scan all files in backup to find any changes
        all_changes = []
        
        # Walk through backup directory
        for root, dirs, files in os.walk(self.backup_dir):
            # Skip nested backup directories
            dirs[:] = [d for d in dirs if not d.startswith('.omnia_backup')]
            
            for file in files:
                if not file.endswith('.md'):
                    continue
                
                backup_file = os.path.join(root, file)
                rel_path = Path(backup_file).relative_to(self.backup_dir)
                current_file = os.path.join(self.project_root, rel_path)
                
                if not os.path.exists(current_file):
                    continue
                
                # Compare files
                try:
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        backup_lines = f.readlines()
                except:
                    continue
                
                try:
                    with open(current_file, 'r', encoding='utf-8') as f:
                        current_lines = f.readlines()
                except:
                    continue
                
                # Find differences
                for i, (backup_line, current_line) in enumerate(zip(backup_lines, current_lines)):
                    if backup_line.rstrip() != current_line.rstrip():
                        all_changes.append({
                            'file': str(current_file),
                            'line': i + 1,
                            'before': backup_line.rstrip(),
                            'after': current_line.rstrip()
                        })
        
        # Mark issues as fixed if their lines changed
        for issue in self.issues:
            for change in all_changes:
                if change['file'] == issue.file_path and change['line'] == issue.line_number:
                    issue.fixed = True
                    issue.original_line = change['before']
                    issue.fix_description = f"Changed to: {change['after'][:50]}..."
                    break
    
    def load_original_report(self) -> bool:
        """Load original accessibility report from before fixes"""
        if not self.original_report_path or not os.path.exists(self.original_report_path):
            print("Original report not provided or not found. Comparison will use current run fixes only.")
            return False
        
        try:
            with open(self.original_report_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # Handle both old flat format and new structured format
            if isinstance(report_data, dict) and 'files' in report_data:
                # New structured format
                for file_path, file_data in report_data['files'].items():
                    for item in file_data.get('issues', []):
                        issue = AccessibilityIssue(
                            file_path=file_path,
                            line_number=item['line'],
                            error_type=item['type'],
                            severity=item['severity'],
                            message=item['message'],
                            suggestion=item['suggestion'],
                            context=item.get('context', '')
                        )
                        self.original_issues.append(issue)
            else:
                # Old flat format
                for item in report_data:
                    issue = AccessibilityIssue(
                        file_path=item['file'],
                        line_number=item['line'],
                        error_type=item['type'],
                        severity=item['severity'],
                        message=item['message'],
                        suggestion=item['suggestion'],
                        context=item.get('context', '')
                    )
                    self.original_issues.append(issue)
            
            print(f"Loaded {len(self.original_issues)} issues from original report")
            return True
        except Exception as e:
            print(f"Error loading original report: {e}")
            return False
    
    def load_report(self) -> bool:
        """Load accessibility report from JSON file"""
        try:
            with open(self.report_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # Handle both old flat format and new structured format
            items_to_load = []
            if isinstance(report_data, dict) and 'files' in report_data:
                # New structured format
                for file_path, file_data in report_data['files'].items():
                    for item in file_data.get('issues', []):
                        items_to_load.append({
                            'file': file_path,
                            'line': item['line'],
                            'type': item['type'],
                            'severity': item['severity'],
                            'message': item['message'],
                            'suggestion': item['suggestion'],
                            'context': item.get('context', ''),
                            'original_line': item.get('original_line', '')
                        })
            else:
                # Old flat format
                items_to_load = []
                for item in report_data:
                    items_to_load.append({
                        'file': item.get('file', ''),
                        'line': item.get('line', 0),
                        'type': item.get('type', ''),
                        'severity': item.get('severity', ''),
                        'message': item.get('message', ''),
                        'suggestion': item.get('suggestion', ''),
                        'context': item.get('context', ''),
                        'original_line': item.get('original_line', '')
                    })
            
            for item in items_to_load:
                # Load original file content for comparison
                original_content = item.get('original_line', '')
                if not original_content and os.path.exists(item['file']):
                    with open(item['file'], 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if item['line'] - 1 < len(lines):
                            original_content = lines[item['line'] - 1].rstrip()
                
                issue = AccessibilityIssue(
                    file_path=item['file'],
                    line_number=item['line'],
                    error_type=item['type'],
                    severity=item['severity'],
                    message=item['message'],
                    suggestion=item['suggestion'],
                    context=item.get('context', ''),
                    original_line=original_content
                )
                self.issues.append(issue)
                self.issues.append(issue)
            
            print(f"Loaded {len(self.issues)} issues from report")
            return True
        except Exception as e:
            print(f"Error loading report: {e}")
            return False
    
    def determine_fix_action(self, issue: AccessibilityIssue) -> FixAction:
        """Determine if an issue can be auto-fixed or needs interaction"""
        # Auto-fixable issues
        # EMPTY_PARAGRAPH check disabled - false positive (blank lines required in Markdown)
        if issue.error_type == "INSECURE_EXTERNAL_LINK":
            return FixAction.AUTO
        elif issue.error_type == "BARE_URL":
            return FixAction.AUTO
        elif issue.error_type == "INVALID_CODE_LANGUAGE":
            return FixAction.AUTO
        elif issue.error_type == "NON_DESCRIPTIVE_LINK":
            # Check if this specific non-descriptive link can be auto-fixed via config mapping
            auto_fix_mappings = self.config.get("auto_fix_descriptive_links", {})
            # Extract URL from the issue message or original line
            if issue.original_line:
                url_match = re.search(r'\[([^\]]+)\]\(([^\)]+)\)', issue.original_line)
                if url_match:
                    url = url_match.group(2).strip()
                    if url in auto_fix_mappings:
                        return FixAction.AUTO
            # Also check if it's a bare URL pattern that can be auto-fixed
            if issue.original_line and re.search(r'^https?://[^\s]+$', issue.original_line.strip()):
                return FixAction.AUTO
            return FixAction.INTERACTIVE
        elif issue.error_type == "MISSING_FIGURE_CAPTION":
            # Check if this specific image can be auto-fixed via config mapping
            auto_fix_captions = self.config.get("auto_fix_image_captions", {})
            if issue.original_line:
                url_match = re.search(r'!\[([^\]]*)\]\(([^\)]+)\)', issue.original_line)
                if url_match:
                    url = url_match.group(2).strip()
                    image_filename = url.split('/')[-1]
                    if image_filename in auto_fix_captions:
                        return FixAction.AUTO
            return FixAction.INTERACTIVE

        # Issues requiring user input
        elif issue.error_type == "MISSING_IMAGE_ALT":
            return FixAction.INTERACTIVE
        elif issue.error_type == "EMPTY_IMAGE_ALT":
            return FixAction.INTERACTIVE
        elif issue.error_type == "EMPTY_SECTION_TITLE":
            return FixAction.INTERACTIVE
        elif issue.error_type == "MISSING_DOCUMENT_TITLE":
            return FixAction.INTERACTIVE

        # Skip other issues for manual review
        return FixAction.SKIP
    
    def backup_file(self, file_path: str) -> bool:
        """Create backup of file before modification"""
        if not self.backup:
            return True
        
        try:
            backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(file_path, backup_path)
            print(f"  Backup created: {backup_path}")
            return True
        except Exception as e:
            print(f"  Warning: Could not create backup: {e}")
            return False
    
    def _mark_issue_fixed(self, file_path: str, line_number: int, fix_description: str):
        """Mark an issue as fixed with description"""
        for issue in self.issues:
            if issue.file_path == file_path and issue.line_number == line_number:
                issue.fixed = True
                issue.fix_description = fix_description
                break

    def fix_empty_paragraph(self, file_path: str, lines: List[str], line_number: int) -> Tuple[List[str], bool]:
        """Fix empty paragraph by removing the empty line (DISABLED - False Positive)"""
        # This method is disabled because empty paragraph check is a false positive
        # Blank lines are required in Markdown syntax for paragraph separation
        return lines, False
    
    def fix_insecure_link(self, file_path: str, lines: List[str], line_number: int) -> Tuple[List[str], bool]:
        """Fix insecure http link by changing to https"""
        idx = line_number - 1
        if idx < 0 or idx >= len(lines):
            return lines, False
        
        line = lines[idx]
        if 'http://' in line and 'localhost' not in line and '127.0.0.1' not in line:
            new_line = re.sub(r'http://([^\s]+)', r'https://\1', line)
            lines[idx] = new_line
            self._mark_issue_fixed(file_path, line_number, "Changed http:// to https://")
            return lines, True
        
        return lines, False
    
    def fix_bare_url(self, file_path: str, lines: List[str], line_number: int) -> Tuple[List[str], bool]:
        """Fix bare URL by formatting as Markdown link"""
        idx = line_number - 1
        if idx < 0 or idx >= len(lines):
            return lines, False
        
        line = lines[idx]
        url_matches = re.finditer(r'https?://[^\s\)]+', line)
        fixed = False
        
        for match in url_matches:
            url = match.group()
            # Check if already formatted
            if not re.search(r'`[^`]*' + re.escape(url) + r'[^`]*`_', line):
                if not re.search(r'<[^>]*' + re.escape(url) + r'[^>]*>', line):
                    # Format as link with URL as text
                    new_link = f"`{url} <{url}>`_"
                    new_line = line.replace(url, new_link, 1)
                    lines[idx] = new_line
                    fixed = True
                    self._mark_issue_fixed(file_path, line_number, f"Formatted bare URL as link: {url[:50]}...")
                    break
        
        return lines, fixed
    
    def fix_invalid_code_language(self, file_path: str, lines: List[str], line_number: int, config: Dict) -> Tuple[List[str], bool]:
        """Fix invalid code language by parsing attributes and replacing with supported language"""
        idx = line_number - 1
        if idx < 0 or idx >= len(lines):
            return lines, False
        
        line = lines[idx]
        # Match code block pattern: ```language attributes``` or ```language``` or ```language attr1="value" attr2="value"```
        # The language can be followed by attributes with quotes
        code_block_pattern = r'^(\s*)```(\S+)(.*)$'
        match = re.match(code_block_pattern, line)
        
        if not match:
            return lines, False
        
        indent = match.group(1)
        current_language_full = match.group(2).strip()
        attributes = match.group(3).strip()
        
        # Extract base language from complex string like "bash title=\"...\"" or just "bash"
        # Split by first space to get language and attributes separately
        parts = current_language_full.split(None, 1)
        base_language = parts[0].lower()
        
        # Get supported languages from config
        supported_languages = config.get('supported_code_languages', [])
        
        # If base language is already supported, preserve attributes
        # This fixes cases where "bash title=\"...\"" is flagged but "bash" is supported
        # The new Omnia template requires attributes like title="Run on: OIM host"
        if base_language in supported_languages:
            # Preserve the original line with attributes since base language is valid
            # No fix needed - the validator now properly parses attributes
            return lines, False
        
        # Try to find a supported language that matches
        # Common mappings for invalid languages
        language_mappings = {
            'text': 'text',
            'txt': 'text',
            'plaintext': 'text',
            'sh': 'bash',
            'zsh': 'bash',
            'cmd': 'bash',
            'powershell': 'bash',
            'ps1': 'bash',
            'js': 'javascript',
            'ts': 'typescript',
            'py': 'python',
            'yml': 'yaml',
            'c++': 'cpp',
            'c#': 'csharp',
        }
        
        # Try mapping
        new_language = language_mappings.get(base_language, 'text')
        
        # If still not supported, default to 'text' which is in supported list
        if new_language not in supported_languages:
            new_language = 'text'
        
        # Use just the mapped language, discard all attributes
        new_line = f"{indent}```{new_language}\n"
        fix_desc = f"Changed code language from '{current_language_full}' to '{new_language}'"
        self._mark_issue_fixed(file_path, line_number, fix_desc)
        lines[idx] = new_line
        
        return lines, True
    
    def fix_missing_image_alt(self, file_path: str, lines: List[str], line_number: int, alt_text: str) -> Tuple[List[str], bool]:
        """Fix missing image alt by adding :alt: directive"""
        idx = line_number - 1
        if idx < 0 or idx >= len(lines):
            return lines, False
        
        line = lines[idx]
        
        if '.. image::' not in line and '.. figure::' not in line:
            return lines, False
        
        indent = len(line) - len(line.lstrip())
        alt_line = ' ' * (indent + 3) + f':alt: {alt_text}'
        lines.insert(idx + 1, alt_line)
        self._mark_issue_fixed(file_path, line_number, f"Added alt text: {alt_text}")
        return lines, True
    
    def fix_empty_image_alt(self, file_path: str, lines: List[str], line_number: int, alt_text: str) -> Tuple[List[str], bool]:
        """Fix empty image alt by replacing with descriptive text"""
        idx = line_number - 1
        if idx < 0 or idx >= len(lines):
            return lines, False
        
        line = lines[idx]
        if line.strip().startswith(':alt:'):
            new_line = re.sub(r':alt:\s*', f':alt: {alt_text}', line)
            lines[idx] = new_line
            self._mark_issue_fixed(file_path, line_number, f"Replaced empty alt with: {alt_text}")
            return lines, True
        
        return lines, False
    
    def fix_non_descriptive_link(self, file_path: str, lines: List[str], line_number: int, new_text: str) -> Tuple[List[str], bool]:
        """Fix non-descriptive link text"""
        idx = line_number - 1
        if idx < 0 or idx >= len(lines):
            return lines, False
        
        line = lines[idx]
        patterns = ['click here', 'read more', 'learn more', 'here', 'this link']
        fixed = False
        
        for pattern in patterns:
            if pattern in line.lower():
                new_line = re.sub(re.escape(pattern), new_text, line, flags=re.IGNORECASE)
                lines[idx] = new_line
                fixed = True
                self._mark_issue_fixed(file_path, line_number, f"Replaced '{pattern}' with: {new_text}")
                break
        
        return lines, fixed

    def fix_non_descriptive_link_url(self, file_path: str, lines: List[str], line_number: int) -> Tuple[List[str], bool]:
        """Fix non-descriptive link where URL is used as link text using config mappings"""
        idx = line_number - 1
        if idx < 0 or idx >= len(lines):
            return lines, False

        line = lines[idx]
        auto_fix_mappings = self.config.get("auto_fix_descriptive_links", {})
        fixed = False

        # Check for bare URLs used as link text: [https://example.com](https://example.com)
        url_link_pattern = r'\[([^\]]+)\]\([^\)]+\)'
        matches = re.finditer(url_link_pattern, line)
        
        for match in matches:
            link_text = match.group(1).strip()
            # Extract URL from the link
            url_match = re.search(r'\[([^\]]+)\]\(([^\)]+)\)', line)
            if url_match:
                url = url_match.group(2).strip()
                
                # Check if this URL has a mapping in config
                if url in auto_fix_mappings:
                    descriptive_text = auto_fix_mappings[url]
                    # Replace the link text with descriptive text
                    new_link = f"[{descriptive_text}]({url})"
                    new_line = line.replace(match.group(0), new_link)
                    lines[idx] = new_line
                    fixed = True
                    self._mark_issue_fixed(file_path, line_number, f"Replaced bare URL link text with: {descriptive_text}")
                    break
                # If no mapping but link text is a bare URL, use a generic descriptive text
                elif re.match(r'^https?://[^\s]+$', link_text):
                    # Extract domain name for descriptive text
                    domain = re.sub(r'^https?://', '', url).split('/')[0]
                    descriptive_text = f"{domain} link"
                    new_link = f"[{descriptive_text}]({url})"
                    new_line = line.replace(match.group(0), new_link)
                    lines[idx] = new_line
                    fixed = True
                    self._mark_issue_fixed(file_path, line_number, f"Replaced bare URL link text with: {descriptive_text}")
                    break

        return lines, fixed
    
    def fix_empty_section_title(self, file_path: str, lines: List[str], line_number: int, title: str) -> Tuple[List[str], bool]:
        """Fix empty section title by adding title text"""
        idx = line_number - 1
        if idx > 0:
            lines[idx - 1] = title
            self._mark_issue_fixed(file_path, line_number, f"Added section title: {title}")
            return lines, True
        
        return lines, False
    
    def fix_missing_figure_caption(self, file_path: str, lines: List[str], line_number: int, caption: str) -> Tuple[List[str], bool]:
        """Fix missing figure caption by adding caption"""
        idx = line_number - 1
        if idx < 0 or idx >= len(lines):
            return lines, False
        
        line = lines[idx]
        if '.. figure::' in line:
            indent = len(line) - len(line.lstrip())
            caption_line = ' ' * indent + caption
            lines.insert(idx + 1, caption_line)
            self._mark_issue_fixed(file_path, line_number, f"Added figure caption: {caption}")
            return lines, True
        
        return lines, False

    def fix_missing_image_caption_markdown(self, file_path: str, lines: List[str], line_number: int) -> Tuple[List[str], bool]:
        """Fix missing image caption in Markdown by adding descriptive alt text or caption"""
        idx = line_number - 1
        if idx < 0 or idx >= len(lines):
            return lines, False

        line = lines[idx]
        auto_fix_captions = self.config.get("auto_fix_image_captions", {})
        fixed = False

        # Check for Markdown image syntax: ![alt](url)
        image_pattern = r'!\[([^\]]*)\]\([^\)]+\)'
        matches = re.finditer(image_pattern, line)
        
        for match in matches:
            alt_text = match.group(1).strip()
            # Extract image filename from URL
            url_match = re.search(r'!\[([^\]]*)\]\(([^\)]+)\)', line)
            if url_match:
                url = url_match.group(2).strip()
                # Extract filename from URL
                image_filename = url.split('/')[-1]
                
                # Check if this image has a caption mapping in config
                if image_filename in auto_fix_captions:
                    caption = auto_fix_captions[image_filename]
                    # Replace with enhanced alt text
                    new_image = f"![{caption}]({url})"
                    new_line = line.replace(match.group(0), new_image)
                    lines[idx] = new_line
                    fixed = True
                    self._mark_issue_fixed(file_path, line_number, f"Enhanced image alt text with caption: {caption}")
                    break

        return lines, fixed
    
    def fix_missing_document_title(self, file_path: str, lines: List[str], line_number: int, title: str) -> Tuple[List[str], bool]:
        """Fix missing document title by adding title at top"""
        # Add title at the beginning
        title_line = title + '\n'
        underline = '=' * len(title) + '\n'
        lines.insert(0, underline)
        lines.insert(0, title_line)
        self._mark_issue_fixed(file_path, line_number, f"Added document title: {title}")
        return lines, True
    
    def apply_auto_fixes(self, auto_fix: bool = True, auto_fix_suggestions: bool = False) -> Dict[str, int]:
        """Apply automatic fixes to all auto-fixable issues"""
        auto_fix_count = 0
        skipped_count = 0
        
        by_file: Dict[str, List[AccessibilityIssue]] = {}
        for issue in self.issues:
            action = self.determine_fix_action(issue)
            
            if action != FixAction.AUTO:
                skipped_count += 1
                continue
            
            if issue.severity == "SUGGESTION" and not auto_fix_suggestions:
                skipped_count += 1
                continue
            
            if issue.file_path not in by_file:
                by_file[issue.file_path] = []
            by_file[issue.file_path].append(issue)
        
        if not auto_fix:
            print("Auto-fix disabled. Skipping automatic fixes.")
            return {"auto_fixed": 0, "skipped": len(self.issues)}
        
        print(f"\nApplying automatic fixes to {len(by_file)} files...")
        
        for file_path, file_issues in by_file.items():
            if not os.path.exists(file_path):
                print(f"  File not found: {file_path}")
                continue
            
            if not self.backup_file(file_path):
                print(f"  Skipping {file_path} (backup failed)")
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except Exception as e:
                print(f"  Error reading {file_path}: {e}")
                continue
            
            file_issues.sort(key=lambda x: x.line_number, reverse=True)
            fixed_count = 0
            
            for issue in file_issues:
                # EMPTY_PARAGRAPH check disabled - false positive (blank lines required in Markdown)
                if issue.error_type == "INSECURE_EXTERNAL_LINK":
                    lines, fixed = self.fix_insecure_link(file_path, lines, issue.line_number)
                elif issue.error_type == "BARE_URL":
                    lines, fixed = self.fix_bare_url(file_path, lines, issue.line_number)
                elif issue.error_type == "INVALID_CODE_LANGUAGE":
                    lines, fixed = self.fix_invalid_code_language(file_path, lines, issue.line_number, self.config)
                elif issue.error_type == "NON_DESCRIPTIVE_LINK":
                    lines, fixed = self.fix_non_descriptive_link_url(file_path, lines, issue.line_number)
                elif issue.error_type == "MISSING_FIGURE_CAPTION":
                    lines, fixed = self.fix_missing_image_caption_markdown(file_path, lines, issue.line_number)
                else:
                    fixed = False
                
                if fixed:
                    fixed_count += 1
                    auto_fix_count += 1
            
            if fixed_count > 0:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    print(f"  Fixed {fixed_count} issues in {file_path}")
                    self.files_modified.append(file_path)
                except Exception as e:
                    print(f"  Error writing {file_path}: {e}")
        
        print(f"Auto-fix complete: {auto_fix_count} issues fixed, {skipped_count} skipped")
        return {"auto_fixed": auto_fix_count, "skipped": skipped_count}
    
    def apply_interactive_fixes(self) -> Dict[str, int]:
        """Apply interactive fixes requiring user input"""
        interactive_count = 0
        skipped_count = 0
        
        by_file: Dict[str, List[AccessibilityIssue]] = {}
        for issue in self.issues:
            action = self.determine_fix_action(issue)
            if action == FixAction.INTERACTIVE:
                if issue.file_path not in by_file:
                    by_file[issue.file_path] = []
                by_file[issue.file_path].append(issue)
            elif action == FixAction.SKIP:
                skipped_count += 1
        
        if not by_file:
            print("No interactive fixes needed or all issues skipped.")
            return {"interactive_fixed": 0, "skipped": skipped_count}
        
        print(f"\nInteractive fixes needed for {len(by_file)} files")
        print("You'll be prompted for each issue requiring manual input")
        
        for file_path, file_issues in by_file.items():
            if not os.path.exists(file_path):
                print(f"\nFile not found: {file_path}")
                continue
            
            print(f"\n{'='*80}")
            print(f"File: {file_path}")
            print(f"{'='*80}")
            
            if not self.backup_file(file_path):
                print("Skipping (backup failed)")
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except Exception as e:
                print(f"Error reading file: {e}")
                continue
            
            file_issues.sort(key=lambda x: x.line_number, reverse=True)
            file_fixed_count = 0
            
            for issue in file_issues:
                print(f"\n[{issue.severity}] Line {issue.line_number}: {issue.message}")
                print(f"Suggestion: {issue.suggestion}")
                if issue.context:
                    print(f"Context: {issue.context}")
                
                idx = issue.line_number - 1
                if 0 <= idx < len(lines):
                    context_start = max(0, idx - 2)
                    context_end = min(len(lines), idx + 3)
                    print("Context:")
                    for i in range(context_start, context_end):
                        marker = ">>>" if i == idx else "   "
                        print(f"  {marker} {i+1}: {lines[i].rstrip()}")
                
                if issue.error_type == "MISSING_IMAGE_ALT":
                    alt_text = input("Enter alt text for image (or press Enter to skip): ").strip()
                    if alt_text:
                        lines, fixed = self.fix_missing_image_alt(file_path, lines, issue.line_number, alt_text)
                        if fixed:
                            file_fixed_count += 1
                            interactive_count += 1
                            print("  ✓ Fixed")
                
                elif issue.error_type == "EMPTY_IMAGE_ALT":
                    alt_text = input("Enter descriptive alt text (or press Enter to skip): ").strip()
                    if alt_text:
                        lines, fixed = self.fix_empty_image_alt(file_path, lines, issue.line_number, alt_text)
                        if fixed:
                            file_fixed_count += 1
                            interactive_count += 1
                            print("  ✓ Fixed")
                
                elif issue.error_type == "NON_DESCRIPTIVE_LINK":
                    new_text = input("Enter descriptive link text (or press Enter to skip): ").strip()
                    if new_text:
                        lines, fixed = self.fix_non_descriptive_link(file_path, lines, issue.line_number, new_text)
                        if fixed:
                            file_fixed_count += 1
                            interactive_count += 1
                            print("  ✓ Fixed")
                
                elif issue.error_type == "EMPTY_SECTION_TITLE":
                    title = input("Enter section title (or press Enter to skip): ").strip()
                    if title:
                        lines, fixed = self.fix_empty_section_title(file_path, lines, issue.line_number, title)
                        if fixed:
                            file_fixed_count += 1
                            interactive_count += 1
                            print("  ✓ Fixed")
                
                elif issue.error_type == "MISSING_FIGURE_CAPTION":
                    caption = input("Enter figure caption (or press Enter to skip): ").strip()
                    if caption:
                        lines, fixed = self.fix_missing_figure_caption(file_path, lines, issue.line_number, caption)
                        if fixed:
                            file_fixed_count += 1
                            interactive_count += 1
                            print("  ✓ Fixed")
                
                elif issue.error_type == "MISSING_DOCUMENT_TITLE":
                    title = input("Enter document title (or press Enter to skip): ").strip()
                    if title:
                        lines, fixed = self.fix_missing_document_title(file_path, lines, issue.line_number, title)
                        if fixed:
                            file_fixed_count += 1
                            interactive_count += 1
                            print("  ✓ Fixed")
            
            if file_fixed_count > 0:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    print(f"\n✓ Fixed {file_fixed_count} issues in {file_path}")
                    self.files_modified.append(file_path)
                except Exception as e:
                    print(f"Error writing file: {e}")
        
        print(f"\nInteractive fixes complete: {interactive_count} issues fixed, {skipped_count} skipped")
        return {"interactive_fixed": interactive_count, "skipped": skipped_count}
    
    def generate_summary(self) -> str:
        """Generate summary of fixes applied"""
        summary = []
        summary.append("=" * 80)
        summary.append("OMNIA ACCESSIBILITY FIXER SUMMARY")
        summary.append("=" * 80)
        summary.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(f"Total issues in report: {len(self.issues)}")
        summary.append(f"Files modified: {len(self.files_modified)}")
        summary.append("")
        
        if self.fixes_applied:
            summary.append("Fixes Applied:")
            for fix_type, count in self.fixes_applied.items():
                summary.append(f"  {fix_type}: {count}")
        else:
            summary.append("No fixes applied yet.")
        
        summary.append("")
        
        if self.files_modified:
            summary.append("Modified Files:")
            for file_path in self.files_modified:
                summary.append(f"  {file_path}")
        
        summary.append("")
        summary.append("=" * 80)
        return "\n".join(summary)
    
    def generate_comparison_report(self) -> str:
        """Generate comparison report showing before/after fixes in table format"""
        # Use original issues if available for accurate comparison
        issues_to_compare = self.original_issues if self.original_issues else self.issues
        
        report = []
        report.append("=" * 80)
        report.append("OMNIA ACCESSIBILITY FIXER COMPARISON REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if self.original_issues:
            report.append(f"Original issues (before fixes): {len(self.original_issues)}")
            report.append(f"Current issues (after fixes): {len(self.issues)}")
            # Count actual fixed issues, not just count difference
            fixed_count = sum(1 for i in self.issues if i.fixed)
            report.append(f"Issues fixed: {fixed_count}")
        else:
            report.append(f"Total issues in report: {len(self.issues)}")
            report.append(f"Issues fixed: {sum(1 for i in self.issues if i.fixed)}")
            report.append(f"Issues not fixed: {sum(1 for i in self.issues if not i.fixed)}")
        report.append("")
        
        # Summary by issue type
        report.append("SUMMARY BY ISSUE TYPE:")
        report.append("-" * 80)
        by_type = {}
        # Use self.issues for counting since that's where fixed flags are set
        for issue in self.issues:
            if issue.error_type not in by_type:
                by_type[issue.error_type] = {"total": 0, "fixed": 0, "not_fixed": 0}
            by_type[issue.error_type]["total"] += 1
            if issue.fixed:
                by_type[issue.error_type]["fixed"] += 1
            else:
                by_type[issue.error_type]["not_fixed"] += 1
        
        # Create table for summary
        type_table = []
        type_table.append(f"{'Issue Type':<30} {'Total':>10} {'Fixed':>10} {'Not Fixed':>10}")
        type_table.append("-" * 62)
        for issue_type, counts in sorted(by_type.items()):
            type_table.append(f"{issue_type:<30} {counts['total']:>10} {counts['fixed']:>10} {counts['not_fixed']:>10}")
        report.extend(type_table)
        report.append("")
        
        # Summary by severity
        report.append("SUMMARY BY SEVERITY:")
        report.append("-" * 80)
        by_severity = {}
        # Use self.issues for counting since that's where fixed flags are set
        for issue in self.issues:
            if issue.severity not in by_severity:
                by_severity[issue.severity] = {"total": 0, "fixed": 0}
            by_severity[issue.severity]["total"] += 1
            if issue.fixed:
                by_severity[issue.severity]["fixed"] += 1
        
        severity_table = []
        severity_table.append(f"{'Severity':<15} {'Total':>10} {'Fixed':>10} {'Remaining':>10}")
        severity_table.append("-" * 47)
        for severity, counts in sorted(by_severity.items()):
            remaining = counts['total'] - counts['fixed']
            severity_table.append(f"{severity:<15} {counts['total']:>10} {counts['fixed']:>10} {remaining:>10}")
        report.extend(severity_table)
        report.append("")
        
        # Detailed table for fixed issues (showing before/after)
        fixed_issues = [i for i in self.issues if i.fixed]
        if fixed_issues:
            report.append("FIXED ISSUES (Before -> After):")
            report.append("-" * 80)
            
            # Group fixed issues by file
            by_file = {}
            for issue in fixed_issues:
                if issue.file_path not in by_file:
                    by_file[issue.file_path] = []
                by_file[issue.file_path].append(issue)
            
            for file_path, file_issues in sorted(by_file.items()):
                # Get relative file path for readability
                try:
                    rel_path = Path(file_path).relative_to(self.project_root)
                except:
                    rel_path = file_path
                
                report.append(f"\nFile: {rel_path}")
                report.append("-" * 80)
                
                # Table header
                table = []
                table.append(f"{'Line':<6} {'Type':<20} {'Before':<35} {'After':<35}")
                table.append("-" * 96)
                
                for issue in sorted(file_issues, key=lambda x: x.line_number):
                    before = issue.original_line[:32] + "..." if len(issue.original_line) > 35 else issue.original_line
                    after = issue.fix_description[:32] + "..." if len(issue.fix_description) > 35 else issue.fix_description
                    table.append(f"{issue.line_number:<6} {issue.error_type:<20} {before:<35} {after:<35}")
                
                report.extend(table)
        
        # Summary of not fixed issues (by type, not individual)
        not_fixed_issues = [i for i in self.issues if not i.fixed]
        if not_fixed_issues:
            report.append("\n\nNOT FIXED ISSUES (Requires Manual Review):")
            report.append("-" * 80)
            
            # Group by type for not fixed
            by_type_not_fixed = {}
            for issue in not_fixed_issues:
                if issue.error_type not in by_type_not_fixed:
                    by_type_not_fixed[issue.error_type] = []
                by_type_not_fixed[issue.error_type].append(issue)
            
            for issue_type, issues in sorted(by_type_not_fixed.items()):
                report.append(f"\n{issue_type} ({len(issues)} issues):")
                report.append(f"  Example: {issues[0].message}")
                report.append(f"  Suggestion: {issues[0].suggestion}")
                report.append(f"  Files affected: {len(set(i.file_path for i in issues))}")
        
        report.append("\n" + "=" * 80)
        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Omnia Markdown Accessibility Fixer - Automatically fixes and interactively prompts for accessibility issues"
    )
    parser.add_argument(
        "report",
        help="Path to accessibility report JSON file"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Don't create backup files"
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        default=True,
        help="Apply automatic fixes (default: True)"
    )
    parser.add_argument(
        "--no-auto-fix",
        action="store_true",
        help="Disable automatic fixes"
    )
    parser.add_argument(
        "--auto-fix-suggestions",
        action="store_true",
        help="Also auto-fix SUGGESTION level issues"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run interactive fixing session"
    )
    parser.add_argument(
        "--auto-only",
        action="store_true",
        help="Only apply automatic fixes, skip interactive"
    )
    parser.add_argument(
        "-p", "--project-root",
        help="Project root directory for Omnia-specific context"
    )
    parser.add_argument(
        "--comparison-report",
        help="Path to write comparison report (before/after fixes)"
    )
    parser.add_argument(
        "--backup-dir",
        help="Backup directory to compare against (for before/after comparison)"
    )
    parser.add_argument(
        "--original-report",
        help="Original accessibility report from before fixes (for accurate comparison)"
    )
    parser.add_argument(
        "--diff-only",
        action="store_true",
        help="Generate pure file diff comparison (doesn't require accessibility report)"
    )
    
    args = parser.parse_args()
    
    if args.no_auto_fix:
        args.auto_fix = False
    
    # If diff-only mode, generate file diff without loading report
    if args.diff_only:
        if not args.backup_dir:
            print("Error: --backup-dir is required for --diff-only mode")
            sys.exit(1)
        
        fixer = OmniaMDAccessibilityFixer(args.report, backup=False, project_root=args.project_root, backup_dir=args.backup_dir)
        diff_report = fixer.generate_file_diff_report(args.backup_dir)
        
        output_file = args.comparison_report if args.comparison_report else "file_diff_report.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(diff_report)
        print(f"File diff report written to: {output_file}")
        sys.exit(0)
    
    fixer = OmniaMDAccessibilityFixer(args.report, backup=not args.no_backup, project_root=args.project_root, backup_dir=args.backup_dir, original_report_path=args.original_report)
    
    if not fixer.load_report():
        sys.exit(1)
    
    # Load original report if provided for accurate comparison
    if args.original_report:
        fixer.load_original_report()
    
    auto_results = fixer.apply_auto_fixes(
        auto_fix=args.auto_fix,
        auto_fix_suggestions=args.auto_fix_suggestions
    )
    fixer.fixes_applied.update(auto_results)
    
    if not args.auto_only and args.interactive:
        interactive_results = fixer.apply_interactive_fixes()
        fixer.fixes_applied.update(interactive_results)
    
    print("\n" + fixer.generate_summary())
    
    # Generate comparison report if requested
    if args.comparison_report:
        # Compare with backup if provided to get actual before/after state
        if args.backup_dir:
            print("Comparing with backup directory...")
            fixer.compare_with_backup()
        
        comparison_report = fixer.generate_comparison_report()
        try:
            with open(args.comparison_report, 'w', encoding='utf-8') as f:
                f.write(comparison_report)
            print(f"\nComparison report written to: {args.comparison_report}")
        except Exception as e:
            print(f"Error writing comparison report: {e}")


if __name__ == "__main__":
    main()
