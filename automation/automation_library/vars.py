#  Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""
vars.py

This module stores configuration details for connecting to the OIM server
and executing validation tasks. The variables are used across automation
scripts in the automation_library.
"""

from typing import Final

#: Username for OIM server login
USERNAME: Final[str] = ""

#: Password for OIM server login
PASSWORD: Final[str] = ""

#: IP address of the OIM server
IP: Final[str] = ""
