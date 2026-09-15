#!/usr/bin/env python3
"""
Omnia Markdown Accessibility Validator
Enhanced for Omnia Documentation Process (GitHub, mkdocs, Windsurf/Devin)
Based on Validator methodology from CET Knowledge Base
Validates Markdown/mkdocs documentation for accessibility compliance
"""

import os
import re
import sys
import json
import argparse
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class ErrorSeverity(Enum):
    """Error severity levels matching Validator"""
    ERROR = "ERROR"
    WARNING = "WARNING"
    SUGGESTION = "SUGGESTION"


@dataclass
class ValidationResult:
    """Represents a single validation result"""
    file_path: str
    line_number: int
    error_type: str
    severity: ErrorSeverity
    message: str
    suggestion: str = ""
    context: str = ""  # Additional context for Omnia workflow
    original_line: str = ""  # Original line content for fixer reference


class OmniaMDAccessibilityValidator:
    """Validates Markdown files for accessibility issues - Omnia-specific implementation"""
    
    def __init__(self, config_path: str = None, project_root: str = None, enable_backup: bool = True):
        self.results: List[ValidationResult] = []
        self.config = self._load_config(config_path)
        self.project_root = project_root or os.getcwd()
        self.omnia_specific_patterns = self._load_omnia_patterns()
        self.enable_backup = enable_backup
        self.backup_dir = None
        self.backup_metadata = None
        
        # Backup will be created when validating directory, not in __init__
        self.backup_metadata = {}
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        default_config = {
            # Core accessibility checks
            "check_empty_section_titles": True,
            "check_missing_image_alt": True,
            "check_non_descriptive_links": True,
            "check_empty_table_headers": True,
            "check_missing_figure_captions": True,
            "check_empty_code_blocks": False,
            "check_semantic_markup": False,
            "check_empty_paragraphs": False,
            "check_external_links": True,
            
            # Omnia-specific checks
            "check_omnia_structure": True,
            "check_documentation_links": False,
            "check_code_block_languages": True,
            "check_rst_directives": True,
            "check_internal_references": True,
            
            # Pattern configurations
            "url_pattern": r"https?://[^\s]+",
            "non_descriptive_link_patterns": [
                r"^https?://[^\s]+$",
                r"^www\.[^\s]+$",
                r"click here",
                r"read more",
                r"learn more",
                r"here",
                r"this link",
                r"link"
            ],
            
            # Omnia-specific patterns
            "omnia_internal_domains": [
                "dell.com",
                "delltechnologies.com",
                "omnia-docs",
                "readthedocs.io"
            ],
            "supported_code_languages": [
                "python", "bash", "shell", "json", "yaml", "xml", "javascript",
                "java", "c", "cpp", "go", "rust", "powershell", "sql", "html", "css",
                "typescript", "ruby", "php", "text", "csv", "ini", "toml", "ldif"
            ],
            
            # Valid code block patterns for Omnia template
            "valid_code_block_patterns": [
                r"^```bash title=\"[^\"]+\"$",
                r"^```bash title='[^']+'$",
                r"^```bash title=[^\s]+$"
            ],
            
            # Auto-fix mappings
            "auto_fix_descriptive_links": {},
            "auto_fix_image_captions": {},
            
            # Severity settings
            "severity_settings": {
                "EMPTY_SECTION_TITLE": "ERROR",
                "MISSING_IMAGE_ALT": "ERROR",
                "EMPTY_IMAGE_ALT": "ERROR",
                "NON_DESCRIPTIVE_LINK": "ERROR",
                "EMPTY_TABLE_HEADER": "ERROR",
                "MISSING_FIGURE_CAPTION": "ERROR",
                "EMPTY_CODE_BLOCK": "WARNING",
                "NON_SEMANTIC_MARKUP": "WARNING",
                "INSECURE_EXTERNAL_LINK": "WARNING",
                "INVALID_CODE_LANGUAGE": "WARNING",
                "BROKEN_INTERNAL_LINK": "ERROR",
                "MISSING_DIRECTIVE_OPTION": "WARNING",
                "MISSING_DOCUMENT_TITLE": "WARNING",
                "BARE_URL": "SUGGESTION",
                "BARE_REF": "SUGGESTION"
            },
            
            # Exclusion patterns
            "exclude_patterns": [
                "_build",
                ".git",
                "__pycache__",
                "*.pyc",
                ".tox",
                "*.egg-info"
            ],
            "include_patterns": ["*.md"]
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _load_omnia_patterns(self) -> Dict:
        """Load Omnia-specific validation patterns for Markdown"""
        return {
            "common_directives": [
                "image", "figure", "code-block", "code", "note", "warning",
                "caution", "tip", "table", "list-table", "csv-table",
                "toctree", "figure", "literalinclude", "include"
            ],
            "required_directive_options": {
                "image": ["alt"],
                "figure": ["alt"],
                "code-block": [],
                "code": [],
                "literalinclude": []
            },
            "markdown_elements": [
                "headers", "images", "links", "code_blocks", "tables",
                "blockquotes", "lists", "horizontal_rules"
            ]
        }
    
    def validate_file(self, file_path: str) -> List[ValidationResult]:
        """Validate a single Markdown file"""
        self.results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            self.results.append(ValidationResult(
                file_path=file_path,
                line_number=0,
                error_type="FILE_READ_ERROR",
                severity=ErrorSeverity.ERROR,
                message=f"Failed to read file: {str(e)}",
                context="Omnia workflow: File access error"
            ))
            return self.results
        
        # Run core accessibility checks
        if self.config["check_empty_section_titles"]:
            self._check_empty_section_titles(file_path, lines)
        
        if self.config["check_missing_image_alt"]:
            self._check_missing_image_alt(file_path, lines)
        
        if self.config["check_non_descriptive_links"]:
            self._check_non_descriptive_links(file_path, lines)
        
        if self.config["check_empty_table_headers"]:
            self._check_empty_table_headers(file_path, lines)
        
        if self.config["check_missing_figure_captions"]:
            self._check_missing_figure_captions(file_path, lines)
        
        if self.config["check_empty_code_blocks"]:
            self._check_empty_code_blocks(file_path, lines)
        
        if self.config["check_semantic_markup"]:
            self._check_semantic_markup(file_path, lines)
        
        if self.config["check_empty_paragraphs"]:
            self._check_empty_paragraphs(file_path, lines)
        
        if self.config["check_external_links"]:
            self._check_external_links(file_path, lines)
        
        # Run Omnia-specific checks
        if self.config["check_omnia_structure"]:
            self._check_omnia_structure(file_path, lines)
        
        if self.config["check_documentation_links"]:
            self._check_documentation_links(file_path, lines)
        
        if self.config["check_code_block_languages"]:
            self._check_code_block_languages(file_path, lines)
        
        if self.config.get("check_rst_directives", False):
            self._check_rst_directives(file_path, lines)
        
        if self.config["check_internal_references"]:
            self._check_internal_references(file_path, lines)
        
        return self.results
    
    def _check_empty_section_titles(self, file_path: str, lines: List[str]):
        """Check for empty section titles (Validator: Section Title element is empty)"""
        for i, line in enumerate(lines, 1):
            # Markdown headers start with # characters
            if re.match(r'^#{1,6}\s*$', line.strip()):
                # This is a header with no content
                self.results.append(ValidationResult(
                    file_path=file_path,
                    line_number=i,
                    error_type="EMPTY_SECTION_TITLE",
                    severity=ErrorSeverity.ERROR,
                    message="Section title is empty",
                    suggestion="Add a descriptive title for this section after the # symbols",
                    context="Omnia: Empty sections break navigation in mkdocs"
                ))
            elif re.match(r'^#{1,6}\s+$', line.strip()):
                # Header with only whitespace
                self.results.append(ValidationResult(
                    file_path=file_path,
                    line_number=i,
                    error_type="EMPTY_SECTION_TITLE",
                    severity=ErrorSeverity.ERROR,
                    message="Section title contains only whitespace",
                    suggestion="Add a descriptive title for this section after the # symbols",
                    context="Omnia: Empty sections break navigation in mkdocs"
                ))
    
    def _check_missing_image_alt(self, file_path: str, lines: List[str]):
        """Check for missing image alt text (Validator: Image is missing alt element)"""
        for i, line in enumerate(lines, 1):
            # Markdown image syntax: ![alt text](url) or <img> tags
            if '![' in line and '](' in line:
                # Extract the alt text between ![ and ]
                match = re.search(r'!\[([^\]]*)\]\([^\)]+\)', line)
                if match:
                    alt_text = match.group(1).strip()
                    if not alt_text:
                        self.results.append(ValidationResult(
                            file_path=file_path,
                            line_number=i,
                            error_type="EMPTY_IMAGE_ALT",
                            severity=ErrorSeverity.ERROR,
                            message="Image alt text is empty",
                            suggestion="Add descriptive alt text for accessibility",
                            context="Omnia: Alt text is mandatory for WCAG compliance"
                        ))
                else:
                    # Malformed image syntax
                    self.results.append(ValidationResult(
                        file_path=file_path,
                        line_number=i,
                        error_type="MISSING_IMAGE_ALT",
                        severity=ErrorSeverity.ERROR,
                        message="Image syntax is malformed or missing alt text",
                        suggestion="Use proper Markdown image syntax: ![alt text](url)",
                        context="Omnia: Required for screen reader compatibility"
                    ))
            elif '<img' in line.lower():
                # HTML img tag - check for alt attribute
                if 'alt=' not in line.lower():
                    self.results.append(ValidationResult(
                        file_path=file_path,
                        line_number=i,
                        error_type="MISSING_IMAGE_ALT",
                        severity=ErrorSeverity.ERROR,
                        message="HTML img tag is missing alt attribute",
                        suggestion="Add alt attribute to img tag for accessibility",
                        context="Omnia: Alt text is mandatory for WCAG compliance"
                    ))
                elif re.search(r'alt\s*=\s*["\']\s*["\']', line, re.IGNORECASE):
                    self.results.append(ValidationResult(
                        file_path=file_path,
                        line_number=i,
                        error_type="EMPTY_IMAGE_ALT",
                        severity=ErrorSeverity.ERROR,
                        message="HTML img tag has empty alt attribute",
                        suggestion="Add descriptive alt text to alt attribute",
                        context="Omnia: Alt text is mandatory for WCAG compliance"
                    ))
    
    def _check_non_descriptive_links(self, file_path: str, lines: List[str]):
        """Check for non-descriptive link text (Validator: Link text is not descriptive)"""
        for i, line in enumerate(lines, 1):
            # Markdown link syntax: [text](url)
            matches = re.finditer(r'\[([^\]]+)\]\([^\)]+\)', line)
            for match in matches:
                link_text = match.group(1).strip()
                
                for pattern in self.config["non_descriptive_link_patterns"]:
                    if re.search(pattern, link_text, re.IGNORECASE):
                        self.results.append(ValidationResult(
                            file_path=file_path,
                            line_number=i,
                            error_type="NON_DESCRIPTIVE_LINK",
                            severity=ErrorSeverity.ERROR,
                            message=f"Link text is not descriptive: '{link_text}'",
                            suggestion="Use descriptive link text that describes the destination",
                            context="Omnia: Non-descriptive links fail WCAG 2.4.4",
                            original_line=line
                        ))
                        break
    
    def _check_empty_table_headers(self, file_path: str, lines: List[str]):
        """Check for empty table headers (Validator: Table is missing thead element or empty)"""
        in_table = False
        table_start = 0
        header_row = False
        
        for i, line in enumerate(lines, 1):
            # Markdown table syntax: pipes | with header separator
            if '|' in line and line.strip().startswith('|'):
                if not in_table:
                    in_table = True
                    table_start = i
                    header_row = True
                    continue
                
                # Check for separator row (contains only |, -, :, spaces)
                if re.match(r'^[\s\|:\-]+$', line.strip()):
                    header_row = False
                    continue
                
                if header_row:
                    # This is a header row - check for empty cells
                    cells = [cell.strip() for cell in line.split('|')]
                    for cell in cells:
                        if not cell and cell != '':
                            self.results.append(ValidationResult(
                                file_path=file_path,
                                line_number=i,
                                error_type="EMPTY_TABLE_HEADER",
                                severity=ErrorSeverity.ERROR,
                                message="Table header cell is empty",
                                suggestion="Add content to table header cell or use N/A if not applicable",
                                context="Omnia: Empty headers break table navigation for screen readers"
                            ))
                
                # Check if table ends
                if not line.strip().startswith('|'):
                    in_table = False
                    header_row = False
    
    def _check_missing_figure_captions(self, file_path: str, lines: List[str]):
        """Check for missing figure captions (Validator: Figure is missing title element)"""
        for i, line in enumerate(lines, 1):
            # Markdown images can have captions using figure syntax or text below
            if '![' in line and '](' in line:
                # Extract alt text by getting the content between ![ and ]
                alt_start = line.find('![')
                alt_end = line.find(']', alt_start)
                if alt_start != -1 and alt_end != -1:
                    alt_text = line[alt_start+2:alt_end].strip()
                    
                    # Extract image URL to check if alt text is just the filename
                    url_start = line.find('](')
                    url_end = line.find(')', url_start)
                    image_url = ""
                    if url_start != -1 and url_end != -1:
                        image_url = line[url_start+2:url_end].strip()
                        # Extract filename from URL
                        image_filename = image_url.split('/')[-1].split('\\')[-1]
                        # Remove extension for comparison
                        image_name = image_filename.rsplit('.', 1)[0] if '.' in image_filename else image_filename
                    
                    # Check if alt text is descriptive (not just filename or generic)
                    is_non_descriptive = False
                    
                    # Empty alt text
                    if not alt_text:
                        is_non_descriptive = True
                    # Generic words
                    elif alt_text.lower() in ['image', 'img', 'picture', 'screenshot', 'diagram', 'chart', 'figure', '']:
                        is_non_descriptive = True
                    # Alt text is just the filename (case-insensitive)
                    elif image_name and alt_text.lower() == image_name.lower():
                        is_non_descriptive = True
                    # Alt text is too short (less than 10 characters)
                    elif len(alt_text) < 10:
                        is_non_descriptive = True
                    # Alt text contains only technical terms without context (pattern matching)
                    elif re.match(r'^[a-z_]+$', alt_text.lower()) and len(alt_text.split('_')) > 2:
                        is_non_descriptive = True
                    
                    if is_non_descriptive:
                        self.results.append(ValidationResult(
                            file_path=file_path,
                            line_number=i,
                            error_type="MISSING_FIGURE_CAPTION",
                            severity=ErrorSeverity.ERROR,
                            message="Image alt text is missing or not descriptive",
                            suggestion="Add descriptive alt text that describes the image content for screen readers",
                            context="Omnia: Descriptive alt text is required for WCAG compliance",
                            original_line=line
                        ))
    
    def _check_empty_code_blocks(self, file_path: str, lines: List[str]):
        """Check for empty code blocks (Validator: Missing content errors)"""
        in_code_block = False
        code_block_start = 0
        code_block_language = ""
        
        for i, line in enumerate(lines, 1):
            # Markdown code block syntax: ```language
            if line.strip().startswith('```'):
                if not in_code_block:
                    # Start of code block
                    in_code_block = True
                    code_block_start = i
                    code_block_language = line.strip()[3:].strip()
                else:
                    # End of code block
                    if i - code_block_start <= 1:
                        self.results.append(ValidationResult(
                            file_path=file_path,
                            line_number=code_block_start,
                            error_type="EMPTY_CODE_BLOCK",
                            severity=ErrorSeverity.WARNING,
                            message="Code block is empty",
                            suggestion="Add code content or remove empty code block",
                            context="Omnia: Empty code blocks confuse readers"
                        ))
                    in_code_block = False
                    code_block_language = ""
    
    def _check_semantic_markup(self, file_path: str, lines: List[str]):
        """Check for non-semantic markup (Validator: Semantic tagging errors)"""
        for i, line in enumerate(lines, 1):
            if re.search(r'<(b|u|i)>', line, re.IGNORECASE):
                self.results.append(ValidationResult(
                    file_path=file_path,
                    line_number=i,
                    error_type="NON_SEMANTIC_MARKUP",
                    severity=ErrorSeverity.WARNING,
                    message="Non-semantic HTML markup detected",
                    suggestion="Use Markdown markup (e.g., **bold** instead of <b>) for better accessibility",
                    context="Omnia: Use Markdown semantic markup for proper mkdocs rendering"
                ))
    
    def _check_empty_paragraphs(self, file_path: str, lines: List[str]):
        """Check for empty paragraphs (DISABLED - False Positive: Blank lines are required in Markdown for paragraph separation)"""
        # This check is disabled because blank lines are required in Markdown syntax
        # to separate paragraphs, sections, and other structural elements.
        # Flagging normal Markdown blank lines as accessibility issues creates false positives.
        # Markdown requires blank lines between paragraphs - this is correct syntax, not an error.
        pass
    
    def _check_external_links(self, file_path: str, lines: List[str]):
        """Check external links use https (Validator: Ensure URL begins with https)"""
        for i, line in enumerate(lines, 1):
            if 'http://' in line and 'https://' not in line:
                matches = re.finditer(r'http://[^\s]+', line)
                for match in matches:
                    url = match.group()
                    if 'localhost' not in url and '127.0.0.1' not in url:
                        self.results.append(ValidationResult(
                            file_path=file_path,
                            line_number=i,
                            error_type="INSECURE_EXTERNAL_LINK",
                            severity=ErrorSeverity.WARNING,
                            message=f"External link uses http instead of https: {url}",
                            suggestion="Use https:// for external links (unless linking to mailto or ftp)",
                            context="Omnia: HTTPS required for security compliance"
                        ))
    
    # Omnia-specific checks
    
    def _check_omnia_structure(self, file_path: str, lines: List[str]):
        """Check for Omnia documentation structure compliance"""
        # Check for proper title structure (Markdown headers)
        has_title = False
        for i, line in enumerate(lines[:10], 1):
            if re.match(r'^#{1,6}\s+.+$', line.strip()):
                has_title = True
                break
        
        if not has_title and len(lines) > 5:
            self.results.append(ValidationResult(
                file_path=file_path,
                line_number=1,
                error_type="MISSING_DOCUMENT_TITLE",
                severity=ErrorSeverity.WARNING,
                message="Document appears to be missing a title",
                suggestion="Add a document title at the top using Markdown heading syntax (# Title)",
                context="Omnia: Titles are required for mkdocs navigation"
            ))
    
    def _check_documentation_links(self, file_path: str, lines: List[str]):
        """Check for proper documentation link formatting"""
        for i, line in enumerate(lines, 1):
            # Check for bare URLs that should be formatted as links
            url_matches = re.finditer(r'https?://[^\s\)]+', line)
            for match in url_matches:
                url = match.group()
                # Check if it's already in a Markdown link format
                if not re.search(r'\[[^\]]*\]\([^\)]*' + re.escape(url) + r'[^\)]*\)', line):
                    if not re.search(r'<[^>]*' + re.escape(url) + r'[^>]*>', line):
                        self.results.append(ValidationResult(
                            file_path=file_path,
                            line_number=i,
                            error_type="BARE_URL",
                            severity=ErrorSeverity.SUGGESTION,
                            message=f"Bare URL detected: {url[:50]}...",
                            suggestion="Format URLs as links: [Link text](URL)",
                            context="Omnia: Format URLs for better readability"
                        ))
    
    def _check_code_block_languages(self, file_path: str, lines: List[str]):
        """Check for proper code block language specification"""
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('```'):
                # Extract language from Markdown code block
                # Handle PyMdownx SuperFences attributes: ```language attr="value"
                lang_full = line.strip()[3:].strip()
                
                # Check if this matches any valid code block patterns (e.g., bash title="Run on")
                valid_patterns = self.config.get("valid_code_block_patterns", [])
                is_valid_pattern = False
                for pattern in valid_patterns:
                    if re.search(pattern, line.strip()):
                        is_valid_pattern = True
                        break
                
                if is_valid_pattern:
                    continue  # Skip validation for valid patterns
                
                # Extract only the base language name (first word before any attributes)
                lang = lang_full.split()[0] if lang_full else ""
                
                if lang and lang not in self.config["supported_code_languages"]:
                    self.results.append(ValidationResult(
                        file_path=file_path,
                        line_number=i,
                        error_type="INVALID_CODE_LANGUAGE",
                        severity=ErrorSeverity.WARNING,
                        message=f"Potentially unsupported code language: '{lang}'",
                        suggestion=f"Use one of: {', '.join(self.config['supported_code_languages'][:5])}...",
                        context="Omnia: Ensure language is supported by Pygments for syntax highlighting"
                    ))
    
    def _check_rst_directives(self, file_path: str, lines: List[str]):
        """Check for proper Markdown element usage (replaces RST directive check)"""
        for i, line in enumerate(lines, 1):
            # Check for HTML elements that might need accessibility attributes
            if '<' in line and '>' in line:
                # Check for HTML elements that should have specific attributes
                if re.search(r'<(div|span|p)', line, re.IGNORECASE):
                    # These are generally OK in Markdown
                    pass
                elif re.search(r'<(button|input|select|textarea)', line, re.IGNORECASE):
                    # Form elements should have labels or aria-labels
                    if 'aria-label' not in line.lower() and 'label=' not in line.lower():
                        self.results.append(ValidationResult(
                            file_path=file_path,
                            line_number=i,
                            error_type="MISSING_DIRECTIVE_OPTION",
                            severity=ErrorSeverity.WARNING,
                            message="Form element may be missing accessibility label",
                            suggestion="Add aria-label or associate with a label element",
                            context="Omnia: Form elements need labels for accessibility"
                        ))
    
    def _check_internal_references(self, file_path: str, lines: List[str]):
        """Check for proper internal reference formatting"""
        for i, line in enumerate(lines, 1):
            # Check for Markdown internal links that might need descriptive text
            # Markdown uses [text](#anchor) for internal references
            ref_matches = re.finditer(r'\[([^\]]+)\]\(#[^\)]+\)', line)
            for match in ref_matches:
                link_text = match.group(1).strip()
                # Check if link text is descriptive
                if not link_text or link_text.isspace():
                    self.results.append(ValidationResult(
                        file_path=file_path,
                        line_number=i,
                        error_type="BARE_REF",
                        severity=ErrorSeverity.SUGGESTION,
                        message="Internal reference link text is empty or whitespace",
                        suggestion="Use descriptive link text for internal references",
                        context="Omnia: Descriptive references improve link clarity"
                    ))
    
    def _create_backup(self, directory: str):
        """Create backup of all Markdown files in the directory before validation (matching RST behavior)"""
        if not self.enable_backup:
            return
        
        # Resolve directory to absolute path for backup creation
        abs_directory = os.path.abspath(directory)
        
        # Create backup in the docs directory itself (matching original RST behavior)
        # This creates .omnia_backup_TIMESTAMP inside the docs directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = os.path.join(abs_directory, f'.omnia_backup_{timestamp}')
        
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # Find all Markdown files
            pattern = "**/*.md"
            md_files = list(Path(directory).glob(pattern))
            
            if not md_files:
                print(f"Backup created: {self.backup_dir} (no Markdown files found)")
                return
            
            # Copy each Markdown file to backup directory
            for file_path in md_files:
                if file_path.is_file():
                    # Check exclusion patterns
                    excluded = False
                    for pattern in self.config["exclude_patterns"]:
                        if pattern in str(file_path):
                            excluded = True
                            break
                    
                    if not excluded:
                        # Preserve directory structure
                        rel_path = file_path.relative_to(directory)
                        backup_path = os.path.join(self.backup_dir, rel_path)
                        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                        shutil.copy2(file_path, backup_path)
            
            # Store backup metadata
            self.backup_metadata = {
                'timestamp': timestamp,
                'backup_dir': self.backup_dir,
                'files_backed': len(md_files),
                'source_directory': directory
            }
            
            # Save metadata
            metadata_path = os.path.join(self.backup_dir, 'backup_metadata.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.backup_metadata, f, indent=2)
            
            print(f"Backup created: {self.backup_dir} ({len(md_files)} files backed up)")
            
        except Exception as e:
            print(f"Warning: Failed to create backup: {e}")
            self.backup_dir = None
    
    def validate_directory(self, directory: str, recursive: bool = True) -> List[ValidationResult]:
        """Validate all Markdown files in a directory"""
        # Create backup before validation (matching original RST behavior)
        if self.enable_backup:
            self._create_backup(directory)
        
        all_results = []
        pattern = "**/*.md" if recursive else "*.md"
        
        for file_path in Path(directory).glob(pattern):
            if file_path.is_file():
                # Check exclusion patterns
                excluded = False
                for pattern in self.config["exclude_patterns"]:
                    if pattern in str(file_path):
                        excluded = True
                        break
                
                # Also exclude backup directories
                if '.omnia_backup' in str(file_path):
                    excluded = True
                
                if not excluded:
                    results = self.validate_file(str(file_path))
                    all_results.extend(results)
        
        return all_results
    
    def generate_report(self, results: List[ValidationResult], output_format: str = "text") -> str:
        """Generate validation report in specified format"""
        if output_format == "json":
            # Create structured JSON report with summary and grouped issues
            # Calculate summary statistics
            total_issues = len(results)
            errors = [r for r in results if r.severity == ErrorSeverity.ERROR]
            warnings = [r for r in results if r.severity == ErrorSeverity.WARNING]
            suggestions = [r for r in results if r.severity == ErrorSeverity.SUGGESTION]
            
            # Group by issue type
            by_type = {}
            for r in results:
                if r.error_type not in by_type:
                    by_type[r.error_type] = []
                by_type[r.error_type].append(r)
            
            # Group by file
            by_file = {}
            for r in results:
                if r.file_path not in by_file:
                    by_file[r.file_path] = []
                by_file[r.file_path].append(r)
            
            # Build summary
            summary = {
                "total_issues": total_issues,
                "by_severity": {
                    "ERROR": len(errors),
                    "WARNING": len(warnings),
                    "SUGGESTION": len(suggestions)
                },
                "by_issue_type": {
                    issue_type: len(issues)
                    for issue_type, issues in sorted(by_type.items())
                },
                "files_with_issues": len(by_file)
            }
            
            # Build detailed issues (grouped by file for better readability)
            file_details = {}
            for file_path, file_results in sorted(by_file.items()):
                # Get relative path if possible
                try:
                    rel_path = str(Path(file_path).relative_to(self.project_root))
                except:
                    rel_path = file_path
                
                # Group by severity within file
                file_errors = [r for r in file_results if r.severity == ErrorSeverity.ERROR]
                file_warnings = [r for r in file_results if r.severity == ErrorSeverity.WARNING]
                file_suggestions = [r for r in file_results if r.severity == ErrorSeverity.SUGGESTION]
                
                file_details[file_path] = {
                    "relative_path": rel_path,
                    "total_issues": len(file_results),
                    "summary": {
                        "ERROR": len(file_errors),
                        "WARNING": len(file_warnings),
                        "SUGGESTION": len(file_suggestions)
                    },
                    # Only include detailed issues for errors and warnings (limit suggestions)
                    "issues": [
                        {
                            "line": r.line_number,
                            "type": r.error_type,
                            "severity": r.severity.value,
                            "message": r.message,
                            "suggestion": r.suggestion,
                            "context": r.context,
                            "original_line": r.original_line
                        }
                        for r in file_errors + file_warnings
                    ],
                    # For suggestions, just show count and a few examples
                    "suggestion_summary": {
                        "count": len(file_suggestions),
                        "example_types": list(set(r.error_type for r in file_suggestions[:5]))
                    } if file_suggestions else None
                }
            
            # Build complete report
            report_data = {
                "metadata": {
                    "generated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "validator_version": "1.1",
                    "project_root": self.project_root
                },
                "summary": summary,
                "files": file_details
            }
            
            return json.dumps(report_data, indent=2)
        
        # Text format (default)
        report = []
        report.append("=" * 80)
        report.append("OMNIA MARKDOWN ACCESSIBILITY VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Issues Found: {len(results)}")
        report.append("")
        
        # Group by severity
        errors = [r for r in results if r.severity == ErrorSeverity.ERROR]
        warnings = [r for r in results if r.severity == ErrorSeverity.WARNING]
        suggestions = [r for r in results if r.severity == ErrorSeverity.SUGGESTION]
        
        report.append(f"Errors: {len(errors)}")
        report.append(f"Warnings: {len(warnings)}")
        report.append(f"Suggestions: {len(suggestions)}")
        report.append("")
        
        # Group by file
        by_file = {}
        for result in results:
            if result.file_path not in by_file:
                by_file[result.file_path] = []
            by_file[result.file_path].append(result)
        
        for file_path, file_results in by_file.items():
            report.append("-" * 80)
            report.append(f"File: {file_path}")
            report.append("-" * 80)
            
            for result in file_results:
                severity_indicator = {
                    ErrorSeverity.ERROR: "[ERROR]",
                    ErrorSeverity.WARNING: "[WARN]",
                    ErrorSeverity.SUGGESTION: "[SUGGEST]"
                }
                report.append(f"{severity_indicator[result.severity]} Line {result.line_number}: {result.message}")
                if result.suggestion:
                    report.append(f"  Suggestion: {result.suggestion}")
                if result.context:
                    report.append(f"  Context: {result.context}")
                report.append("")
        
        report.append("=" * 80)
        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(
        description="Omnia Markdown Accessibility Validator - Validates Markdown/mkdocs documentation for accessibility compliance"
    )
    parser.add_argument(
        "path",
        help="Path to Markdown file or directory to validate"
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Recursively validate all Markdown files in directory"
    )
    parser.add_argument(
        "-c", "--config",
        help="Path to configuration JSON file"
    )
    parser.add_argument(
        "-p", "--project-root",
        help="Project root directory for Omnia-specific checks"
    )
    parser.add_argument(
        "-o", "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "-f", "--output-file",
        help="Write report to file instead of stdout"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Disable automatic backup of Markdown files before validation"
    )
    
    args = parser.parse_args()
    
    enable_backup = not args.no_backup
    validator = OmniaMDAccessibilityValidator(args.config, args.project_root, enable_backup)
    
    if os.path.isfile(args.path):
        results = validator.validate_file(args.path)
    else:
        results = validator.validate_directory(args.path, args.recursive)
    
    report = validator.generate_report(results, args.output)
    
    # Default to saving report to reports folder if no output file specified
    if not args.output_file:
        reports_dir = "reports/baseline_validation"
        os.makedirs(reports_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_output_file = os.path.join(reports_dir, f"accessibility_report_{timestamp}.json")
        
        # Always save JSON report for use by fixer
        json_report = validator.generate_report(results, "json")
        with open(default_output_file, 'w', encoding='utf-8') as f:
            f.write(json_report)
        print(f"Report automatically saved to: {default_output_file}")
        
        # Also print text report to console
        print(validator.generate_report(results, "text"))
    else:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(args.output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report written to: {args.output_file}")
    
    # Exit with error code if errors found
    error_count = sum(1 for r in results if r.severity == ErrorSeverity.ERROR)
    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
