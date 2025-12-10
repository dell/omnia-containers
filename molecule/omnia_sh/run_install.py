#!/usr/bin/env python3
"""
Run omnia.sh --install for Molecule converge.
"""

import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from automation_library.functions.omnia_sh_func import run_omnia_sh_install, check_prerequisites

# Check prerequisites first
prereq = check_prerequisites()
if not prereq['passed']:
    print('Prerequisites check failed')
    for check in prereq['checks']:
        if not check['passed']:
            print(f"  FAILED: {check['name']}")
            if 'errors' in check:
                for err in check['errors']:
                    print(f"    - {err}")
    sys.exit(1)

# Run install
result = run_omnia_sh_install()
if not result['success']:
    print(f"Install failed: {result.get('error', 'Unknown error')}")
    sys.exit(1)

print('omnia.sh --install completed successfully')
