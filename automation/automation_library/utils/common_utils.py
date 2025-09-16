# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import subprocess
import os

def run_command(command):
    """
    Execute a shell command and return its stdout, stderr, and exit code.
    """
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def check_service_status(service_name, service_status_command):
    """
    Check if the given systemd service is active.
    """
    cmd = service_status_command.format(service_name=service_name)
    stdout, stderr, return_code = run_command(cmd)
    if return_code == 0:
        return f"Service '{service_name}' is active."
    return f"Service '{service_name}' is NOT active."


def check_container_status(container_name, list_containers_command):
    """
    Check if the container exists in the list of containers.
    """
    stdout, stderr, return_code = run_command(list_containers_command)
    container_list = stdout.splitlines()
    if container_name in container_list:
        return f"Container '{container_name}' exists."
    return f"Container '{container_name}' does NOT exist."

def check_systemd_service_file(systemd_service_path, service_name):
    """
    Check if the systemd service file exists at the specified path.
    """
    if os.path.exists(systemd_service_path):
        return f"Systemd service file '{service_name}' exists at '{systemd_service_path}'."
    return f"Systemd service file '{service_name}' does NOT exist at '{systemd_service_path}'."

def check_quadlet_file(quadlet_file_path):
    """
    Check if a quadlet file exists at the specified path
    """
    if os.path.exists(quadlet_file_path):
        return f"Quadlet file exists at '{quadlet_file_path}'."
    return f"Quadlet file does NOT exist at '{quadlet_file_path}'."


def check_metadata_file_in_container_exec(container_name, metadata_path, metadata_command):
    """
    Check metadata file existence using podman exec inside the container.
    """
    cmd = metadata_command.format(container_name=container_name, metadata_path=metadata_path)
    stdout, stderr, return_code = run_command(cmd)
    if return_code == 0 and os.path.basename(metadata_path) in stdout:
        return f"Metadata file '{metadata_path}' exists inside container '{container_name}'."
    return f"Metadata file '{metadata_path}' does NOT exist inside container '{container_name}'."


def check_systemd_unit_status(target_name, status_command, expected_absence_msg):
    """
    Check the status of a systemd unit (e.g., service, target).
    Returns a user-friendly message indicating if it exists or not.
    """
    cmd = status_command.format(target_name=target_name)
    stdout, stderr, return_code = run_command(cmd)
    output = stdout + stderr

    if expected_absence_msg in output:
        return f"Systemd unit '{target_name}' does NOT exist."
    else:
        return f"Systemd unit '{target_name}' still exists or is inactive."
