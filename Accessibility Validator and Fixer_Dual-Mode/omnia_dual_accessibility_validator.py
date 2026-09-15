#!/usr/bin/env python3
"""
Omnia Dual-Mode Accessibility Validator
Validates both RST/Sphinx and Markdown/mkdocs documentation for accessibility compliance
Automatically detects file format and applies appropriate validation logic
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
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ErrorSeverity(Enum):
    """Severity levels for accessibility issues"""
    ERROR = "ERROR"
    WARNING = "WARNING"
    SUGGESTION = "SUGGESTION"


class DocumentFormat(Enum):
    """Document format types"""
    RST = "rst"
    MARKDOWN = "md"
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """Result of a single validation check"""
    file_path: str
    line_number: int
    error_type: str
    severity: ErrorSeverity
    message: str
    suggestion: str
    context: str = ""


class OmniaDualAccessibilityValidator:
    """Dual-mode validator that handles both RST and Markdown formats"""
    
    def __init__(self, config_path: str = None, project_root: str = None, enable_backup: bool = True):
        self.config_path = config_path
        self.project_root = project_root or os.getcwd()
        self.enable_backup = enable_backup
        self.results: List[ValidationResult] = []
        self.backup_dir = None
        self.backup_metadata = None
        self.config = self._load_config()
        self.omnia_specific_patterns = self._load_omnia_patterns()
        
    def _load_config(self) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            "include_patterns": ["*.rst", "*.md"],
            "exclude_patterns": [
                ".git",
                ".omnia_backup",
                "__pycache__",
                "node_modules",
                ".pytest_cache"
            ],
            "checks": {
                "check_empty_section_titles": True,
                "check_missing_image_alt": True,
                "check_non_descriptive_links": True,
                "check_empty_table_headers": True,
                "check_missing_figure_captions": True,
                "check_empty_code_blocks": True,
                "check_semantic_markup": True,
                "check_empty_paragraphs": False,
                "check_external_links": True,
                "check_omnia_structure": True,
                "check_documentation_links": True,
                "check_code_block_languages": True,
                "check_directives": True,
                "check_internal_references": True
            },
            "non_descriptive_link_patterns": [
                r"click here",
                r"read more",
                r"learn more",
                r"here\b",
                r"this link",
                r"more information"
            ],
            "omnia_internal_domains": [
                "dell.com",
                "delltechnologies.com",
                "omnia-docs",
                "readthedocs.io"
            ],
            "supported_code_languages": [
                "python", "bash", "shell", "json", "yaml", "xml",
                "javascript", "java", "c", "cpp", "go", "rust",
                "typescript", "html", "css", "sql", "php", "ruby"
            ]
        }
        
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        return default_config
    
    def _load_omnia_patterns(self) -> Dict:
        """Load Omnia-specific patterns"""
        return {
            "required_directive_options": {
                "image": ["alt"],
                "figure": ["alt"]
            },
            "markdown_elements": {
                "headers": r'^#{1,6}\s+',
                "images": r'!\[[^\]]*\]\([^\)]+\)',
                "links": r'\[[^\]]+\]\([^\)]+\)',
                "code_blocks": r'```[\w]*',
                "tables": r'\|.*\|'
            }
        }
    
    def _detect_format(self, file_path: str) -> DocumentFormat:
        """Detect document format based on file extension"""
        ext = Path(file_path).suffix.lower()
        if ext == '.rst':
            return DocumentFormat.RST
        elif ext == '.md':
            return DocumentFormat.MARKDOWN
        else:
            return DocumentFormat.UNKNOWN
    
    def validate_file(self, file_path: str) -> List[ValidationResult]:
        """Validate a single file (detects format automatically)"""
        format_type = self._detect_format(file_path)
        
        if format_type == DocumentFormat.UNKNOWN:
            print(f"Skipping unknown format: {file_path}")
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []
        
        print(f"Validating {file_path} as {format_type.value.upper()}")
        
        if format_type == DocumentFormat.RST:
            self._validate_rst_file(file_path, lines)
        elif format_type == DocumentFormat.MARKDOWN:
            self._validate_markdown_file(file_path, lines)
        
        return self.results
    
    def _validate_rst_file(self, file_path: str, lines: List[str]):
        """Validate RST file using RST-specific logic"""
        if self.config["checks"]["check_empty_section_titles"]:
            self._check_rst_empty_section_titles(file_path, lines)
        
        if self.config["checks"]["check_missing_image_alt"]:
            self._check_rst_missing_image_alt(file_path, lines)
        
        if self.config["checks"]["check_non_descriptive_links"]:
            self._check_rst_non_descriptive_links(file_path, lines)
        
        if self.config["checks"]["check_empty_table_headers"]:
            self._check_rst_empty_table_headers(file_path, lines)
        
        if self.config["checks"]["check_missing_figure_captions"]:
            self._check_rst_missing_figure_captions(file_path, lines)
        
        if self.config["checks"]["check_empty_code_blocks"]:
            self._check_rst_empty_code_blocks(file_path, lines)
        
        if self.config["checks"]["check_semantic_markup"]:
            self._check_semantic_markup(file_path, lines)
        
        if self.config["checks"]["check_external_links"]:
            self._check_external_links(file_path, lines)
        
        # Omnia-specific checks
        if self.config["checks"]["check_omnia_structure"]:
            self._check_rst_omnia_structure(file_path, lines)
        
        if self.config["checks"]["check_documentation_links"]:
            self._check_rst_documentation_links(file_path, lines)
        
        if self.config["checks"]["check_code_block_languages"]:
            self._check_rst_code_block_languages(file_path, lines)
        
        if self.config["checks"]["check_directives"]:
            self._check_rst_directives(file_path, lines)
        
        if self.config["checks"]["check_internal_references"]:
            self._check_rst_internal_references(file_path, lines)
    
    def _validate_markdown_file(self, file_path: str, lines: List[str]):
        """Validate Markdown file using Markdown-specific logic"""
        if self.config["checks"]["check_empty_section_titles"]:
            self._check_md_empty_section_titles(file_path, lines)
        
        if self.config["checks"]["check_missing_image_alt"]:
            self._check_md_missing_image_alt(file_path, lines)
        
        if self.config["checks"]["check_non_descriptive_links"]:
            self._check_md_non_descriptive_links(file_path, lines)
        
        if self.config["checks"]["check_empty_table_headers"]:
            self._check_md_empty_table_headers(file_path, lines)
        
        if self.config["checks"]["check_missing_figure_captions"]:
            self._check_md_missing_figure_captions(file_path, lines)
        
        if self.config["checks"]["check_empty_code_blocks"]:
            self._check_md_empty_code_blocks(file_path, lines)
        
        if self.config["checks"]["check_semantic_markup"]:
            self._check_semantic_markup(file_path, lines)
        
        if self.config["checks"]["check_external_links"]:
            self._check_external_links(file_path, lines)
        
        # Omnia-specific checks
        if self.config["checks"]["check_omnia_structure"]:
            self._check_md_omnia_structure(file_path, lines)
        
        if self.config["checks"]["check_documentation_links"]:
            self._check_md_documentation_links(file_path, lines)
        
        if self.config["checks"]["check_code_block_languages"]:
            self._check_md_code_block_languages(file_path, lines)
        
        if self.config["checks"]["check_directives"]:
            self._check_md_directives(file_path, lines)
        
        if self.config["checks"]["check_internal_references"]:
            self._check_md_internal_references(file_path, lines)
    
    # RST-specific validation methods
    def _check_rst_empty_section_titles(self, file_path: str, lines: List[str]):
        """Check for empty section titles in RST"""
        for i, line in enumerate(lines, 1):
            if re.match(r'^[=+\-~`\'"^_*#:]{3,}$', line.strip()) and i > 1:
                title_line = lines[i-2].strip()
                if not title_line:
                    self.results.append(ValidationResult(
                        file_path=file_path,
                        line_number=i-1,
                        error_type="EMPTY_SECTION_TITLE",
                        severity=ErrorSeverity.ERROR,
                        message="Section title is empty",
                        suggestion="Add a descriptive title for this section",
                        context="Omnia: Empty sections break navigation in Sphinx"
                    ))
    
    def _check_rst_missing_image_alt(self, file_path: str, lines: List[str]):
        """Check for missing alt text in RST image directives"""
        for i, line in enumerate(lines, 1):
            if '.. image::' in line or '.. figure::' in line:
                directive_match = re.match(r'\.\. (?:image|figure)::\s+(\S+)', line)
                if directive_match:
                    # Check next few lines for :alt: directive
                    alt_found = False
                    for j in range(i, min(i+5, len(lines))):
                        if ':alt:' in lines[j]:
                            alt_found = True
                            break
                        if lines[j].strip() and not lines[j].startswith('  '):
                            break
                    
                    if not alt_found:
                        self.results.append(ValidationResult(
                            file_path=file_path,
                            line_number=i,
                            error_type="MISSING_IMAGE_ALT",
                            severity=ErrorSeverity.ERROR,
                            message="Image directive is missing :alt: option",
                            suggestion="Add :alt: directive with descriptive text",
                            context="Omnia: Alt text is mandatory for WCAG compliance"
                        ))
    
    def _check_rst_non_descriptive_links(self, file_path: str, lines: List[str]):
        """Check for non-descriptive link text in RST"""
        for i, line in enumerate(lines, 1):
            # Check for inline links
            link_match = re.search(r'`([^`]+)`_', line)
            if link_match:
                link_text = link_match.group(1).strip().lower()
                for pattern in self.config["non_descriptive_link_patterns"]:
                    if re.search(pattern, link_text):
                        self.results.append(ValidationResult(
                            file_path=file_path,
                            line_number=i,
                            error_type="NON_DESCRIPTIVE_LINK",
                            severity=ErrorSeverity.ERROR,
                            message=f"Link text is not descriptive: '{link_text}'",
                            suggestion="Use descriptive link text that describes the destination",
                            context="Omnia: Non-descriptive links fail WCAG 2.4.4"
                        ))
                        break
    
    def _check_rst_empty_table_headers(self, file_path: str, lines: List[str]):
        """Check for empty table headers in RST"""
        in_table = False
        table_start = 0
        
        for i, line in enumerate(lines, 1):
            if '.. list-table::' in line or '.. csv-table::' in line or '.. table::' in line:
                in_table = True
                table_start = i
                continue
            
            if in_table:
                if line.strip().startswith('*') or line.strip().startswith('+'):
                    header_content = line.replace('*', '').replace('+', '').strip()
                    if not header_content and not line.strip().endswith('*') and not line.strip().endswith('+'):
                        self.results.append(ValidationResult(
                            file_path=file_path,
                            line_number=i,
                            error_type="EMPTY_TABLE_HEADER",
                            severity=ErrorSeverity.ERROR,
                            message="Table header cell is empty",
                            suggestion="Add content to table header cell or use N/A if not applicable",
                            context="Omnia: Empty headers break table navigation for screen readers"
                        ))
                
                if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                    if not any(marker in line for marker in ['*','+','-','|']):
                        in_table = False
    
    def _check_rst_missing_figure_captions(self, file_path: str, lines: List[str]):
        """Check for missing figure captions in RST"""
        for i, line in enumerate(lines, 1):
            if '.. figure::' in line:
                caption_found = False
                for j in range(i, min(i+10, len(lines))):
                    if lines[j].strip() and not lines[j].startswith(' ') and not lines[j].startswith('\t'):
                        if lines[j].strip():
                            caption_found = True
                        break
                
                if not caption_found:
                    self.results.append(ValidationResult(
                        file_path=file_path,
                        line_number=i,
                        error_type="MISSING_FIGURE_CAPTION",
                        severity=ErrorSeverity.ERROR,
                        message="Figure is missing caption",
                        suggestion="Add a descriptive caption for the figure",
                        context="Omnia: Captions improve figure discoverability in ReadTheDocs"
                    ))
    
    def _check_rst_empty_code_blocks(self, file_path: str, lines: List[str]):
        """Check for empty code blocks in RST"""
        in_code_block = False
        code_block_start = 0
        code_block_indent = 0
        
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('.. code-block::') or line.strip().startswith('.. code::'):
                in_code_block = True
                code_block_start = i
                code_block_indent = len(line) - len(line.lstrip())
                continue
            
            if in_code_block:
                if line.strip() and not line.startswith(' ' * (code_block_indent + 1)):
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
                    code_block_indent = 0
    
    def _check_rst_omnia_structure(self, file_path: str, lines: List[str]):
        """Check for proper RST document structure"""
        has_title = False
        for i, line in enumerate(lines[:10], 1):
            if re.match(r'^[=+\-~`\'"^_*#:]{3,}$', line.strip()) and i > 1:
                title_line = lines[i-2].strip()
                if title_line:
                    has_title = True
                    break
        
        if not has_title and len(lines) > 5:
            self.results.append(ValidationResult(
                file_path=file_path,
                line_number=1,
                error_type="MISSING_DOCUMENT_TITLE",
                severity=ErrorSeverity.WARNING,
                message="Document appears to be missing a title",
                suggestion="Add a document title using RST heading syntax",
                context="Omnia: Titles are required for ReadTheDocs navigation"
            ))
    
    def _check_rst_documentation_links(self, file_path: str, lines: List[str]):
        """Check for proper RST link formatting"""
        for i, line in enumerate(lines, 1):
            url_matches = re.finditer(r'https?://[^\s\)]+', line)
            for match in url_matches:
                url = match.group()
                if not re.search(r'`[^`]*' + re.escape(url) + r'[^`]*`_', line):
                    if not re.search(r'<[^>]*' + re.escape(url) + r'[^>]*>', line):
                        self.results.append(ValidationResult(
                            file_path=file_path,
                            line_number=i,
                            error_type="BARE_URL",
                            severity=ErrorSeverity.SUGGESTION,
                            message=f"Bare URL detected: {url[:50]}...",
                            suggestion="Format URLs as links: `Link text <URL>`_",
                            context="Omnia: Format URLs for better readability"
                        ))
    
    def _check_rst_code_block_languages(self, file_path: str, lines: List[str]):
        """Check for proper code block language specification in RST"""
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('.. code-block::'):
                lang = line.split('::')[1].strip()
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
        """Check for proper RST directive usage"""
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('.. '):
                directive_match = re.match(r'\.\.\s+(\w+)::', line)
                if directive_match:
                    directive = directive_match.group(1)
                    if directive in self.omnia_specific_patterns["required_directive_options"]:
                        required_options = self.omnia_specific_patterns["required_directive_options"][directive]
                        if required_options:
                            options_found = set()
                            for j in range(i, min(i+5, len(lines))):
                                opt_match = re.match(r'\s+:(\w+):', lines[j])
                                if opt_match:
                                    options_found.add(opt_match.group(1))
                            
                            missing = set(required_options) - options_found
                            if missing:
                                self.results.append(ValidationResult(
                                    file_path=file_path,
                                    line_number=i,
                                    error_type="MISSING_DIRECTIVE_OPTION",
                                    severity=ErrorSeverity.WARNING,
                                    message=f"Directive '{directive}' missing required option(s): {', '.join(missing)}",
                                    suggestion=f"Add missing directive options: {', '.join([f':{opt}:' for opt in missing])}",
                                    context="Omnia: Directive options required for proper rendering"
                                ))
    
    def _check_rst_internal_references(self, file_path: str, lines: List[str]):
        """Check for proper RST internal reference formatting"""
        for i, line in enumerate(lines, 1):
            ref_matches = re.finditer(r':ref:`([^`]+)`', line)
            for match in ref_matches:
                ref_content = match.group(1)
                if not re.search(r'<[^>]+>', ref_content):
                    self.results.append(ValidationResult(
                        file_path=file_path,
                        line_number=i,
                        error_type="BARE_REF",
                        severity=ErrorSeverity.SUGGESTION,
                        message=f"Internal reference may need descriptive text: :ref:`{ref_content}`",
                        suggestion="Use format: :ref:`Descriptive text <label>`",
                        context="Omnia: Descriptive references improve link clarity"
                    ))
    
    # Markdown-specific validation methods
    def _check_md_empty_section_titles(self, file_path: str, lines: List[str]):
        """Check for empty section titles in Markdown"""
        for i, line in enumerate(lines, 1):
            if re.match(r'^#{1,6}\s*$', line.strip()):
                self.results.append(ValidationResult(
                    file_path=file_path,
                    line_number=i,
                    error_type="EMPTY_SECTION_TITLE",
                    severity=ErrorSeverity.ERROR,
                    message="Section title is empty",
                    suggestion="Add a descriptive title for this section after the # symbols",
                    context="Omnia: Empty sections break navigation in mkdocs"
                ))
            elif re.match(r'^#{1,6}\s+\s+$', line.strip()):
                self.results.append(ValidationResult(
                    file_path=file_path,
                    line_number=i,
                    error_type="EMPTY_SECTION_TITLE",
                    severity=ErrorSeverity.ERROR,
                    message="Section title contains only whitespace",
                    suggestion="Add a descriptive title for this section after the # symbols",
                    context="Omnia: Empty sections break navigation in mkdocs"
                ))
    
    def _check_md_missing_image_alt(self, file_path: str, lines: List[str]):
        """Check for missing alt text in Markdown images"""
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
                            suggestion="Add descriptive alt text for the image",
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
                        suggestion="Add alt attribute to img tag",
                        context="Omnia: Alt text is mandatory for WCAG compliance"
                    ))
    
    def _check_md_non_descriptive_links(self, file_path: str, lines: List[str]):
        """Check for non-descriptive link text in Markdown"""
        for i, line in enumerate(lines, 1):
            # Markdown links: [text](url)
            link_match = re.search(r'\[([^\]]+)\]\([^\)]+\)', line)
            if link_match:
                link_text = link_match.group(1).strip().lower()
                for pattern in self.config["non_descriptive_link_patterns"]:
                    if re.search(pattern, link_text):
                        self.results.append(ValidationResult(
                            file_path=file_path,
                            line_number=i,
                            error_type="NON_DESCRIPTIVE_LINK",
                            severity=ErrorSeverity.ERROR,
                            message=f"Link text is not descriptive: '{link_text}'",
                            suggestion="Use descriptive link text that describes the destination",
                            context="Omnia: Non-descriptive links fail WCAG 2.4.4"
                        ))
                        break
    
    def _check_md_empty_table_headers(self, file_path: str, lines: List[str]):
        """Check for empty table headers in Markdown"""
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
    
    def _check_md_missing_figure_captions(self, file_path: str, lines: List[str]):
        """Check for missing figure captions in Markdown"""
        for i, line in enumerate(lines, 1):
            # Markdown images can have captions using figure syntax or text below
            if '![' in line and '](' in line:
                # Check if there's a caption on the same line or next line
                match = re.search(r'!\[[^\]]*\]\([^\)]+\)', line)
                if match:
                    # Check if there's text after the image on the same line
                    after_image = line[match.end():].strip()
                    if not after_image and i < len(lines):
                        # Check next line for potential caption
                        next_line = lines[i].strip() if i < len(lines) else ""
                        if next_line and not next_line.startswith('![') and not next_line.startswith('|'):
                            # Next line might be a caption
                            pass
                        else:
                            self.results.append(ValidationResult(
                                file_path=file_path,
                                line_number=i,
                                error_type="MISSING_FIGURE_CAPTION",
                                severity=ErrorSeverity.WARNING,
                                message="Image may be missing caption",
                                suggestion="Add a descriptive caption for the image for better accessibility",
                                context="Omnia: Captions improve image discoverability in mkdocs"
                            ))
    
    def _check_md_empty_code_blocks(self, file_path: str, lines: List[str]):
        """Check for empty code blocks in Markdown"""
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
    
    def _check_md_omnia_structure(self, file_path: str, lines: List[str]):
        """Check for proper Markdown document structure"""
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
                suggestion="Add a document title using Markdown heading syntax (# Title)",
                context="Omnia: Titles are required for mkdocs navigation"
            ))
    
    def _check_md_documentation_links(self, file_path: str, lines: List[str]):
        """Check for proper Markdown link formatting"""
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
    
    def _check_md_code_block_languages(self, file_path: str, lines: List[str]):
        """Check for proper code block language specification in Markdown"""
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('```'):
                # Extract language from Markdown code block
                lang = line.strip()[3:].strip()
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
    
    def _check_md_directives(self, file_path: str, lines: List[str]):
        """Check for proper Markdown element usage"""
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
    
    def _check_md_internal_references(self, file_path: str, lines: List[str]):
        """Check for proper Markdown internal reference formatting"""
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
    
    # Shared validation methods
    def _check_semantic_markup(self, file_path: str, lines: List[str]):
        """Check for non-semantic markup"""
        for i, line in enumerate(lines, 1):
            if re.search(r'<(b|u|i)>', line, re.IGNORECASE):
                self.results.append(ValidationResult(
                    file_path=file_path,
                    line_number=i,
                    error_type="NON_SEMANTIC_MARKUP",
                    severity=ErrorSeverity.WARNING,
                    message="Non-semantic HTML markup detected",
                    suggestion="Use semantic markup (e.g., **bold** instead of <b>) for better accessibility",
                    context="Omnia: Use semantic markup for proper rendering"
                ))
    
    def _check_external_links(self, file_path: str, lines: List[str]):
        """Check external links use https"""
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
    
    def validate_directory(self, directory: str, recursive: bool = True) -> List[ValidationResult]:
        """Validate all files in directory (auto-detects format)"""
        all_results = []
        pattern = "**/*" if recursive else "*"
        
        for file_path in Path(directory).glob(pattern):
            if file_path.is_file():
                # Check inclusion/exclusion patterns
                ext = file_path.suffix.lower()
                included = False
                for pattern in self.config["include_patterns"]:
                    if ext == pattern.lstrip('*'):
                        included = True
                        break
                
                if not included:
                    continue
                
                # Check exclusion patterns
                excluded = False
                for pattern in self.config["exclude_patterns"]:
                    if pattern in str(file_path):
                        excluded = True
                        break
                
                if excluded:
                    continue
                
                file_results = self.validate_file(str(file_path))
                all_results.extend(file_results)
        
        return all_results
    
    def generate_report(self, results: List[ValidationResult], output_format: str = "text") -> str:
        """Generate validation report"""
        if output_format == "json":
            return self._generate_json_report(results)
        
        # Text format (default)
        report = []
        report.append("=" * 80)
        report.append("OMNIA DUAL-MODE ACCESSIBILITY VALIDATION REPORT")
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
        
        severity_indicator = {
            ErrorSeverity.ERROR: "[ERROR]",
            ErrorSeverity.WARNING: "[WARN]",
            ErrorSeverity.SUGGESTION: "[SUGGEST]"
        }
        
        for file_path, file_results in sorted(by_file.items()):
            report.append("-" * 80)
            report.append(f"File: {file_path}")
            report.append("-" * 80)
            
            for result in sorted(file_results, key=lambda x: x.line_number):
                report.append(f"{severity_indicator[result.severity]} Line {result.line_number}: {result.message}")
                if result.suggestion:
                    report.append(f"  Suggestion: {result.suggestion}")
                if result.context:
                    report.append(f"  Context: {result.context}")
                report.append("")
        
        report.append("=" * 80)
        return "\n".join(report)
    
    def _generate_json_report(self, results: List[ValidationResult]) -> str:
        """Generate JSON format report"""
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "total_issues": len(results),
            "summary": {
                "error": sum(1 for r in results if r.severity == ErrorSeverity.ERROR),
                "warning": sum(1 for r in results if r.severity == ErrorSeverity.WARNING),
                "suggestion": sum(1 for r in results if r.severity == ErrorSeverity.SUGGESTION)
            },
            "files": {}
        }
        
        for result in results:
            if result.file_path not in report_data["files"]:
                report_data["files"][result.file_path] = {
                    "total_issues": 0,
                    "issues": []
                }
            
            report_data["files"][result.file_path]["total_issues"] += 1
            report_data["files"][result.file_path]["issues"].append({
                "line": result.line_number,
                "type": result.error_type,
                "severity": result.severity.value,
                "message": result.message,
                "suggestion": result.suggestion,
                "context": result.context
            })
        
        return json.dumps(report_data, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Omnia Dual-Mode Accessibility Validator - Validates both RST/Sphinx and Markdown/mkdocs documentation"
    )
    parser.add_argument(
        "path",
        help="Path to file or directory to validate"
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Recursively validate all files in directory"
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
        help="Disable automatic backup of files before validation"
    )
    
    args = parser.parse_args()
    
    enable_backup = not args.no_backup
    validator = OmniaDualAccessibilityValidator(args.config, args.project_root, enable_backup)
    
    if os.path.isfile(args.path):
        results = validator.validate_file(args.path)
    else:
        results = validator.validate_directory(args.path, args.recursive)
    
    report = validator.generate_report(results, args.output)
    
    if args.output_file:
        output_dir = os.path.dirname(args.output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report written to: {args.output_file}")
    else:
        print(report)
    
    # Exit with error code if errors found
    error_count = sum(1 for r in results if r.severity == ErrorSeverity.ERROR)
    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()
