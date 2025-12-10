"""
Shared Pytest/Testinfra configuration for ALL molecule scenarios.

This conftest is automatically loaded by pytest for all test files
under the molecule/ directory. Individual scenarios can override
fixtures by defining them in their own conftest.py.

Usage:
    molecule test -s omnia_sh      # Uses this shared conftest
    molecule test -s new_module    # Also uses this shared conftest
    molecule test                  # Runs all scenarios with shared conftest
"""

import os
import sys
import pytest

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from automation_library.testing import get_testinfra_host


@pytest.fixture(scope="module")
def host():
    """
    Shared testinfra host fixture for all molecule scenarios.
    
    Automatically connects to the OIM server specified in user_config.yml.
    If running on the OIM server itself, uses local connection.
    If running remotely, uses Ansible inventory from molecule.
    """
    return get_testinfra_host()
