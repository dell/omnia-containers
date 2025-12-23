#!/usr/bin/env python3
"""
Local test script for SSH connectivity from omnia_core to nodes.
This script runs locally without requiring testinfra remote connection.
"""

import subprocess
import csv
import sys

# Configuration
PXE_MAPPING_FILE = "/opt/omnia/input/project_default/pxe_mapping_file.csv"
SSH_TIMEOUT = 10
OMNIA_CORE_ALIAS = "omnia_core"


def run_command(cmd, timeout=30):
    """Run a shell command and return result."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
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


def parse_pxe_mapping_file(file_path):
    """Parse PXE mapping file and extract node information."""
    nodes = []
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('HOSTNAME') or row.get('ADMIN_IP'):
                    nodes.append({
                        "hostname": row.get('HOSTNAME', ''),
                        "admin_ip": row.get('ADMIN_IP', ''),
                        "functional_group": row.get('FUNCTIONAL_GROUP_NAME', ''),
                        "group_name": row.get('GROUP_NAME', ''),
                        "bmc_ip": row.get('BMC_IP', ''),
                    })
        return {"success": True, "nodes": nodes, "error": None}
    except Exception as e:
        return {"success": False, "nodes": [], "error": str(e)}


def ssh_from_omnia_core(target, command="hostname"):
    """SSH from omnia_core to target node."""
    ssh_cmd = (
        f"ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout={SSH_TIMEOUT} "
        f"{OMNIA_CORE_ALIAS} 'ssh -o BatchMode=yes -o StrictHostKeyChecking=no "
        f"-o ConnectTimeout={SSH_TIMEOUT} {target} \"{command}\"'"
    )
    return run_command(ssh_cmd, timeout=SSH_TIMEOUT * 3)


def print_header(text):
    """Print formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_result(test_name, passed, details=""):
    """Print test result."""
    status = "✔ PASS" if passed else "✘ FAIL"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset}: {test_name}")
    if details:
        for line in details.split('\n'):
            print(f"       {line}")


def test_parse_pxe_mapping_file():
    """Test 1: Parse PXE mapping file."""
    print_header("Test 1: Parse PXE Mapping File")
    
    result = parse_pxe_mapping_file(PXE_MAPPING_FILE)
    
    if result["success"]:
        details = f"Found {len(result['nodes'])} node(s):\n"
        for node in result["nodes"]:
            details += f"  - {node['hostname']} ({node['admin_ip']}) - {node['functional_group']}\n"
        print_result("Parse PXE mapping file", True, details.strip())
        return True, result["nodes"]
    else:
        print_result("Parse PXE mapping file", False, f"Error: {result['error']}")
        return False, []


def test_ssh_by_hostname(nodes):
    """Test 2: SSH to nodes using hostname."""
    print_header("Test 2: SSH to Nodes by Hostname")
    
    success_count = 0
    failed_count = 0
    
    for node in nodes:
        hostname = node["hostname"]
        if not hostname:
            continue
            
        print(f"\n  → SSH to {hostname} via omnia_core...")
        result = ssh_from_omnia_core(hostname, "hostname")
        
        if result["success"]:
            print_result(f"SSH to {hostname}", True, f"Output: {result['stdout']}")
            success_count += 1
        else:
            print_result(f"SSH to {hostname}", False, f"Error: {result['stderr']}")
            failed_count += 1
    
    print(f"\n  Summary: {success_count} passed, {failed_count} failed")
    return failed_count == 0


def test_ssh_by_admin_ip(nodes):
    """Test 3: SSH to nodes using admin IP."""
    print_header("Test 3: SSH to Nodes by Admin IP")
    
    success_count = 0
    failed_count = 0
    
    for node in nodes:
        admin_ip = node["admin_ip"]
        hostname = node["hostname"]
        if not admin_ip:
            continue
            
        print(f"\n  → SSH to {hostname} ({admin_ip}) via omnia_core...")
        result = ssh_from_omnia_core(admin_ip, "hostname && uptime")
        
        if result["success"]:
            print_result(f"SSH to {admin_ip}", True, f"Output: {result['stdout']}")
            success_count += 1
        else:
            print_result(f"SSH to {admin_ip}", False, f"Error: {result['stderr']}")
            failed_count += 1
    
    print(f"\n  Summary: {success_count} passed, {failed_count} failed")
    return failed_count == 0


def test_verify_all_nodes(nodes):
    """Test 4: Verify SSH connectivity to all nodes."""
    print_header("Test 4: Verify SSH Connectivity to All Nodes")
    
    results = []
    
    for node in nodes:
        admin_ip = node["admin_ip"]
        hostname = node["hostname"]
        
        if not admin_ip:
            results.append({"node": hostname, "verified": False, "error": "No admin IP"})
            continue
            
        result = ssh_from_omnia_core(admin_ip, "echo SSH_OK && hostname")
        verified = result["success"] and "SSH_OK" in result["stdout"]
        
        results.append({
            "node": hostname,
            "ip": admin_ip,
            "verified": verified,
            "output": result["stdout"] if verified else result["stderr"]
        })
    
    print("\n  Connectivity Results:")
    all_verified = True
    for r in results:
        status = "✔" if r["verified"] else "✘"
        color = "\033[92m" if r["verified"] else "\033[91m"
        reset = "\033[0m"
        print(f"    {color}{status}{reset} {r['node']} ({r.get('ip', 'N/A')})")
        if not r["verified"]:
            all_verified = False
    
    print_result("All nodes reachable", all_verified)
    return all_verified


def test_ssh_to_slurm_nodes(nodes):
    """Test 5: SSH to Slurm nodes and check Slurm status."""
    print_header("Test 5: SSH to Slurm Nodes")
    
    slurm_nodes = [n for n in nodes if "slurm" in n.get("functional_group", "").lower()]
    
    if not slurm_nodes:
        print("  No Slurm nodes found in mapping file")
        return True
    
    print(f"  Found {len(slurm_nodes)} Slurm node(s)")
    
    for node in slurm_nodes:
        admin_ip = node["admin_ip"]
        hostname = node["hostname"]
        func_group = node["functional_group"]
        
        print(f"\n  → {hostname} ({func_group})")
        
        # Check hostname
        result = ssh_from_omnia_core(admin_ip, "hostname")
        if result["success"]:
            print(f"    Hostname: {result['stdout']}")
        
        # Check if Slurm is installed
        result = ssh_from_omnia_core(admin_ip, "which sinfo 2>/dev/null && sinfo --version || echo 'Slurm not installed'")
        print(f"    Slurm: {result['stdout']}")
        
        # Check uptime
        result = ssh_from_omnia_core(admin_ip, "uptime")
        if result["success"]:
            print(f"    Uptime: {result['stdout']}")
    
    print_result("Slurm nodes SSH test", True)
    return True


def main():
    """Run all SSH tests."""
    print("\n" + "="*60)
    print("  SSH Connectivity Tests: omnia_core → Compute Nodes")
    print("="*60)
    print(f"  PXE Mapping File: {PXE_MAPPING_FILE}")
    print(f"  SSH Timeout: {SSH_TIMEOUT}s")
    
    # Check omnia_core connectivity first
    print("\n  Checking omnia_core connectivity...")
    result = run_command(f"ssh -o BatchMode=yes -o ConnectTimeout=5 {OMNIA_CORE_ALIAS} 'echo OK'")
    if not result["success"]:
        print_result("omnia_core connectivity", False, "Cannot connect to omnia_core container")
        sys.exit(1)
    print_result("omnia_core connectivity", True)
    
    # Run tests
    results = []
    
    # Test 1: Parse mapping file
    passed, nodes = test_parse_pxe_mapping_file()
    results.append(("Parse PXE mapping file", passed))
    
    if not nodes:
        print("\nNo nodes found. Exiting.")
        sys.exit(1)
    
    # Test 2: SSH by hostname
    passed = test_ssh_by_hostname(nodes)
    results.append(("SSH by hostname", passed))
    
    # Test 3: SSH by admin IP
    passed = test_ssh_by_admin_ip(nodes)
    results.append(("SSH by admin IP", passed))
    
    # Test 4: Verify all nodes
    passed = test_verify_all_nodes(nodes)
    results.append(("Verify all nodes", passed))
    
    # Test 5: Slurm nodes
    passed = test_ssh_to_slurm_nodes(nodes)
    results.append(("Slurm nodes SSH", passed))
    
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
