# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Formatting utilities for automation library.

Contains:
- Colors: ANSI color codes for terminal output
- Symbols: Unicode symbols for status indicators
- log(): Simple timestamped logging
- TestLogger: Structured test output logger
"""

import os
import sys
from datetime import datetime


def _supports_color() -> bool:
    """Check if terminal supports ANSI colors."""
    # Check for NO_COLOR environment variable
    if os.environ.get("NO_COLOR"):
        return False
    # Check if stdout is a TTY
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    # Check TERM environment
    term = os.environ.get("TERM", "")
    if term == "dumb":
        return False
    return True


_USE_COLOR = _supports_color()


# =============================================================================
# ANSI COLOR CODES
# =============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    # Reset
    RESET = "\033[0m" if _USE_COLOR else ""
    BOLD = "\033[1m" if _USE_COLOR else ""
    DIM = "\033[2m" if _USE_COLOR else ""

    # Regular colors
    BLACK = "\033[30m" if _USE_COLOR else ""
    RED = "\033[31m" if _USE_COLOR else ""
    GREEN = "\033[32m" if _USE_COLOR else ""
    YELLOW = "\033[33m" if _USE_COLOR else ""
    BLUE = "\033[34m" if _USE_COLOR else ""
    MAGENTA = "\033[35m" if _USE_COLOR else ""
    CYAN = "\033[36m" if _USE_COLOR else ""
    WHITE = "\033[37m" if _USE_COLOR else ""
    GRAY = "\033[90m" if _USE_COLOR else ""

    # Bright colors
    BRIGHT_RED = "\033[91m" if _USE_COLOR else ""
    BRIGHT_GREEN = "\033[92m" if _USE_COLOR else ""
    BRIGHT_YELLOW = "\033[93m" if _USE_COLOR else ""
    BRIGHT_BLUE = "\033[94m" if _USE_COLOR else ""
    BRIGHT_MAGENTA = "\033[95m" if _USE_COLOR else ""
    BRIGHT_CYAN = "\033[96m" if _USE_COLOR else ""

    # Background
    BG_RED = "\033[41m" if _USE_COLOR else ""
    BG_GREEN = "\033[42m" if _USE_COLOR else ""
    BG_YELLOW = "\033[43m" if _USE_COLOR else ""
    BG_BLUE = "\033[44m" if _USE_COLOR else ""


# =============================================================================
# UNICODE SYMBOLS
# =============================================================================

class Symbols:
    """Unicode symbols for status indicators."""
    CHECK = "✔"
    CROSS = "✘"
    ARROW = "→"
    ARROW_RIGHT = "➜"
    BULLET = "●"
    CIRCLE = "○"
    BOX = "■"
    TRIANGLE = "▶"

    # Box drawing
    DASH = "─"
    PIPE = "│"
    CORNER_TL = "┌"
    CORNER_TR = "┐"
    CORNER_BL = "└"
    CORNER_BR = "┘"
    TEE_L = "├"
    TEE_R = "┤"


# =============================================================================
# LOGGING
# =============================================================================

_debug_mode = False


def set_debug_mode(enabled: bool) -> None:
    """Enable or disable debug mode globally."""
    global _debug_mode
    _debug_mode = enabled


def log(message: str, level: str = "INFO") -> None:
    """
    Print log message with timestamp and color.

    Args:
        message: Message to log
        level: Log level (INFO, DEBUG, WARN, ERROR, OK)
    """
    if level == "DEBUG" and not _debug_mode:
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    level_colors = {
        "INFO": Colors.BRIGHT_BLUE,
        "DEBUG": Colors.GRAY,
        "WARN": Colors.BRIGHT_YELLOW,
        "ERROR": Colors.BRIGHT_RED,
        "OK": Colors.BRIGHT_GREEN,
    }
    color = level_colors.get(level, "")
    print(f"{color}[{timestamp}] [{level}] {message}{Colors.RESET}")


# =============================================================================
# TEST LOGGER
# =============================================================================

_last_output = ""


def get_test_output(test_name: str = None) -> str:
    """Get captured output for the last test."""
    return _last_output


class TestLogger:
    """
    Structured test output logger for pytest/molecule tests.

    Usage:
        log = TestLogger("Verify container exists")
        log.check("Checking file...")
        log.passed("File exists", "details here")
    """

    def __init__(self, test_name: str):
        global _last_output
        self.test_name = test_name
        self._output_lines = []
        self._add_line("")
        self._add_line(f"  {Colors.BRIGHT_CYAN}{Colors.BOLD}{Symbols.TRIANGLE} {test_name}{Colors.RESET}")

    def _add_line(self, line: str):
        """Add line to output and print."""
        global _last_output
        self._output_lines.append(line)
        print(line)
        _last_output = "\n".join(self._output_lines)

    def check(self, message: str):
        """Log check being performed."""
        self._add_line(f"  {Colors.BRIGHT_YELLOW}{Symbols.ARROW}{Colors.RESET} {message}")

    def passed(self, message: str, details: str = None):
        """Log passed result."""
        self._add_line(f"  {Colors.BRIGHT_GREEN}{Symbols.CHECK} PASS:{Colors.RESET} {message}")
        if details:
            for line in details.split('\n'):
                self._add_line(f"    {Colors.GRAY}{Symbols.PIPE}{Colors.RESET} {line}")

    def failed(self, message: str, details: str = None):
        """Log failed result."""
        self._add_line(f"  {Colors.BRIGHT_RED}{Symbols.CROSS} FAIL:{Colors.RESET} {message}")
        if details:
            for line in details.split('\n'):
                self._add_line(f"    {Colors.GRAY}{Symbols.PIPE}{Colors.RESET} {line}")

    def skipped(self, message: str, details: str = None):
        """Log skipped result."""
        self._add_line(f"  {Colors.BRIGHT_YELLOW}{Symbols.CIRCLE} SKIP:{Colors.RESET} {message}")
        if details:
            for line in details.split('\n'):
                self._add_line(f"    {Colors.GRAY}{Symbols.PIPE}{Colors.RESET} {line}")

    def get_output(self) -> str:
        """Get all captured output."""
        return "\n".join(self._output_lines)
