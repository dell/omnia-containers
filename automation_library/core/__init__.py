"""
Core utilities for automation library.

Modules:
- formatting: Colors, Symbols, log(), TestLogger
- host: Testinfra host connection utilities
- report: Test report generation
"""

from .formatting import Colors, Symbols, log, set_debug_mode, TestLogger, get_test_output
from .host import get_testinfra_host, load_user_config, load_omnia_sh_config
from .report import TestReport, get_current_report, set_current_report

__all__ = [
    # Formatting
    "Colors",
    "Symbols",
    "log",
    "set_debug_mode",
    "TestLogger",
    "get_test_output",
    # Host
    "get_testinfra_host",
    "load_user_config",
    "load_omnia_sh_config",
    # Report
    "TestReport",
    "get_current_report",
    "set_current_report",
]
