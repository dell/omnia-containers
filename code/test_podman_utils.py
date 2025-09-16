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

"""Tests for PodmanRemote utility using pytest."""

import subprocess  # Standard library
import pytest      # Third-party
import paramiko    # Third-party

from podman_utils import PodmanRemote  # Local modules
import config


def get_remote_containers(user, host, password):
    """
    Get a list of running container names directly using SSH and paramiko.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username=user, password=password)
    _, stdout, _ = ssh.exec_command("podman ps --format '{{.Names}}'")
    containers = stdout.read().decode().strip().split('\n')
    ssh.close()
    return [c for c in containers if c]


@pytest.fixture(scope="session")
def podman():
    """
    Fixture to create a PodmanRemote client for all tests.
    """
    return PodmanRemote(config.USER, config.HOST, config.PASSWORD)

@pytest.fixture(scope="session")
def containers():
    """
    Fixture to get list of running containers for use in other tests.
    """
    containers_list = get_remote_containers(config.USER, config.HOST, config.PASSWORD)
    if not containers_list:
        pytest.skip("No running containers found on remote host to test")
    return containers_list


def test_list_running_containers(podman):
    """
    Test retrieving the list of running containers.
    """
    print("Checking podman object:", podman)

    running_containers = podman.list_running_containers()
    print("Running containers:", running_containers)

    assert isinstance(running_containers, list)
    for container in running_containers:
        assert isinstance(container, str)



VALID_CONTAINERS = [
    'mysqldb',
    'activemq',
    'idrac_telemetry_receiver',
    'prometheus_pump',
    'prometheus',
]


def test_get_container_logs(podman, containers):
    """
    Test getting logs from specific valid containers if running.
    """
    running_valid_containers = [c for c in VALID_CONTAINERS if c in containers]

    if not running_valid_containers:
        pytest.skip(f"None of the valid containers {VALID_CONTAINERS} found in running containers")

    for container in running_valid_containers:
        try:
            logs = podman.get_container_logs(container)
            print(f"\n--- Logs for container '{container}': ---\n{logs}\n--- End logs ---\n")
            assert isinstance(logs, str)
            if logs == "":
                pytest.skip(f"Logs for container '{container}' are empty")
        except subprocess.CalledProcessError as err:
            pytest.fail(
                f"get_container_logs failed for '{container}': {err}"
            )


def test_start_container(podman, containers):
    """
    Test starting containers using PodmanRemote.
    """
    for container_name in containers:
        try:
            output = podman.start_container(container_name)
            assert (
                container_name in output
                or "started" in output.lower()
                or "already running" in output.lower()
            )
        except subprocess.CalledProcessError as err:
            pytest.fail(f"start_container failed for {container_name}: {err}")


def test_stop_container(podman, containers):
    """
    Test stopping containers using PodmanRemote.
    """
    for container_name in containers:
        try:
            output = podman.stop_container(container_name)
            assert (
                container_name in output
                or "stopped" in output.lower()
                or "already stopped" in output.lower()
            )
        except subprocess.CalledProcessError as err:
            pytest.fail(f"stop_container failed for {container_name}: {err}")


def test_remove_container(podman, containers):
    """
    Test removing containers using PodmanRemote (forced removal).
    """
    for container_name in containers:
        try:
            result = podman.remove_container(container_name)
            assert (
                container_name in result
                or "No such container" in result
                or "Removed" in result
            )
        except subprocess.CalledProcessError as err:
            pytest.fail(
                f"Failed to remove container '{container_name}': {err.output.strip()}"
            )
        except subprocess.SubprocessError as err:
            pytest.fail(
                f"Subprocess error while removing container '{container_name}': {err}"
            )
