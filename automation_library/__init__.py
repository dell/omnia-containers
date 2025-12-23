# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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
