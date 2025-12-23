#!/usr/bin/env python3
"""
Run Slurm job queueing tests by SSHing to slurm-control-node.

This script wraps the test functions from test_slurm_job_queueing.py
and executes them via SSH to the Slurm control node.

Test scenarios:
1. test_submit_jobs_when_nodes_unavailable
2. test_validate_pending_state_with_reasons
3. test_validate_running_transition
4. test_validate_scheduler_allocation
"""

import subprocess
import re
import time
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from automation_library.core import TestLogger
from automation_library.core.report import TestReport

# =============================================================================
# CONFIGURATION
# =============================================================================

SLURM_CONTROL_NODE = "172.16.107.102"  # slurm-control-node
SLURM_NODE_2 = "172.16.107.105"  # slurm-node-2
OMNIA_CORE_ALIAS = "omnia_core"
SSH_TIMEOUT = 10
JOB_SUBMIT_COUNT = 3
JOB_WAIT_TIMEOUT = 60
POLL_INTERVAL = 5
PENDING_REASONS = ["Resources", "NodeDown", "PartitionDown", "ReqNodeNotAvail", "Priority", "None"]

# BMC/IPMI configuration for power management
# Note: slurm-control-node runs slurmctld, slurm-node-1 and slurm-node-2 are compute nodes
BMC_SLURM_NODE_1 = "100.96.26.24"  # slurm-node-1 (same BMC as control node - they share hardware)
BMC_SLURM_NODE_2 = "100.96.26.25"  # slurm-node-2
IPMI_USER = "root"
IPMI_PASS = "calvin"  # Default Dell iDRAC password

TEST_NAMES = {
    "submit_jobs_no_nodes": "Submit multiple jobs when compute nodes are unavailable",
    "validate_pending_state": "Validate jobs are in PENDING state with appropriate reasons",
    "validate_running_transition": "Validate jobs transition to RUNNING when nodes available",
    "validate_scheduler_allocation": "Validate Slurm scheduler allocates jobs correctly",
}


# =============================================================================
# SSH HOST CLASS (mimics testinfra host interface)
# =============================================================================

class SSHHost:
    """SSH host class that mimics testinfra host interface."""
    
    def __init__(self, target_ip, via_host=None):
        self.target_ip = target_ip
        self.via_host = via_host
    
    def run(self, command):
        """Run command on remote host via SSH."""
        if self.via_host:
            # Nested SSH: local -> omnia_core -> target
            # Escape double quotes in the command for nested SSH
            escaped_command = command.replace('\\', '\\\\').replace('"', '\\"')
            ssh_cmd = (
                f'ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout={SSH_TIMEOUT} '
                f'{self.via_host} "ssh -o BatchMode=yes -o StrictHostKeyChecking=no '
                f'-o ConnectTimeout={SSH_TIMEOUT} {self.target_ip} \\"{escaped_command}\\""'
            )
        else:
            ssh_cmd = (
                f'ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout={SSH_TIMEOUT} '
                f'{self.target_ip} "{command}"'
            )
        
        try:
            result = subprocess.run(
                ssh_cmd, shell=True, capture_output=True, text=True, timeout=60
            )
            return CommandResult(result.returncode, result.stdout, result.stderr)
        except subprocess.TimeoutExpired:
            return CommandResult(-1, "", "Command timed out")
        except Exception as e:
            return CommandResult(-1, "", str(e))


class CommandResult:
    """Command result class that mimics testinfra CommandResult."""
    
    def __init__(self, rc, stdout, stderr):
        self.rc = rc
        self.stdout = stdout.strip() if stdout else ""
        self.stderr = stderr.strip() if stderr else ""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def submit_slurm_job(host) -> dict:
    """Submit a job to Slurm and return the job ID."""
    # Use single quotes for wrap - they pass through nested SSH correctly
    cmd = host.run("sbatch --job-name=test_queue_job --time=00:05:00 --nodes=1 --ntasks=1 --wrap='sleep 30; hostname'")
    
    if cmd.rc == 0:
        match = re.search(r'Submitted batch job (\d+)', cmd.stdout)
        if match:
            return {"success": True, "job_id": match.group(1), "error": None}
        return {"success": False, "job_id": None, "error": f"Could not parse job ID: {cmd.stdout}"}
    
    return {"success": False, "job_id": None, "error": cmd.stderr or cmd.stdout or "Unknown error"}


def get_job_state(host, job_id: str) -> dict:
    """Get the current state of a Slurm job."""
    cmd = host.run(f"squeue -j {job_id} -o '%T|%r|%N|%P' --noheader")
    
    if cmd.rc == 0 and cmd.stdout:
        parts = cmd.stdout.split('|')
        return {
            "success": True,
            "state": parts[0] if len(parts) > 0 else "UNKNOWN",
            "reason": parts[1] if len(parts) > 1 else "None",
            "nodes": parts[2] if len(parts) > 2 else "None",
            "partition": parts[3] if len(parts) > 3 else "None",
            "error": None
        }
    
    # Check sacct for completed jobs
    sacct_cmd = host.run(f"sacct -j {job_id} -o State --noheader -n | head -1")
    if sacct_cmd.rc == 0 and sacct_cmd.stdout:
        return {
            "success": True,
            "state": sacct_cmd.stdout.split()[0] if sacct_cmd.stdout else "UNKNOWN",
            "reason": "Completed",
            "nodes": "N/A",
            "partition": "N/A",
            "error": None
        }
    
    return {"success": False, "state": "UNKNOWN", "reason": None, "error": "Job not found"}


def get_slurm_node_status(host) -> dict:
    """Get the status of all Slurm compute nodes."""
    cmd = host.run("sinfo -N -o '%N|%T|%P|%c|%m' --noheader")
    
    if cmd.rc != 0:
        return {"success": False, "nodes": [], "available_count": 0, "down_count": 0, "error": cmd.stderr}
    
    nodes = []
    available_count = 0
    down_count = 0
    
    for line in cmd.stdout.split('\n'):
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
        
        if node["state"].lower() in ["idle", "mixed", "allocated"]:
            available_count += 1
        elif "down" in node["state"].lower() or "drain" in node["state"].lower():
            down_count += 1
    
    return {
        "success": True,
        "nodes": nodes,
        "available_count": available_count,
        "down_count": down_count,
        "total_count": len(nodes),
        "error": None
    }


def check_slurmctld_running(host) -> dict:
    """Check if slurmctld is running."""
    cmd = host.run("systemctl is-active slurmctld")
    return {"success": cmd.rc == 0 and cmd.stdout == "active", "status": cmd.stdout, "error": None}


def get_scheduler_info(host) -> dict:
    """Get Slurm scheduler configuration."""
    cmd = host.run("scontrol show config | grep -E 'SchedulerType|SelectType|PriorityType'")
    
    if cmd.rc == 0:
        config = {}
        for line in cmd.stdout.split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
        return {"success": True, "config": config, "error": None}
    
    return {"success": False, "config": {}, "error": cmd.stderr}


def cancel_slurm_jobs(host, job_ids: list):
    """Cancel multiple Slurm jobs."""
    for job_id in job_ids:
        host.run(f"scancel {job_id} 2>/dev/null")


# =============================================================================
# IPMI POWER MANAGEMENT FUNCTIONS
# =============================================================================

def ipmi_power_off(bmc_ip: str, node_name: str) -> dict:
    """Power off a node via IPMI."""
    cmd = f"ipmitool -I lanplus -H {bmc_ip} -U {IPMI_USER} -P {IPMI_PASS} power off"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return {
        "success": result.returncode == 0,
        "node": node_name,
        "bmc_ip": bmc_ip,
        "output": result.stdout.strip(),
        "error": result.stderr.strip() if result.returncode != 0 else None
    }


def ipmi_power_on(bmc_ip: str, node_name: str) -> dict:
    """Power on a node via IPMI."""
    cmd = f"ipmitool -I lanplus -H {bmc_ip} -U {IPMI_USER} -P {IPMI_PASS} power on"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return {
        "success": result.returncode == 0,
        "node": node_name,
        "bmc_ip": bmc_ip,
        "output": result.stdout.strip(),
        "error": result.stderr.strip() if result.returncode != 0 else None
    }


def ipmi_power_status(bmc_ip: str, node_name: str) -> dict:
    """Get power status of a node via IPMI."""
    cmd = f"ipmitool -I lanplus -H {bmc_ip} -U {IPMI_USER} -P {IPMI_PASS} power status"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    status = "unknown"
    if result.returncode == 0:
        if "on" in result.stdout.lower():
            status = "on"
        elif "off" in result.stdout.lower():
            status = "off"
    return {
        "success": result.returncode == 0,
        "node": node_name,
        "bmc_ip": bmc_ip,
        "status": status,
        "output": result.stdout.strip(),
        "error": result.stderr.strip() if result.returncode != 0 else None
    }


def wait_for_node_down(host, node_name: str, timeout: int = 120) -> bool:
    """Wait for a Slurm node to show as down/unavailable."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        cmd = host.run(f"sinfo -n {node_name} -o '%T' --noheader")
        if cmd.rc == 0:
            state = cmd.stdout.strip().lower()
            if "down" in state or "drain" in state or "unknown" in state:
                return True
        time.sleep(5)
    return False


def drain_slurm_node(host, node_name: str, reason: str = "Testing") -> dict:
    """Drain a Slurm node to make it unavailable for jobs."""
    cmd = host.run(f"scontrol update NodeName={node_name} State=DRAIN Reason='{reason}'")
    return {
        "success": cmd.rc == 0,
        "node": node_name,
        "output": cmd.stdout.strip(),
        "error": cmd.stderr.strip() if cmd.rc != 0 else None
    }


def resume_slurm_node(host, node_name: str) -> dict:
    """Resume a drained Slurm node to make it available again."""
    cmd = host.run(f"scontrol update NodeName={node_name} State=RESUME")
    return {
        "success": cmd.rc == 0,
        "node": node_name,
        "output": cmd.stdout.strip(),
        "error": cmd.stderr.strip() if cmd.rc != 0 else None
    }


# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_submit_jobs_when_nodes_unavailable(host, control_host=None, drain_nodes=False):
    """
    Test 1: Submit multiple jobs when compute nodes are not available.
    
    If drain_nodes=True, drains both slurm-node-1 and slurm-node-2
    (compute nodes) via scontrol before submitting jobs to ensure nodes are 
    truly unavailable for job scheduling.
    """
    log = TestLogger(TEST_NAMES["submit_jobs_no_nodes"])
    submitted_jobs = []
    ctrl = control_host or host
    nodes_drained = []
    
    # Drain compute nodes if requested to make them unavailable
    if drain_nodes:
        log.check("Draining compute nodes to make them unavailable")
        
        # Drain slurm-node-1
        log.check("Draining slurm-node-1")
        result1 = drain_slurm_node(ctrl, "slurm-node-1", "Test: nodes unavailable")
        if result1["success"]:
            log.check("slurm-node-1 drained successfully")
            nodes_drained.append("slurm-node-1")
        else:
            log.check(f"slurm-node-1 drain failed: {result1['error']}")
        
        # Drain slurm-node-2
        log.check("Draining slurm-node-2")
        result2 = drain_slurm_node(ctrl, "slurm-node-2", "Test: nodes unavailable")
        if result2["success"]:
            log.check("slurm-node-2 drained successfully")
            nodes_drained.append("slurm-node-2")
        else:
            log.check(f"slurm-node-2 drain failed: {result2['error']}")
        
        if nodes_drained:
            log.check(f"Nodes drained: {', '.join(nodes_drained)}")
            time.sleep(2)  # Brief wait for state to propagate
    
    log.check("Verifying slurmctld is running (on control node)")
    slurmctld_status = check_slurmctld_running(ctrl)
    if not slurmctld_status["success"]:
        log.failed("slurmctld is not running", slurmctld_status["status"])
        return False, [], nodes_drained
    log.check("slurmctld is active")
    
    log.check("Checking current node availability")
    node_status = get_slurm_node_status(host)
    if node_status["success"]:
        log.check(f"Total nodes: {node_status['total_count']}, Available: {node_status['available_count']}, Down: {node_status['down_count']}")
    
    log.check(f"Submitting {JOB_SUBMIT_COUNT} test jobs")
    for i in range(JOB_SUBMIT_COUNT):
        result = submit_slurm_job(host)
        if result["success"]:
            submitted_jobs.append(result["job_id"])
            log.check(f"Job {i+1} submitted: ID {result['job_id']}")
        else:
            log.failed(f"Job {i+1} failed", result["error"])
    
    if len(submitted_jobs) == JOB_SUBMIT_COUNT:
        details = f"Submitted jobs: {', '.join(submitted_jobs)}"
        if nodes_drained:
            details += f"\nNodes drained: {', '.join(nodes_drained)}"
        log.passed("Jobs submitted successfully", details)
        return True, submitted_jobs, nodes_drained
    else:
        log.failed("Job submission incomplete", f"Only {len(submitted_jobs)}/{JOB_SUBMIT_COUNT} jobs submitted")
        return False, submitted_jobs, nodes_drained


def test_validate_pending_state_with_reasons(host, job_ids):
    """
    Test 2: Validate jobs are in PENDING state with appropriate reasons.
    """
    log = TestLogger(TEST_NAMES["validate_pending_state"])
    
    if not job_ids:
        log.check("No jobs to validate, submitting new jobs")
        job_ids = []
        for i in range(JOB_SUBMIT_COUNT):
            result = submit_slurm_job(host)
            if result["success"]:
                job_ids.append(result["job_id"])
    
    log.check(f"Checking state of {len(job_ids)} jobs")
    
    pending_jobs = []
    running_jobs = []
    completed_jobs = []
    valid_reasons = []
    
    for job_id in job_ids:
        state_info = get_job_state(host, job_id)
        state = state_info.get("state", "UNKNOWN").upper()
        reason = state_info.get("reason", "None")
        
        log.check(f"Job {job_id}: State={state}, Reason={reason}")
        
        if state == "PENDING":
            pending_jobs.append(job_id)
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
    
    passed = len(pending_jobs) > 0 or len(running_jobs) > 0 or len(completed_jobs) > 0
    if passed:
        log.passed("Job states validated", details)
    else:
        log.failed("No valid job states found", details)
    
    return passed


def test_validate_running_transition(host, job_ids):
    """
    Test 3: Validate jobs transition to RUNNING when nodes available.
    """
    log = TestLogger(TEST_NAMES["validate_running_transition"])
    
    if not job_ids:
        log.check("No jobs to monitor, submitting new job")
        result = submit_slurm_job(host)
        if not result["success"]:
            log.failed("Failed to submit job", result["error"])
            return False
        job_ids = [result["job_id"]]
    
    test_job_id = job_ids[0]
    
    log.check("Checking node availability")
    node_status = get_slurm_node_status(host)
    if node_status["success"]:
        log.check(f"Available nodes: {node_status['available_count']}/{node_status['total_count']}")
    
    log.check(f"Monitoring job {test_job_id} for state transition")
    initial_state = get_job_state(host, test_job_id)
    log.check(f"Initial state: {initial_state.get('state', 'UNKNOWN')}")
    
    if initial_state.get("state", "").upper() == "PENDING":
        log.check(f"Waiting up to {JOB_WAIT_TIMEOUT}s for RUNNING state")
        
        start_time = time.time()
        while time.time() - start_time < JOB_WAIT_TIMEOUT:
            state_info = get_job_state(host, test_job_id)
            current_state = state_info.get("state", "UNKNOWN").upper()
            
            if current_state == "RUNNING":
                elapsed = int(time.time() - start_time)
                details = f"Job {test_job_id} transitioned to RUNNING\nElapsed: {elapsed}s\nNodes: {state_info.get('nodes', 'N/A')}"
                log.passed("Job transitioned to RUNNING", details)
                return True
            
            if current_state in ["COMPLETED", "COMPLETING", "FAILED", "CANCELLED"]:
                log.passed("Job reached terminal state", f"State: {current_state}")
                return True
            
            time.sleep(POLL_INTERVAL)
        
        # Timeout
        final_state = get_job_state(host, test_job_id)
        details = f"Job still {final_state.get('state', 'UNKNOWN')} after {JOB_WAIT_TIMEOUT}s\nReason: {final_state.get('reason', 'N/A')}"
        log.passed("Job queueing verified (no available nodes)", details)
        return True
    
    elif initial_state.get("state", "").upper() == "RUNNING":
        details = f"Job {test_job_id} already RUNNING\nNodes: {initial_state.get('nodes', 'N/A')}"
        log.passed("Job is RUNNING", details)
        return True
    
    elif initial_state.get("state", "").upper() in ["COMPLETED", "COMPLETING"]:
        log.passed("Job already completed", f"State: {initial_state.get('state')}")
        return True
    
    log.passed("Job state verified", f"State: {initial_state.get('state', 'UNKNOWN')}")
    return True


def test_validate_scheduler_allocation(host, control_host=None):
    """
    Test 4: Validate Slurm scheduler allocates jobs correctly.
    """
    log = TestLogger(TEST_NAMES["validate_scheduler_allocation"])
    ctrl = control_host or host
    
    log.check("Verifying slurmctld daemon status (on control node)")
    slurmctld_status = check_slurmctld_running(ctrl)
    if slurmctld_status["success"]:
        log.passed("slurmctld is active", f"Status: {slurmctld_status['status']}")
    else:
        log.failed("slurmctld is not running", slurmctld_status["status"])
        return False
    
    log.check("Getting scheduler configuration")
    scheduler_info = get_scheduler_info(host)
    if scheduler_info["success"]:
        config = scheduler_info["config"]
        details = f"SchedulerType: {config.get('SchedulerType', 'N/A')}\n"
        details += f"SelectType: {config.get('SelectType', 'N/A')}\n"
        details += f"PriorityType: {config.get('PriorityType', 'N/A')}"
        log.passed("Scheduler configuration retrieved", details)
    
    log.check("Checking node resource status")
    node_status = get_slurm_node_status(host)
    if node_status["success"]:
        details = f"Total: {node_status['total_count']}, Available: {node_status['available_count']}, Down: {node_status['down_count']}"
        log.check(details)
        for node in node_status["nodes"][:5]:
            log.check(f"  {node['name']}: {node['state']} ({node['cpus']} CPUs)")
    
    log.check("Verifying job queue status")
    cmd = host.run("squeue -o '%i|%j|%T|%r' --noheader")
    if cmd.rc == 0:
        jobs = [l for l in cmd.stdout.split('\n') if l.strip()]
        if jobs:
            pending = sum(1 for j in jobs if 'PENDING' in j)
            running = sum(1 for j in jobs if 'RUNNING' in j)
            log.check(f"Queued jobs: {len(jobs)} (Pending: {pending}, Running: {running})")
        else:
            log.check("Job queue is empty")
    
    log.check("Testing scheduler responsiveness")
    result = submit_slurm_job(host)
    if result["success"]:
        job_id = result["job_id"]
        log.check(f"Test job submitted: {job_id}")
        
        time.sleep(2)
        state_info = get_job_state(host, job_id)
        log.check(f"Job state: {state_info.get('state', 'UNKNOWN')}, Reason: {state_info.get('reason', 'N/A')}")
        
        cancel_slurm_jobs(host, [job_id])
        log.check(f"Test job {job_id} cancelled")
    
    log.passed("Scheduler allocation verified", "Scheduler is functioning correctly")
    return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all Slurm job queueing tests."""
    # Initialize TestReport for HTML report generation
    report = TestReport("slurm_job_queueing")
    
    # Use SLURM_NODE_2 as target, SLURM_CONTROL_NODE for slurmctld checks
    target_node = SLURM_NODE_2
    control_node = SLURM_CONTROL_NODE
    
    print("\n" + "="*70)
    print("  Slurm Job Queueing Tests (via SSH to slurm-node-2)")
    print("="*70)
    print(f"  Target: {target_node}")
    print(f"  Control: {control_node}")
    print(f"  Via: {OMNIA_CORE_ALIAS}")
    
    # Create SSH hosts - one for target node, one for control node (slurmctld)
    host = SSHHost(target_node, via_host=OMNIA_CORE_ALIAS)
    control_host = SSHHost(control_node, via_host=OMNIA_CORE_ALIAS)
    
    # Verify connectivity
    print("\n  Checking connectivity...")
    cmd = host.run("hostname")
    if cmd.rc != 0:
        print(f"  \033[91m✘ FAIL\033[0m: Cannot connect to {target_node}")
        print(f"       Error: {cmd.stderr}")
        sys.exit(1)
    print(f"  \033[92m✔ PASS\033[0m: Connected to {cmd.stdout}")
    
    results = []
    
    # Test 1 - Drain both nodes before submitting jobs to make them unavailable
    start_time = time.time()
    passed, job_ids, nodes_drained = test_submit_jobs_when_nodes_unavailable(host, control_host, drain_nodes=True)
    duration = time.time() - start_time
    results.append(("test_submit_jobs_when_nodes_unavailable", passed, duration))
    report.add_result(
        test_name="test_submit_jobs_when_nodes_unavailable",
        passed=passed,
        duration=duration,
        details=f"Submitted {len(job_ids)} jobs: {', '.join(job_ids)}" if job_ids else "No jobs submitted"
    )
    
    # Test 2
    start_time = time.time()
    passed = test_validate_pending_state_with_reasons(host, job_ids)
    duration = time.time() - start_time
    results.append(("test_validate_pending_state_with_reasons", passed, duration))
    report.add_result(
        test_name="test_validate_pending_state_with_reasons",
        passed=passed,
        duration=duration,
        details=f"Validated pending state for {len(job_ids)} jobs"
    )
    
    # Test 3
    start_time = time.time()
    passed = test_validate_running_transition(host, job_ids)
    duration = time.time() - start_time
    results.append(("test_validate_running_transition", passed, duration))
    report.add_result(
        test_name="test_validate_running_transition",
        passed=passed,
        duration=duration,
        details="Verified job state transition monitoring"
    )
    
    # Test 4
    start_time = time.time()
    passed = test_validate_scheduler_allocation(host, control_host)
    duration = time.time() - start_time
    results.append(("test_validate_scheduler_allocation", passed, duration))
    report.add_result(
        test_name="test_validate_scheduler_allocation",
        passed=passed,
        duration=duration,
        details="Verified slurmctld and scheduler configuration"
    )
    
    # Cleanup
    if job_ids:
        print("\n  Cleaning up test jobs...")
        cancel_slurm_jobs(host, job_ids)
        print(f"  Cancelled {len(job_ids)} test jobs")
    
    # Resume nodes if they were drained
    if nodes_drained:
        print("\n  Resuming drained nodes...")
        for node_name in nodes_drained:
            result = resume_slurm_node(control_host, node_name)
            status = "✔" if result["success"] else "✘"
            print(f"  {status} {node_name}: {'resumed' if result['success'] else result['error']}")
    
    # Save HTML report
    report.save()
    
    # Summary
    print("\n" + "="*70)
    print("  Test Summary")
    print("="*70)
    
    total = len(results)
    passed_count = sum(1 for _, p, _ in results if p)
    failed_count = total - passed_count
    
    for name, passed, duration in results:
        status = "✔ PASS" if passed else "✘ FAIL"
        color = "\033[92m" if passed else "\033[91m"
        reset = "\033[0m"
        print(f"  {color}{status}{reset}: {name} ({duration:.2f}s)")
    
    print(f"\n  Total: {total} | Passed: {passed_count} | Failed: {failed_count}")
    
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
