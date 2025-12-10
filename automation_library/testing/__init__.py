"""
Testing utilities for molecule/pytest tests.

This module provides shared fixtures and utilities for testinfra tests
that can be reused across multiple molecule scenarios.

Usage:
    from automation_library.testing import get_testinfra_host
"""

from .testinfra_utils import get_testinfra_host, load_user_config, is_local_ip

__all__ = [
    "get_testinfra_host",
    "load_user_config",
    "is_local_ip",
]
