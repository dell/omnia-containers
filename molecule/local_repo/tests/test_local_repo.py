# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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

import subprocess
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
import config

def test_softwares_downloaded():
    ip = config.OIM_IP
    password = config.OIM_PASS

    ssh_command = [
        "sshpass", "-p", password,
        "ssh", "-o", "StrictHostKeyChecking=no",
        f"root@{ip}",
        "podman exec omnia_core /bin/bash -c \"cat /opt/omnia/log/local_repo/software.csv | grep fail\""
    ]

    try:
        result = subprocess.run(ssh_command, capture_output=True, text=True, timeout=15)
    except Exception as e:
        pytest.fail(f"\n❌ SSH or command execution failed: {e}")

    if result.returncode not in [0, 1]:
        pytest.fail(f"\n❌ Command error: {result.stderr.strip()}")

    output = result.stdout.strip()

    if output:
        failed_packages = [line.split(",")[0] for line in output.splitlines()]
        print(f"\n❌ The following packages failed: {', '.join(failed_packages)}")
        pytest.fail("One or more packages failed to install.")
    else:
        print("\n✅ All packages installed successfully.")
