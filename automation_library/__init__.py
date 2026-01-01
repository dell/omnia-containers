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

A Python library for automating Omnia deployment verification and testing.

Modules:
    - core: Formatting, logging, host utilities, reports
    - checks: Prerequisite checks and validations
    - omnia_sh: omnia.sh operations and verification
    - local_repo: Local repository automation
    - prepare_oim: OIM preparation automation
    - telemetry: Telemetry (iDRAC, Kafka, LDMS) automation and verification
"""

__version__ = "0.1.0"

from .core import Colors, Symbols, log, set_debug_mode, TestLogger

__all__ = ["Colors", "Symbols", "log", "set_debug_mode", "TestLogger", "__version__"]
