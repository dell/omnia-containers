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
import subprocess
import time
from datetime import datetime, timedelta

def test_nodes_booted(run_sshpass_command):
    """
    Retry for up to 1 hour to verify:
    - All nodes are in 'booted' state.
    - SSH works from omnia_core once nodes are booted.
    Fail immediately if SSH fails after boot is complete.
    """

    timeout = timedelta(hours=1)
    start_time = datetime.now()
    retry_interval = 10  # seconds

    while datetime.now() - start_time < timeout:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking node statuses...", flush=True)

        # 1. Get node statuses
        cmd = "podman exec -it omnia_provision nodels all nodelist.status"
        result = run_sshpass_command(cmd)

        if result.returncode != 0:
            print(f"\nFailed to run 'nodels': {result.stderr}", flush=True)
            time.sleep(retry_interval)
            continue

        not_booted_nodes = []
        booted_nodes = []

        for line in result.stdout.splitlines():
            if ":" not in line:
                continue
            node, status = line.split(":", 1)
            status = status.strip().lower()
            node = node.strip()
            if "booted" not in status and "install-complete" not in status:
                not_booted_nodes.append(f"{node}: {status}")
            else:
                booted_nodes.append(node)

        # Check if there are any nodes at all
        if not booted_nodes and not not_booted_nodes:
            raise AssertionError("\nNo nodes were found in the nodelist. Aborting test.")

        # Always print current boot status
        if booted_nodes:
            print("\nBooted nodes:\n" + "\n".join(booted_nodes), flush=True)
            
        if not_booted_nodes:
            print("\nStill waiting for these nodes to boot:\n" + "\n".join(not_booted_nodes), flush=True)
            time.sleep(retry_interval)
            continue  # Retry boot status again in next cycle

        # All nodes booted, proceed to SSH check
        print("\nAll nodes are booted. Checking SSH access...", flush=True)

        reachable_nodes = []
        unreachable_nodes = []

        for node in booted_nodes:
            cmd = (
                f"podman exec omnia_core ssh -o StrictHostKeyChecking=no "
                f"-o ConnectTimeout=5 {node} hostname"
            )
            result = run_sshpass_command(cmd)

            if result.returncode != 0:
                error_message = result.stderr.strip().splitlines()[0] if result.stderr else "Unknown error"
                unreachable_nodes.append(f"{node}: {error_message}")
            else:
                reachable_nodes.append(node)

        if reachable_nodes:
            print("\nSSH passed for the following nodes:\n" + "\n".join(reachable_nodes), flush=True)
    
        if unreachable_nodes:
            print("\nSSH failed for the following nodes from omnia_core:\n" + "\n".join(unreachable_nodes), flush=True)
            raise AssertionError(
                "\nAll nodes are booted, but SSH failed for the following nodes:\n" +
                "\n".join(unreachable_nodes)
            )
        
        assert reachable_nodes, f"\nSSH failed for all the nodes from omnia_core."

        # All good!
        print("\nAll nodes are reachable via SSH from omnia_core.", flush=True)
        print("\nSSH passed for:\n" + "\n".join(reachable_nodes), flush=True)
        return  # Test success

    # After 1 hour, timeout
    raise AssertionError("\nTimeout: Nodes did not finish booting within 1 hour.")
