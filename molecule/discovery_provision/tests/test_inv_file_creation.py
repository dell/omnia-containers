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

import pytest

CONTAINER_NAME = "omnia_core"

def test_omnia_inventroy_files(run_sshpass_command):
    
    print("\nVerifying omnia_inventory files")
    
    files_to_be_created = ["cluster_layout", "compute_cpu_amd", "compute_cpu_intel", "compute_gpu_amd", "compute_gpu_intel", "compute_gpu_nvidia", "compute_hostname_ip"]
    
    files_created = []
    files_not_created = []
    
    cmd = f"podman exec -it {CONTAINER_NAME} ls /opt/omnia/omnia_inventory/"
    
    for inv in files_to_be_created:
        
    
        result = run_sshpass_command(cmd)
        if inv in result.stdout:
            files_created.append(inv)
        else:
            files_not_created.append(inv)
    
    if files_created:
        print("\nFollowing inventory files exist:\n" + "\n".join(files_created))
    
    assert files_created, print(f"\nNo inventory files exist in omnia_inventory.")
    
    assert not files_not_created, print("\nFollowing Inventory files are not created:\n" + "\n".join(files_not_created))
    
    print("\nAll the inventory files exist.")
    
def test_compute_hostname_ip(run_sshpass_command):
    
    print("\nVerifying that the compute_hostname_ip file is not empty.")
    
    file_path = "/opt/omnia/omnia_inventory/compute_hostname_ip"
    cmd = f"podman exec -it {CONTAINER_NAME} cat {file_path}"
    
    result = run_sshpass_command(cmd)
    assert result.returncode == 0, f"Failed to read file: {result.stderr}"

    lines = result.stdout.strip().splitlines()
    assert len(lines) > 2, print(f"\nContents is missing from file compute_hostname_ip.")
    
    print("\ncompute_hostname_ip file is not empty.")
