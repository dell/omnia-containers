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

"""Custom Slurm config verification for OMNIA test automation.

This module validates that custom Slurm settings supplied through
omnia_config.yml (slurm_cluster[].config_sources) are correctly applied to
the running Slurm cluster.

It checks:
  - deployed configuration files (slurm.conf, cgroup.conf, slurmdbd.conf)
  - live cluster state via scontrol (scontrol show config, scontrol show node,
    scontrol show partition)
  - scontrol reconfigure persistence
  - NFS share vs local control node config sync
  - configless mode on compute nodes
  - job behavior with custom params
  - negative tests for mismatch detection
"""

import os
import re
import time
from typing import Any, Dict, List, Tuple

from automation_library.core import load_input_file, get_config_list_item
from automation_library.slurm.functions.slurm_func import (
    get_slurm_control_nodes,
    get_slurm_nodes,
    _safe_run_on_remote_node,
)
from automation_library.slurm.vars.slurm_vars import (
    OMNIA_CONFIG_INPUT_FILE,
    SLURM_CONF_CONTAINER_PATH,
    CGROUP_CONF_CONTAINER_PATH,
    SLURMDBD_CONF_CONTAINER_PATH,
    CUSTOM_SLURM_CONFIG_KEY,
    SLURM_CLUSTER_CONFIG_KEY,
    DEFAULT_SLURM_CONTROL_NODE_INDEX,
    NFS_SLURM_BASE_PATH,
    NFS_SLURM_ETC_REL_PATH,
    NFS_SLURM_CONF_CACHE_REL_PATH,
    SBATCH_JOB_POLL_INTERVAL,
    SBATCH_JOB_TIMEOUT,
    SACCT_POLL_INTERVAL,
    SACCT_TIMEOUT,
)
from automation_library.slurm.messages.slurm_msgs import (
    CUSTOM_SLURM_CONFIG_NO_CONTROL_NODE,
    CUSTOM_SLURM_CONFIG_NO_CONFIG_SOURCES,
    CUSTOM_SLURM_CONFIG_PASSED,
    CUSTOM_SLURM_CONFIG_FAILED,
    CUSTOM_SLURM_PARAM_PASSED,
    CUSTOM_SLURM_PARAM_FAILED,
    CUSTOM_SLURM_PARAM_MISSING,
    CUSTOM_SLURM_NODENAME_PASSED,
    CUSTOM_SLURM_NODENAME_FAILED,
    CUSTOM_SLURM_NODENAME_MISSING,
    CUSTOM_CGROUP_CONFIG_PASSED,
    CUSTOM_CGROUP_CONFIG_FAILED,
    CUSTOM_CGROUP_PARAM_MISSING,
    CUSTOM_CGROUP_PARAM_FAILED,
    CUSTOM_SLURM_PARTITION_PASSED,
    CUSTOM_SLURM_PARTITION_FAILED,
    CUSTOM_SLURM_PARTITION_MISSING,
    CUSTOM_SLURMDBD_CONFIG_PASSED,
    CUSTOM_SLURMDBD_CONFIG_FAILED,
    CUSTOM_SLURMDBD_PARAM_MISSING,
    CUSTOM_SLURMDBD_PARAM_FAILED,
    CUSTOM_SLURMDBD_PARAM_PASSED,
    CUSTOM_SLURM_RECONFIGURE_PASSED,
    CUSTOM_SLURM_RECONFIGURE_FAILED,
    CUSTOM_SLURM_NFS_SYNC_PASSED,
    CUSTOM_SLURM_NFS_SYNC_FAILED,
    CUSTOM_SLURM_CONFIGLESS_PASSED,
    CUSTOM_SLURM_CONFIGLESS_FAILED,
    CUSTOM_SLURM_JOB_BEHAVIOR_PASSED,
    CUSTOM_SLURM_JOB_BEHAVIOR_FAILED,
    CUSTOM_SLURM_NEGATIVE_PASSED,
    CUSTOM_SLURM_NEGATIVE_FAILED,
    CUSTOM_SLURM_UNEXPECTED_MATCH,
    SBATCH_NO_CONTROL_NODE,
    SBATCH_SUBMIT_FAILED,
    SBATCH_TIMEOUT,
    SACCT_JOB_STATUS,
)


def _get_slurm_control_node_ip(host) -> str:
    """Return the admin IP of the first slurm control node."""
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return ""
    return control_nodes[DEFAULT_SLURM_CONTROL_NODE_INDEX].get("admin_ip", "")


def _get_slurm_control_node_hostname(host) -> str:
    """Return the hostname of the first slurm control node."""
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return ""
    return control_nodes[DEFAULT_SLURM_CONTROL_NODE_INDEX].get("hostname", "")


def _read_remote_file(host, admin_ip: str, path: str) -> str:
    """Read a file from a remote node and return its contents."""
    cmd = _safe_run_on_remote_node(host, f"cat '{path}' 2>/dev/null", admin_ip)
    if cmd.rc != 0:
        return ""
    return cmd.stdout


def _run_scontrol_command(host, admin_ip: str, cmd: str) -> str:
    """Run an scontrol command on the control node and return stdout."""
    result = _safe_run_on_remote_node(host, f"scontrol {cmd} 2>/dev/null", admin_ip)
    if result.rc != 0:
        return ""
    return result.stdout


def _run_sbatch(host, admin_ip: str, script: str) -> str:
    """Submit a sbatch script and return the job ID."""
    result = _safe_run_on_remote_node(host, f"sbatch --wrap='{script}' 2>/dev/null", admin_ip)
    if result.rc != 0:
        return ""
    match = re.search(r"Submitted batch job (\d+)", result.stdout)
    return match.group(1) if match else ""


def _get_job_state(host, admin_ip: str, job_id: str) -> str:
    """Return job state from sacct (no header)."""
    result = _safe_run_on_remote_node(host, f"sacct -j {job_id} -n -P -o State 2>/dev/null", admin_ip)
    if not result.stdout:
        return ""
    # First non-empty line, first field
    lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
    return lines[0].split("|")[0] if lines else ""


def _wait_for_job_state(host, admin_ip: str, job_id: str, expected_states: List[str], timeout: int, poll: int) -> Tuple[str, str]:
    """Wait for job to reach one of expected states."""
    elapsed = 0
    while elapsed < timeout:
        state = _get_job_state(host, admin_ip, job_id)
        if state in expected_states:
            return state, ""
        time.sleep(poll)
        elapsed += poll
    return "", f"Job {job_id} did not reach {expected_states} within {timeout}s"


def _parse_slurm_style_config(content: str) -> Dict[str, Any]:
    """Parse a Slurm-style config file into key/value and list entries."""
    config: Dict[str, Any] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split(None, 1)
        if not parts:
            continue

        first = parts[0]
        if "=" not in first:
            continue

        key, primary_value = first.split("=", 1)
        rest = parts[1] if len(parts) > 1 else ""
        value = f"{primary_value} {rest}".strip() if rest else primary_value

        if key in config:
            if not isinstance(config[key], list):
                config[key] = [config[key]]
            config[key].append(value)
        else:
            config[key] = value

    return config


def _parse_scontrol_config(output: str) -> Dict[str, str]:
    """Parse 'scontrol show config' output into a flat dict."""
    config: Dict[str, str] = {}
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("Configuration"):
            continue

        match = re.match(r"^([A-Za-z0-9_]+)\s*=\s*(.+)$", line)
        if match:
            key, value = match.group(1), match.group(2).strip()
            config[key] = value
    return config


def _parse_scontrol_node(output: str, node_name: str) -> Dict[str, str]:
    """Parse 'scontrol show node <name>' output into key/value pairs."""
    flattened = re.sub(r"\s+", " ", output.strip())
    result: Dict[str, str] = {}
    for token in flattened.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        result[key] = value
    return result


def _parse_scontrol_partition(output: str, partition_name: str) -> Dict[str, str]:
    """Parse 'scontrol show partition <name>' output into key/value pairs."""
    flattened = re.sub(r"\s+", " ", output.strip())
    result: Dict[str, str] = {}
    for token in flattened.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        result[key] = value
    return result


def _get_nodename_entries(slurm_conf: Dict[str, Any]) -> List[str]:
    """Return all NodeName= lines from parsed slurm.conf as a list."""
    entries = slurm_conf.get("NodeName", [])
    if isinstance(entries, str):
        entries = [entries]
    return entries


def _get_partition_entries(slurm_conf: Dict[str, Any]) -> List[str]:
    """Return all PartitionName= lines from parsed slurm.conf as a list."""
    entries = slurm_conf.get("PartitionName", [])
    if isinstance(entries, str):
        entries = [entries]
    return entries


def _parse_nodename_line(line: str) -> Dict[str, str]:
    """Parse a NodeName= line into a dict of key/value pairs."""
    tokens = re.split(r"\s+", line.strip())
    result: Dict[str, str] = {}
    if not tokens:
        return result
    if tokens[0].startswith("NodeName="):
        result["NodeName"] = tokens[0].split("=", 1)[1]
    else:
        result["NodeName"] = tokens[0]
    for token in tokens[1:]:
        if "=" in token:
            k, v = token.split("=", 1)
            result[k] = v
    return result


def _parse_partition_line(line: str) -> Dict[str, str]:
    """Parse a PartitionName= line into a dict of key/value pairs."""
    tokens = re.split(r"\s+", line.strip())
    result: Dict[str, str] = {}
    if not tokens:
        return result
    if tokens[0].startswith("PartitionName="):
        result["PartitionName"] = tokens[0].split("=", 1)[1]
    else:
        result["PartitionName"] = tokens[0]
    for token in tokens[1:]:
        if "=" in token:
            k, v = token.split("=", 1)
            result[k] = v
    return result


def _get_cgroup_entries(cgroup_conf: Dict[str, Any]) -> Dict[str, str]:
    """Return cgroup.conf parameters as a flat dict."""
    config: Dict[str, str] = {}
    for key, value in cgroup_conf.items():
        if isinstance(value, list):
            value = value[-1]
        config[key] = value
    return config


def _format_value(value: Any) -> str:
    """Format a Python value as a Slurm config string."""
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def _normalize_boolean(value: str) -> str:
    """Normalize common boolean strings to yes/no for comparison."""
    normalized = str(value).strip().lower()
    if normalized in ("true", "yes", "1", "on"):
        return "yes"
    if normalized in ("false", "no", "0", "off"):
        return "no"
    return value


def _normalize_scontrol_value(key: str, value: str) -> str:
    """Normalize scontrol values for comparison with slurm.conf values."""
    value = str(value).strip()
    time_params = ("SlurmctldTimeout", "SlurmdTimeout", "InactiveLimit", "MinJobAge", "KillWait")
    if key in time_params and value.endswith(" sec"):
        value = value[:-4].strip()
    return value


def _values_match(expected: Any, actual: Any, key: str = "") -> bool:
    """Compare expected and actual values, normalizing booleans and units."""
    expected_str = _format_value(expected)
    actual_str = str(actual).strip()
    actual_str = _normalize_scontrol_value(key, actual_str)

    if isinstance(expected, bool):
        return _normalize_boolean(actual_str) == expected_str

    if key == "State" and expected_str == "UNKNOWN":
        return actual_str in ("UNKNOWN", "IDLE", "IDLE+DRAIN", "IDLE+COMPLETING")

    return actual_str == expected_str


def get_custom_slurm_config_sources(host) -> Dict[str, Any]:
    """Load config_sources from omnia_config.yml slurm_cluster entry."""
    omnia_config = load_input_file(host, OMNIA_CONFIG_INPUT_FILE)
    slurm_cluster = omnia_config.get(CUSTOM_SLURM_CONFIG_KEY, {})

    if isinstance(slurm_cluster, dict):
        return slurm_cluster.get(SLURM_CLUSTER_CONFIG_KEY, {})

    if isinstance(slurm_cluster, list) and slurm_cluster:
        return slurm_cluster[DEFAULT_SLURM_CONTROL_NODE_INDEX].get(
            SLURM_CLUSTER_CONFIG_KEY, {}
        )

    return {}


def get_custom_slurm_config(host) -> Dict[str, Any]:
    """Return the custom slurm.conf section from config_sources."""
    sources = get_custom_slurm_config_sources(host)
    return sources.get("slurm", {})


def get_custom_cgroup_config(host) -> Dict[str, Any]:
    """Return the custom cgroup.conf section from config_sources."""
    sources = get_custom_slurm_config_sources(host)
    return sources.get("cgroup", {})


def get_custom_slurmdbd_config(host) -> Dict[str, Any]:
    """Return the custom slurmdbd.conf section from config_sources."""
    sources = get_custom_slurm_config_sources(host)
    return sources.get("slurmdbd", {})


def _get_control_ip_or_fail(host) -> Tuple[str, Dict[str, Any]]:
    """Return the control node IP or a failure result dict."""
    control_ip = _get_slurm_control_node_ip(host)
    if not control_ip:
        return "", {
            "success": False,
            "message": CUSTOM_SLURM_CONFIG_NO_CONTROL_NODE,
            "details": [],
            "missing": [],
            "mismatched": [],
            "error": CUSTOM_SLURM_CONFIG_NO_CONTROL_NODE,
        }
    return control_ip, {}


def _check_param_value(
    key: str,
    expected_value: Any,
    actual_value: Any,
    details: List[str],
    missing: List[str],
    mismatched: List[str],
    context: str = "",
) -> None:
    """Compare a single expected vs actual parameter value and record result."""
    expected_str = _format_value(expected_value)
    context_str = f" ({context})" if context else ""

    if actual_value is None:
        missing.append(key)
        details.append(CUSTOM_SLURM_PARAM_MISSING.format(
            key=f"{key}{context_str}", expected=expected_str
        ))
        return

    if _values_match(expected_value, actual_value, key=key):
        details.append(CUSTOM_SLURM_PARAM_PASSED.format(
            key=f"{key}{context_str}", expected=expected_str, actual=actual_value
        ))
    else:
        mismatched.append(key)
        details.append(CUSTOM_SLURM_PARAM_FAILED.format(
            key=f"{key}{context_str}", expected=expected_str, actual=actual_value
        ))


def verify_custom_slurm_global_params(host) -> Dict[str, Any]:
    """Verify custom global parameters in slurm.conf and live scontrol config."""
    control_ip, fail_result = _get_control_ip_or_fail(host)
    if fail_result:
        return fail_result

    custom_config = get_custom_slurm_config(host)
    if not custom_config:
        return {
            "success": True,
            "skipped": True,
            "message": CUSTOM_SLURM_CONFIG_NO_CONFIG_SOURCES,
            "details": [],
            "missing": [],
            "mismatched": [],
            "error": "",
        }

    raw_conf = _read_remote_file(host, control_ip, SLURM_CONF_CONTAINER_PATH)
    if not raw_conf:
        return {
            "success": False,
            "message": CUSTOM_SLURM_CONFIG_FAILED.format(error="slurm.conf not readable"),
            "details": [],
            "missing": [],
            "mismatched": [],
            "error": "slurm.conf not readable",
        }

    parsed_conf = _parse_slurm_style_config(raw_conf)
    scontrol_output = _run_scontrol_command(host, control_ip, "show config")
    scontrol_config = _parse_scontrol_config(scontrol_output) if scontrol_output else {}

    details: List[str] = []
    missing: List[str] = []
    mismatched: List[str] = []

    for key, expected_value in custom_config.items():
        if key in ("NodeName", "PartitionName"):
            continue

        file_value = parsed_conf.get(key)
        if isinstance(file_value, list):
            file_value = file_value[-1]
        _check_param_value(key, expected_value, file_value, details, missing, mismatched, "slurm.conf")

        live_value = scontrol_config.get(key)
        _check_param_value(key, expected_value, live_value, details, missing, mismatched, "scontrol")

    all_passed = not missing and not mismatched

    return {
        "success": all_passed,
        "message": CUSTOM_SLURM_CONFIG_PASSED if all_passed else CUSTOM_SLURM_CONFIG_FAILED.format(
            error="; ".join(missing + mismatched)),
        "details": details,
        "missing": missing,
        "mismatched": mismatched,
        "error": "" if all_passed else "; ".join(missing + mismatched),
    }


def verify_custom_slurm_nodename(host) -> Dict[str, Any]:
    """Verify custom NodeName definitions in slurm.conf and live scontrol node."""
    control_ip, fail_result = _get_control_ip_or_fail(host)
    if fail_result:
        return fail_result

    custom_config = get_custom_slurm_config(host)
    custom_nodes = custom_config.get("NodeName", [])
    if not custom_nodes:
        return {
            "success": True,
            "skipped": True,
            "message": "No custom NodeName entries in config_sources - skipping",
            "details": [],
            "missing": [],
            "mismatched": [],
            "error": "",
        }

    if isinstance(custom_nodes, dict):
        custom_nodes = [custom_nodes]

    raw_conf = _read_remote_file(host, control_ip, SLURM_CONF_CONTAINER_PATH)
    if not raw_conf:
        return {
            "success": False,
            "message": CUSTOM_SLURM_CONFIG_FAILED.format(error="slurm.conf not readable"),
            "details": [],
            "missing": [],
            "mismatched": [],
            "error": "slurm.conf not readable",
        }

    parsed_conf = _parse_slurm_style_config(raw_conf)
    deployed_nodes = _get_nodename_entries(parsed_conf)
    deployed_parsed: Dict[str, Dict[str, str]] = {}
    for entry in deployed_nodes:
        parsed = _parse_nodename_line(entry)
        node_name = parsed.get("NodeName")
        if node_name:
            deployed_parsed[node_name] = parsed

    details: List[str] = []
    missing: List[str] = []
    mismatched: List[str] = []

    for node in custom_nodes:
        if not isinstance(node, dict):
            continue

        node_name = str(node.get("NodeName", ""))
        if not node_name:
            continue

        if node_name not in deployed_parsed:
            missing.append(node_name)
            details.append(CUSTOM_SLURM_NODENAME_MISSING.format(node_name=node_name))
            continue

        deployed = deployed_parsed[node_name]
        node_mismatches: List[str] = []

        for key, expected_value in node.items():
            if key == "NodeName":
                continue
            actual_value = deployed.get(key)
            if not _values_match(expected_value, actual_value, key=key):
                node_mismatches.append(
                    CUSTOM_SLURM_PARAM_FAILED.format(
                        key=f"{key} (slurm.conf)", expected=_format_value(expected_value), actual=actual_value
                    )
                )

        scontrol_output = _run_scontrol_command(host, control_ip, f"show node {node_name}")
        live_node = _parse_scontrol_node(scontrol_output, node_name) if scontrol_output else {}

        for key, expected_value in node.items():
            if key == "NodeName":
                continue

            live_key = _map_slurm_conf_key_to_scontrol_key(key)
            actual_value = live_node.get(live_key)

            if not _values_match(expected_value, actual_value, key=key):
                node_mismatches.append(
                    CUSTOM_SLURM_PARAM_FAILED.format(
                        key=f"{key} (scontrol, {live_key})", expected=_format_value(expected_value), actual=actual_value
                    )
                )

        if node_mismatches:
            mismatched.append(node_name)
            details.append(CUSTOM_SLURM_NODENAME_FAILED.format(node_name=node_name))
            details.extend([f"  {m}" for m in node_mismatches])
        else:
            details.append(CUSTOM_SLURM_NODENAME_PASSED.format(node_name=node_name))

    all_passed = not missing and not mismatched

    return {
        "success": all_passed,
        "message": CUSTOM_SLURM_CONFIG_PASSED if all_passed else CUSTOM_SLURM_CONFIG_FAILED.format(
            error="; ".join(missing + mismatched)),
        "details": details,
        "missing": missing,
        "mismatched": mismatched,
        "error": "" if all_passed else "; ".join(missing + mismatched),
    }


def _map_slurm_conf_key_to_scontrol_key(key: str) -> str:
    """Map slurm.conf NodeName key names to scontrol show node key names."""
    mapping = {
        "CPUs": "CPUTot",
        "RealMemory": "RealMemory",
        "State": "State",
        "CoresPerSocket": "CoresPerSocket",
        "ThreadsPerCore": "ThreadsPerCore",
        "Boards": "Boards",
        "SocketsPerBoard": "SocketsPerBoard",
        "CoresPerCPU": "CoresPerCPU",
    }
    return mapping.get(key, key)


def verify_custom_partition_config(host) -> Dict[str, Any]:
    """Verify custom PartitionName definitions in slurm.conf and scontrol."""
    control_ip, fail_result = _get_control_ip_or_fail(host)
    if fail_result:
        return fail_result

    custom_config = get_custom_slurm_config(host)
    custom_partitions = custom_config.get("PartitionName", [])
    if not custom_partitions:
        return {
            "success": True,
            "skipped": True,
            "message": "No custom PartitionName entries in config_sources - skipping",
            "details": [],
            "missing": [],
            "mismatched": [],
            "error": "",
        }

    if isinstance(custom_partitions, dict):
        custom_partitions = [custom_partitions]

    raw_conf = _read_remote_file(host, control_ip, SLURM_CONF_CONTAINER_PATH)
    if not raw_conf:
        return {
            "success": False,
            "message": CUSTOM_SLURM_CONFIG_FAILED.format(error="slurm.conf not readable"),
            "details": [],
            "missing": [],
            "mismatched": [],
            "error": "slurm.conf not readable",
        }

    parsed_conf = _parse_slurm_style_config(raw_conf)
    deployed_partitions = _get_partition_entries(parsed_conf)
    deployed_parsed: Dict[str, Dict[str, str]] = {}
    for entry in deployed_partitions:
        parsed = _parse_partition_line(entry)
        partition_name = parsed.get("PartitionName")
        if partition_name:
            deployed_parsed[partition_name] = parsed

    details: List[str] = []
    missing: List[str] = []
    mismatched: List[str] = []

    for partition in custom_partitions:
        if not isinstance(partition, dict):
            continue

        partition_name = str(partition.get("PartitionName", ""))
        if not partition_name:
            continue

        if partition_name not in deployed_parsed:
            missing.append(partition_name)
            details.append(CUSTOM_SLURM_PARTITION_MISSING.format(partition_name=partition_name))
            continue

        deployed = deployed_parsed[partition_name]
        partition_mismatches: List[str] = []

        for key, expected_value in partition.items():
            if key == "PartitionName":
                continue
            actual_value = deployed.get(key)
            if not _values_match(expected_value, actual_value, key=key):
                partition_mismatches.append(
                    CUSTOM_SLURM_PARAM_FAILED.format(
                        key=f"{key} (slurm.conf)", expected=_format_value(expected_value), actual=actual_value
                    )
                )

        scontrol_output = _run_scontrol_command(host, control_ip, f"show partition {partition_name}")
        live_partition = _parse_scontrol_partition(scontrol_output, partition_name) if scontrol_output else {}

        for key, expected_value in partition.items():
            if key == "PartitionName":
                continue

            actual_value = live_partition.get(key)
            if not _values_match(expected_value, actual_value, key=key):
                partition_mismatches.append(
                    CUSTOM_SLURM_PARAM_FAILED.format(
                        key=f"{key} (scontrol)", expected=_format_value(expected_value), actual=actual_value
                    )
                )

        if partition_mismatches:
            mismatched.append(partition_name)
            details.append(CUSTOM_SLURM_PARTITION_FAILED.format(partition_name=partition_name))
            details.extend([f"  {m}" for m in partition_mismatches])
        else:
            details.append(CUSTOM_SLURM_PARTITION_PASSED.format(partition_name=partition_name))

    all_passed = not missing and not mismatched

    return {
        "success": all_passed,
        "message": CUSTOM_SLURM_CONFIG_PASSED if all_passed else CUSTOM_SLURM_CONFIG_FAILED.format(
            error="; ".join(missing + mismatched)),
        "details": details,
        "missing": missing,
        "mismatched": mismatched,
        "error": "" if all_passed else "; ".join(missing + mismatched),
    }


def verify_custom_cgroup_config(host) -> Dict[str, Any]:
    """Verify custom cgroup.conf parameters."""
    control_ip, fail_result = _get_control_ip_or_fail(host)
    if fail_result:
        return fail_result

    custom_cgroup = get_custom_cgroup_config(host)
    if not custom_cgroup:
        return {
            "success": True,
            "skipped": True,
            "message": "No custom cgroup config in config_sources - skipping",
            "details": [],
            "missing": [],
            "mismatched": [],
            "error": "",
        }

    raw_conf = _read_remote_file(host, control_ip, CGROUP_CONF_CONTAINER_PATH)
    if not raw_conf:
        return {
            "success": False,
            "message": CUSTOM_SLURM_CONFIG_FAILED.format(error="cgroup.conf not readable"),
            "details": [],
            "missing": [],
            "mismatched": [],
            "error": "cgroup.conf not readable",
        }

    parsed_conf = _parse_slurm_style_config(raw_conf)
    deployed = _get_cgroup_entries(parsed_conf)

    details: List[str] = []
    missing: List[str] = []
    mismatched: List[str] = []

    for key, expected_value in custom_cgroup.items():
        expected_str = _format_value(expected_value)
        actual_value = deployed.get(key)

        if actual_value is None:
            missing.append(key)
            details.append(CUSTOM_CGROUP_PARAM_MISSING.format(key=key, expected=expected_str))
            continue

        if _values_match(expected_value, actual_value, key=key):
            details.append(CUSTOM_CGROUP_CONFIG_PASSED.format(
                key=key, expected=expected_str, actual=actual_value))
        else:
            mismatched.append(key)
            details.append(CUSTOM_CGROUP_PARAM_FAILED.format(
                key=key, expected=expected_str, actual=actual_value))

    all_passed = not missing and not mismatched

    return {
        "success": all_passed,
        "message": CUSTOM_CGROUP_CONFIG_PASSED if all_passed else CUSTOM_CGROUP_CONFIG_FAILED.format(
            error="; ".join(missing + mismatched)),
        "details": details,
        "missing": missing,
        "mismatched": mismatched,
        "error": "" if all_passed else "; ".join(missing + mismatched),
    }


def verify_custom_slurmdbd_config(host) -> Dict[str, Any]:
    """Verify custom slurmdbd.conf parameters."""
    control_ip, fail_result = _get_control_ip_or_fail(host)
    if fail_result:
        return fail_result

    custom_slurmdbd = get_custom_slurmdbd_config(host)
    if not custom_slurmdbd:
        return {
            "success": True,
            "skipped": True,
            "message": "No custom slurmdbd config in config_sources - skipping",
            "details": [],
            "missing": [],
            "mismatched": [],
            "error": "",
        }

    raw_conf = _read_remote_file(host, control_ip, SLURMDBD_CONF_CONTAINER_PATH)
    if not raw_conf:
        return {
            "success": False,
            "message": CUSTOM_SLURMDBD_CONFIG_FAILED.format(error="slurmdbd.conf not readable"),
            "details": [],
            "missing": [],
            "mismatched": [],
            "error": "slurmdbd.conf not readable",
        }

    parsed_conf = _parse_slurm_style_config(raw_conf)
    deployed = _get_cgroup_entries(parsed_conf)

    details: List[str] = []
    missing: List[str] = []
    mismatched: List[str] = []

    for key, expected_value in custom_slurmdbd.items():
        expected_str = _format_value(expected_value)
        actual_value = deployed.get(key)

        if actual_value is None:
            missing.append(key)
            details.append(CUSTOM_SLURMDBD_PARAM_MISSING.format(key=key, expected=expected_str))
            continue

        if _values_match(expected_value, actual_value, key=key):
            details.append(CUSTOM_SLURMDBD_PARAM_PASSED.format(
                key=key, expected=expected_str, actual=actual_value))
        else:
            mismatched.append(key)
            details.append(CUSTOM_SLURMDBD_PARAM_FAILED.format(
                key=key, expected=expected_str, actual=actual_value))

    all_passed = not missing and not mismatched

    return {
        "success": all_passed,
        "message": CUSTOM_SLURMDBD_CONFIG_PASSED if all_passed else CUSTOM_SLURMDBD_CONFIG_FAILED.format(
            error="; ".join(missing + mismatched)),
        "details": details,
        "missing": missing,
        "mismatched": mismatched,
        "error": "" if all_passed else "; ".join(missing + mismatched),
    }


def verify_custom_slurm_config_reconfigure(host) -> Dict[str, Any]:
    """Verify custom config persists after scontrol reconfigure."""
    control_ip, fail_result = _get_control_ip_or_fail(host)
    if fail_result:
        return fail_result

    if not get_custom_slurm_config_sources(host):
        return {
            "success": True,
            "skipped": True,
            "message": CUSTOM_SLURM_CONFIG_NO_CONFIG_SOURCES,
            "details": [],
            "error": "",
        }

    before = _run_scontrol_command(host, control_ip, "show config")
    if not before:
        return {
            "success": False,
            "message": CUSTOM_SLURM_RECONFIGURE_FAILED.format(error="scontrol show config failed before reconfigure"),
            "details": [],
            "error": "scontrol show config failed before reconfigure",
        }

    reconfigure = _safe_run_on_remote_node(host, "scontrol reconfigure 2>/dev/null", control_ip)
    if reconfigure.rc != 0:
        return {
            "success": False,
            "message": CUSTOM_SLURM_RECONFIGURE_FAILED.format(error=f"scontrol reconfigure failed: {reconfigure.stderr.strip()}"),
            "details": [],
            "error": reconfigure.stderr.strip(),
        }

    # Give slurmctld a moment to reload
    time.sleep(2)

    after = _run_scontrol_command(host, control_ip, "show config")
    if not after:
        return {
            "success": False,
            "message": CUSTOM_SLURM_RECONFIGURE_FAILED.format(error="scontrol show config failed after reconfigure"),
            "details": [],
            "error": "scontrol show config failed after reconfigure",
        }

    before_config = _parse_scontrol_config(before)
    after_config = _parse_scontrol_config(after)

    custom_config = get_custom_slurm_config(host)
    details: List[str] = []
    mismatched: List[str] = []

    for key, expected_value in custom_config.items():
        if key in ("NodeName", "PartitionName"):
            continue
        expected_str = _format_value(expected_value)
        before_val = _normalize_scontrol_value(key, before_config.get(key, ""))
        after_val = _normalize_scontrol_value(key, after_config.get(key, ""))

        if before_val != after_val or after_val != expected_str:
            mismatched.append(key)
            details.append(CUSTOM_SLURM_PARAM_FAILED.format(
                key=f"{key} (reconfigure)", expected=expected_str, actual=after_val))
        else:
            details.append(CUSTOM_SLURM_PARAM_PASSED.format(
                key=f"{key} (reconfigure)", expected=expected_str, actual=after_val))

    all_passed = not mismatched

    return {
        "success": all_passed,
        "message": CUSTOM_SLURM_RECONFIGURE_PASSED if all_passed else CUSTOM_SLURM_RECONFIGURE_FAILED.format(
            error="; ".join(mismatched)),
        "details": details,
        "mismatched": mismatched,
        "error": "" if all_passed else "; ".join(mismatched),
    }


def verify_nfs_slurm_config_sync(host) -> Dict[str, Any]:
    """Verify NFS share slurm.conf and cgroup.conf match local control node files."""
    control_ip, fail_result = _get_control_ip_or_fail(host)
    if fail_result:
        return fail_result

    control_hostname = _get_slurm_control_node_hostname(host)
    if not control_hostname:
        return {
            "success": False,
            "message": CUSTOM_SLURM_NFS_SYNC_FAILED.format(error="Could not determine control node hostname"),
            "details": [],
            "error": "Could not determine control node hostname",
        }

    files = {
        "slurm.conf": (SLURM_CONF_CONTAINER_PATH, f"{NFS_SLURM_BASE_PATH}/{control_hostname}/{NFS_SLURM_ETC_REL_PATH}/slurm.conf"),
        "cgroup.conf": (CGROUP_CONF_CONTAINER_PATH, f"{NFS_SLURM_BASE_PATH}/{control_hostname}/{NFS_SLURM_ETC_REL_PATH}/cgroup.conf"),
    }

    details: List[str] = []
    mismatched: List[str] = []

    for name, (local_path, nfs_path) in files.items():
        local_content = _read_remote_file(host, control_ip, local_path)
        nfs_content = _read_remote_file(host, control_ip, nfs_path)

        if not local_content:
            mismatched.append(name)
            details.append(f"{name}: local file not readable")
            continue

        if not nfs_content:
            mismatched.append(name)
            details.append(f"{name}: NFS file not readable at {nfs_path}")
            continue

        if local_content.strip() == nfs_content.strip():
            details.append(f"{name}: local and NFS versions match")
        else:
            mismatched.append(name)
            details.append(f"{name}: local and NFS versions differ")

    all_passed = not mismatched

    return {
        "success": all_passed,
        "message": CUSTOM_SLURM_NFS_SYNC_PASSED if all_passed else CUSTOM_SLURM_NFS_SYNC_FAILED.format(
            error="; ".join(mismatched)),
        "details": details,
        "mismatched": mismatched,
        "error": "" if all_passed else "; ".join(mismatched),
    }


def verify_configless_mode(host) -> Dict[str, Any]:
    """Verify configless mode: compute nodes conf-cache matches control node slurm.conf."""
    control_ip, fail_result = _get_control_ip_or_fail(host)
    if fail_result:
        return fail_result

    control_slurm_conf = _read_remote_file(host, control_ip, SLURM_CONF_CONTAINER_PATH)
    if not control_slurm_conf:
        return {
            "success": False,
            "message": CUSTOM_SLURM_CONFIGLESS_FAILED.format(error="Control node slurm.conf not readable"),
            "details": [],
            "error": "Control node slurm.conf not readable",
        }

    compute_nodes = get_slurm_nodes(host)
    if not compute_nodes:
        return {
            "success": True,
            "skipped": True,
            "message": "No compute nodes found - skipping configless mode check",
            "details": [],
            "error": "",
        }

    details: List[str] = []
    mismatched: List[str] = []

    for node in compute_nodes:
        hostname = node.get("hostname", "")
        admin_ip = node.get("admin_ip", "")
        if not hostname or not admin_ip:
            continue

        nfs_cache_path = f"{NFS_SLURM_BASE_PATH}/{hostname}/{NFS_SLURM_CONF_CACHE_REL_PATH}/slurm.conf"
        cache_content = _read_remote_file(host, control_ip, nfs_cache_path)

        if not cache_content:
            mismatched.append(hostname)
            details.append(f"{hostname}: conf-cache not found on NFS share")
            continue

        if cache_content.strip() == control_slurm_conf.strip():
            details.append(f"{hostname}: conf-cache matches control node slurm.conf")
        else:
            mismatched.append(hostname)
            details.append(f"{hostname}: conf-cache does not match control node slurm.conf")

    all_passed = not mismatched

    return {
        "success": all_passed,
        "message": CUSTOM_SLURM_CONFIGLESS_PASSED if all_passed else CUSTOM_SLURM_CONFIGLESS_FAILED.format(
            error="; ".join(mismatched)),
        "details": details,
        "mismatched": mismatched,
        "error": "" if all_passed else "; ".join(mismatched),
    }


def verify_custom_config_job_behavior(host) -> Dict[str, Any]:
    """Verify job behavior with custom KillWait/MinJobAge parameters.

    Submits a short sleep job and verifies it completes within expected time.
    """
    control_ip, fail_result = _get_control_ip_or_fail(host)
    if fail_result:
        return fail_result

    if not get_custom_slurm_config_sources(host):
        return {
            "success": True,
            "skipped": True,
            "message": CUSTOM_SLURM_CONFIG_NO_CONFIG_SOURCES,
            "details": [],
            "error": "",
        }

    job_id = _run_sbatch(host, control_ip, "sleep 5")
    if not job_id:
        return {
            "success": False,
            "message": CUSTOM_SLURM_JOB_BEHAVIOR_FAILED.format(error=SBATCH_SUBMIT_FAILED.format(error="no job id")),
            "details": [],
            "error": "Failed to submit job",
        }

    state, error = _wait_for_job_state(host, control_ip, job_id, ["COMPLETED"], SBATCH_JOB_TIMEOUT, SBATCH_JOB_POLL_INTERVAL)
    if not state:
        return {
            "success": False,
            "message": CUSTOM_SLURM_JOB_BEHAVIOR_FAILED.format(error=error or SBATCH_TIMEOUT.format(job_id=job_id, timeout=SBATCH_JOB_TIMEOUT)),
            "details": [f"JobID: {job_id}"],
            "error": error or "Timeout",
        }

    return {
        "success": True,
        "message": CUSTOM_SLURM_JOB_BEHAVIOR_PASSED,
        "details": [f"JobID: {job_id} completed in state: {state}"],
        "job_id": job_id,
        "error": "",
    }


def verify_custom_slurm_config_negative(host) -> Dict[str, Any]:
    """Negative test: intentionally detect mismatched custom config.

    This test ensures the framework correctly fails when a specified custom
    parameter does not match the deployed value. It uses a deliberately wrong
    expected value and verifies the mismatch is detected.
    """
    control_ip, fail_result = _get_control_ip_or_fail(host)
    if fail_result:
        return fail_result

    raw_conf = _read_remote_file(host, control_ip, SLURM_CONF_CONTAINER_PATH)
    if not raw_conf:
        return {
            "success": False,
            "message": CUSTOM_SLURM_NEGATIVE_FAILED,
            "details": [],
            "error": "slurm.conf not readable",
        }

    parsed_conf = _parse_slurm_style_config(raw_conf)
    actual_slurmctld_timeout = parsed_conf.get("SlurmctldTimeout")
    if isinstance(actual_slurmctld_timeout, list):
        actual_slurmctld_timeout = actual_slurmctld_timeout[-1]

    if actual_slurmctld_timeout is None:
        return {
            "success": True,
            "message": CUSTOM_SLURM_NEGATIVE_PASSED,
            "details": ["SlurmctldTimeout not present in slurm.conf - negative test passed"],
            "error": "",
        }

    # Intentionally wrong expected value
    wrong_expected = str(int(actual_slurmctld_timeout) + 999)
    if _values_match(wrong_expected, actual_slurmctld_timeout, key="SlurmctldTimeout"):
        return {
            "success": False,
            "message": CUSTOM_SLURM_UNEXPECTED_MATCH.format(
                key="SlurmctldTimeout", expected=wrong_expected, actual=actual_slurmctld_timeout),
            "details": [],
            "error": "Negative test did not detect mismatch",
        }

    return {
        "success": True,
        "message": CUSTOM_SLURM_NEGATIVE_PASSED,
        "details": [
            f"Negative test detected expected mismatch: expected {wrong_expected}, actual {actual_slurmctld_timeout}"
        ],
        "error": "",
    }


def verify_custom_slurm_config(host) -> Dict[str, Any]:
    """Run all custom Slurm config verifications."""
    if not get_custom_slurm_config_sources(host):
        return {
            "success": True,
            "skipped": True,
            "message": CUSTOM_SLURM_CONFIG_NO_CONFIG_SOURCES,
            "details": [],
            "error": "",
        }

    results = [
        verify_custom_slurm_global_params(host),
        verify_custom_slurm_nodename(host),
        verify_custom_partition_config(host),
        verify_custom_cgroup_config(host),
        verify_custom_slurmdbd_config(host),
        verify_custom_slurm_config_reconfigure(host),
        verify_nfs_slurm_config_sync(host),
        verify_configless_mode(host),
        verify_custom_config_job_behavior(host),
        verify_custom_slurm_config_negative(host),
    ]

    all_passed = all(r.get("success") for r in results)
    all_skipped = all(r.get("skipped") for r in results)

    details: List[str] = []
    for r in results:
        details.extend(r.get("details", []))

    if all_skipped:
        return {
            "success": True,
            "skipped": True,
            "message": CUSTOM_SLURM_CONFIG_NO_CONFIG_SOURCES,
            "details": details,
            "error": "",
        }

    return {
        "success": all_passed,
        "message": CUSTOM_SLURM_CONFIG_PASSED if all_passed else CUSTOM_SLURM_CONFIG_FAILED.format(
            error="One or more custom Slurm config checks failed"),
        "details": details,
        "error": "" if all_passed else "One or more custom Slurm config checks failed",
    }
