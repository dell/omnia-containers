# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""
Loads environment variables for remote connection and file transfer.

Expected variables:
- DEST_IP
- DEST_USER
- DEST_PASS
- LOCAL_FILE
- REMOTE_PATH
"""

import os
import sys

DEST_IP: str = os.getenv("DEST_IP")
DEST_USER: str = os.getenv("DEST_USER")
DEST_PASS: str = os.getenv("DEST_PASS")
LOCAL_FILE: str = os.getenv("LOCAL_FILE")
REMOTE_PATH: str = os.getenv("REMOTE_PATH")

# Validate required variables
REQUIRED_VARS = {
    "DEST_IP": DEST_IP,
    "DEST_USER": DEST_USER,
    "DEST_PASS": DEST_PASS,
    "LOCAL_FILE": LOCAL_FILE,
    "REMOTE_PATH": REMOTE_PATH,
}

missing = [key for key, value in REQUIRED_VARS.items() if not value]
if missing:
    sys.exit(f"Missing required environment variables: {', '.join(missing)}")
