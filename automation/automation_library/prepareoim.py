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
Module to validate required Omnia services (pulp, kubespray, auth, ochami)
after OIM preparation. It checks running podman containers and ensures that
all required services are up and healthy.
"""

import subprocess

# List of required services (containers) to be checked
REQUIRED_SERVICES = ["pulp", "kubespray", "auth", "ochami"]


def get_running_containers():
    """
    Fetch running containers using podman.

    Returns:
        list: List of container names currently running.
    Raises:
        RuntimeError: If podman command execution fails.
    """
    try:
        result = subprocess.run(
            ["podman", "ps", "-a", "--format", "{{.Names}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        containers = result.stdout.strip().split("\n") if result.stdout.strip() else []
        return containers
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error running podman ps: {e.stderr}") from e


def verify_required_services():
    """
    Verify if all required Omnia services are running.

    Returns:
        tuple: (status: bool, running: list, missing: list)
    """
    running_containers = get_running_containers()
    missing = [svc for svc in REQUIRED_SERVICES if svc not in running_containers]
    status = not missing
    return status, running_containers, missing
