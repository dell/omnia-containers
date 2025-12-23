"""
OIM Prerequisite Checks Module

This module contains all prerequisite validation checks for OIM deployment.
Organized into logical function groups while preserving the original functionality.
"""

from .functions.main import run_all_prereq_checks

__all__ = ["run_all_prereq_checks"]
