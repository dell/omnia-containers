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
Loads required environment variables for remote SSH operations.

Exits with an error if any variable is missing.
"""

import os
import sys
from typing import Optional

def get_env_var(var_name: str) -> Optional[str]:
    """
    Fetch an environment variable and exit if it's not found.
    """
    value = os.getenv(var_name)
    if not value:
        sys.exit(f"Missing required environment variable: {var_name}")
    return value

DEST_IP: str = get_env_var("DEST_IP")
DEST_USER: str = get_env_var("DEST_USER")
DEST_PASS: str = get_env_var("DEST_PASS")
LOCAL_FILE: str = get_env_var("LOCAL_FILE")
REMOTE_PATH: str = get_env_var("REMOTE_PATH")
