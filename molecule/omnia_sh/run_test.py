#!/usr/bin/env python3
"""
Omnia.sh Test Runner

This script runs the omnia.sh test suite using the automation library.
It can be run directly without Molecule for quick testing.

Usage:
    python3 molecule/omnia_sh/run_test.py
    python3 molecule/omnia_sh/run_test.py --debug

Author: Dell Technologies
"""

import os
import sys
import argparse

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from automation_library.functions.omnia_sh_func import (
    run_full_test,
    set_debug_mode,
)
from automation_library.vars.omnia_sh_vars import OMNIA_SH_VARS, get_omnia_sh_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run omnia.sh tests")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    
    if args.debug:
        set_debug_mode(True)
    
    print("=" * 80)
    print("OMNIA.SH TEST RUNNER")
    print("=" * 80)
    print()
    print(f"Configuration from user_config.yml:")
    print(f"  Share Option    : {OMNIA_SH_VARS['share_option']}")
    print(f"  NFS Server IP   : {OMNIA_SH_VARS['nfs_server_ip'] or '(not set)'}")
    print(f"  NFS Share Path  : {OMNIA_SH_VARS['nfs_share_path'] or '(not set)'}")
    print(f"  Omnia Shared Path: {OMNIA_SH_VARS['omnia_shared_path']}")
    print(f"  omnia.sh Path   : {get_omnia_sh_path()}")
    print(f"  Container Name  : {OMNIA_SH_VARS['container_name']}")
    print(f"  SSH Port        : {OMNIA_SH_VARS['ssh_port']}")
    print(f"  Cleanup After   : {OMNIA_SH_VARS['cleanup_after_test']}")
    print()
    print("=" * 80)
    print()
    
    # Run full test
    result = run_full_test()
    
    print()
    print("=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    
    if result["passed"]:
        print("\n  ✔ ALL TESTS PASSED\n")
        return 0
    else:
        print(f"\n  ✘ {result['failed_count']} TEST(S) FAILED\n")
        print("Failed tests:")
        for r in result["results"]:
            if not r["passed"]:
                print(f"  - {r['name']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
