"""
Omnia Automation Library

A Python library for automating OIM prerequisite checks and omnia.sh testing.

Modules:
    - core: Formatting, logging, host utilities, reports
    - checks: OIM prerequisite checks
    - local_repo: Local repository operations
    - omnia_sh: omnia.sh operations
    - prepare_oim: OIM preparation operations
    - build_images: Build image x86_64 operations

Usage:
    from automation_library.core import TestLogger, Colors
    from automation_library.checks import run_all_prereq_checks
    from automation_library.build_images import check_s3_container_running
"""

__version__ = "0.1.0"

from .core import Colors, Symbols, log, set_debug_mode, TestLogger

__all__ = ["Colors", "Symbols", "log", "set_debug_mode", "TestLogger", "__version__"]
