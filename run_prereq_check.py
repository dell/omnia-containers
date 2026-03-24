#!/usr/bin/env python3
# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
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
OIM Prerequisite Check Runner

This script runs all OIM prerequisite checks and generates a detailed report.

Usage:
    python3 run_prereq_check.py [OPTIONS]

Options:
    --stop-on-failure      Stop running checks on first failure (overrides config)
    --continue-on-failure  Continue running checks even if one fails (overrides config)
    --no-report            Don't save report to file
    --debug                Show debug messages (verbose output)
    --help                 Show this help message

Note: By default, uses 'skip_on_failure' setting from user_config.yml
"""

import sys
import os

# Add the automation library to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from automation_library.checks.functions.main import run_all_prereq_checks
from automation_library.core.formatting import set_debug_mode


def main():
    """Main entry point."""
    # Show help
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)
    
    # Parse arguments - None means use config file setting
    stop_on_failure = None
    if "--stop-on-failure" in sys.argv:
        stop_on_failure = True
    elif "--continue-on-failure" in sys.argv:
        stop_on_failure = False
    
    save_report = "--no-report" not in sys.argv
    debug_mode = "--debug" in sys.argv
    
    # Set debug mode
    set_debug_mode(debug_mode)
    
    # Run checks
    result = run_all_prereq_checks(
        stop_on_failure=stop_on_failure,
        save_report=save_report
    )
    
    # Exit with appropriate code
    if result["passed"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
