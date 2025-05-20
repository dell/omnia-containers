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
        print(f"\n⏳ [{datetime.now().strftime('%H:%M:%S')}] Checking node statuses...", flush=True)

        # 1. Get node statuses
        cmd = "podman exec -it omnia_provision nodels all nodelist.status"
        result = run_sshpass_command(cmd)

        if result.returncode != 0:
            print(f"\n❌ Failed to run 'nodels': {result.stderr}", flush=True)
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

        # ✅ Check if there are any nodes at all
        if not booted_nodes and not not_booted_nodes:
            raise AssertionError("\n❌ No nodes were found in the nodelist. Aborting test.")

        # Always print current boot status
        if booted_nodes:
            print("\n✅ Booted nodes:\n" + "\n".join(booted_nodes), flush=True)
            
        if not_booted_nodes:
            print("\n⏳ Still waiting for these nodes to boot:\n" + "\n".join(not_booted_nodes), flush=True)
            time.sleep(retry_interval)
            continue  # Retry boot status again in next cycle

        # All nodes booted, proceed to SSH check
        print("\n✅ All nodes are booted. Checking SSH access...", flush=True)

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
            print("\n❌ SSH failed for the following nodes from omnia_core:\n" + "\n".join(unreachable_nodes), flush=True)
            raise AssertionError(
                "\n❌ All nodes are booted, but SSH failed for the following nodes:\n" +
                "\n".join(unreachable_nodes)
            )
        
        assert reachable_nodes, f"\n❌ SSH failed for all the nodes from omnia_core."

        # All good!
        print("\n✅ All nodes are reachable via SSH from omnia_core.", flush=True)
        print("\n✅ SSH passed for:\n" + "\n".join(reachable_nodes), flush=True)
        return  # Test success

    # After 1 hour, timeout
    raise AssertionError("\n❌ Timeout: Nodes did not finish booting within 1 hour.")
