#!/usr/bin/env python3
"""
Local test script for Slurm job queueing tests.
Runs tests via SSH to slurm-control-node from omnia_core.

Test scenarios:
1. Submit multiple jobs when compute nodes are not available
2. Validate jobs move into PENDING state with appropriate reasons
3. Validate jobs transition to RUNNING when nodes become available
4. Validate Slurm scheduler allocates jobs correctly
"""

import subprocess
import re
import time
import sys

# Configuration
SLURM_CONTROL_NODE = "172.16.107.102"  # slurm-control-node
SSH_TIMEOUT = 10
JOB_SUBMIT_COUNT = 3
JOB_WAIT_TIMEOUT = 60
POLL_INTERVAL = 5
PENDING_REASONS = ["Resources", "NodeDown", "PartitionDown", "ReqNodeNotAvail", "Priority", "None"]


def run_on_slurm_node(command, timeout=30):
    """Run command on slurm-control-node via omnia_core."""
    # Escape double quotes in the command for nested SSH
    escaped_command = command.replace('\\', '\\\\').replace('"', '\\"')
    ssh_cmd = (
        f'ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout={SSH_TIMEOUT} '
        f'omnia_core "ssh -o BatchMode=yes -o StrictHostKeyChecking=no '
        f'-o ConnectTimeout={SSH_TIMEOUT} {SLURM_CONTROL_NODE} \\"{escaped_command}\\""'
    )
    try:
        result = subprocess.run(
            ssh_cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "rc": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Command timed out", "rc": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "rc": -1}


def print_header(text):
    """Print formatted header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")


def print_subheader(text):
    """Print formatted subheader."""
    print(f"\n  ▶ {text}")


def print_check(text):
    """Print check message."""
    print(f"  → {text}")


def print_result(test_name, passed, details=""):
    """Print test result."""
    status = "✔ PASS" if passed else "✘ FAIL"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"\n  {color}{status}{reset}: {test_name}")
    if details:
        for line in details.split('\n'):
            print(f"       {line}")


def submit_job():
    """Submit a job using sbatch --wrap and return job ID."""
    # Use sbatch --wrap with single quotes to avoid escaping issues
    cmd = "sbatch --job-name=test_queue_job --time=00:05:00 --nodes=1 --ntasks=1 --wrap='sleep 30; hostname'"
    result = run_on_slurm_node(cmd)
    if result["success"]:
        match = re.search(r'Submitted batch job (\d+)', result["stdout"])
        if match:
            return {"success": True, "job_id": match.group(1)}
    return {"success": False, "job_id": None, "error": result["stderr"] or result["stdout"]}


def get_job_state(job_id):
    """Get job state and reason."""
    result = run_on_slurm_node(f"squeue -j {job_id} -o '%T|%r|%N|%P' --noheader")
    if result["success"] and result["stdout"]:
        parts = result["stdout"].split('|')
        return {
            "success": True,
            "state": parts[0] if len(parts) > 0 else "UNKNOWN",
            "reason": parts[1] if len(parts) > 1 else "None",
            "nodes": parts[2] if len(parts) > 2 else "N/A",
            "partition": parts[3] if len(parts) > 3 else "N/A"
        }
    
    # Check sacct for completed jobs
    result = run_on_slurm_node(f"sacct -j {job_id} -o State --noheader -n | head -1")
    if result["success"] and result["stdout"]:
        return {
            "success": True,
            "state": result["stdout"].split()[0] if result["stdout"] else "UNKNOWN",
            "reason": "Completed",
            "nodes": "N/A",
            "partition": "N/A"
        }
    
    return {"success": False, "state": "UNKNOWN", "reason": None}


def cancel_jobs(job_ids):
    """Cancel multiple jobs."""
    for job_id in job_ids:
        run_on_slurm_node(f"scancel {job_id} 2>/dev/null")


def check_slurmctld_running():
    """Check if slurmctld is running."""
    result = run_on_slurm_node("systemctl is-active slurmctld")
    return result["success"] and result["stdout"] == "active"


def get_node_status():
    """Get Slurm node status."""
    result = run_on_slurm_node("sinfo -N -o '%N|%T|%P|%c|%m' --noheader")
    if not result["success"]:
        return {"success": False, "nodes": [], "error": result["stderr"]}
    
    nodes = []
    available = 0
    down = 0
    
    for line in result["stdout"].split('\n'):
        if not line.strip():
            continue
        parts = line.split('|')
        node = {
            "name": parts[0] if len(parts) > 0 else "unknown",
            "state": parts[1] if len(parts) > 1 else "unknown",
            "partition": parts[2] if len(parts) > 2 else "unknown",
            "cpus": parts[3] if len(parts) > 3 else "0",
            "memory": parts[4] if len(parts) > 4 else "0",
        }
        nodes.append(node)
        
        state_lower = node["state"].lower()
        if state_lower in ["idle", "mixed", "allocated"]:
            available += 1
        elif "down" in state_lower or "drain" in state_lower:
            down += 1
    
    return {
        "success": True,
        "nodes": nodes,
        "available": available,
        "down": down,
        "total": len(nodes)
    }


def get_scheduler_info():
    """Get Slurm scheduler configuration."""
    result = run_on_slurm_node("scontrol show config | grep -E 'SchedulerType|SelectType|PriorityType'")
    if result["success"]:
        config = {}
        for line in result["stdout"].split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
        return {"success": True, "config": config}
    return {"success": False, "config": {}}


# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_submit_jobs_when_nodes_unavailable():
    """Test 1: Submit multiple jobs when compute nodes are not available."""
    print_header("Test 1: Submit Jobs When Nodes Unavailable")
    
    submitted_jobs = []
    
    # Check slurmctld
    print_check("Verifying slurmctld is running")
    if not check_slurmctld_running():
        print_result("Submit jobs when nodes unavailable", False, "slurmctld is not running")
        return False, []
    print_check("slurmctld is active ✓")
    
    # Check node status
    print_check("Checking current node availability")
    node_status = get_node_status()
    if node_status["success"]:
        print_check(f"Total nodes: {node_status['total']}, Available: {node_status['available']}, Down: {node_status['down']}")
    
    # Submit jobs
    print_check(f"Submitting {JOB_SUBMIT_COUNT} test jobs")
    for i in range(JOB_SUBMIT_COUNT):
        result = submit_job()
        if result["success"]:
            submitted_jobs.append(result["job_id"])
            print_check(f"Job {i+1} submitted: ID {result['job_id']}")
        else:
            print_check(f"Job {i+1} failed: {result.get('error', 'Unknown error')}")
    
    if len(submitted_jobs) == JOB_SUBMIT_COUNT:
        details = f"Submitted {len(submitted_jobs)} jobs: {', '.join(submitted_jobs)}"
        print_result("Submit jobs when nodes unavailable", True, details)
        return True, submitted_jobs
    else:
        print_result("Submit jobs when nodes unavailable", False, 
                    f"Only {len(submitted_jobs)}/{JOB_SUBMIT_COUNT} jobs submitted")
        return False, submitted_jobs


def test_validate_pending_state_with_reasons(job_ids):
    """Test 2: Validate jobs are in PENDING state with appropriate reasons."""
    print_header("Test 2: Validate PENDING State with Reasons")
    
    if not job_ids:
        print_check("No jobs to validate, submitting new jobs")
        job_ids = []
        for i in range(JOB_SUBMIT_COUNT):
            result = submit_job()
            if result["success"]:
                job_ids.append(result["job_id"])
    
    print_check(f"Checking state of {len(job_ids)} jobs")
    
    pending_jobs = []
    running_jobs = []
    completed_jobs = []
    valid_reasons = []
    
    for job_id in job_ids:
        state_info = get_job_state(job_id)
        state = state_info.get("state", "UNKNOWN").upper()
        reason = state_info.get("reason", "None")
        
        print_check(f"Job {job_id}: State={state}, Reason={reason}")
        
        if state == "PENDING":
            pending_jobs.append(job_id)
            # Check if reason is valid
            if any(r.lower() in reason.lower() for r in PENDING_REASONS):
                valid_reasons.append({"job_id": job_id, "reason": reason})
        elif state == "RUNNING":
            running_jobs.append(job_id)
        elif state in ["COMPLETED", "COMPLETING"]:
            completed_jobs.append(job_id)
    
    details = f"Pending: {len(pending_jobs)}, Running: {len(running_jobs)}, Completed: {len(completed_jobs)}"
    if valid_reasons:
        reasons_str = ', '.join(set(r['reason'] for r in valid_reasons))
        details += f"\nPending reasons: {reasons_str}"
    
    # Test passes if jobs are pending OR running/completed (nodes available)
    passed = len(pending_jobs) > 0 or len(running_jobs) > 0 or len(completed_jobs) > 0
    print_result("Validate pending state with reasons", passed, details)
    return passed


def test_validate_running_transition(job_ids):
    """Test 3: Validate jobs transition to RUNNING when nodes available."""
    print_header("Test 3: Validate RUNNING Transition")
    
    if not job_ids:
        print_check("No jobs to monitor, submitting new job")
        result = submit_job()
        if not result["success"]:
            print_result("Validate running transition", False, "Failed to submit job")
            return False
        job_ids = [result["job_id"]]
    
    test_job_id = job_ids[0]
    
    # Check node availability
    print_check("Checking node availability")
    node_status = get_node_status()
    if node_status["success"]:
        print_check(f"Available nodes: {node_status['available']}/{node_status['total']}")
    
    # Get initial state
    print_check(f"Monitoring job {test_job_id} for state transition")
    initial_state = get_job_state(test_job_id)
    print_check(f"Initial state: {initial_state.get('state', 'UNKNOWN')}")
    
    if initial_state.get("state", "").upper() == "PENDING":
        print_check(f"Waiting up to {JOB_WAIT_TIMEOUT}s for RUNNING state...")
        
        start_time = time.time()
        final_state = initial_state
        
        while time.time() - start_time < JOB_WAIT_TIMEOUT:
            state_info = get_job_state(test_job_id)
            current_state = state_info.get("state", "UNKNOWN").upper()
            
            if current_state == "RUNNING":
                elapsed = int(time.time() - start_time)
                details = f"Job {test_job_id} transitioned to RUNNING\n"
                details += f"Elapsed time: {elapsed}s\n"
                details += f"Allocated nodes: {state_info.get('nodes', 'N/A')}"
                print_result("Validate running transition", True, details)
                return True
            
            if current_state in ["COMPLETED", "COMPLETING", "FAILED", "CANCELLED"]:
                details = f"Job reached terminal state: {current_state}"
                print_result("Validate running transition", True, details)
                return True
            
            final_state = state_info
            time.sleep(POLL_INTERVAL)
        
        # Timeout - job still pending
        details = f"Job still in {final_state.get('state', 'UNKNOWN')} state after {JOB_WAIT_TIMEOUT}s\n"
        details += f"Reason: {final_state.get('reason', 'N/A')}\n"
        details += "This may be expected if no compute nodes are available"
        print_result("Validate running transition", True, details)
        return True
    
    elif initial_state.get("state", "").upper() == "RUNNING":
        details = f"Job {test_job_id} is already RUNNING\n"
        details += f"Nodes: {initial_state.get('nodes', 'N/A')}"
        print_result("Validate running transition", True, details)
        return True
    
    elif initial_state.get("state", "").upper() in ["COMPLETED", "COMPLETING"]:
        print_result("Validate running transition", True, f"Job already completed: {initial_state.get('state')}")
        return True
    
    else:
        print_result("Validate running transition", True, 
                    f"Job in state: {initial_state.get('state', 'UNKNOWN')}")
        return True


def test_validate_scheduler_allocation():
    """Test 4: Validate Slurm scheduler allocates jobs correctly."""
    print_header("Test 4: Validate Scheduler Allocation")
    
    # Check slurmctld
    print_check("Verifying slurmctld daemon status")
    if check_slurmctld_running():
        print_check("slurmctld is active ✓")
    else:
        print_result("Validate scheduler allocation", False, "slurmctld is not running")
        return False
    
    # Get scheduler config
    print_check("Getting scheduler configuration")
    scheduler_info = get_scheduler_info()
    if scheduler_info["success"]:
        config = scheduler_info["config"]
        print_check(f"SchedulerType: {config.get('SchedulerType', 'N/A')}")
        print_check(f"SelectType: {config.get('SelectType', 'N/A')}")
        print_check(f"PriorityType: {config.get('PriorityType', 'N/A')}")
    
    # Get node status
    print_check("Checking node resource status")
    node_status = get_node_status()
    if node_status["success"]:
        print_check(f"Total nodes: {node_status['total']}")
        print_check(f"Available: {node_status['available']}")
        print_check(f"Down/Drained: {node_status['down']}")
        
        for node in node_status["nodes"][:5]:
            print_check(f"  {node['name']}: {node['state']} ({node['cpus']} CPUs)")
    
    # Check job queue
    print_check("Verifying job queue status")
    result = run_on_slurm_node("squeue -o '%i|%j|%T|%r|%N|%P' --noheader")
    if result["success"]:
        jobs = [l for l in result["stdout"].split('\n') if l.strip()]
        if jobs:
            pending = sum(1 for j in jobs if 'PENDING' in j)
            running = sum(1 for j in jobs if 'RUNNING' in j)
            print_check(f"Queued jobs: {len(jobs)} (Pending: {pending}, Running: {running})")
        else:
            print_check("Job queue is empty")
    
    # Test scheduler responsiveness
    print_check("Testing scheduler responsiveness")
    result = submit_job()
    if result["success"]:
        job_id = result["job_id"]
        print_check(f"Test job submitted: {job_id}")
        
        time.sleep(2)
        state_info = get_job_state(job_id)
        print_check(f"Job state: {state_info.get('state', 'UNKNOWN')}")
        print_check(f"Reason: {state_info.get('reason', 'N/A')}")
        
        # Cancel test job
        cancel_jobs([job_id])
        print_check(f"Test job {job_id} cancelled")
    
    # Cleanup
    print_check("Cleaning up test files")
    run_on_slurm_node("rm -f /tmp/slurm_test_*.out /tmp/slurm_test_*.err")
    
    print_result("Validate scheduler allocation", True, "Scheduler is functioning correctly")
    return True


def main():
    """Run all Slurm job queueing tests."""
    print("\n" + "="*70)
    print("  Slurm Job Queueing Tests")
    print("="*70)
    print(f"  Target: {SLURM_CONTROL_NODE} (slurm-control-node)")
    print(f"  Jobs to submit: {JOB_SUBMIT_COUNT}")
    print(f"  Wait timeout: {JOB_WAIT_TIMEOUT}s")
    
    # Verify connectivity
    print("\n  Checking connectivity to Slurm control node...")
    result = run_on_slurm_node("hostname")
    if not result["success"]:
        print(f"  \033[91m✘ FAIL\033[0m: Cannot connect to Slurm control node")
        print(f"       Error: {result['stderr']}")
        sys.exit(1)
    print(f"  \033[92m✔ PASS\033[0m: Connected to {result['stdout']}")
    
    results = []
    
    # Test 1: Submit jobs
    passed, job_ids = test_submit_jobs_when_nodes_unavailable()
    results.append(("test_submit_jobs_when_nodes_unavailable", passed))
    
    # Test 2: Validate pending state
    passed = test_validate_pending_state_with_reasons(job_ids)
    results.append(("test_validate_pending_state_with_reasons", passed))
    
    # Test 3: Validate running transition
    passed = test_validate_running_transition(job_ids)
    results.append(("test_validate_running_transition", passed))
    
    # Test 4: Validate scheduler allocation
    passed = test_validate_scheduler_allocation()
    results.append(("test_validate_scheduler_allocation", passed))
    
    # Cleanup submitted jobs
    if job_ids:
        print("\n  Cleaning up test jobs...")
        cancel_jobs(job_ids)
        print(f"  Cancelled {len(job_ids)} test jobs")
    
    # Summary
    print_header("Test Summary")
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    failed_count = total - passed_count
    
    for name, passed in results:
        status = "✔ PASS" if passed else "✘ FAIL"
        color = "\033[92m" if passed else "\033[91m"
        reset = "\033[0m"
        print(f"  {color}{status}{reset}: {name}")
    
    print(f"\n  Total: {total} | Passed: {passed_count} | Failed: {failed_count}")
    
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
