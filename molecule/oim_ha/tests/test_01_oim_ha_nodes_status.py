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
import time
from datetime import datetime, timedelta

@pytest.mark.qtest_id("TC-3694")
def test_oim_ha_nodes_booted(run_sshpass_command):
    print("\nVerifying OIM HA nodes boot status")
    try:
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

            # 2. Parse output
            try:
                output = result.stdout.strip()
                if not output:
                    print("Empty output from nodels command")
                    time.sleep(retry_interval)
                    continue

                # Split output into lines
                lines = output.split('\n')
                for line in lines:
                    if not line.strip():
                        continue

                    # Split line into node and status
                    parts = line.split()
                    if len(parts) < 2:
                        print(f"Invalid line format: {line}")
                        continue

                    node = parts[0]
                    status = parts[1]
                    
                    if status.lower() == "booted":
                        booted_nodes.append(node)
                    else:
                        not_booted_nodes.append(f"{node}: {status}")

                # Print status
                print(f"\nBooted nodes: {booted_nodes}")
                print(f"Not booted nodes: {not_booted_nodes}")

                # Check if all nodes are booted
                if not not_booted_nodes:
                    print("\nAll nodes are booted!")
                    return

                # Wait before next check
                print(f"Waiting {retry_interval} seconds before next check...")
                time.sleep(retry_interval)

            except Exception as e:
                print(f"Error parsing node status output: {str(e)}")
                time.sleep(retry_interval)
                continue

        # If we reach here, timeout occurred
        pytest.fail(f"Timeout waiting for nodes to boot. Still unbooted: {not_booted_nodes}")

    except Exception as e:
        pytest.fail(f"Error in test_oim_ha_nodes_booted: {str(e)}")
