"""
Pytest/Testinfra configuration for omnia_sh tests.

The shared 'host' fixture is inherited from molecule/conftest.py.
Add scenario-specific fixtures here if needed.
"""

# No additional fixtures needed - using shared host fixture from molecule/conftest.py
# 
# To add scenario-specific fixtures:
#
# import pytest
# 
# @pytest.fixture(scope="module")
# def omnia_sh_specific_fixture():
#     return {"key": "value"}
