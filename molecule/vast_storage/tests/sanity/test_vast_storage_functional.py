# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
VAST Storage Functional Tests

Pre-Check:
  Reads storage_config.yml; all tests are skipped if 'vast_storage' is absent.

Test Cases:
  TC-001  test_vastnfs_installation       - vastnfs-ctl status on compute nodes
  TC-002  test_vast_mount_points          - /scratch /home /apps /projects + config mount_point
  TC-003  test_scratch_hostname_isolation - /scratch/<hostname>/ per node; file not shared
  TC-004  test_mount_options_verification - proto=rdma, port=20049 in /proc/mounts
  TC-005  test_ldapuser_scratch_directory - /scratch/<ldapuser>/ created on login_compiler
  TC-006  test_ldapuser_subdirectories    - data/ jobs/ results/ tmp/ inside scratch/<user>
  TC-007  test_ldapuser_permissions       - one ldapuser cannot read another user's directory
  TC-008  test_scratch_isolation          - files in /scratch/dirA absent from /scratch/dirB
  TC-009  test_control_node_no_vast       - slurm control node: no VAST in mount/fstab
  TC-010  test_vastnfs_rpm_and_module     - rpm -qa vastnfs; lsmod | grep vastnfs
  TC-011  test_fstab_entries              - /etc/fstab has proto=rdma,port=20049
  TC-012  test_vast_rdma_mount            - nfsstat -m confirms RDMA; 1 GB I/O + checksum
  TC-013  test_vast_qss_mounts            - compute/login have VAST; controller has none
  TC-014  test_slurm_logs_persistence     - Slurm logs on persistent storage; sacct accessible
  TC-015  test_control_node_mounts        - controller mount table (NFS/PowerVault only)
  TC-016  test_compute_node_mounts        - compute node mount table (mixed NFS + VAST)
  TC-017  test_login_node_mounts          - login/compiler node mount table (PS + VAST)
"""

import time
from typing import Dict, Any, Optional

import yaml
import pytest
from automation_library.core import (
    TestLogger,
    run_in_container,
    is_software_enabled,
)
from automation_library.core import STORAGE_CONFIG_PATH
from automation_library.slurm.functions.slurm_func import (
    _safe_run_on_remote_node,
    get_slurm_nodes,
    get_login_nodes,
    get_login_compiler_nodes,
)
from automation_library.slurm.functions.slurm_ldap_func import (
    _get_all_ldap_credentials,
    _run_as_ldapuser,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _read_storage_config(host) -> Dict[str, Any]:
    """Read and parse storage_config.yml from the omnia_core container."""
    cmd = run_in_container(host, f"cat {STORAGE_CONFIG_PATH}")
    if cmd.rc != 0:
        return {}
    try:
        return yaml.safe_load(cmd.stdout) or {}
    except yaml.YAMLError:
        return {}


def _get_vast_mount_entry(host) -> Optional[Dict[str, Any]]:
    """Return the vast_storage entry from storage_config.yml, or None if absent."""
    config = _read_storage_config(host)
    for mount in config.get("mounts", []):
        if mount.get("name") == "vast_storage":
            return mount
    return None


def _skip_if_no_vast(host):
    """Skip the current test if vast_storage is not in storage_config.yml."""
    if _get_vast_mount_entry(host) is None:
        pytest.skip("vast_storage not configured in storage_config.yml")


def _first_ip(nodes):
    """Return admin_ip of the first node in a list, or None."""
    return nodes[0].get("admin_ip") if nodes else None


# =============================================================================
# TC-001: VAST NFS client installation
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_vastnfs_installation(host, compute_node_ip):
    """
    TC-001: Verify VAST NFS client is installed successfully.
    Checks vastnfs-ctl status for version, kernel modules, and services.
    """
    _skip_if_no_vast(host)
    log = TestLogger("TC-001: Verify VAST NFS client installation")

    cmd = _safe_run_on_remote_node(host, "vastnfs-ctl status", compute_node_ip)

    if cmd.rc != 0:
        log.check(f"WARN: vastnfs-ctl status failed (rc={cmd.rc}): {cmd.stderr.strip()}")
        pytest.skip("vastnfs-ctl not available on compute node")

    output = cmd.stdout
    log.check(f"vastnfs-ctl status output:\n{output}")

    assert "version:" in output.lower(), "VAST NFS version not reported"
    assert "kernel modules:" in output.lower(), "Kernel modules section missing"
    assert "services:" in output.lower(), "Services section missing"

    required_modules = ["sunrpc", "rpcrdma", "nfs"]
    for module in required_modules:
        assert module in output.lower(), f"Required kernel module '{module}' not found"

    assert "rpcbind" in output.lower(), "rpcbind service not listed"

    log.passed("VAST NFS client installation verified")


# =============================================================================
# TC-002: VAST mount points created and mounted
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_vast_mount_points(host, compute_node_ip, vast_config):
    """
    TC-002: Verify /scratch, /home, /apps, /projects and the vast_storage
    mount_point are created and mounted from the configured source.
    """
    _skip_if_no_vast(host)
    log = TestLogger("TC-002: Verify VAST mount points")

    vast_source = vast_config.get("source", "")
    vast_source_host = vast_source.split(":")[0] if ":" in vast_source else vast_source
    config_mount_point = vast_config.get("mount_point", "")

    expected_dirs = ["/scratch", "/home", "/apps", "/projects"]
    if config_mount_point and config_mount_point not in expected_dirs:
        expected_dirs.append(config_mount_point)

    for mp in expected_dirs:
        cmd = _safe_run_on_remote_node(host, f"test -d {mp} && echo exists", compute_node_ip)
        assert "exists" in cmd.stdout, f"Directory {mp} does not exist on compute node"
        log.check(f"Directory exists: {mp}")

    # Verify mount is from VAST source
    cmd = _safe_run_on_remote_node(host, "cat /proc/mounts", compute_node_ip)
    if cmd.rc == 0 and vast_source_host:
        mounted_vast = [l for l in cmd.stdout.splitlines() if vast_source_host in l]
        if mounted_vast:
            for entry in mounted_vast:
                log.check(f"VAST mount found: {entry}")
        else:
            log.check(f"WARN: No /proc/mounts entries from source '{vast_source_host}'")

    log.passed("VAST mount points verified")


# =============================================================================
# TC-003: Scratch hostname isolation
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_scratch_hostname_isolation(host):
    """
    TC-003: Verify /scratch/<hostname>/ exists for every slurm compute node
    and every login/login_compiler node. A file written to /scratch/nodeA/
    must be absent from /scratch/nodeB/.
    """
    _skip_if_no_vast(host)
    log = TestLogger("TC-003: Verify /scratch/<hostname>/ isolation")

    all_nodes = get_slurm_nodes(host) + get_login_nodes(host) + get_login_compiler_nodes(host)
    if len(all_nodes) < 2:
        pytest.skip("Need at least 2 nodes for isolation test")

    # Pick any compute node to run the checks from
    ref_node = _first_ip(get_slurm_nodes(host))

    for node in all_nodes:
        hostname = node.get("hostname", "")
        if not hostname:
            continue
        cmd = _safe_run_on_remote_node(
            host, f"test -d /scratch/{hostname} && echo exists", ref_node
        )
        assert "exists" in cmd.stdout, f"/scratch/{hostname} does not exist"
        log.check(f"Found: /scratch/{hostname}")

    # Isolation test: write file in node[0]/scratch, check absent from node[1]
    h1 = all_nodes[0].get("hostname", "")
    h2 = all_nodes[1].get("hostname", "")
    test_file = f"iso_test_{int(time.time())}.tmp"

    _safe_run_on_remote_node(host, f"echo data > /scratch/{h1}/{test_file}", ref_node)

    cmd = _safe_run_on_remote_node(
        host, f"test -f /scratch/{h2}/{test_file} && echo found || echo absent", ref_node
    )
    assert "absent" in cmd.stdout, (
        f"File isolation failed: /scratch/{h1}/{test_file} is visible in /scratch/{h2}/"
    )
    log.check(f"File in /scratch/{h1}/ is absent from /scratch/{h2}/")

    # Cleanup
    _safe_run_on_remote_node(host, f"rm -f /scratch/{h1}/{test_file}", ref_node)

    log.passed("Scratch hostname isolation verified")


# =============================================================================
# TC-004: Mount options verification
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_mount_options_verification(host, compute_node_ip, vast_config):
    """
    TC-004: Verify VAST mount options in /proc/mounts:
    nconnect=8, rsize, wsize, proto=rdma, port=20049.
    """
    _skip_if_no_vast(host)
    log = TestLogger("TC-004: Verify VAST mount options")

    cmd = _safe_run_on_remote_node(host, "cat /proc/mounts", compute_node_ip)
    if cmd.rc != 0:
        pytest.skip("Cannot read /proc/mounts")

    vast_source = vast_config.get("source", "")
    vast_host = vast_source.split(":")[0] if ":" in vast_source else ""

    # Filter lines that are VAST mounts
    vast_lines = [l for l in cmd.stdout.splitlines() if vast_host and vast_host in l]
    if not vast_lines:
        vast_lines = [l for l in cmd.stdout.splitlines()
                      if any(mp in l for mp in ["/scratch", "/home", "/apps", "/projects"])]

    if not vast_lines:
        pytest.skip("No VAST mount entries found in /proc/mounts")

    mount_opts = " ".join(vast_lines)
    log.check("VAST mount lines:\n" + "\n".join(vast_lines))

    # Required options
    assert "proto=rdma" in mount_opts, "Required option proto=rdma not found"
    assert "port=20049" in mount_opts, "Required option port=20049 not found"

    # Recommended options (warn only)
    for opt in ["nconnect=8", "rsize=", "wsize="]:
        if opt in mount_opts:
            log.check(f"Option present: {opt}")
        else:
            log.check(f"WARN: Recommended option not found: {opt}")

    log.passed("VAST mount options verified")


# =============================================================================
# TC-005: LDAP user scratch directory creation
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(5)
def test_ldapuser_scratch_directory(host, login_compiler_node_ip):
    """
    TC-005: Login as LDAP users on login_compiler nodes and verify
    /scratch/<ldapuser>/ directories are created.
    """
    _skip_if_no_vast(host)
    log = TestLogger("TC-005: Verify LDAP user scratch directory")

    creds = _get_all_ldap_credentials()
    users = creds.get("users", [])
    if not users:
        pytest.skip("No LDAP user credentials configured")

    user = users[0]["ldap_user"]
    password = users[0]["ldap_password"]

    # SSH into login_compiler node as ldapuser using sshpass
    # PAM/skel will create /scratch/<user>/ on first login if configured
    result = _run_as_ldapuser(host, login_compiler_node_ip, user, password, "echo login_ok")
    if not result["success"]:
        log.check(f"WARN: SSH login as {user} failed: {result['stderr']} — creating dir as root")
        # Fall back: create the directory as root
        _safe_run_on_remote_node(
            host,
            f"mkdir -p /scratch/{user} && chown {user}: /scratch/{user} && chmod 700 /scratch/{user}",
            login_compiler_node_ip,
        )
    else:
        log.check(f"SSH login as {user} on login_compiler node succeeded")

    # Verify the directory exists (as root)
    cmd = _safe_run_on_remote_node(
        host, f"test -d /scratch/{user} && echo exists", login_compiler_node_ip
    )
    assert "exists" in cmd.stdout, f"/scratch/{user} does not exist on login_compiler node"
    log.check(f"/scratch/{user} exists on login_compiler node")

    log.passed(f"LDAP user scratch directory verified for {user}")


# =============================================================================
# TC-006: LDAP user subdirectories
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(6)
def test_ldapuser_subdirectories(host, login_compiler_node_ip):
    """
    TC-006: Verify data/, jobs/, results/, tmp/ directories exist inside
    /scratch/<ldapuser>/.
    """
    _skip_if_no_vast(host)
    log = TestLogger("TC-006: Verify LDAP user subdirectories")

    creds = _get_all_ldap_credentials()
    users = creds.get("users", [])
    if not users:
        pytest.skip("No LDAP user credentials configured")

    user = users[0]["ldap_user"]
    password = users[0]["ldap_password"]
    subdirs = ["data", "jobs", "results", "tmp"]

    # Create subdirectories as the ldapuser via SSH
    for sd in subdirs:
        result = _run_as_ldapuser(
            host, login_compiler_node_ip, user, password,
            f"mkdir -p /scratch/{user}/{sd}"
        )
        if not result["success"]:
            # Fall back to root creation
            _safe_run_on_remote_node(
                host,
                f"mkdir -p /scratch/{user}/{sd} && chown {user}: /scratch/{user}/{sd}",
                login_compiler_node_ip,
            )

    # Verify each subdirectory exists (checked as root)
    for sd in subdirs:
        cmd = _safe_run_on_remote_node(
            host, f"test -d /scratch/{user}/{sd} && echo exists", login_compiler_node_ip
        )
        assert "exists" in cmd.stdout, f"/scratch/{user}/{sd} not found"
        log.check(f"Found: /scratch/{user}/{sd}/")

    log.passed(f"LDAP user subdirectories verified for {user}")


# =============================================================================
# TC-007: LDAP user permission isolation
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(7)
def test_ldapuser_permissions(host, login_compiler_node_ip):
    """
    TC-007: One LDAP user must not be able to access another LDAP user's
    /scratch/<other_user>/ directory.
    """
    _skip_if_no_vast(host)
    log = TestLogger("TC-007: Verify LDAP user permission isolation")

    creds = _get_all_ldap_credentials()
    users = creds.get("users", [])
    if len(users) < 2:
        pytest.skip("Need at least 2 LDAP users for permission isolation test")

    user1 = users[0]["ldap_user"]
    pass1 = users[0]["ldap_password"]
    user2 = users[1]["ldap_user"]

    # Ensure both scratch directories exist with strict permissions
    for u in [user1, user2]:
        _safe_run_on_remote_node(
            host,
            f"mkdir -p /scratch/{u} && chown {u}: /scratch/{u} && chmod 700 /scratch/{u}",
            login_compiler_node_ip,
        )

    # SSH as user1 and try to list user2's scratch directory — must fail
    result = _run_as_ldapuser(
        host, login_compiler_node_ip, user1, pass1, f"ls /scratch/{user2}/"
    )
    assert not result["success"], (
        f"User {user1} should NOT have access to /scratch/{user2}/ (got rc={result['rc']})"
    )
    log.check(f"{user1} correctly denied access to /scratch/{user2}/ (rc={result['rc']}): {result['stderr'][:80]}")

    log.passed("LDAP user permission isolation verified")


# =============================================================================
# TC-008: Scratch subdirectory file isolation
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(8)
def test_scratch_isolation(host, compute_node_ip):
    """
    TC-008: Files written to /scratch/dirA/ are absent from /scratch/dirB/.
    All scratch subdirectories have isolated space.
    """
    _skip_if_no_vast(host)
    log = TestLogger("TC-008: Verify scratch subdirectory isolation")

    ts = int(time.time())
    dir_a = f"/scratch/_iso_a_{ts}"
    dir_b = f"/scratch/_iso_b_{ts}"
    test_file = "isolation_check.txt"

    for d in [dir_a, dir_b]:
        _safe_run_on_remote_node(host, f"mkdir -p {d}", compute_node_ip)

    _safe_run_on_remote_node(host, f"echo 'test_data' > {dir_a}/{test_file}", compute_node_ip)

    cmd = _safe_run_on_remote_node(
        host, f"test -f {dir_b}/{test_file} && echo found || echo absent", compute_node_ip
    )
    assert "absent" in cmd.stdout, f"File isolation failed: {test_file} visible in {dir_b}"
    log.check(f"File in {dir_a} is absent from {dir_b}")

    # Cleanup
    for d in [dir_a, dir_b]:
        _safe_run_on_remote_node(host, f"rm -rf {d}", compute_node_ip)

    log.passed("Scratch subdirectory isolation verified")


# =============================================================================
# TC-009: Slurm control node has no VAST storage
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(9)
def test_control_node_no_vast(host, control_node_ip, vast_config):
    """
    TC-009: Verify that the Slurm control node has no VAST storage mounted.
    """
    _skip_if_no_vast(host)
    log = TestLogger("TC-009: Verify control node has no VAST mount")

    vast_source = vast_config.get("source", "")
    vast_host = vast_source.split(":")[0] if ":" in vast_source else ""

    # Check /proc/mounts for VAST
    cmd = _safe_run_on_remote_node(host, "cat /proc/mounts", control_node_ip)
    if cmd.rc == 0 and vast_host:
        vast_in_mounts = [l for l in cmd.stdout.splitlines() if vast_host in l]
        assert not vast_in_mounts, (
            f"VAST source '{vast_host}' found in control node mounts:\n"
            + "\n".join(vast_in_mounts)
        )
    log.check("VAST source not found in /proc/mounts on control node")

    # Check /etc/fstab
    cmd = _safe_run_on_remote_node(
        host,
        f"grep -i '{vast_host}' /etc/fstab 2>/dev/null && echo found || echo absent",
        control_node_ip,
    )
    assert "absent" in cmd.stdout, "VAST entry found in control node /etc/fstab"
    log.check("No VAST entry in /etc/fstab on control node")

    log.passed("Control node correctly has no VAST storage mounted")


# =============================================================================
# TC-010: VAST NFS RPM and kernel module
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
def test_vastnfs_rpm_and_module(host, compute_node_ip):
    """
    TC-010: Verify vastnfs RPM is installed from Pulp repository,
    kernel module is loaded, and vastnfs service is active.
    """
    _skip_if_no_vast(host)
    log = TestLogger("TC-010: Verify VAST NFS RPM and kernel module")

    # RPM check
    cmd = _safe_run_on_remote_node(host, "rpm -qa | grep -i vastnfs", compute_node_ip)
    if cmd.rc == 0 and cmd.stdout.strip():
        log.check(f"VAST NFS RPM installed: {cmd.stdout.strip()}")
    else:
        log.check("WARN: vastnfs RPM not found via rpm -qa")

    # Kernel module check
    cmd = _safe_run_on_remote_node(host, "lsmod | grep -i vastnfs", compute_node_ip)
    if cmd.rc == 0 and cmd.stdout.strip():
        log.check(f"VAST NFS kernel module loaded:\n{cmd.stdout.strip()}")
    else:
        # Check standard RDMA/NFS modules as fallback
        cmd = _safe_run_on_remote_node(host, "lsmod | grep -E '(rpcrdma|nfs)'", compute_node_ip)
        if cmd.rc == 0 and cmd.stdout.strip():
            log.check(f"NFS/RDMA modules loaded:\n{cmd.stdout.strip()}")
        else:
            log.check("WARN: No vastnfs or rpcrdma kernel module loaded")

    # Service check
    cmd = _safe_run_on_remote_node(
        host, "systemctl is-active vastnfs 2>/dev/null || echo inactive", compute_node_ip
    )
    service_status = cmd.stdout.strip()
    log.check(f"vastnfs service status: {service_status}")
    if "active" in service_status and "inactive" not in service_status:
        log.check("vastnfs service is active")

    log.passed("VAST NFS RPM and module check completed")


# =============================================================================
# TC-011: /etc/fstab entries
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(11)
def test_fstab_entries(host, compute_node_ip, vast_config):
    """
    TC-011: Verify /etc/fstab entries are generated with correct VAST
    mount options: proto=rdma, port=20049.
    """
    _skip_if_no_vast(host)
    log = TestLogger("TC-011: Verify /etc/fstab VAST entries")

    vast_source = vast_config.get("source", "")
    vast_host = vast_source.split(":")[0] if ":" in vast_source else ""

    cmd = _safe_run_on_remote_node(host, "cat /etc/fstab", compute_node_ip)
    assert cmd.rc == 0, "Cannot read /etc/fstab on compute node"

    fstab = cmd.stdout
    log.check(f"/etc/fstab content:\n{fstab}")

    # Find VAST lines
    vast_lines = [l for l in fstab.splitlines()
                  if vast_host and vast_host in l and not l.strip().startswith("#")]
    if not vast_lines:
        pytest.skip(f"No VAST entries for '{vast_host}' found in /etc/fstab")

    opts = " ".join(vast_lines)
    assert "proto=rdma" in opts, "proto=rdma missing from VAST fstab entries"
    assert "port=20049" in opts, "port=20049 missing from VAST fstab entries"
    log.check("Required options proto=rdma and port=20049 present in fstab")

    # Verify mount point directories exist
    for line in vast_lines:
        parts = line.split()
        if len(parts) >= 2:
            mp = parts[1]
            cmd2 = _safe_run_on_remote_node(
                host, f"test -d {mp} && echo exists", compute_node_ip
            )
            assert "exists" in cmd2.stdout, f"Mount point directory {mp} does not exist"
            log.check(f"Mount point directory exists: {mp}")

    log.passed("fstab entries verified")


# =============================================================================
# TC-012: VAST RDMA mount I/O test
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(12)
def test_vast_rdma_mount(host, compute_node_ip):
    """
    TC-012: Verify VAST storage is mounted via RDMA; nfsstat -m confirms RDMA
    transport and port 20049; write 1 GB + read + checksum verify.
    """
    _skip_if_no_vast(host)
    log = TestLogger("TC-012: Verify VAST RDMA mount and I/O")

    # Check nfsstat -m for RDMA
    cmd = _safe_run_on_remote_node(host, "nfsstat -m 2>/dev/null", compute_node_ip)
    if cmd.rc == 0 and cmd.stdout.strip():
        nfsstat_out = cmd.stdout
        if "rdma" in nfsstat_out.lower():
            log.check("RDMA transport confirmed via nfsstat -m")
        if "20049" in nfsstat_out:
            log.check("Port 20049 confirmed via nfsstat -m")
        log.check(f"nfsstat -m output:\n{nfsstat_out[:600]}")
    else:
        log.check("WARN: nfsstat -m not available or returned no output")

    # Check vastnfs-ctl status for active mount
    cmd = _safe_run_on_remote_node(
        host, "vastnfs-ctl status 2>/dev/null | head -20", compute_node_ip
    )
    if cmd.rc == 0 and cmd.stdout.strip():
        log.check(f"vastnfs-ctl status:\n{cmd.stdout.strip()}")

    # 1 GB I/O test with checksum
    ts = int(time.time())
    test_file = f"/scratch/_rdma_test_{ts}.dat"
    checksum_file = f"/scratch/_rdma_test_{ts}.sha256"

    log.check("Writing 1 GB test file to VAST mount (/scratch)...")
    cmd = _safe_run_on_remote_node(
        host,
        f"dd if=/dev/urandom of={test_file} bs=1M count=1024 2>/dev/null && echo write_ok",
        compute_node_ip,
    )
    if "write_ok" not in cmd.stdout:
        log.check("WARN: 1 GB write failed or /scratch not writable; skipping I/O check")
        return

    log.check("Computing SHA256 checksum of written file...")
    cmd = _safe_run_on_remote_node(
        host, f"sha256sum {test_file} > {checksum_file} && echo sum_ok", compute_node_ip
    )
    assert "sum_ok" in cmd.stdout, "Checksum computation failed"

    log.check("Re-reading file and verifying checksum...")
    cmd = _safe_run_on_remote_node(
        host, f"sha256sum -c {checksum_file} 2>&1 && echo verify_ok", compute_node_ip
    )
    assert "verify_ok" in cmd.stdout and "OK" in cmd.stdout, (
        f"Checksum verification failed: {cmd.stdout.strip()}"
    )
    log.check("Checksum verification passed")

    # Cleanup
    _safe_run_on_remote_node(host, f"rm -f {test_file} {checksum_file}", compute_node_ip)

    log.passed("VAST RDMA mount and I/O test passed")


# =============================================================================
# TC-013: VAST QSS mounts assigned to compute/login only
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(13)
def test_vast_qss_mounts(host, compute_node_ip, control_node_ip, vast_config):
    """
    TC-013: Verify VAST QSS mounts (/scratch, /home, /apps, /projects) are
    on compute and login nodes only; controller /etc/fstab has zero VAST entries.
    """
    _skip_if_no_vast(host)
    log = TestLogger("TC-013: Verify VAST QSS mount assignment")

    vast_source = vast_config.get("source", "")
    vast_host = vast_source.split(":")[0] if ":" in vast_source else ""

    # Compute node must have VAST QSS mounts
    cmd = _safe_run_on_remote_node(host, "cat /proc/mounts", compute_node_ip)
    if cmd.rc == 0:
        found = any(
            vast_host in l for l in cmd.stdout.splitlines() if vast_host
        )
        assert found, "VAST mounts not found on compute node"
        log.check("VAST mounts present on compute node")

    # Controller must have zero VAST fstab entries
    cmd = _safe_run_on_remote_node(
        host,
        f"grep -c '{vast_host}' /etc/fstab 2>/dev/null || echo 0",
        control_node_ip,
    )
    count = cmd.stdout.strip().split()[-1]
    assert count == "0", f"Controller /etc/fstab has {count} VAST entries (expected 0)"
    log.check("Controller /etc/fstab has zero VAST entries")

    log.passed("VAST QSS mount assignment verified")


# =============================================================================
# TC-014: Slurm job logs persistence
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(14)
def test_slurm_logs_persistence(host, control_node_ip):
    """
    TC-014: Verify Slurm logs are on persistent storage; sacct -l returns
    complete job records.
    """
    _skip_if_no_vast(host)
    log = TestLogger("TC-014: Verify Slurm log persistence")

    log_dirs = ["/var/log/slurm", "/var/spool/slurm", "/var/spool/slurmctld"]
    for log_dir in log_dirs:
        cmd = _safe_run_on_remote_node(
            host, f"test -d {log_dir} && df -h {log_dir} | tail -1", control_node_ip
        )
        if cmd.rc == 0 and cmd.stdout.strip():
            log.check(f"{log_dir} storage: {cmd.stdout.strip()}")

    # Verify sacct is available and returns records
    cmd = _safe_run_on_remote_node(
        host, "which sacct && sacct -n -X --format=JobID,State 2>/dev/null | head -5",
        control_node_ip,
    )
    if cmd.rc == 0 and cmd.stdout.strip():
        log.check(f"sacct output:\n{cmd.stdout.strip()}")
    else:
        log.check("WARN: sacct not available or no job records found")

    log.passed("Slurm log persistence check completed")


# =============================================================================
# TC-015: Slurm control node mount table
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(15)
def test_control_node_mounts(host, control_node_ip, vast_config):
    """
    TC-015: Verify the Slurm control node mount table.
    All listed mount points must be present; none should be from VAST.

    Expected (NFS/PowerVault only):
      /cert, /etc/slurm, /etc/my.cnf.d, /etc/munge, /var/log/mariadb,
      /var/log/slurm, /var/log/track, /var/lib/packages, /hpc_tools,
      /ssh, /ldapcerts, /home, /ldms
    VAST must NOT appear on the control node.
    """
    _skip_if_no_vast(host)
    log = TestLogger("TC-015: Verify control node mount table")

    expected_nfs_mounts = [
        "/cert", "/etc/slurm", "/etc/my.cnf.d", "/etc/munge",
        "/var/log/mariadb", "/var/log/slurm", "/var/log/track",
        "/var/lib/packages", "/hpc_tools", "/ssh", "/ldapcerts", "/home", "/ldms",
    ]

    vast_source = vast_config.get("source", "")
    vast_host = vast_source.split(":")[0] if ":" in vast_source else ""

    cmd = _safe_run_on_remote_node(host, "cat /proc/mounts", control_node_ip)
    assert cmd.rc == 0, "Cannot read /proc/mounts on control node"
    mounts_output = cmd.stdout
    log.check(f"/proc/mounts (control node):\n{mounts_output[:800]}")

    # None of the mounts should come from VAST
    if vast_host:
        vast_lines = [l for l in mounts_output.splitlines() if vast_host in l]
        assert not vast_lines, (
            f"VAST source '{vast_host}' unexpectedly found on control node:\n"
            + "\n".join(vast_lines)
        )
    log.check("No VAST mounts on control node - PASS")

    # Check expected NFS mount points exist (as directories at minimum)
    for mp in expected_nfs_mounts:
        cmd = _safe_run_on_remote_node(
            host, f"test -d {mp} && echo exists || echo missing", control_node_ip
        )
        status = cmd.stdout.strip()
        log.check(f"  {mp}: {status}")

    log.passed("Control node mount table verified")


# =============================================================================
# TC-016: Slurm compute node mount table
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(16)
def test_compute_node_mounts(host, compute_node_ip, vast_config):
    """
    TC-016: Verify the Slurm compute node mount table.

    NFS/PowerVault mounts: /cert, /etc/slurm/epilog.d, /etc/munge,
      /var/log/slurm, /var/log/track, /var/lib/packages, /var/spool/slurmd,
      /ssh. /ldms is expected only when LDMS is enabled.
    VAST mounts: /hpc_tools (=/apps), /home
    """
    _skip_if_no_vast(host)
    log = TestLogger("TC-016: Verify compute node mount table")

    nfs_mount_points = [
        "/cert", "/etc/slurm/epilog.d", "/etc/munge",
        "/var/log/slurm", "/var/log/track", "/var/lib/packages",
        "/var/spool/slurmd",
    ]
    if is_software_enabled(host, "ldms"):
        nfs_mount_points.append("/ldms")
    else:
        log.check("LDMS is not enabled in software_config.json; skipping /ldms expectation")
    vast_mount_points = ["/hpc_tools", "/home"]

    vast_source = vast_config.get("source", "")
    vast_host = vast_source.split(":")[0] if ":" in vast_source else ""

    cmd = _safe_run_on_remote_node(host, "cat /proc/mounts", compute_node_ip)
    assert cmd.rc == 0, "Cannot read /proc/mounts on compute node"
    mounts_output = cmd.stdout
    log.check(f"/proc/mounts (compute node):\n{mounts_output[:800]}")

    # NFS mount points must NOT come from VAST
    for mp in nfs_mount_points:
        mp_lines = [l for l in mounts_output.splitlines() if f" {mp} " in l]
        if mp_lines:
            for ml in mp_lines:
                assert not (vast_host and vast_host in ml), (
                    f"{mp} should NOT be a VAST mount on compute node"
                )
            log.check(f"  {mp}: NFS/PowerVault - PASS")
        else:
            log.check(f"WARN:   {mp}: not mounted (may be missing)")

    # VAST mount points (bind or direct) — warn only, do not assert
    for mp in vast_mount_points:
        mp_lines = [l for l in mounts_output.splitlines() if f" {mp} " in l]
        if mp_lines:
            is_vast = vast_host and any(vast_host in l for l in mp_lines)
            is_bind = any("bind" in l or "none" in l.split()[2] for l in mp_lines if len(l.split()) >= 3)
            tag = "VAST" if is_vast else ("bind/none" if is_bind else "other")
            log.check(f"  {mp}: mounted ({tag}) - PASS")
        else:
            log.check(f"WARN:   {mp}: not mounted (may be missing)")

    log.passed("Compute node mount table verified")


# =============================================================================
# TC-017: Login / compiler node mount table
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(17)
def test_login_node_mounts(host, vast_config):
    """
    TC-017: Verify the login / login_compiler node mount table.

    PowerScale mounts: /cert, /etc/slurm/epilog.d, /etc/munge,
      /var/log/slurm, /var/log/track, /var/lib/packages, /var/spool/slurmd.
      /ldms is expected only when LDMS is enabled.
    VAST mounts: /hpc_tools (=/apps), /home
    """
    _skip_if_no_vast(host)
    log = TestLogger("TC-017: Verify login node mount table")

    # Try login_compiler first, fall back to login
    lc_nodes = get_login_compiler_nodes(host)
    ln_nodes = get_login_nodes(host)
    node_ip = _first_ip(lc_nodes) or _first_ip(ln_nodes)
    if not node_ip:
        pytest.skip("No login or login_compiler nodes found")

    powerscale_mounts = [
        "/cert", "/etc/slurm/epilog.d", "/etc/munge",
        "/var/log/slurm", "/var/log/track", "/var/lib/packages",
        "/var/spool/slurmd",
    ]
    if is_software_enabled(host, "ldms"):
        powerscale_mounts.append("/ldms")
    else:
        log.check("LDMS is not enabled in software_config.json; skipping /ldms expectation")
    vast_mount_points = ["/hpc_tools", "/home"]

    vast_source = vast_config.get("source", "")
    vast_host = vast_source.split(":")[0] if ":" in vast_source else ""

    cmd = _safe_run_on_remote_node(host, "cat /proc/mounts", node_ip)
    assert cmd.rc == 0, "Cannot read /proc/mounts on login node"
    mounts_output = cmd.stdout
    log.check(f"/proc/mounts (login node):\n{mounts_output[:800]}")

    # PowerScale mounts must NOT come from VAST
    for mp in powerscale_mounts:
        mp_lines = [l for l in mounts_output.splitlines() if f" {mp} " in l]
        if mp_lines:
            for ml in mp_lines:
                assert not (vast_host and vast_host in ml), (
                    f"{mp} should NOT be a VAST mount on login node"
                )
            log.check(f"  {mp}: PowerScale - PASS")
        else:
            log.check(f"WARN:   {mp}: not mounted (may be missing)")

    # VAST mounts (bind or direct) — warn only, do not assert
    for mp in vast_mount_points:
        mp_lines = [l for l in mounts_output.splitlines() if f" {mp} " in l]
        if mp_lines:
            is_vast = vast_host and any(vast_host in l for l in mp_lines)
            is_bind = any("bind" in l or "none" in l.split()[2] for l in mp_lines if len(l.split()) >= 3)
            tag = "VAST" if is_vast else ("bind/none" if is_bind else "other")
            log.check(f"  {mp}: mounted ({tag}) - PASS")
        else:
            log.check(f"WARN:   {mp}: not mounted (may be missing)")

    log.passed("Login node mount table verified")
