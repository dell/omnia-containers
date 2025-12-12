"""
Omnia Automation Library

A Python library for automating OIM prerequisite checks and omnia.sh testing.

Modules:
    - core: Formatting, logging, host utilities, reports
    - functions: Prereq checks, omnia.sh operations
    - messages: User-facing messages
    - vars: Configuration variables

Usage:
    from automation_library.core import TestLogger, Colors
    from automation_library.functions import run_all_prereq_checks
"""

__version__ = "0.1.0"

from .core import Colors, Symbols, log, set_debug_mode, TestLogger

__all__ = ["Colors", "Symbols", "log", "set_debug_mode", "TestLogger", "__version__"]
