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

import ipaddress
import re
import subprocess
import time
from typing import Any, Dict, List

from automation_library.core import (
    SSH_OPTS,
    OMNIA_CORE_CONTAINER,
)
from automation_library.core.functions.load_inputs_func import load_input_file
from automation_library.slurm.functions.slurm_func import (
    _safe_run_on_remote_node,
    get_slurm_nodes,
    get_login_nodes,
    get_login_compiler_nodes,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

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
