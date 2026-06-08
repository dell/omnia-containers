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
InfiniBand (IB) verification functions for Slurm cluster test automation.

All tests operate on nodes that have IB_NIC_NAME and IB_IP populated
in the PXE mapping file.  If no IB-configured nodes are found the caller
should skip the test.

Public API
----------
get_ib_nodes(host)                  -> List[Dict]
get_ib_subnet_info(host)            -> Dict
verify_ib_hardware_and_link(host)   -> Dict   (TC46)
verify_doca_ofed_installed(host)    -> Dict   (TC47)
verify_ib_ip_assigned(host)         -> Dict   (TC48)
verify_ib_mtu(host)                 -> Dict   (TC49)
verify_ib_subnet_mask(host)         -> Dict   (TC50)
verify_ib_ip_in_subnet(host)        -> Dict   (TC51)
verify_ib_ping(host)                -> Dict   (TC52)
verify_ib_bandwidth(host)           -> Dict   (TC53)
verify_ib_latency(host)             -> Dict   (TC54)
"""

import base64
import ipaddress
import os
import re
import subprocess
import time
from typing import Any, Dict, List

from automation_library.core import (
    SSH_OPTS,
    OMNIA_CORE_CONTAINER,
    run_in_container,
)
from automation_library.core.functions.load_inputs_func import load_input_file
from automation_library.slurm.functions.slurm_func import (
    _safe_run_on_remote_node,
    get_slurm_control_nodes,
    get_slurm_nodes,
    get_login_nodes,
    get_login_compiler_nodes,
)
from automation_library.slurm.vars.slurm_vars import (
    UCX_MPI_PATH,
    UCX_MPI_LIB_PATH,
    UCX_JOB_TIMEOUT,
    UCX_JOB_POLL_INTERVAL,
    UCX_IB_BW_THRESHOLD_GBS,
    UCX_IB_LARGE_MSG_BYTES,
)
from automation_library.slurm.messages.slurm_msgs import (
    UCX_IB_PASSED,
    UCX_IB_FAILED,
    UCX_IB_NO_NODES,
    UCX_IB_COMPILE_FAILED,
    UCX_IB_RANKS_MISSING,
    UCX_IB_TRANSPORT_TCP,
    UCX_IB_COUNTER_NO_INCREASE,
    UCX_IB_BW_LOW,
    UCX_IB_JOB_FAILED,
    UCX_IB_OUTPUT_UNREADABLE,
    UCX_INSTALLED_PASSED,
    UCX_INSTALLED_FAILED,
    UCX_NO_LOGIN_COMPILER,
    UCX_NO_SUBMIT_NODE,
    UCX_IB_IP_NOT_ASSIGNED,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_UCX_SCRIPT_REMOTE_PATH = "/scratch/omnia_verify_ib_only.sh"
_IB_BW_DURATION = 10          # seconds for bandwidth test
_IB_BW_PORT = 18515           # perftest default port
_IB_SERVER_WAIT = 3           # seconds to wait before starting client
_NETWORK_SPEC_FILE = "network_spec.yml"
_IB_MTU_MIN = 2044             # minimum acceptable IPoIB MTU (datagram mode)


# ---------------------------------------------------------------------------
# Node discovery
# ---------------------------------------------------------------------------

def get_ib_nodes(host) -> List[Dict[str, str]]:
    """Return all Slurm cluster nodes that have IB_NIC_NAME and IB_IP set.

    Searches across compute, login, and login_compiler nodes.
    Returns an empty list if the PXE mapping has no IB_NIC_NAME / IB_IP columns
    or all values are blank.
    """
    all_nodes = (
        get_slurm_nodes(host)
        + get_login_nodes(host)
        + get_login_compiler_nodes(host)
    )
    ib_nodes = [
        n for n in all_nodes
        if n.get("ib_nic_name", "").strip() and n.get("ib_ip", "").strip()
    ]
    return ib_nodes


# ---------------------------------------------------------------------------
# Network spec helpers
# ---------------------------------------------------------------------------

def get_ib_subnet_info(host) -> Dict[str, str]:
    """Read ib_network subnet and netmask_bits from network_spec.yml.

    Returns:
        {"subnet": "...", "netmask_bits": "...", "error": ""}
        On failure: {"subnet": "", "netmask_bits": "", "error": "<msg>"}
    """
    config = load_input_file(host, _NETWORK_SPEC_FILE)
    if not config:
        return {"subnet": "", "netmask_bits": "", "error": "Cannot read network_spec.yml"}

    networks = config.get("Networks", [])
    for entry in networks:
        if "ib_network" in entry:
            ib = entry["ib_network"]
            return {
                "subnet": str(ib.get("subnet", "")),
                "netmask_bits": str(ib.get("netmask_bits", "")),
                "error": "",
            }

    return {"subnet": "", "netmask_bits": "", "error": "ib_network not found in network_spec.yml"}


def _get_ib_device_name(host, node_ip: str) -> str:
    """Return the first IB device that has State: Active and Link layer: InfiniBand.

    Parses 'ibstat' output in Python so that RoCE (Ethernet link-layer) and
    inactive ports are automatically excluded.  Returns the CA name string
    (e.g. 'mlx5_0') or '' when no qualifying device is found.
    """
    cmd = _safe_run_on_remote_node(host, "ibstat 2>/dev/null", node_ip)
    if cmd.rc != 0 or not cmd.stdout.strip():
        return ""

    current_ca = None
    has_active = False
    has_ib_link = False

    for line in cmd.stdout.splitlines():
        stripped = line.strip()
        m = re.match(r"^CA '(\S+)'", stripped)
        if m:
            if current_ca and has_active and has_ib_link:
                return current_ca
            current_ca = m.group(1)
            has_active = False
            has_ib_link = False
        elif "State: Active" in stripped:
            has_active = True
        elif "Link layer: InfiniBand" in stripped:
            has_ib_link = True

    if current_ca and has_active and has_ib_link:
        return current_ca
    return ""


def _get_ib_iface_from_ip(host, node_ip: str, ib_ip: str) -> str:
    """Return the Linux interface name that carries the given IB IP.

    Parsed in Python to avoid shell $N expansion inside SSH double-quotes.
    ip -o addr show output: "N: ifname  FAMILY cidr brd ..."
    """
    cmd = _safe_run_on_remote_node(
        host,
        f"ip -o addr show | grep '{ib_ip}/'",
        node_ip,
    )
    if cmd.rc == 0 and cmd.stdout.strip():
        parts = cmd.stdout.strip().split()
        return parts[1] if len(parts) > 1 else ""
    return ""


def _get_ib_iface_by_type(host, node_ip: str) -> str:
    """Return the first interface with link-type infiniband.

    Parsed in Python to avoid shell $N expansion inside SSH double-quotes.
    """
    cmd = _safe_run_on_remote_node(
        host,
        "ip -d link show type infiniband 2>/dev/null",
        node_ip,
    )
    if cmd.rc == 0 and cmd.stdout.strip():
        for line in cmd.stdout.strip().splitlines():
            m = re.match(r'^\d+:\s+(\S+):', line)
            if m:
                return m.group(1)
    return ""


# ---------------------------------------------------------------------------
# TC46 – Hardware & Link Verification
# ---------------------------------------------------------------------------

def verify_ib_hardware_and_link(host) -> Dict[str, Any]:
    """TC46: Verify IB hardware and link state using ibstat, ibstatus,
    ibv_devinfo, ibv_devices on every IB-configured node.

    Returns:
        Dict with success, message, per_node (list of node result dicts), error.
    """
    ib_nodes = get_ib_nodes(host)
    if not ib_nodes:
        return {
            "success": False,
            "skipped": True,
            "message": "No IB-configured nodes found in PXE mapping",
            "per_node": [],
        }

    per_node = []
    overall_ok = True

    for node in ib_nodes:
        node_ip = node["admin_ip"]
        hostname = node.get("hostname", node_ip)
        result = {"hostname": hostname, "node_ip": node_ip, "checks": {}, "success": True}

        for cmd_str in [
            "ibv_devices",
            "ibv_devinfo 2>/dev/null | head -30",
            "ibstat 2>/dev/null | head -40",
            "ibstatus 2>/dev/null | head -40",
        ]:
            cmd = _safe_run_on_remote_node(host, cmd_str, node_ip)
            tool = cmd_str.split()[0]
            result["checks"][tool] = {
                "rc": cmd.rc,
                "output": cmd.stdout.strip()[:600],
            }
            if cmd.rc != 0 or not cmd.stdout.strip():
                result["success"] = False
                result["checks"][tool]["error"] = cmd.stderr.strip()[:200]

        # Verify port state is ACTIVE — warn only for RoCE/non-IB devices
        ibstat_output = result["checks"].get("ibstat", {}).get("output", "")
        if ibstat_output:
            if "State: Active" in ibstat_output:
                result["checks"]["ibstat_state"] = "Port Active - PASS"
            else:
                is_roce = any(kw in ibstat_output for kw in ("RoCE", "bnxt_re", "base lid:        0x0"))
                tag = "RoCE/non-IB device (warn only)" if is_roce else "Port NOT in Active state (warn only)"
                result["checks"]["ibstat_state"] = tag

        if not result["success"]:
            overall_ok = False
        per_node.append(result)

    return {
        "success": overall_ok,
        "message": "IB hardware and link verified" if overall_ok else "IB hardware/link check failed on one or more nodes",
        "per_node": per_node,
        "error": "",
    }


# ---------------------------------------------------------------------------
# TC47 – DOCA-OFED installation
# ---------------------------------------------------------------------------

def verify_doca_ofed_installed(host) -> Dict[str, Any]:
    """TC47: Verify DOCA-OFED (or MLNX_OFED) is installed on all IB nodes.

    Checks:
      - ofed_info -s  (DOCA-OFED or MLNX_OFED version string)
      - ibverbs-providers or libibverbs RPM present
      - ib_uverbs kernel module loaded
    """
    ib_nodes = get_ib_nodes(host)
    if not ib_nodes:
        return {"success": False, "skipped": True,
                "message": "No IB-configured nodes found", "per_node": []}

    per_node = []
    overall_ok = True

    for node in ib_nodes:
        node_ip = node["admin_ip"]
        hostname = node.get("hostname", node_ip)
        result = {"hostname": hostname, "node_ip": node_ip, "checks": {}, "success": True}

        # OFED version
        cmd = _safe_run_on_remote_node(host, "ofed_info -s 2>/dev/null || mlnx_ofed_info -s 2>/dev/null", node_ip)
        if cmd.rc == 0 and cmd.stdout.strip():
            result["checks"]["ofed_version"] = cmd.stdout.strip()
        else:
            result["success"] = False
            result["checks"]["ofed_version"] = f"NOT FOUND (rc={cmd.rc})"

        # RPM check
        cmd = _safe_run_on_remote_node(
            host,
            "rpm -qa 2>/dev/null | grep -iE '(mlnx-ofed|doca-ofed|libibverbs|ibverbs-providers)' | head -5",
            node_ip,
        )
        result["checks"]["rpms"] = cmd.stdout.strip() if cmd.stdout.strip() else "No OFED RPMs found"
        if not cmd.stdout.strip():
            result["success"] = False

        # Kernel module
        cmd = _safe_run_on_remote_node(host, "lsmod | grep ib_uverbs", node_ip)
        if cmd.rc == 0 and cmd.stdout.strip():
            result["checks"]["ib_uverbs_module"] = "loaded - PASS"
        else:
            result["success"] = False
            result["checks"]["ib_uverbs_module"] = "NOT loaded"

        if not result["success"]:
            overall_ok = False
        per_node.append(result)

    return {
        "success": overall_ok,
        "message": "DOCA-OFED verified on all IB nodes" if overall_ok else "DOCA-OFED check failed on one or more nodes",
        "per_node": per_node,
        "error": "",
    }


# ---------------------------------------------------------------------------
# TC48 – IB IP assignment
# ---------------------------------------------------------------------------

def verify_ib_ip_assigned(host) -> Dict[str, Any]:
    """TC48: Verify the IB IP from PXE mapping is assigned to the IB
    interface on each node.
    """
    ib_nodes = get_ib_nodes(host)
    if not ib_nodes:
        return {"success": False, "skipped": True,
                "message": "No IB-configured nodes found", "per_node": []}

    per_node = []
    overall_ok = True

    for node in ib_nodes:
        node_ip = node["admin_ip"]
        hostname = node.get("hostname", node_ip)
        ib_ip = node["ib_ip"].strip()
        result = {"hostname": hostname, "node_ip": node_ip, "ib_ip": ib_ip, "success": True}

        cmd = _safe_run_on_remote_node(
            host,
            f"ip addr show | grep '{ib_ip}' && echo found || echo missing",
            node_ip,
        )
        if "found" in cmd.stdout:
            iface = _get_ib_iface_from_ip(host, node_ip, ib_ip)
            result["interface"] = iface
            result["status"] = f"IB IP {ib_ip} assigned to {iface} - PASS"
        else:
            result["success"] = False
            overall_ok = False
            result["status"] = f"IB IP {ib_ip} NOT found on node"

        per_node.append(result)

    return {
        "success": overall_ok,
        "message": "IB IP assignment verified" if overall_ok else "IB IP not assigned on one or more nodes",
        "per_node": per_node,
        "error": "",
    }


# ---------------------------------------------------------------------------
# TC49 – MTU verification
# ---------------------------------------------------------------------------

def verify_ib_mtu(host) -> Dict[str, Any]:
    """TC49: Verify IB interface MTU is set to the IPoIB standard value
    (>= 2044 for datagram mode).  Confirms via 'ip link show <iface>'.
    Also verifies a standard IPoIB ping (size 1400 bytes) succeeds.
    """
    ib_nodes = get_ib_nodes(host)
    if not ib_nodes:
        return {"success": False, "skipped": True,
                "message": "No IB-configured nodes found", "per_node": []}

    per_node = []
    overall_ok = True

    for node in ib_nodes:
        node_ip = node["admin_ip"]
        hostname = node.get("hostname", node_ip)
        ib_ip = node["ib_ip"].strip()
        result = {"hostname": hostname, "node_ip": node_ip, "success": True}

        # Resolve interface name
        iface = _get_ib_iface_from_ip(host, node_ip, ib_ip)
        if not iface:
            iface = _get_ib_iface_by_type(host, node_ip)
        result["interface"] = iface

        if iface:
            cmd = _safe_run_on_remote_node(host, f"ip link show {iface}", node_ip)
            result["ip_link_output"] = cmd.stdout.strip()
            match = re.search(r"mtu\s+(\d+)", cmd.stdout)
            if match:
                mtu = int(match.group(1))
                result["mtu"] = mtu
                if mtu >= _IB_MTU_MIN:
                    result["mtu_status"] = f"MTU {mtu} >= {_IB_MTU_MIN} - PASS"
                else:
                    result["success"] = False
                    result["mtu_status"] = f"MTU {mtu} < {_IB_MTU_MIN} - FAIL"
            else:
                result["success"] = False
                result["mtu_status"] = "MTU not found in ip link output"
        else:
            result["success"] = False
            result["mtu_status"] = "IB interface not found on node"

        if not result["success"]:
            overall_ok = False
        per_node.append(result)

    return {
        "success": overall_ok,
        "message": "IB MTU verified on all nodes" if overall_ok else "IB MTU check failed on one or more nodes",
        "per_node": per_node,
        "error": "",
    }


# ---------------------------------------------------------------------------
# TC50 – Subnet mask from network_spec.yml
# ---------------------------------------------------------------------------

def verify_ib_subnet_mask(host) -> Dict[str, Any]:
    """TC50: Verify the IB interface on each node carries the correct subnet
    mask as defined in the ib_network section of network_spec.yml.
    """
    ib_nodes = get_ib_nodes(host)
    if not ib_nodes:
        return {"success": False, "skipped": True,
                "message": "No IB-configured nodes found", "per_node": []}

    subnet_info = get_ib_subnet_info(host)
    if subnet_info["error"]:
        return {"success": False, "skipped": True,
                "message": subnet_info["error"], "per_node": []}

    expected_prefix = subnet_info["netmask_bits"]
    per_node = []
    overall_ok = True

    for node in ib_nodes:
        node_ip = node["admin_ip"]
        hostname = node.get("hostname", node_ip)
        ib_ip = node["ib_ip"].strip()
        result = {
            "hostname": hostname,
            "node_ip": node_ip,
            "ib_ip": ib_ip,
            "expected_prefix": expected_prefix,
            "success": True,
        }

        # Get the prefix length — use ip -o addr and parse in Python
        # (avoids awk $N shell-expansion inside SSH double-quotes)
        cmd = _safe_run_on_remote_node(
            host,
            f"ip -o addr show | grep '{ib_ip}/'",
            node_ip,
        )
        configured = ""
        if cmd.rc == 0 and cmd.stdout.strip():
            parts = cmd.stdout.strip().split()
            configured = next((p for p in parts if "/" in p and ib_ip in p), "")
        result["configured_cidr"] = configured

        if configured and "/" in configured:
            _, prefix = configured.split("/", 1)
            prefix = prefix.split()[0].strip()  # take only the numeric part
            if prefix == str(expected_prefix):
                result["status"] = f"Prefix /{prefix} matches network_spec.yml /{expected_prefix} - PASS"
            else:
                result["success"] = False
                result["status"] = f"Prefix /{prefix} != expected /{expected_prefix} - FAIL"
        else:
            result["success"] = False
            result["status"] = f"Cannot determine prefix for {ib_ip}"

        if not result["success"]:
            overall_ok = False
        per_node.append(result)

    return {
        "success": overall_ok,
        "message": "IB subnet mask verified" if overall_ok else "IB subnet mask mismatch on one or more nodes",
        "per_node": per_node,
        "subnet_info": subnet_info,
        "error": "",
    }


# ---------------------------------------------------------------------------
# TC51 – IB IP in correct subnet
# ---------------------------------------------------------------------------

def verify_ib_ip_in_subnet(host) -> Dict[str, Any]:
    """TC51: Verify each node's IB_IP is within the ib_network subnet
    defined in network_spec.yml.
    """
    ib_nodes = get_ib_nodes(host)
    if not ib_nodes:
        return {"success": False, "skipped": True,
                "message": "No IB-configured nodes found", "per_node": []}

    subnet_info = get_ib_subnet_info(host)
    if subnet_info["error"]:
        return {"success": False, "skipped": True,
                "message": subnet_info["error"], "per_node": []}

    try:
        network = ipaddress.ip_network(
            f"{subnet_info['subnet']}/{subnet_info['netmask_bits']}", strict=False
        )
    except ValueError as exc:
        return {"success": False, "skipped": True,
                "message": f"Invalid ib_network in network_spec.yml: {exc}", "per_node": []}

    per_node = []
    overall_ok = True

    for node in ib_nodes:
        ib_ip = node["ib_ip"].strip()
        hostname = node.get("hostname", node["admin_ip"])
        result = {"hostname": hostname, "ib_ip": ib_ip, "network": str(network), "success": True}

        try:
            addr = ipaddress.ip_address(ib_ip)
            if addr in network:
                result["status"] = f"{ib_ip} is in {network} - PASS"
            else:
                result["success"] = False
                result["status"] = f"{ib_ip} is NOT in {network} - FAIL"
        except ValueError:
            result["success"] = False
            result["status"] = f"Invalid IB IP address: {ib_ip}"

        if not result["success"]:
            overall_ok = False
        per_node.append(result)

    return {
        "success": overall_ok,
        "message": "All IB IPs are in the correct subnet" if overall_ok else "IB IP subnet mismatch",
        "per_node": per_node,
        "error": "",
    }


# ---------------------------------------------------------------------------
# TC52 – IB ping
# ---------------------------------------------------------------------------

def verify_ib_ping(host) -> Dict[str, Any]:
    """TC52: Verify IB connectivity by pinging each node's IB IP from
    every other IB-configured node that can reach it.

    Uses 'ping -c 4 -W 2 <ib_ip>' over the IPoIB interface.
    Requires at least 2 IB nodes.
    """
    ib_nodes = get_ib_nodes(host)
    if len(ib_nodes) < 2:
        return {"success": False, "skipped": True,
                "message": "Need at least 2 IB nodes for ping test", "per_node": []}

    per_node = []
    overall_ok = True

    for i, src_node in enumerate(ib_nodes):
        src_ip = src_node["admin_ip"]
        src_hostname = src_node.get("hostname", src_ip)

        for j, dst_node in enumerate(ib_nodes):
            if i == j:
                continue
            dst_ib_ip = dst_node["ib_ip"].strip()
            dst_hostname = dst_node.get("hostname", dst_node["admin_ip"])

            cmd = _safe_run_on_remote_node(
                host,
                f"ping -c 4 -W 2 {dst_ib_ip} 2>&1",
                src_ip,
            )
            success = cmd.rc == 0 and "0% packet loss" in cmd.stdout
            result = {
                "src": src_hostname,
                "dst": dst_hostname,
                "dst_ib_ip": dst_ib_ip,
                "success": success,
                "output": cmd.stdout.strip()[:400],
            }
            if not success:
                overall_ok = False
                result["error"] = cmd.stderr.strip()[:200]
            per_node.append(result)

    return {
        "success": overall_ok,
        "message": "IB ping test passed between all node pairs" if overall_ok else "IB ping failed between some node pairs",
        "per_node": per_node,
        "error": "",
    }


# ---------------------------------------------------------------------------
# Perftest server/client helper
# ---------------------------------------------------------------------------

def _run_perftest(
    host,
    test: str,
    server_dev_arg: str,
    client_dev_arg: str,
    server_admin_ip: str,
    client_admin_ip: str,
    server_ib_ip: str,
) -> Dict[str, Any]:
    """Run one perftest (bandwidth or latency) with the server in a background thread.

    The server SSH command is launched via subprocess.Popen (not testinfra) so it
    runs concurrently without any testinfra thread-safety issues.  The client is
    then run normally through testinfra.  No explicit port is needed; each test
    binary uses its own default port.

    Returns a dict::

        {
          "cmd": CommandResult,      # client-side result
          "server_proc": str,        # always empty (no pgrep needed)
          "server_rc": int,          # server subprocess return code (-1 if not finished)
          "server_stdout": str,      # server subprocess stdout (truncated)
          "server_stderr": str,      # server subprocess stderr (truncated)
        }
    """
    # Kill any leftover server from a previous run, then start fresh
    _safe_run_on_remote_node(host, f"pkill -f {test} 2>/dev/null; true", server_admin_ip)

    # Build the exact podman+ssh command testinfra would use, but launch it via
    # subprocess.Popen so it runs in the background without blocking testinfra
    escaped = f"{test} {server_dev_arg}".replace('"', '\\"')
    srv_shell_cmd = (
        f"podman exec {OMNIA_CORE_CONTAINER} "
        f"ssh {SSH_OPTS} -o UserKnownHostsFile=/dev/null "
        f'root@{server_admin_ip} "{escaped}" 2>/dev/null'
    )
    with subprocess.Popen(
        srv_shell_cmd, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ) as srv_proc:
        # Give server time to start listening
        time.sleep(_IB_SERVER_WAIT + 2)

        # Run client via testinfra (main thread, no concurrency issues)
        cmd = _safe_run_on_remote_node(
            host,
            f"{test} {client_dev_arg} {server_ib_ip} 2>&1",
            client_admin_ip,
        )

        # Cleanup
        _safe_run_on_remote_node(host, f"pkill -f {test} 2>/dev/null", server_admin_ip)
        try:
            srv_proc.terminate()
        except OSError:
            pass
        srv_out, srv_err = b"", b""
        try:
            srv_out, srv_err = srv_proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            srv_proc.kill()
            srv_out, srv_err = srv_proc.communicate()
        srv_rc = srv_proc.returncode if srv_proc.returncode is not None else -1

    return {
        "cmd": cmd,
        "server_proc": "",
        "server_rc": srv_rc,
        "server_stdout": srv_out.decode(errors="replace").strip()[:300],
        "server_stderr": srv_err.decode(errors="replace").strip()[:300],
    }


# ---------------------------------------------------------------------------
# TC53 – IB bandwidth (read / write / send)
# ---------------------------------------------------------------------------

def verify_ib_bandwidth(host) -> Dict[str, Any]:
    """TC53: Run IB bandwidth tests (ib_read_bw, ib_write_bw, ib_send_bw)
    between the first two nodes that have an Active InfiniBand (not RoCE) device.

    Server runs on capable[0], client on capable[1].
    Each side uses its own Active InfiniBand device name.
    Server startup is verified via 'ss -tlnp' before connecting the client.
    """
    ib_nodes = get_ib_nodes(host)
    if len(ib_nodes) < 2:
        return {"success": False, "skipped": True,
                "message": "Need at least 2 IB nodes for bandwidth test", "results": {}}

    # Select only nodes that have an Active InfiniBand (not RoCE) device
    capable = []
    for n in ib_nodes:
        dev = _get_ib_device_name(host, n["admin_ip"])
        if dev:
            capable.append({**n, "ib_dev": dev})

    if len(capable) < 2:
        return {
            "success": False, "skipped": True,
            "message": "Need at least 2 nodes with Active InfiniBand device for bandwidth test",
            "results": {},
        }

    server_node = capable[0]
    client_node = capable[1]
    server_admin_ip = server_node["admin_ip"]
    client_admin_ip = client_node["admin_ip"]
    server_ib_ip = server_node["ib_ip"].strip()
    server_dev_arg = f"-d {server_node['ib_dev']}"
    client_dev_arg = f"-d {client_node['ib_dev']}"

    bw_tests = ["ib_read_bw", "ib_write_bw", "ib_send_bw"]
    results = {}
    overall_ok = True

    for test in bw_tests:
        perf = _run_perftest(
            host, test, server_dev_arg, client_dev_arg,
            server_admin_ip, client_admin_ip, server_ib_ip,
        )
        cmd = perf["cmd"]

        # Parse result line — BW_average column from perftest table
        bw_line = next(
            (l for l in cmd.stdout.splitlines() if "average" in l.lower() or "bandwidth" in l.lower()),
            "",
        )
        if not bw_line:
            for line in reversed(cmd.stdout.splitlines()):
                if line.strip() and any(c.isdigit() for c in line):
                    bw_line = line.strip()
                    break

        success = cmd.rc == 0 and bool(cmd.stdout.strip())
        results[test] = {
            "success": success,
            "rc": cmd.rc,
            "result_line": bw_line[:200],
            "output": cmd.stdout.strip()[-600:],
        }
        if not success:
            overall_ok = False
            results[test]["error"] = (cmd.stderr or "").strip()[:200]
            results[test]["server_proc"] = perf["server_proc"]
            results[test]["server_rc"] = perf["server_rc"]
            results[test]["server_out"] = perf["server_stdout"]
            results[test]["server_err"] = perf["server_stderr"]

    return {
        "success": overall_ok,
        "message": "IB bandwidth tests completed" if overall_ok else "IB bandwidth test failed",
        "server": server_node.get("hostname", server_admin_ip),
        "client": client_node.get("hostname", client_admin_ip),
        "server_dev": server_node["ib_dev"],
        "client_dev": client_node["ib_dev"],
        "results": results,
        "error": "",
    }


# ---------------------------------------------------------------------------
# TC54 – IB latency (read / write / send)
# ---------------------------------------------------------------------------

def verify_ib_latency(host) -> Dict[str, Any]:
    """TC54: Run IB latency tests (ib_read_lat, ib_write_lat, ib_send_lat)
    between the first two nodes that have an Active InfiniBand (not RoCE) device.

    Server runs on capable[0], client on capable[1].
    Each side uses its own Active InfiniBand device name.
    Server startup is verified via 'ss -tlnp' before connecting the client.
    """
    ib_nodes = get_ib_nodes(host)
    if len(ib_nodes) < 2:
        return {"success": False, "skipped": True,
                "message": "Need at least 2 IB nodes for latency test", "results": {}}

    # Select only nodes that have an Active InfiniBand (not RoCE) device
    capable = []
    for n in ib_nodes:
        dev = _get_ib_device_name(host, n["admin_ip"])
        if dev:
            capable.append({**n, "ib_dev": dev})

    if len(capable) < 2:
        return {
            "success": False, "skipped": True,
            "message": "Need at least 2 nodes with Active InfiniBand device for latency test",
            "results": {},
        }

    server_node = capable[0]
    client_node = capable[1]
    server_admin_ip = server_node["admin_ip"]
    client_admin_ip = client_node["admin_ip"]
    server_ib_ip = server_node["ib_ip"].strip()
    server_dev_arg = f"-d {server_node['ib_dev']}"
    client_dev_arg = f"-d {client_node['ib_dev']}"

    lat_tests = ["ib_read_lat", "ib_write_lat", "ib_send_lat"]
    results = {}
    overall_ok = True

    for test in lat_tests:
        perf = _run_perftest(
            host, test, server_dev_arg, client_dev_arg,
            server_admin_ip, client_admin_ip, server_ib_ip,
        )
        cmd = perf["cmd"]

        # Parse result line — t_avg column from perftest table
        lat_line = next(
            (l for l in cmd.stdout.splitlines() if "average" in l.lower() or "t_avg" in l.lower()),
            "",
        )
        if not lat_line:
            for line in reversed(cmd.stdout.splitlines()):
                if line.strip() and any(c.isdigit() for c in line):
                    lat_line = line.strip()
                    break

        success = cmd.rc == 0 and bool(cmd.stdout.strip())
        results[test] = {
            "success": success,
            "rc": cmd.rc,
            "result_line": lat_line[:200],
            "output": cmd.stdout.strip()[-600:],
        }
        if not success:
            overall_ok = False
            results[test]["error"] = (cmd.stderr or "").strip()[:200]
            results[test]["server_proc"] = perf["server_proc"]
            results[test]["server_rc"] = perf["server_rc"]
            results[test]["server_out"] = perf["server_stdout"]
            results[test]["server_err"] = perf["server_stderr"]

    return {
        "success": overall_ok,
        "message": "IB latency tests completed" if overall_ok else "IB latency test failed",
        "server": server_node.get("hostname", server_admin_ip),
        "client": client_node.get("hostname", client_admin_ip),
        "server_dev": server_node["ib_dev"],
        "client_dev": client_node["ib_dev"],
        "results": results,
        "error": "",
    }


# ---------------------------------------------------------------------------
# UCX helpers
# ---------------------------------------------------------------------------

def _ucx_transfer_script(
    host,
    node_ip: str,
    local_path: str,
    remote_path: str,
    replacements: Dict[str, str],
) -> Dict[str, Any]:
    """Read a local script, apply template replacements, and base64-transfer it."""
    with open(local_path, "r", encoding="utf-8") as fh:
        content = fh.read()
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    encoded = base64.b64encode(content.encode()).decode()
    cmd = _safe_run_on_remote_node(
        host,
        f"echo {encoded} | base64 -d > {remote_path} && chmod a+rx {remote_path}",
        node_ip,
    )
    if cmd.rc != 0:
        return {"success": False, "error": cmd.stderr.strip() or "transfer failed"}
    return {"success": True, "error": ""}


def _ucx_poll_job_state(
    host, control_ip: str, job_id: str,
    target_state: str, timeout: int, poll_interval: int,
) -> str:
    """Poll sacct/squeue until job reaches target_state or a terminal state."""
    start = time.time()
    observed = ""
    while time.time() - start < timeout:
        time.sleep(poll_interval)
        if target_state == "RUNNING":
            cmd = _safe_run_on_remote_node(
                host, f"squeue -j {job_id} -h -o '%T' 2>/dev/null", control_ip,
            )
            observed = cmd.stdout.strip() if cmd.rc == 0 else ""
        else:
            cmd = _safe_run_on_remote_node(
                host,
                f"sacct -j {job_id} --format=JobID,State -n -P 2>/dev/null",
                control_ip,
            )
            if cmd.rc == 0:
                for line in cmd.stdout.strip().split("\n"):
                    parts = line.strip().split("|")
                    if len(parts) >= 2 and parts[0] == job_id:
                        observed = parts[1].strip()
                        break
        if observed == target_state:
            return observed
        if observed in ("COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL"):
            return observed
    return observed


def _parse_ucx_job_output(output: str) -> Dict[str, Any]:
    """Parse verify_ib_only job output and extract verification results.

    Checks:
      - compile_ok   : "Compile: PASS" present
      - ranks_ok     : "[Rank 0]" and "[Rank 1]" both present
      - transport_ib : rc_mlx5 / dc_mlx5 / ud_mlx5 / mlx5_ / rc_verbs detected
      - transport_tcp_found : tcp mentioned in inter-node UCX selection (bad)
      - counter_increase : at least one node's port_xmit_data value rose
      - bw_ok        : large-message bandwidth >= UCX_IB_BW_THRESHOLD_GBS
    """
    results: Dict[str, Any] = {
        "compile_ok": False,
        "ranks_ok": False,
        "transport_ib": False,
        "transport_tcp_found": False,
        "counter_increase": False,
        "bw_ok": False,
        "bw_large_msg_gbs": 0.0,
        "counter_detail": "",
        "transport_detail": "",
    }

    results["compile_ok"] = "Compile: PASS" in output
    results["ranks_ok"] = ("[Rank 0]" in output and "[Rank 1]" in output)

    ib_patterns = [
        r"rc_mlx5", r"dc_mlx5", r"ud_mlx5",
        r"mlx5_\d", r"rc_verbs", r"ud_verbs",
        r"transport.*\bib\b", r"\bib\b.*transport",
    ]
    for pat in ib_patterns:
        if re.search(pat, output, re.IGNORECASE):
            results["transport_ib"] = True
            results["transport_detail"] = f"IB transport detected ({pat})"
            break

    tcp_patterns = [r"WIRE.*inter.*cfg.*tcp", r"inter.*cfg.*tcp", r"tcp.*inter.node.*selected"]
    for pat in tcp_patterns:
        if re.search(pat, output, re.IGNORECASE):
            results["transport_tcp_found"] = True
            break

    before_vals: Dict[str, int] = {}
    after_vals: Dict[str, int] = {}
    in_before = False
    in_after = False
    ctr_re = re.compile(r"\[([^\]]+)\].*xmit_data=(\d+)")
    for line in output.splitlines():
        if "IB COUNTERS BEFORE" in line:
            in_before, in_after = True, False
            continue
        if "IB COUNTERS AFTER" in line:
            in_before, in_after = False, True
            continue
        if "=== RUN:" in line:
            in_before = False
        m = ctr_re.search(line)
        if m:
            node_name, val = m.group(1), int(m.group(2))
            if in_before:
                before_vals.setdefault(node_name, val)
            elif in_after:
                after_vals[node_name] = val

    increases = [
        f"{n}: {before_vals[n]} -> {after_vals.get(n, before_vals[n])}"
        for n in before_vals
        if after_vals.get(n, before_vals[n]) > before_vals[n]
    ]
    results["counter_increase"] = len(increases) > 0
    results["counter_detail"] = (
        "; ".join(increases) if increases else "No counter increase detected"
    )

    bw_re = re.compile(r"msg=\s*(\d+)\s*B.*bw=\s*([\d.]+)\s*GB/s")
    large_msg_bw = 0.0
    for line in output.splitlines():
        m = bw_re.search(line)
        if m and int(m.group(1)) >= UCX_IB_LARGE_MSG_BYTES:
            bw = float(m.group(2))
            if bw > large_msg_bw:
                large_msg_bw = bw
    results["bw_large_msg_gbs"] = large_msg_bw
    results["bw_ok"] = large_msg_bw >= UCX_IB_BW_THRESHOLD_GBS

    return results


# ---------------------------------------------------------------------------
# TC56 – UCX installation check on login_compiler nodes
# ---------------------------------------------------------------------------

def verify_ucx_installed(host) -> Dict[str, Any]:
    """TC56: Verify UCX is installed and functional on login_compiler and login nodes.

    Checks login_compiler nodes first; if none are registered, falls back to
    login nodes.  Does NOT require IB hardware — this is a software presence
    check that runs on any cluster that has at least one login-type node.

    Distinguishes between two skip scenarios:
      - omnia_core container is not running (infrastructure issue)
      - No login-type nodes registered in PXE mapping (expected in minimal clusters)

    Returns:
        Dict with success, message, per_node (list of per-node results), error.
    """
    login_compiler = get_login_compiler_nodes(host)
    login = get_login_nodes(host)

    candidates = (
        [{**n, "_node_type": "login_compiler_node"} for n in login_compiler]
        + [{**n, "_node_type": "login_node"} for n in login]
    )

    if not candidates:
        probe = run_in_container(host, "echo ok")
        if probe.rc != 0:
            skip_msg = (
                f"omnia_core container is not running (probe rc={probe.rc}). "
                "Start the container and re-run the test suite."
            )
            return {
                "success": False, "skipped": True,
                "message": skip_msg, "per_node": [], "error": skip_msg,
            }
        return {
            "success": False, "skipped": True,
            "message": UCX_NO_LOGIN_COMPILER,
            "per_node": [], "error": UCX_NO_LOGIN_COMPILER,
        }

    per_node = []
    overall_ok = True

    for node in candidates:
        hostname = node.get("hostname", "unknown")
        admin_ip = node.get("admin_ip", "")
        node_type = node.get("_node_type", "unknown")
        if not admin_ip:
            per_node.append({
                "hostname": hostname, "node_type": node_type,
                "success": False, "ucx_version": "", "transports": [],
                "error": "No admin IP",
            })
            overall_ok = False
            continue

        version_cmd = _safe_run_on_remote_node(
            host, "ucx_info -v 2>&1", admin_ip,
        )
        ucx_found = version_cmd.rc == 0 and bool(version_cmd.stdout.strip())
        ucx_version = ""
        if ucx_found:
            for line in version_cmd.stdout.splitlines():
                if "version" in line.lower() or "ucx" in line.lower():
                    ucx_version = line.strip()[:120]
                    break

        transports_cmd = _safe_run_on_remote_node(
            host,
            "ucx_info -d 2>&1 | grep -E '^Transport:' | awk '{print $2}'",
            admin_ip,
        )
        transports = [
            t.strip() for t in transports_cmd.stdout.splitlines()
            if t.strip()
        ] if transports_cmd.rc == 0 else []

        node_ok = ucx_found
        per_node.append({
            "hostname": hostname,
            "node_type": node_type,
            "success": node_ok,
            "ucx_version": ucx_version,
            "transports": transports,
            "error": "" if node_ok else "ucx_info not found or returned non-zero exit",
        })
        if not node_ok:
            overall_ok = False

    failed_nodes = [n["hostname"] for n in per_node if not n["success"]]
    return {
        "success": overall_ok,
        "message": (
            UCX_INSTALLED_PASSED if overall_ok
            else UCX_INSTALLED_FAILED.format(nodes=", ".join(failed_nodes))
        ),
        "per_node": per_node,
        "error": "" if overall_ok else UCX_INSTALLED_FAILED.format(nodes=", ".join(failed_nodes)),
    }


# ---------------------------------------------------------------------------
# TC55 – UCX IB-only transport verification
# ---------------------------------------------------------------------------

def verify_ucx_ib_only(host) -> Dict[str, Any]:
    """TC55: Submit an MPI ping-pong job with UCX_TLS=ib,sm,self and verify
    that inter-node communication uses InfiniBand RDMA exclusively.

    Verification steps:
      1. Transfer & submit verify_ib_only.sh (root, from control node).
      2. Wait for COMPLETED.
      3. Read job output from /scratch/root/results/verify_ib_only_<jobid>.out.
      4. Assert: compile PASS, both MPI ranks ran, UCX selected IB transport
         (rc_mlx5/dc_mlx5), IB hardware counters (port_xmit_data) increased,
         and large-message bandwidth exceeds UCX_IB_BW_THRESHOLD_GBS.

    Skips if fewer than 2 IB-configured slurm compute nodes exist.

    Returns:
        Dict with success, message, job_id, nodes, steps, job_output_snippet,
        parsed verification details, and error.
    """
    ib_compute = [
        n for n in get_slurm_nodes(host)
        if n.get("ib_nic_name", "").strip() and n.get("ib_ip", "").strip()
    ]
    if len(ib_compute) < 2:
        return {
            "success": False,
            "skipped": True,
            "message": UCX_IB_NO_NODES,
            "steps": [],
            "error": UCX_IB_NO_NODES,
        }

    # Verify IB IP is actually assigned on each candidate node's interface.
    # A node may have ib_ip in PXE mapping but the IP may not be configured
    # on the interface (e.g. IB driver present but no IP). UCX rc_mlx5 uses
    # RDMA verbs (LID/GID-based) and bypasses IP entirely, so a job would
    # silently pass even when IB IP is missing. We must gate on real IP
    # assignment to ensure the test is valid.
    ip_unassigned = []
    ip_verified = []
    for _n in ib_compute:
        _admin_ip = _n.get("admin_ip", "")
        _ib_ip = _n.get("ib_ip", "").strip()
        _hostname = _n.get("hostname", _admin_ip)
        _chk = _safe_run_on_remote_node(
            host,
            f"ip addr show | grep '{_ib_ip}' && echo found || echo missing",
            _admin_ip,
        )
        if _chk.rc == 0 and "found" in _chk.stdout:
            ip_verified.append(_n)
        else:
            ip_unassigned.append(_hostname)

    if len(ip_verified) < 2:
        _bad = ", ".join(ip_unassigned)
        _msg = UCX_IB_IP_NOT_ASSIGNED.format(nodes=_bad)
        return {
            "success": False,
            "message": _msg,
            "steps": [],
            "error": _msg,
            "ip_unassigned": ip_unassigned,
        }

    ib_compute = ip_verified

    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": "No slurm control nodes found",
            "steps": [],
            "error": "No slurm control nodes",
        }
    control_ip = control_nodes[0].get("admin_ip", "")

    login_compiler_nodes = get_login_compiler_nodes(host)
    if not login_compiler_nodes:
        return {
            "success": False,
            "message": UCX_NO_SUBMIT_NODE,
            "steps": [],
            "error": UCX_NO_SUBMIT_NODE,
        }
    submit_node = login_compiler_nodes[0]
    submit_ip = submit_node.get("admin_ip", "")
    submit_hostname = submit_node.get("hostname", "unknown")

    node1_hostname = ib_compute[0].get("hostname", "")
    node2_hostname = ib_compute[1].get("hostname", "")
    nodes_arg = f"{node1_hostname},{node2_hostname}"

    steps: list = []

    _safe_run_on_remote_node(
        host,
        "mkdir -p /scratch/root/results && chmod 755 /scratch/root /scratch/root/results",
        submit_ip,
    )

    jobs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "slurm_jobs",
    )
    xfer = _ucx_transfer_script(
        host, submit_ip,
        os.path.join(jobs_dir, "verify_ib_only.sh"),
        _UCX_SCRIPT_REMOTE_PATH,
        {
            "{{NODES}}": nodes_arg,
            "{{MPI_PATH}}": UCX_MPI_PATH,
            "{{MPI_LIB_PATH}}": UCX_MPI_LIB_PATH,
        },
    )
    if not xfer["success"]:
        return {
            "success": False,
            "message": f"Script transfer failed: {xfer['error']}",
            "steps": steps,
            "error": xfer["error"],
        }
    steps.append({
        "step": "transfer_script", "success": True,
        "nodes": nodes_arg, "submit_node": submit_hostname,
    })

    submit_cmd = _safe_run_on_remote_node(
        host, f"sbatch {_UCX_SCRIPT_REMOTE_PATH}", submit_ip,
    )
    if submit_cmd.rc != 0 or "Submitted batch job" not in submit_cmd.stdout:
        _safe_run_on_remote_node(host, f"rm -f {_UCX_SCRIPT_REMOTE_PATH}", submit_ip)
        err = submit_cmd.stderr.strip() or submit_cmd.stdout.strip()
        return {
            "success": False,
            "message": f"Job submission failed: {err}",
            "steps": steps,
            "error": err,
        }

    match = re.search(r"Submitted batch job (\d+)", submit_cmd.stdout)
    job_id = match.group(1)
    steps.append({"step": "submit_job", "success": True, "job_id": job_id})

    state = _ucx_poll_job_state(
        host, control_ip, job_id,
        "COMPLETED", UCX_JOB_TIMEOUT, UCX_JOB_POLL_INTERVAL,
    )
    steps.append({"step": "wait_complete", "success": state == "COMPLETED", "state": state})

    if state != "COMPLETED":
        _safe_run_on_remote_node(host, f"rm -f {_UCX_SCRIPT_REMOTE_PATH}", submit_ip)
        return {
            "success": False,
            "message": UCX_IB_JOB_FAILED.format(state=state),
            "job_id": job_id,
            "nodes": nodes_arg,
            "steps": steps,
            "error": f"Job ended in state: {state}",
        }

    output_path = f"/scratch/root/results/verify_ib_only_{job_id}.out"
    cat_cmd = _safe_run_on_remote_node(
        host, f"cat {output_path} 2>/dev/null", submit_ip,
    )
    job_output = cat_cmd.stdout if (cat_cmd.rc == 0 and cat_cmd.stdout.strip()) else ""

    if not job_output:
        _safe_run_on_remote_node(host, f"rm -f {_UCX_SCRIPT_REMOTE_PATH}", submit_ip)
        return {
            "success": False,
            "message": UCX_IB_OUTPUT_UNREADABLE.format(path=output_path),
            "job_id": job_id,
            "nodes": nodes_arg,
            "steps": steps,
            "error": f"Empty or missing output file: {output_path}",
        }
    steps.append({"step": "read_output", "success": True, "output_path": output_path})

    parsed = _parse_ucx_job_output(job_output)

    failures = []
    if not parsed["compile_ok"]:
        failures.append(UCX_IB_COMPILE_FAILED)
    if not parsed["ranks_ok"]:
        failures.append(UCX_IB_RANKS_MISSING)
    if parsed["transport_tcp_found"]:
        failures.append(UCX_IB_TRANSPORT_TCP)
    if not parsed["transport_ib"]:
        failures.append("UCX IB/RDMA transport not detected in job output")
    if not parsed["counter_increase"]:
        failures.append(UCX_IB_COUNTER_NO_INCREASE)
    if not parsed["bw_ok"]:
        failures.append(UCX_IB_BW_LOW.format(
            bw=parsed["bw_large_msg_gbs"],
            threshold=UCX_IB_BW_THRESHOLD_GBS,
        ))

    steps.append({
        "step": "verify_output",
        "success": len(failures) == 0,
        "compile_ok": parsed["compile_ok"],
        "ranks_ok": parsed["ranks_ok"],
        "transport_ib": parsed["transport_ib"],
        "transport_tcp_found": parsed["transport_tcp_found"],
        "transport_detail": parsed["transport_detail"],
        "counter_increase": parsed["counter_increase"],
        "counter_detail": parsed["counter_detail"],
        "bw_ok": parsed["bw_ok"],
        "bw_gbs": parsed["bw_large_msg_gbs"],
        "failures": failures,
    })

    _safe_run_on_remote_node(host, f"rm -f {_UCX_SCRIPT_REMOTE_PATH}", submit_ip)

    all_ok = len(failures) == 0
    return {
        "success": all_ok,
        "message": (
            UCX_IB_PASSED if all_ok
            else UCX_IB_FAILED.format(error="; ".join(failures))
        ),
        "job_id": job_id,
        "nodes": nodes_arg,
        "submit_node": submit_hostname,
        "steps": steps,
        "job_output_snippet": job_output[-1200:],
        "error": "" if all_ok else "; ".join(failures),
    }
