"""Discovery Workflow Validation - Core Functions.

Implements post-run validation for cluster provisioning and configuration after
running discovery.

This module validates 5 key scenarios:
1. Openchami Container - The openchami container is running without errors.
2. Provisioning Images - All required images for provisioning are available in the S3 bucket.
3. Discovery Playbook Execution - discovery.yml runs successfully with exit code 0.
4. Node Boot Validation - Nodes are reachable via ping and SSH.
5. Package Installation - All required packages are installed on nodes according to their functional group.

Author: Dell Technologies
"""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..core.formatting import log as _log
from ..messages.discovery_msgs import DISCOVERY_MSGS
from ..vars.discovery_vars import DISCOVERY_VARS
from .prepare_oim_func import check_container_running


def _result(name: str, success: bool, details: Optional[str] = None, error: Optional[str] = None, **extra) -> Dict[str, Any]:
    """Create a structured result dictionary."""
    res: Dict[str, Any] = {
        "name": name,
        "success": success,
        "details": details,
        "error": error,
    }
    res.update(extra)
    return res


def _run(host, cmd: str) -> Tuple[int, str, str]:
    """Run a command on the host and return (rc, stdout, stderr)."""
    out = host.run(f"bash -lc {json.dumps(cmd)}")
    return out.rc, (out.stdout or "").strip(), (out.stderr or "").strip()


def _run_in_container(host, inner_cmd: str) -> Tuple[int, str, str]:
    if not bool(DISCOVERY_VARS.get("run_checks_in_container", True)):
        return _run(host, inner_cmd)

    container = (
        (DISCOVERY_VARS.get("discovery_container_name") or "").strip()
        or DISCOVERY_VARS.get("openchami_container_name", "omnia_core")
    )
    cmd = f"podman exec {container} bash -lc {json.dumps(inner_cmd)}"
    return _run(host, cmd)


def _require(value: Any, item_name: str) -> Tuple[bool, Optional[str]]:
    """Check if a required config value is present."""
    if value is None:
        return False, DISCOVERY_MSGS["missing_config"].format(item=item_name)
    if isinstance(value, str) and value.strip() == "":
        return False, DISCOVERY_MSGS["missing_config"].format(item=item_name)
    if isinstance(value, list) and len(value) == 0:
        return False, DISCOVERY_MSGS["missing_config"].format(item=item_name)
    if isinstance(value, dict) and len(value) == 0:
        return False, DISCOVERY_MSGS["missing_config"].format(item=item_name)
    return True, None


def _parse_hostport(value: str, default_port: int) -> Tuple[str, int]:
    v = (value or "").strip()
    if not v:
        return "", default_port
    if ":" in v and not v.endswith(":"):
        host, port_s = v.rsplit(":", 1)
        try:
            return host.strip(), int(port_s.strip())
        except ValueError:
            return v, default_port
    return v, default_port


def _ldap_lookup(host, node: str, user: str, ldap_user: str, timeout_sec: int = 20) -> Tuple[bool, Dict[str, Any]]:
    """Validate LDAP user visibility on a node.

    Preference order:
    1) If discovery_validation.external_ldap_ip is set and ldapsearch exists, run ldapsearch against it.
    2) Fallback to getent (SSSD/NSS path).
    """
    ldap_user = (ldap_user or "").strip()
    if not ldap_user:
        return True, {"method": "skipped", "reason": "ldap_test_user_not_set"}

    ext = (DISCOVERY_VARS.get("external_ldap_ip") or "").strip()
    if ext:
        ldap_host, ldap_port = _parse_hostport(ext, 1389)
        # If user provided host:port, respect it; otherwise default to 1389 (commonly used for proxy setups).
        target = f"ldap://{ldap_host}:{ldap_port}"
        base_dn = "dc=omnia,dc=test"
        # Only attempt ldapsearch if the node has it.
        rc0, out0, _ = _ssh_run(host, node, user, "command -v ldapsearch", timeout_sec=10)
        if rc0 == 0 and (out0 or "").strip():
            rc1, out1, err1 = _ssh_run(
                host,
                node,
                user,
                f"ldapsearch -LLL -x -H {target} -b {json.dumps(base_dn)} (uid={json.dumps(ldap_user)}) uid",
                timeout_sec=timeout_sec,
            )
            ok = (rc1 == 0) and ("uid:" in (out1 or ""))
            return ok, {"method": "ldapsearch", "rc": rc1, "out": out1, "err": err1, "target": target}

    rc2, out2, err2 = _ssh_run(host, node, user, f"getent passwd {ldap_user}", timeout_sec=timeout_sec)
    ok2 = rc2 == 0 and bool((out2 or "").strip())
    return ok2, {"method": "getent", "rc": rc2, "out": out2, "err": err2}


_SLAPD_PROXY_CACHE: Dict[str, Any] = {}


def _slapd_meta_proxy_status(host) -> Dict[str, Any]:
    # slapd.conf belongs to the LDAP service container.
    auth_container = "omnia_auth"
    cr = check_container_running(host, auth_container)
    if not cr.get("success"):
        res = {
            "ok": False,
            "rc": None,
            "slapd_conf": "",
            "has_database_meta": False,
            "has_back_meta": False,
            "has_back_ldap": False,
            "detected_uri": "",
            "container_error": f"{auth_container} container is not running: {cr.get('status')}",
        }
        return res

    rc_c, out_c, _ = _run(
        host,
        f"podman exec {auth_container} bash -lc "
        + json.dumps("test -f /opt/omnia/auth/slapd.conf && cat /opt/omnia/auth/slapd.conf || true"),
    )
    slapd_text = out_c or ""
    lower_lines = [
        ln.strip().lower()
        for ln in slapd_text.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]

    db_backends: List[str] = []
    for ln in lower_lines:
        if not ln.startswith("database"):
            continue
        parts = ln.split()
        if len(parts) >= 2:
            db_backends.append(parts[1])

    has_database_meta = "meta" in db_backends
    has_back_meta = any(ln.startswith("moduleload") and "back_meta.la" in ln for ln in lower_lines)
    has_back_ldap = any(ln.startswith("moduleload") and "back_ldap.la" in ln for ln in lower_lines)

    detected_uri = ""
    for ln in slapd_text.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        if s.lower().startswith("uri"):
            parts = s.split(None, 1)
            if len(parts) == 2:
                detected_uri = parts[1].strip().strip('"').strip("'")
                break

    # Strict: fail if slapd.conf is configured as local LDAP (e.g. mdb) instead of meta proxy.
    # Allow 'config' database if present; it's unrelated to the proxy backend.
    non_proxy_dbs = [d for d in db_backends if d not in {"meta", "config"}]
    ok = (
        bool(slapd_text.strip())
        and has_database_meta
        and has_back_meta
        and has_back_ldap
        and bool(detected_uri)
        and not non_proxy_dbs
    )
    res = {
        "ok": ok,
        "rc": rc_c,
        "slapd_conf": slapd_text,
        "db_backends": db_backends,
        "non_proxy_db_backends": non_proxy_dbs,
        "has_database_meta": has_database_meta,
        "has_back_meta": has_back_meta,
        "has_back_ldap": has_back_ldap,
        "detected_uri": detected_uri,
    }
    return res


def validate_openchami_container(host) -> Dict[str, Any]:
    """Validate that the OpenCHAMI container is running without errors."""
    container = DISCOVERY_VARS["openchami_container_name"]
    rc_ps, out_ps, err_ps = _run(host, "podman ps -a")
    result = check_container_running(host, container)
    if result["success"]:
        return _result(
            name="Openchami Container Running",
            success=True,
            details=DISCOVERY_MSGS["openchami_running"].format(container=container),
            podman_ps=out_ps if rc_ps == 0 else (err_ps or out_ps),
        )
    return _result(
        name="Openchami Container Running",
        success=False,
        details=None,
        error=DISCOVERY_MSGS["openchami_not_running"].format(container=container) + f": {result.get('status')}",
        podman_ps=out_ps if rc_ps == 0 else (err_ps or out_ps),
    )


def validate_s3_provisioning_images(host) -> Dict[str, Any]:
    """Validate that all required provisioning images are available in the S3 bucket."""
    ok, err = _require(DISCOVERY_VARS.get("s3_bucket"), "discovery_validation.s3_bucket")
    if not ok:
        return _result("Provisioning Images Present in S3", False, error=err)

    required = DISCOVERY_VARS.get("required_provisioning_images", [])
    if not required:
        node_groups = DISCOVERY_VARS.get("node_groups", {}) or {}
        ok, err = _require(node_groups, "discovery_validation.node_groups (auto-derived from PXE mapping)")
        if not ok:
            return _result("Provisioning Images Present in S3", False, error=err)

        kernel = (DISCOVERY_VARS.get("required_kernel_version") or "").strip()
        ok, err = _require(kernel, "required_kernel_version")
        if not ok:
            return _result("Provisioning Images Present in S3", False, error=err)

        # Expected keys are derived from PXE mapping functional groups.
        # Format observed in S3: efi-images/<group>/rhel-<group>/(initramfs|vmlinuz)-<kernel>
        required = []
        for group in node_groups.keys():
            required.append(f"efi-images/{group}/rhel-{group}/initramfs-{kernel}.img")
            required.append(f"efi-images/{group}/rhel-{group}/vmlinuz-{kernel}")
    else:
        ok, err = _require(required, "discovery_validation.required_provisioning_images")
        if not ok:
            return _result("Provisioning Images Present in S3", False, error=err)

    bucket = DISCOVERY_VARS["s3_bucket"]
    prefix = DISCOVERY_VARS.get("s3_prefix", "")

    # Use a full listing to also detect unexpected groups.
    # We use s3cmd for compatibility with existing environments.
    rc_ls, out_ls, err_ls = _run(host, f"s3cmd ls -Hr s3://{bucket}")
    if rc_ls != 0:
        return _result(
            "Provisioning Images Present in S3",
            False,
            error=f"s3cmd ls failed (rc={rc_ls}): {err_ls or out_ls}",
        )

    listed_keys: List[str] = []
    listed_groups: List[str] = []
    for line in (out_ls or "").splitlines():
        if "s3://" not in line:
            continue
        try:
            url = line.split()[-1]
        except IndexError:
            continue
        # url example: s3://boot-images/efi-images/<group>/...
        if not url.startswith(f"s3://{bucket}/"):
            continue
        key = url[len(f"s3://{bucket}/"):]
        listed_keys.append(key)
        if key.startswith("efi-images/"):
            parts = key.split("/")
            if len(parts) >= 2:
                listed_groups.append(parts[1])

    expected_groups = set((DISCOVERY_VARS.get("node_groups", {}) or {}).keys())
    unexpected = sorted({g for g in listed_groups if g and g not in expected_groups})
    if unexpected:
        return _result(
            "Provisioning Images Present in S3",
            False,
            error=DISCOVERY_MSGS["s3_images_unexpected"].format(groups=", ".join(unexpected)),
        )

    missing: List[str] = []
    checks: List[Dict[str, Any]] = []
    for key in required:
        obj = f"{prefix.rstrip('/')}/{key}" if prefix else key
        present = obj in listed_keys
        checks.append({"object": obj, "present": present})
        if not present:
            missing.append(obj)

    if missing:
        return _result(
            "Provisioning Images Present in S3",
            False,
            error=DISCOVERY_MSGS["s3_images_missing"].format(missing=", ".join(missing)),
            sub_results=checks,
        )

    return _result(
        "Provisioning Images Present in S3",
        True,
        details=DISCOVERY_MSGS["s3_images_ok"],
        sub_results=checks,
    )


def validate_discovery_execution(host) -> Dict[str, Any]:
    """Validate that discovery.yml runs successfully with exit code 0."""
    marker = DISCOVERY_VARS.get("discovery_success_marker", "")
    cmd = DISCOVERY_VARS.get("discovery_playbook_cmd", "")

    if cmd:
        rc, stdout, stderr = _run(host, cmd)
        if rc == 0:
            return _result(
                "Discovery Playbook Execution",
                True,
                details=f"{DISCOVERY_MSGS['discovery_ok']} (cmd rc=0)",
                output=stdout[-2000:] if stdout else "",  # Last 2000 chars of output
            )
        return _result(
            "Discovery Playbook Execution",
            False,
            details=stdout,
            error=f"Command failed (rc={rc}): {stderr or stdout}",
            output=stdout[-2000:] if stdout else "",
        )

    ok, err = _require(marker, "discovery_validation.discovery_success_marker or discovery_validation.discovery_playbook_cmd")
    if not ok:
        return _result("Discovery Playbook Execution", False, error=err)

    rc, stdout, stderr = _run(host, f"test -f {json.dumps(marker)}")
    if rc == 0:
        return _result(
            "Discovery Playbook Execution",
            True,
            details=f"{DISCOVERY_MSGS['discovery_ok']} (marker exists: {marker})",
        )

    return _result(
        "Discovery Playbook Execution",
        False,
        error=f"{DISCOVERY_MSGS['discovery_fail']}: marker not found: {marker} ({stderr or stdout})",
    )


def _ping(host, node: str) -> bool:
    """Ping a node and return True if reachable."""
    rc, _, _ = _run_in_container(host, f"ping -c 1 -W 2 {json.dumps(node)}")
    return rc == 0


def _ssh_check(host, node: str, user: str, _password: str) -> Tuple[bool, str]:
    """SSH to a node and return (success, message)."""
    base = "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 -o BatchMode=yes -o LogLevel=ERROR"

    rc, stdout, stderr = _run_in_container(host, f"{base} {user}@{node} 'echo ssh_ok'")
    combined = (stdout + "\n" + stderr).strip()
    if rc == 0 and "ssh_ok" in stdout:
        return True, "ssh_ok"

    # If SSH reached the node but authentication failed, treat it as reachable/booted.
    # This matches the user's desired behavior (password prompt/auth required == node is up).
    if "permission denied" in combined.lower() or "password" in combined.lower():
        return True, combined

    return False, (combined or "SSH failed")


def _ssh_run(host, node: str, user: str, remote_cmd: str, timeout_sec: int = 30) -> Tuple[int, str, str]:
    base = "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=8 -o BatchMode=yes -o LogLevel=ERROR"
    # Note: wrap in timeout to prevent hangs (e.g., srun waiting for resources)
    wrapped = f"timeout {int(timeout_sec)}s {remote_cmd}" if timeout_sec and timeout_sec > 0 else remote_cmd
    cmd = f"{base} {user}@{node} {json.dumps(wrapped)}"
    return _run_in_container(host, cmd)


def _slurm_has_allocatable_nodes(sinfo_text: str) -> Tuple[bool, str]:
    states: List[str] = []
    for line in (sinfo_text or "").splitlines():
        s = line.strip().lower()
        if not s:
            continue
        # sinfo -h -o '%T' yields just the state, one per line
        # sinfo default output includes STATE column; handle both.
        parts = s.split()
        if len(parts) == 1:
            states.append(parts[0])
        else:
            states.append(parts[-2] if len(parts) >= 2 else parts[-1])

    if not states:
        return False, "No nodes found in sinfo output"

    bad = {"drain", "drained", "down", "unk", "unknown", "fail", "failing", "maint", "reserved"}
    good = {"idle", "mix", "alloc", "allocated", "completing"}

    if any(st in good for st in states):
        return True, "allocatable_nodes_present"

    if all(st in bad for st in states):
        return False, f"no_allocatable_nodes: states={sorted(set(states))}"

    # Default conservative: if we can't identify a good state, treat as not allocatable.
    return False, f"unable_to_confirm_allocatable_nodes: states={sorted(set(states))}"


def validate_node_boot(host) -> Dict[str, Any]:
    """Validate that nodes are reachable via ping and SSH."""
    nodes = DISCOVERY_VARS.get("nodes", [])
    ok, err = _require(nodes, "discovery_validation.nodes")
    if not ok:
        return _result("Node Boot Validation", False, error=err)

    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")

    booted: List[str] = []
    non_booted: List[str] = []
    details: List[Dict[str, Any]] = []

    for n in nodes:
        ping_ok = _ping(host, n)
        ssh_ok, ssh_msg = (False, "")
        if ping_ok:
            ssh_ok, ssh_msg = _ssh_check(host, n, user, password)
        ok_all = ping_ok and ssh_ok
        details.append({"node": n, "ping": ping_ok, "ssh": ssh_ok, "ssh_msg": ssh_msg})
        if ok_all:
            booted.append(n)
        else:
            non_booted.append(n)

    success = len(non_booted) == 0
    return _result(
        "Node Boot Validation",
        success,
        details=DISCOVERY_MSGS["nodes_boot_ok"] if success else DISCOVERY_MSGS["nodes_boot_fail"],
        booted_nodes=booted,
        non_booted_nodes=non_booted,
        sub_results=details,
    )


def validate_packages_by_group(host) -> Dict[str, Any]:
    """Validate that all required packages are installed on nodes according to their functional group."""
    node_groups: Dict[str, Any] = DISCOVERY_VARS.get("node_groups", {}) or {}
    packages_by_group: Dict[str, Any] = DISCOVERY_VARS.get("packages_by_group", {}) or {}

    ok, err = _require(node_groups, "discovery_validation.node_groups")
    if not ok:
        return _result("Package Installation", False, error=err)

    ok, err = _require(packages_by_group, "discovery_validation.packages_by_group")
    if not ok:
        return _result("Package Installation", False, error=err)

    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")

    missing: List[Dict[str, Any]] = []
    checks: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []

    for group, nodes in node_groups.items():
        pkgs = packages_by_group.get(group, [])
        pkgs_list: List[str] = pkgs if isinstance(pkgs, list) else [p.strip() for p in str(pkgs).split(",") if p.strip()]
        for node in (nodes or []):
            for pkg in pkgs_list:
                ssh_ok, ssh_msg = _ssh_check(host, node, user, password)
                if not ssh_ok:
                    checks.append({"group": group, "node": node, "package": pkg, "rc": -1, "out": "", "err": ssh_msg})
                    missing.append({"group": group, "node": node, "package": pkg, "reason": ssh_msg})
                    continue

                if ssh_msg != "ssh_ok":
                    checks.append({"group": group, "node": node, "package": pkg, "rc": None, "out": "", "err": ssh_msg})
                    skipped.append({"group": group, "node": node, "package": pkg, "reason": ssh_msg})
                    continue

                base_ssh = "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 -o BatchMode=yes -o LogLevel=ERROR"
                rc, stdout, stderr = _run_in_container(host, f"{base_ssh} {user}@{node} rpm -q {json.dumps(pkg)}")
                checks.append({"group": group, "node": node, "package": pkg, "rc": rc, "out": stdout, "err": stderr})
                if rc != 0:
                    missing.append({"group": group, "node": node, "package": pkg, "reason": stderr or stdout})

    if missing:
        return _result(
            "Package Installation",
            False,
            error=DISCOVERY_MSGS["packages_missing"],
            missing=missing,
            sub_results=checks,
        )

    if skipped:
        return _result(
            "Package Installation",
            True,
            details="Skipped package verification on some nodes (SSH authentication required)",
            skipped=True,
            skipped_items=skipped,
            sub_results=checks,
        )

    return _result(
        "Package Installation",
        True,
        details=DISCOVERY_MSGS["packages_ok"],
        sub_results=checks,
    )


def _load_expected_bmc_groups(pxe_mapping_file: str) -> Tuple[Dict[str, str], Optional[str]]:
    """Return mapping of BMC_IP -> GROUP_NAME derived from pxe_mapping_file.csv."""
    if not pxe_mapping_file or not os.path.exists(pxe_mapping_file):
        return {}, f"PXE mapping file not found: {pxe_mapping_file}"

    expected: Dict[str, str] = {}
    try:
        with open(pxe_mapping_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                bmc_ip = (row.get("BMC_IP") or "").strip()
                group_name = (row.get("GROUP_NAME") or "").strip()
                if not bmc_ip or not group_name:
                    continue
                expected[bmc_ip] = group_name
    except OSError as e:
        return {}, str(e)

    if not expected:
        return {}, "No BMC_IP/GROUP_NAME entries found in PXE mapping file"
    return expected, None


def validate_bmc_group_csv(host) -> Dict[str, Any]:
    """Validate that bmc_group_data.csv is generated correctly when iDRAC telemetry support is enabled."""
    if not bool(DISCOVERY_VARS.get("idrac_telemetry_support", False)):
        return _result(
            "BMC Group File",
            True,
            details="iDRAC telemetry support is disabled; skipping BMC Group File validation",
            skipped=True,
        )

    pxe_mapping_file = DISCOVERY_VARS.get("pxe_mapping_file", "")
    expected, err = _load_expected_bmc_groups(pxe_mapping_file)
    if err:
        return _result("BMC Group File", False, error=err)

    csv_path = (DISCOVERY_VARS.get("bmc_group_csv_path") or "").strip()
    ok, err = _require(csv_path, "discovery_validation.bmc_group_csv_path")
    if not ok:
        return _result("BMC Group File", False, error=err)

    rc, out, stderr = _run_in_container(host, f"test -f {json.dumps(csv_path)}")
    if rc != 0:
        return _result(
            "BMC Group File",
            False,
            error=f"{DISCOVERY_MSGS['bmc_group_missing']}: file not found: {csv_path} ({stderr or out})",
        )

    rc, out, stderr = _run_in_container(host, f"cat {json.dumps(csv_path)}")
    if rc != 0:
        return _result(
            "BMC Group File",
            False,
            error=f"{DISCOVERY_MSGS['bmc_group_missing']}: unable to read: {csv_path} ({stderr or out})",
        )

    lines = [ln.strip() for ln in (out or "").splitlines() if ln.strip()]
    if not lines:
        return _result(
            "BMC Group File",
            False,
            error=f"{DISCOVERY_MSGS['bmc_group_missing']}: empty file: {csv_path}",
        )

    header = lines[0].replace(" ", "")
    if header != "BMC_IP,GROUP_NAME,PARENT":
        return _result(
            "BMC Group File",
            False,
            error=f"{DISCOVERY_MSGS['bmc_group_missing']}: invalid header: {lines[0]}",
            csv_content=out,
        )

    found: Dict[str, str] = {}
    extra_rows: List[str] = []
    for ln in lines[1:]:
        parts = [p.strip() for p in ln.split(",")]
        if len(parts) < 2:
            continue
        bmc_ip = parts[0]
        grp = parts[1]
        if bmc_ip and grp:
            found[bmc_ip] = grp
            if bmc_ip not in expected:
                extra_rows.append(ln)

    missing_rows: List[str] = []
    mismatched_rows: List[str] = []
    for bmc_ip, grp in expected.items():
        if bmc_ip not in found:
            missing_rows.append(f"{bmc_ip},{grp}")
        elif found[bmc_ip] != grp:
            mismatched_rows.append(f"{bmc_ip}: expected {grp}, got {found[bmc_ip]}")

    if missing_rows or mismatched_rows or extra_rows:
        problems: List[str] = []
        if missing_rows:
            problems.append("Missing rows: " + "; ".join(missing_rows))
        if mismatched_rows:
            problems.append("Mismatched rows: " + "; ".join(mismatched_rows))
        if extra_rows:
            problems.append("Unexpected rows: " + "; ".join(extra_rows))
        return _result(
            "BMC Group File",
            False,
            error=f"{DISCOVERY_MSGS['bmc_group_missing']}: " + " | ".join(problems),
            csv_content=out,
            expected=expected,
            found=found,
        )

    return _result(
        "BMC Group File",
        True,
        details=DISCOVERY_MSGS["bmc_group_ok"],
        csv_content=out,
        expected=expected,
        found=found,
    )


def validate_slurm_cluster(host) -> Dict[str, Any]:
    """Validate Slurm health (sinfo/srun), LDAP lookup, and optional GPU/IB checks via srun."""
    controller = (DISCOVERY_VARS.get("slurm_controller") or "").strip()
    if not controller:
        return _result(
            "Slurm Cluster",
            True,
            details="Slurm controller not configured/detected; skipping Slurm validation",
            skipped=True,
        )

    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")

    # Need real command execution on controller; if auth is required, skip.
    ssh_ok, ssh_msg = _ssh_check(host, controller, user, password)
    if not ssh_ok:
        return _result("Slurm Cluster", False, error=f"Unable to SSH to slurm controller {controller}: {ssh_msg}")
    if ssh_msg != "ssh_ok":
        return _result(
            "Slurm Cluster",
            True,
            details=f"SSH authentication required for {controller}; skipping Slurm validation",
            skipped=True,
        )

    sub: List[Dict[str, Any]] = []

    def _add(name: str, ok: bool, rc: Optional[int] = None, out: str = "", err: str = "", skipped: bool = False):
        sub.append({"check": name, "success": ok, "skipped": skipped, "rc": rc, "out": out, "err": err})

    # 1) sinfo
    rc, out, err = _ssh_run(host, controller, user, "sinfo -h -o '%T'", timeout_sec=20)
    _add("sinfo", rc == 0, rc=rc, out=out, err=err)

    alloc_ok, alloc_reason = (False, "sinfo_failed")
    if rc == 0:
        alloc_ok, alloc_reason = _slurm_has_allocatable_nodes(out)

    # 2) srun
    if not alloc_ok:
        _add("srun", True, skipped=True, err=f"Skipped srun: {alloc_reason}")
        return _result(
            "Slurm Cluster",
            False,
            error=f"No allocatable nodes for srun ({alloc_reason})",
            details=DISCOVERY_MSGS["slurm_fail"],
            sub_results=sub,
            slurm_controller=controller,
        )

    # Fail fast if scheduler can't allocate quickly.
    rc2, out2, err2 = _ssh_run(host, controller, user, "srun --immediate=10 --time=00:01:00 -N1 -n1 /bin/hostname", timeout_sec=70)
    _add("srun", rc2 == 0, rc=rc2, out=out2, err=err2)

    # 3) LDAP test user lookup (optional)
    ldap_user = (DISCOVERY_VARS.get("ldap_test_user") or "").strip()
    if ldap_user:
        ok3, meta3 = _ldap_lookup(host, controller, user, ldap_user, timeout_sec=20)
        _add("ldap", ok3, rc=meta3.get("rc"), out=meta3.get("out", ""), err=meta3.get("err", ""))
    else:
        _add("ldap", True, skipped=True)

    # 4) GPU check (optional, nodes list)
    gpu_nodes = DISCOVERY_VARS.get("gpu_test_nodes", []) or []
    if gpu_nodes:
        n = str(gpu_nodes[0]).strip()
        rc4, out4, err4 = _ssh_run(host, controller, user, f"srun --immediate=10 --time=00:02:00 -w {n} -n1 nvidia-smi -L", timeout_sec=130)
        _add("gpu", rc4 == 0, rc=rc4, out=out4, err=err4)
    else:
        _add("gpu", True, skipped=True)

    # 5) IB check (optional, nodes list)
    ib_nodes = DISCOVERY_VARS.get("ib_test_nodes", []) or []
    if ib_nodes:
        n = str(ib_nodes[0]).strip()
        rc5, out5, err5 = _ssh_run(host, controller, user, f"srun --immediate=10 --time=00:02:00 -w {n} -n1 ibstat", timeout_sec=130)
        if rc5 != 0:
            rc5, out5, err5 = _ssh_run(host, controller, user, f"srun --immediate=10 --time=00:02:00 -w {n} -n1 ibv_devinfo -l", timeout_sec=130)
        _add("ib", rc5 == 0, rc=rc5, out=out5, err=err5)
    else:
        _add("ib", True, skipped=True)

    mandatory = [x for x in sub if x["check"] in {"sinfo", "srun"}]
    success = all(x["success"] for x in mandatory)
    return _result(
        "Slurm Cluster",
        success,
        details=DISCOVERY_MSGS["slurm_ok"] if success else DISCOVERY_MSGS["slurm_fail"],
        sub_results=sub,
        slurm_controller=controller,
    )


def _slurm_controller_or_skip() -> Tuple[str, Optional[Dict[str, Any]]]:
    controller = (DISCOVERY_VARS.get("slurm_controller") or "").strip()
    if not controller:
        return "", _result(
            "Slurm Controller",
            True,
            details="Slurm controller not configured/detected; skipping",
            skipped=True,
        )
    return controller, None


def _login_node_or_skip() -> Tuple[str, Optional[Dict[str, Any]]]:
    node = (DISCOVERY_VARS.get("login_node") or "").strip()
    if not node:
        return "", _result(
            "Login Node",
            True,
            details="Login node not configured/detected; skipping",
            skipped=True,
        )
    return node, None


def _login_compiler_node_or_skip() -> Tuple[str, Optional[Dict[str, Any]]]:
    node = (DISCOVERY_VARS.get("login_compiler_node") or "").strip()
    if not node:
        return "", _result(
            "Login Compiler Node",
            True,
            details="Login compiler node not configured/detected; skipping",
            skipped=True,
        )
    return node, None


def _ensure_ssh_ok(host, node: str, user: str, password: str, scenario_name: str) -> Optional[Dict[str, Any]]:
    ssh_ok, ssh_msg = _ssh_check(host, node, user, password)
    if not ssh_ok:
        return _result(scenario_name, False, error=f"Unable to SSH to {node}: {ssh_msg}")
    if ssh_msg != "ssh_ok":
        return _result(
            scenario_name,
            True,
            details=f"SSH authentication required for {node}; skipping",
            skipped=True,
        )
    return None


def _systemctl_active_check(host, node: str, user: str, svc: str, scenario_name: str) -> Dict[str, Any]:
    rc, out, err = _ssh_run(host, node, user, f"systemctl is-active {svc}", timeout_sec=15)
    active = (out or "").strip() == "active"
    status_out = ""
    if rc != 0 or not active:
        _, status_out, _ = _ssh_run(host, node, user, f"systemctl status {svc} --no-pager -l", timeout_sec=20)
    return _result(
        scenario_name,
        active,
        details=f"{svc} is active" if active else None,
        error=None if active else f"{svc} is not active",
        rc=rc,
        out=out,
        err=err,
        status=status_out,
        node=node,
        service=svc,
    )


def validate_slurm_sinfo(host) -> Dict[str, Any]:
    controller, skip = _slurm_controller_or_skip()
    if skip:
        skip["name"] = "Slurm sinfo"
        return skip

    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")
    ssh_res = _ensure_ssh_ok(host, controller, user, password, "Slurm sinfo")
    if ssh_res:
        return ssh_res

    rc, out, err = _ssh_run(host, controller, user, "sinfo -h -o '%T'", timeout_sec=20)
    ok = rc == 0
    extra: Dict[str, Any] = {"rc": rc, "out": out, "err": err, "slurm_controller": controller}
    if ok:
        alloc_ok, alloc_reason = _slurm_has_allocatable_nodes(out)
        extra["allocatable"] = alloc_ok
        extra["alloc_reason"] = alloc_reason
    return _result(
        "Slurm sinfo",
        ok,
        details="sinfo succeeded" if ok else None,
        error=None if ok else f"sinfo failed (rc={rc}): {err or out}",
        **extra,
    )


def validate_slurm_srun(host) -> Dict[str, Any]:
    controller, skip = _slurm_controller_or_skip()
    if skip:
        skip["name"] = "Slurm srun"
        return skip

    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")
    ssh_res = _ensure_ssh_ok(host, controller, user, password, "Slurm srun")
    if ssh_res:
        return ssh_res

    rc_si, out_si, err_si = _ssh_run(host, controller, user, "sinfo -h -o '%T'", timeout_sec=20)
    if rc_si != 0:
        return _result(
            "Slurm srun",
            False,
            error=f"sinfo failed (rc={rc_si}): {err_si or out_si}",
            rc=rc_si,
            out=out_si,
            err=err_si,
            slurm_controller=controller,
        )

    alloc_ok, alloc_reason = _slurm_has_allocatable_nodes(out_si)
    if not alloc_ok:
        return _result(
            "Slurm srun",
            True,
            details=f"Skipped srun: {alloc_reason}",
            skipped=True,
            slurm_controller=controller,
        )

    rc, out, err = _ssh_run(host, controller, user, "srun --immediate=10 --time=00:01:00 -N1 -n1 /bin/hostname", timeout_sec=70)
    ok = rc == 0
    return _result(
        "Slurm srun",
        ok,
        details="srun succeeded" if ok else None,
        error=None if ok else f"srun failed (rc={rc}): {err or out}",
        rc=rc,
        out=out,
        err=err,
        slurm_controller=controller,
    )


def validate_slurm_ldap(host) -> Dict[str, Any]:
    controller, skip = _slurm_controller_or_skip()
    if skip:
        skip["name"] = "Slurm LDAP"
        return skip

    ldap_user = (DISCOVERY_VARS.get("ldap_test_user") or "").strip()
    if not ldap_user:
        return _result(
            "Slurm LDAP",
            False,
            error="ldap_test_user not set; LDAP validation is required",
            slurm_controller=controller,
        )

    proxy = _slapd_meta_proxy_status(host)
    if not proxy.get("ok"):
        return _result(
            "Slurm LDAP",
            False,
            error=(
                "slapd.conf is not configured for external LDAP proxy (meta backend). "
                "Expected moduleload back_ldap.la + back_meta.la, database meta, and uri in /opt/omnia/auth/slapd.conf"
            ),
            detected_uri=proxy.get("detected_uri", ""),
            slapd_conf=proxy.get("slapd_conf", ""),
            slurm_controller=controller,
        )

    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")
    ssh_res = _ensure_ssh_ok(host, controller, user, password, "Slurm LDAP")
    if ssh_res:
        return ssh_res

    ok, meta = _ldap_lookup(host, controller, user, ldap_user, timeout_sec=20)
    return _result(
        "Slurm LDAP",
        ok,
        details="LDAP lookup succeeded" if ok else None,
        error=None if ok else f"LDAP lookup failed: {meta.get('err') or meta.get('out')}",
        rc=meta.get("rc"),
        out=meta.get("out", ""),
        err=meta.get("err", ""),
        method=meta.get("method"),
        slurm_controller=controller,
    )


def validate_slurm_gpu(host) -> Dict[str, Any]:
    controller, skip = _slurm_controller_or_skip()
    if skip:
        skip["name"] = "Slurm GPU"
        return skip

    gpu_nodes = DISCOVERY_VARS.get("gpu_test_nodes", []) or []
    if not gpu_nodes:
        return _result(
            "Slurm GPU",
            False,
            error="gpu_test_nodes not set; GPU validation is required",
            slurm_controller=controller,
        )

    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")
    ssh_res = _ensure_ssh_ok(host, controller, user, password, "Slurm GPU")
    if ssh_res:
        return ssh_res

    rc_si, out_si, err_si = _ssh_run(host, controller, user, "sinfo -h -o '%T'", timeout_sec=20)
    if rc_si != 0:
        return _result("Slurm GPU", False, error=f"sinfo failed (rc={rc_si}): {err_si or out_si}", rc=rc_si, out=out_si, err=err_si)
    alloc_ok, alloc_reason = _slurm_has_allocatable_nodes(out_si)
    if not alloc_ok:
        return _result(
            "Slurm GPU",
            False,
            error=f"No allocatable nodes for GPU check ({alloc_reason})",
            rc=rc_si,
            out=out_si,
            err=err_si,
            slurm_controller=controller,
        )

    n = str(gpu_nodes[0]).strip()
    rc, out, err = _ssh_run(host, controller, user, f"srun --immediate=10 --time=00:02:00 -w {n} -n1 nvidia-smi -L", timeout_sec=130)
    ok = rc == 0
    return _result("Slurm GPU", ok, details="GPU check succeeded" if ok else None, error=None if ok else f"GPU check failed (rc={rc}): {err or out}", rc=rc, out=out, err=err, node=n)


def validate_slurm_ib(host) -> Dict[str, Any]:
    controller, skip = _slurm_controller_or_skip()
    if skip:
        skip["name"] = "Slurm IB"
        return skip

    ib_nodes = DISCOVERY_VARS.get("ib_test_nodes", []) or []
    if not ib_nodes:
        return _result(
            "Slurm IB",
            False,
            error="ib_test_nodes not set; IB validation is required",
            slurm_controller=controller,
        )

    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")
    ssh_res = _ensure_ssh_ok(host, controller, user, password, "Slurm IB")
    if ssh_res:
        return ssh_res

    rc_si, out_si, err_si = _ssh_run(host, controller, user, "sinfo -h -o '%T'", timeout_sec=20)
    if rc_si != 0:
        return _result("Slurm IB", False, error=f"sinfo failed (rc={rc_si}): {err_si or out_si}", rc=rc_si, out=out_si, err=err_si)
    alloc_ok, alloc_reason = _slurm_has_allocatable_nodes(out_si)
    if not alloc_ok:
        return _result(
            "Slurm IB",
            False,
            error=f"No allocatable nodes for IB check ({alloc_reason})",
            rc=rc_si,
            out=out_si,
            err=err_si,
            slurm_controller=controller,
        )

    n = str(ib_nodes[0]).strip()
    rc, out, err = _ssh_run(host, controller, user, f"srun --immediate=10 --time=00:02:00 -w {n} -n1 ibstat", timeout_sec=130)
    if rc != 0:
        rc, out, err = _ssh_run(host, controller, user, f"srun --immediate=10 --time=00:02:00 -w {n} -n1 ibv_devinfo -l", timeout_sec=130)
    ok = rc == 0
    return _result("Slurm IB", ok, details="IB check succeeded" if ok else None, error=None if ok else f"IB check failed (rc={rc}): {err or out}", rc=rc, out=out, err=err, node=n)


def validate_login_node(host) -> Dict[str, Any]:
    """Validate login node services (sssd, munge, slurmd), srun, and optional LDAP lookup."""
    login_node = (DISCOVERY_VARS.get("login_node") or "").strip()
    if not login_node:
        return _result(
            "Login Node",
            True,
            details="Login node not configured/detected; skipping Login Node validation",
            skipped=True,
        )

    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")

    ssh_ok, ssh_msg = _ssh_check(host, login_node, user, password)
    if not ssh_ok:
        return _result("Login Node", False, error=f"Unable to SSH to login node {login_node}: {ssh_msg}")
    if ssh_msg != "ssh_ok":
        return _result(
            "Login Node",
            True,
            details=f"SSH authentication required for {login_node}; skipping Login Node validation",
            skipped=True,
        )

    sub: List[Dict[str, Any]] = []

    def _add(name: str, ok: bool, rc: Optional[int] = None, out: str = "", err: str = "", skipped: bool = False, status: str = ""):
        sub.append({"check": name, "success": ok, "skipped": skipped, "rc": rc, "out": out, "err": err, "status": status})

    # systemctl is-active checks
    for svc in ["sssd", "munge", "slurmd"]:
        rc, out, err = _ssh_run(host, login_node, user, f"systemctl is-active {svc}", timeout_sec=15)
        active = (out or "").strip() == "active"
        status_out = ""
        if rc != 0 or not active:
            _, status_out, _ = _ssh_run(host, login_node, user, f"systemctl status {svc} --no-pager -l", timeout_sec=20)
        _add(f"systemctl_{svc}", active, rc=rc, out=out, err=err, status=status_out)

    # If cluster has no allocatable nodes, srun from login node will fail; report clearly.
    rc_si, out_si, _ = _ssh_run(host, login_node, user, "sinfo -h -o '%T'", timeout_sec=20)
    alloc_ok, alloc_reason = (False, "sinfo_failed")
    if rc_si == 0:
        alloc_ok, alloc_reason = _slurm_has_allocatable_nodes(out_si)

    if not alloc_ok:
        _add("srun", True, skipped=True, err=f"Skipped srun: {alloc_reason}")
    else:
        rc2, out2, err2 = _ssh_run(host, login_node, user, "srun --immediate=10 --time=00:01:00 -N1 -n1 /bin/hostname", timeout_sec=70)
        _add("srun", rc2 == 0, rc=rc2, out=out2, err=err2)

    # LDAP test user lookup (optional)
    ldap_user = (DISCOVERY_VARS.get("ldap_test_user") or "").strip()
    if ldap_user:
        ok3, meta3 = _ldap_lookup(host, login_node, user, ldap_user, timeout_sec=20)
        _add("ldap", ok3, rc=meta3.get("rc"), out=meta3.get("out", ""), err=meta3.get("err", ""))
    else:
        _add("ldap", True, skipped=True)

    mandatory = [x for x in sub if x["check"] in {"systemctl_sssd", "systemctl_munge", "systemctl_slurmd", "srun"}]
    success = all(x["success"] for x in mandatory)
    return _result(
        "Login Node",
        success,
        details=DISCOVERY_MSGS["login_node_ok"] if success else DISCOVERY_MSGS["login_node_fail"],
        sub_results=sub,
        login_node=login_node,
    )


def validate_login_sssd(host) -> Dict[str, Any]:
    node, skip = _login_node_or_skip()
    if skip:
        skip["name"] = "Login Node sssd"
        return skip
    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")
    ssh_res = _ensure_ssh_ok(host, node, user, password, "Login Node sssd")
    if ssh_res:
        return ssh_res
    return _systemctl_active_check(host, node, user, "sssd", "Login Node sssd")


def validate_login_munge(host) -> Dict[str, Any]:
    node, skip = _login_node_or_skip()
    if skip:
        skip["name"] = "Login Node munge"
        return skip
    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")
    ssh_res = _ensure_ssh_ok(host, node, user, password, "Login Node munge")
    if ssh_res:
        return ssh_res
    return _systemctl_active_check(host, node, user, "munge", "Login Node munge")


def validate_login_slurmd(host) -> Dict[str, Any]:
    node, skip = _login_node_or_skip()
    if skip:
        skip["name"] = "Login Node slurmd"
        return skip
    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")
    ssh_res = _ensure_ssh_ok(host, node, user, password, "Login Node slurmd")
    if ssh_res:
        return ssh_res
    return _systemctl_active_check(host, node, user, "slurmd", "Login Node slurmd")


def validate_login_srun(host) -> Dict[str, Any]:
    node, skip = _login_node_or_skip()
    if skip:
        skip["name"] = "Login Node srun"
        return skip
    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")
    ssh_res = _ensure_ssh_ok(host, node, user, password, "Login Node srun")
    if ssh_res:
        return ssh_res

    rc_si, out_si, err_si = _ssh_run(host, node, user, "sinfo -h -o '%T'", timeout_sec=20)
    if rc_si != 0:
        return _result("Login Node srun", False, error=f"sinfo failed (rc={rc_si}): {err_si or out_si}", rc=rc_si, out=out_si, err=err_si)
    alloc_ok, alloc_reason = _slurm_has_allocatable_nodes(out_si)
    if not alloc_ok:
        return _result("Login Node srun", True, details=f"Skipped srun: {alloc_reason}", skipped=True)

    rc, out, err = _ssh_run(host, node, user, "srun --immediate=10 --time=00:01:00 -N1 -n1 /bin/hostname", timeout_sec=70)
    ok = rc == 0
    return _result("Login Node srun", ok, details="srun succeeded" if ok else None, error=None if ok else f"srun failed (rc={rc}): {err or out}", rc=rc, out=out, err=err)


def validate_login_ldap(host) -> Dict[str, Any]:
    node, skip = _login_node_or_skip()
    if skip:
        skip["name"] = "Login Node LDAP"
        return skip
    ldap_user = (DISCOVERY_VARS.get("ldap_test_user") or "").strip()
    if not ldap_user:
        return _result(
            "Login Node LDAP",
            False,
            error="ldap_test_user not set; LDAP validation is required",
            login_node=node,
        )

    proxy = _slapd_meta_proxy_status(host)
    if not proxy.get("ok"):
        return _result(
            "Login Node LDAP",
            False,
            error=(
                "slapd.conf is not configured for external LDAP proxy (meta backend). "
                "Expected moduleload back_ldap.la + back_meta.la, database meta, and uri in /opt/omnia/auth/slapd.conf"
            ),
            detected_uri=proxy.get("detected_uri", ""),
            slapd_conf=proxy.get("slapd_conf", ""),
            login_node=node,
        )
    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")
    ssh_res = _ensure_ssh_ok(host, node, user, password, "Login Node LDAP")
    if ssh_res:
        return ssh_res
    ok, meta = _ldap_lookup(host, node, user, ldap_user, timeout_sec=20)
    return _result(
        "Login Node LDAP",
        ok,
        details="LDAP lookup succeeded" if ok else None,
        error=None if ok else f"LDAP lookup failed: {meta.get('err') or meta.get('out')}",
        rc=meta.get("rc"),
        out=meta.get("out", ""),
        err=meta.get("err", ""),
        method=meta.get("method"),
        login_node=node,
    )


def validate_login_compiler_node(host) -> Dict[str, Any]:
    """Validate login compiler node services, srun, optional LDAP lookup, and OpenMPI/UCX installation."""
    node = (DISCOVERY_VARS.get("login_compiler_node") or "").strip()
    if not node:
        return _result(
            "Login Compiler Node",
            True,
            details="Login compiler node not configured/detected; skipping Login Compiler Node validation",
            skipped=True,
        )

    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")

    ssh_ok, ssh_msg = _ssh_check(host, node, user, password)
    if not ssh_ok:
        return _result("Login Compiler Node", False, error=f"Unable to SSH to login compiler node {node}: {ssh_msg}")
    if ssh_msg != "ssh_ok":
        return _result(
            "Login Compiler Node",
            True,
            details=f"SSH authentication required for {node}; skipping Login Compiler Node validation",
            skipped=True,
        )

    sub: List[Dict[str, Any]] = []

    def _add(name: str, ok: bool, rc: Optional[int] = None, out: str = "", err: str = "", skipped: bool = False, status: str = ""):
        sub.append({"check": name, "success": ok, "skipped": skipped, "rc": rc, "out": out, "err": err, "status": status})

    # systemctl is-active checks
    for svc in ["sssd", "munge", "slurmd"]:
        rc, out, err = _ssh_run(host, node, user, f"systemctl is-active {svc}", timeout_sec=15)
        active = (out or "").strip() == "active"
        status_out = ""
        if rc != 0 or not active:
            _, status_out, _ = _ssh_run(host, node, user, f"systemctl status {svc} --no-pager -l", timeout_sec=20)
        _add(f"systemctl_{svc}", active, rc=rc, out=out, err=err, status=status_out)

    # OpenMPI + UCX checks (package/command presence)
    rc_mpi, out_mpi, err_mpi = _ssh_run(
        host,
        node,
        user,
        "bash -lc 'if command -v mpirun >/dev/null 2>&1; then mpirun --version; "
        "elif command -v mpiexec >/dev/null 2>&1; then mpiexec --version; "
        "else echo \"mpirun/mpiexec not found in PATH\" >&2; exit 127; fi'",
        timeout_sec=20,
    )
    _add("openmpi", rc_mpi == 0, rc=rc_mpi, out=out_mpi, err=err_mpi)

    rc_ucx, out_ucx, err_ucx = _ssh_run(
        host,
        node,
        user,
        "bash -lc 'command -v ucx_info >/dev/null 2>&1 && ucx_info -v || { echo \"ucx_info not found in PATH\" >&2; exit 127; }'",
        timeout_sec=20,
    )
    _add("ucx", rc_ucx == 0, rc=rc_ucx, out=out_ucx, err=err_ucx)

    # srun (skip if no allocatable nodes)
    rc_si, out_si, _ = _ssh_run(host, node, user, "sinfo -h -o '%T'", timeout_sec=20)
    alloc_ok, alloc_reason = (False, "sinfo_failed")
    if rc_si == 0:
        alloc_ok, alloc_reason = _slurm_has_allocatable_nodes(out_si)

    if not alloc_ok:
        _add("srun", True, skipped=True, err=f"Skipped srun: {alloc_reason}")
    else:
        rc2, out2, err2 = _ssh_run(host, node, user, "srun --immediate=10 --time=00:01:00 -N1 -n1 /bin/hostname", timeout_sec=70)
        _add("srun", rc2 == 0, rc=rc2, out=out2, err=err2)

    # LDAP test user lookup (optional)
    ldap_user = (DISCOVERY_VARS.get("ldap_test_user") or "").strip()
    if ldap_user:
        ok3, meta3 = _ldap_lookup(host, node, user, ldap_user, timeout_sec=20)
        _add("ldap", ok3, rc=meta3.get("rc"), out=meta3.get("out", ""), err=meta3.get("err", ""))
    else:
        _add("ldap", True, skipped=True)

    mandatory_checks = {"systemctl_sssd", "systemctl_munge", "systemctl_slurmd", "openmpi", "ucx", "srun"}
    mandatory = [x for x in sub if x["check"] in mandatory_checks]
    success = all(x["success"] for x in mandatory)

    return _result(
        "Login Compiler Node",
        success,
        details=DISCOVERY_MSGS["login_compiler_ok"] if success else DISCOVERY_MSGS["login_compiler_fail"],
        sub_results=sub,
        login_compiler_node=node,
    )


def validate_login_compiler_sssd(host) -> Dict[str, Any]:
    node, skip = _login_compiler_node_or_skip()
    if skip:
        skip["name"] = "Login Compiler sssd"
        return skip
    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")
    ssh_res = _ensure_ssh_ok(host, node, user, password, "Login Compiler sssd")
    if ssh_res:
        return ssh_res
    return _systemctl_active_check(host, node, user, "sssd", "Login Compiler sssd")


def validate_login_compiler_munge(host) -> Dict[str, Any]:
    node, skip = _login_compiler_node_or_skip()
    if skip:
        skip["name"] = "Login Compiler munge"
        return skip
    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")
    ssh_res = _ensure_ssh_ok(host, node, user, password, "Login Compiler munge")
    if ssh_res:
        return ssh_res
    return _systemctl_active_check(host, node, user, "munge", "Login Compiler munge")


def validate_login_compiler_slurmd(host) -> Dict[str, Any]:
    node, skip = _login_compiler_node_or_skip()
    if skip:
        skip["name"] = "Login Compiler slurmd"
        return skip
    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")
    ssh_res = _ensure_ssh_ok(host, node, user, password, "Login Compiler slurmd")
    if ssh_res:
        return ssh_res
    return _systemctl_active_check(host, node, user, "slurmd", "Login Compiler slurmd")


def validate_login_compiler_openmpi(host) -> Dict[str, Any]:
    node, skip = _login_compiler_node_or_skip()
    if skip:
        skip["name"] = "Login Compiler OpenMPI"
        return skip
    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")
    ssh_res = _ensure_ssh_ok(host, node, user, password, "Login Compiler OpenMPI")
    if ssh_res:
        return ssh_res
    rc, out, err = _ssh_run(
        host,
        node,
        user,
        "bash -lc 'if command -v mpirun >/dev/null 2>&1; then mpirun --version; "
        "elif command -v mpiexec >/dev/null 2>&1; then mpiexec --version; "
        "else echo \"mpirun/mpiexec not found in PATH\" >&2; exit 127; fi'",
        timeout_sec=20,
    )
    ok = rc == 0
    return _result(
        "Login Compiler OpenMPI",
        ok,
        details="OpenMPI present" if ok else None,
        error=None
        if ok
        else (
            f"OpenMPI not found in PATH for non-interactive SSH session (rc={rc}): {err or out}. "
            "If OpenMPI is provided via environment modules, ensure the module init/default module is loaded for login shells."
        ),
        rc=rc,
        out=out,
        err=err,
        login_compiler_node=node,
    )


def validate_login_compiler_ucx(host) -> Dict[str, Any]:
    node, skip = _login_compiler_node_or_skip()
    if skip:
        skip["name"] = "Login Compiler UCX"
        return skip
    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")
    ssh_res = _ensure_ssh_ok(host, node, user, password, "Login Compiler UCX")
    if ssh_res:
        return ssh_res
    rc, out, err = _ssh_run(
        host,
        node,
        user,
        "bash -lc 'command -v ucx_info >/dev/null 2>&1 && ucx_info -v || { echo \"ucx_info not found in PATH\" >&2; exit 127; }'",
        timeout_sec=20,
    )
    ok = rc == 0
    return _result(
        "Login Compiler UCX",
        ok,
        details="UCX present" if ok else None,
        error=None
        if ok
        else (
            f"UCX not found in PATH for non-interactive SSH session (rc={rc}): {err or out}. "
            "If UCX is provided via environment modules, ensure the module init/default module is loaded for login shells."
        ),
        rc=rc,
        out=out,
        err=err,
        login_compiler_node=node,
    )


def validate_login_compiler_srun(host) -> Dict[str, Any]:
    node, skip = _login_compiler_node_or_skip()
    if skip:
        skip["name"] = "Login Compiler srun"
        return skip
    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")
    ssh_res = _ensure_ssh_ok(host, node, user, password, "Login Compiler srun")
    if ssh_res:
        return ssh_res

    rc_si, out_si, err_si = _ssh_run(host, node, user, "sinfo -h -o '%T'", timeout_sec=20)
    if rc_si != 0:
        return _result("Login Compiler srun", False, error=f"sinfo failed (rc={rc_si}): {err_si or out_si}", rc=rc_si, out=out_si, err=err_si)
    alloc_ok, alloc_reason = _slurm_has_allocatable_nodes(out_si)
    if not alloc_ok:
        return _result("Login Compiler srun", True, details=f"Skipped srun: {alloc_reason}", skipped=True)

    rc, out, err = _ssh_run(host, node, user, "srun --immediate=10 --time=00:01:00 -N1 -n1 /bin/hostname", timeout_sec=70)
    ok = rc == 0
    return _result("Login Compiler srun", ok, details="srun succeeded" if ok else None, error=None if ok else f"srun failed (rc={rc}): {err or out}", rc=rc, out=out, err=err)


def validate_login_compiler_ldap(host) -> Dict[str, Any]:
    node, skip = _login_compiler_node_or_skip()
    if skip:
        skip["name"] = "Login Compiler LDAP"
        return skip
    ldap_user = (DISCOVERY_VARS.get("ldap_test_user") or "").strip()
    if not ldap_user:
        return _result(
            "Login Compiler LDAP",
            False,
            error="ldap_test_user not set; LDAP validation is required",
            login_compiler_node=node,
        )

    proxy = _slapd_meta_proxy_status(host)
    if not proxy.get("ok"):
        return _result(
            "Login Compiler LDAP",
            False,
            error=(
                "slapd.conf is not configured for external LDAP proxy (meta backend). "
                "Expected moduleload back_ldap.la + back_meta.la, database meta, and uri in /opt/omnia/auth/slapd.conf"
            ),
            detected_uri=proxy.get("detected_uri", ""),
            slapd_conf=proxy.get("slapd_conf", ""),
            login_compiler_node=node,
        )
    user = DISCOVERY_VARS.get("node_ssh_user", "root")
    password = DISCOVERY_VARS.get("node_ssh_password", "")
    ssh_res = _ensure_ssh_ok(host, node, user, password, "Login Compiler LDAP")
    if ssh_res:
        return ssh_res
    ok, meta = _ldap_lookup(host, node, user, ldap_user, timeout_sec=20)
    return _result(
        "Login Compiler LDAP",
        ok,
        details="LDAP lookup succeeded" if ok else None,
        error=None if ok else f"LDAP lookup failed: {meta.get('err') or meta.get('out')}",
        rc=meta.get("rc"),
        out=meta.get("out", ""),
        err=meta.get("err", ""),
        method=meta.get("method"),
        login_compiler_node=node,
    )


def validate_external_ldap_proxy(host) -> Dict[str, Any]:
    """Validate external LDAP proxy configured in omnia_auth by performing ldapsearch.

    Requires:
    - discovery_validation.ldap_test_user
    - discovery_validation.external_ldap_ip
    """
    ldap_user = (DISCOVERY_VARS.get("ldap_test_user") or "").strip()
    external = (DISCOVERY_VARS.get("external_ldap_ip") or "").strip()
    if not ldap_user:
        return _result(
            "External LDAP Proxy",
            False,
            error="ldap_test_user not set; External LDAP Proxy validation is required",
        )

    auth_container = "omnia_auth"
    proxy = _slapd_meta_proxy_status(host)
    slapd_text = proxy.get("slapd_conf", "") or ""

    if proxy.get("container_error"):
        return _result(
            "External LDAP Proxy",
            False,
            error=str(proxy.get("container_error")),
        )

    # Strict validation: slapd.conf must be configured as external proxy using meta backend.
    has_database_meta = bool(proxy.get("has_database_meta"))
    has_back_meta = bool(proxy.get("has_back_meta"))
    has_back_ldap = bool(proxy.get("has_back_ldap"))

    if not (has_database_meta and has_back_meta and has_back_ldap):
        return _result(
            "External LDAP Proxy",
            False,
            error=(
                "slapd.conf is not configured for external LDAP proxy (meta backend). "
                "Expected moduleload back_ldap.la + back_meta.la and database meta in /opt/omnia/auth/slapd.conf"
            ),
            slapd_conf=slapd_text,
        )

    detected_uri = (proxy.get("detected_uri") or "").strip()

    if not external and detected_uri:
        # Extract host:port from ldap://host:port/... if present.
        v = detected_uri
        if "ldap://" in v:
            v = v.split("ldap://", 1)[1]
        v = v.split("/", 1)[0]
        external = v

    if not external:
        return _result(
            "External LDAP Proxy",
            False,
            error="external_ldap_ip not set and no uri found in /opt/omnia/auth/slapd.conf",
            slapd_conf=slapd_text,
        )

    ldap_host, ldap_port = _parse_hostport(external, 1389)
    target = f"ldap://{ldap_host}:{ldap_port}"
    base_dn = "dc=omnia,dc=test"

    # Run ldapsearch inside omnia_auth; use timeout to avoid hangs.
    inner = f"timeout 20s ldapsearch -LLL -x -H {target} -b {json.dumps(base_dn)} (uid={json.dumps(ldap_user)}) uid"
    rc, out, err = _run(host, f"podman exec {auth_container} bash -lc {json.dumps(inner)}")
    ok = rc == 0 and ("uid:" in (out or ""))

    return _result(
        "External LDAP Proxy",
        ok,
        details=DISCOVERY_MSGS["external_ldap_ok"] if ok else DISCOVERY_MSGS["external_ldap_fail"],
        error=None
        if ok
        else (
            f"ldapsearch failed (rc={rc}): {err or out}"
            + (
                f" | Hint: external_ldap_ip may not match slapd.conf uri ({detected_uri}); set discovery_validation.external_ldap_ip accordingly"
                if detected_uri
                else " | Hint: set discovery_validation.external_ldap_ip to match the LDAP uri in /opt/omnia/auth/slapd.conf"
            )
        ),
        rc=rc,
        out=out,
        err=err,
        target=target,
        ldap_user=ldap_user,
        detected_uri=detected_uri,
    )


def run_all_discovery_validations(host, save_report: bool = True, report_dir: Optional[str] = None) -> Dict[str, Any]:
    """Run all discovery validation scenarios."""
    _log(DISCOVERY_MSGS["validation_start"], "INFO")

    results: List[Dict[str, Any]] = []
    passed = 0
    failed = 0

    validators = [
        validate_openchami_container,
        validate_s3_provisioning_images,
        validate_discovery_execution,
        validate_node_boot,
        validate_packages_by_group,
        validate_bmc_group_csv,
        validate_slurm_sinfo,
        validate_slurm_srun,
        validate_slurm_ldap,
        validate_slurm_gpu,
        validate_slurm_ib,
        validate_login_sssd,
        validate_login_munge,
        validate_login_slurmd,
        validate_login_srun,
        validate_login_ldap,
        validate_login_compiler_sssd,
        validate_login_compiler_munge,
        validate_login_compiler_slurmd,
        validate_login_compiler_openmpi,
        validate_login_compiler_ucx,
        validate_login_compiler_srun,
        validate_login_compiler_ldap,
        validate_external_ldap_proxy,
    ]

    for fn in validators:
        res = fn(host)
        results.append(res)
        if res["success"]:
            passed += 1
        else:
            failed += 1

    summary = {
        "success": failed == 0,
        "passed": passed,
        "failed": failed,
        "total": passed + failed,
        "results": results,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    if save_report:
        report_dir = report_dir or os.path.join(DISCOVERY_VARS["omnia_shared_path"], "log")
        try:
            os.makedirs(report_dir, exist_ok=True)
        except OSError:
            report_dir = "/tmp"
        path = os.path.join(report_dir, "discovery_validation_report.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
            summary["report_path"] = path
        except OSError as e:
            summary["report_error"] = str(e)

    _log(
        DISCOVERY_MSGS["validation_pass"]
        if summary["success"]
        else DISCOVERY_MSGS["validation_fail"].format(failed_count=failed),
        "OK" if summary["success"] else "ERROR",
    )

    return summary


def run_discovery(host, save_report: bool = True, report_dir: Optional[str] = None) -> Dict[str, Any]:
    """Alias for run_all_discovery_validations."""
    return run_all_discovery_validations(host, save_report=save_report, report_dir=report_dir)


__all__ = [
    "validate_openchami_container",
    "validate_s3_provisioning_images",
    "validate_discovery_execution",
    "validate_node_boot",
    "validate_packages_by_group",
    "validate_bmc_group_csv",
    "validate_slurm_cluster",
    "validate_login_node",
    "validate_login_compiler_node",
    "validate_slurm_sinfo",
    "validate_slurm_srun",
    "validate_slurm_ldap",
    "validate_slurm_gpu",
    "validate_slurm_ib",
    "validate_login_sssd",
    "validate_login_munge",
    "validate_login_slurmd",
    "validate_login_srun",
    "validate_login_ldap",
    "validate_login_compiler_sssd",
    "validate_login_compiler_munge",
    "validate_login_compiler_slurmd",
    "validate_login_compiler_openmpi",
    "validate_login_compiler_ucx",
    "validate_login_compiler_srun",
    "validate_login_compiler_ldap",
    "validate_external_ldap_proxy",
    "run_all_discovery_validations",
    "run_discovery",
]
