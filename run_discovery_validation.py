#!/usr/bin/env python3
"""Discovery Workflow Validation Runner.

Runs the discovery workflow validation suite and exits with 0/1.

Usage:
    python3 run_discovery_validation.py [OPTIONS]

Options:
    --no-report   Don't save report to file
    --debug       Show debug messages
    --help        Show this help
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from automation_library.core.formatting import set_debug_mode
from automation_library.core.host import get_testinfra_host
from automation_library.functions.discovery_func import run_all_discovery_validations


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    save_report = "--no-report" not in sys.argv
    debug_mode = "--debug" in sys.argv

    set_debug_mode(debug_mode)

    host = get_testinfra_host()
    result = run_all_discovery_validations(host, save_report=save_report)

    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
