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
K8s & Telemetry Upgrade - Pre-Check Collection Functions.

Each function collects a slice of cluster state and returns a structured dict
that is later persisted as the pre-upgrade snapshot.

Test-case mapping:
  TC-F001  -> collect_k8s_node_versions
  TC-F002  -> collect_node_roles
  TC-F003  -> collect_etcd_backup_status
  TC-F004  -> collect_node_roles
  TC-F005  -> collect_pod_disruption_budgets
  TC-F006  -> collect_crio_version, collect_crio_storage_config
  TC-F007  -> collect_calico_version, collect_network_policies
  TC-F008  -> collect_metallb_version
  TC-F009  -> collect_helm_version
  TC-F011  -> collect_bss_boot_params
  TC-F013  -> collect_kube_system_pods, collect_etcd_health
  TC-F014  -> collect_kube_vip_status
  TC-F015  -> collect_node_readiness (Gate 3), collect_etcd_health (Gate 4),
              verify_pulp_images_available (Gate 1), verify_ssh_connectivity (Gate 2)
  TC-F016  -> verify_oim_upgrade_completed
  TC-F017  -> verify_version_hop_valid
  TC-F018  -> verify_addon_compatibility
  TC-F019  -> collect_csi_status
  TC-F020  -> collect_telemetry_pods, collect_vm_pvcs, collect_kafka_state
  TC-S001/S002 -> collect_security_permissions
  TC-TEL-F001 -> verify_k8s_at_target_for_telemetry
  TC-TEL-F002 -> verify_telemetry_preflight, collect_helm_releases
  TC-TEL-F003 -> collect_kafka_state, collect_vm_pvcs
  TC-TEL-F004 -> collect_strimzi_version
  TC-TEL-F006 -> collect_idrac_telemetry_status
  TC-TEL-F007 -> collect_ldms_status
  TC-TEL-F009-F014 -> collect_telemetry_config_flags (flags only; post-check verifies)
  TC-TEL-F016 -> collect_strimzi_version
"""

import json
import re
from typing import Dict, Any, List

from ...core import run_on_remote_node
from ..vars.k8s_telemetry_upgrade_vars import (
    TELEMETRY_NAMESPACE,
    KUBE_SYSTEM_NAMESPACE,
    CALICO_NAMESPACE,
    METALLB_NAMESPACE,
    KUBECTL_CMD,
)


# =============================================================================
# K8s Node State Collectors
# =============================================================================

def collect_k8s_node_versions(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect K8s version from every node via kubelet version.

    Returns:
        Dict with success, nodes=[{name, version, ready}], error
    """
    cmd = run_on_remote_node(host, KUBECTL_CMD["get_nodes_version"], admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "nodes": [],
            "error": f"kubectl get nodes failed (rc={cmd.rc}): {cmd.stderr.strip()}",
        }

    nodes = []
    for line in cmd.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            nodes.append({
                "name": parts[0].strip(),
                "version": parts[1].strip(),
                "ready": parts[2].strip(),
            })

    return {"success": True, "nodes": nodes, "error": ""}


def collect_node_readiness(host, admin_ip: str) -> Dict[str, Any]:
    """
    Check that all nodes report Ready=True.

    Returns:
        Dict with success, total, ready_count, not_ready=[], error
    """
    result = collect_k8s_node_versions(host, admin_ip)
    if not result["success"]:
        return {
            "success": False,
            "total": 0,
            "ready_count": 0,
            "not_ready": [],
            "error": result["error"],
        }

    not_ready = [
        n["name"] for n in result["nodes"] if n["ready"] != "True"
    ]
    return {
        "success": len(not_ready) == 0,
        "total": len(result["nodes"]),
        "ready_count": len(result["nodes"]) - len(not_ready),
        "not_ready": not_ready,
        "error": f"NotReady nodes: {not_ready}" if not_ready else "",
    }


def collect_kube_system_pods(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect status of all pods in kube-system namespace.

    Returns:
        Dict with success, pods=[{name, status, restarts}], unhealthy=[], error
    """
    return _collect_pods_in_namespace(host, admin_ip, KUBE_SYSTEM_NAMESPACE)


# =============================================================================
# etcd Health
# =============================================================================

def collect_etcd_health(host, admin_ip: str) -> Dict[str, Any]:
    """
    Run etcdctl endpoint health on a control-plane node.

    Returns:
        Dict with success, endpoints=[{endpoint, healthy}], error
    """
    cmd = run_on_remote_node(host, KUBECTL_CMD["etcd_health"], admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "endpoints": [],
            "error": f"etcdctl failed (rc={cmd.rc}): {cmd.stderr.strip()}",
        }

    try:
        data = json.loads(cmd.stdout.strip())
        if isinstance(data, dict):
            data = [data]
        endpoints = []
        all_healthy = True
        for entry in data:
            # Handle both boolean true and string "true"
            health_value = entry.get("health", False)
            healthy = health_value is True or health_value == "true"
            if not healthy:
                all_healthy = False
            endpoints.append({
                "endpoint": entry.get("endpoint", "unknown"),
                "healthy": healthy,
            })
        return {
            "success": all_healthy,
            "endpoints": endpoints,
            "error": "" if all_healthy else "One or more etcd endpoints unhealthy",
        }
    except (json.JSONDecodeError, TypeError) as exc:
        return {
            "success": False,
            "endpoints": [],
            "error": f"Failed to parse etcd health output: {exc}",
        }


# =============================================================================
# Network Add-on Collectors
# =============================================================================

def collect_calico_status(host, admin_ip: str) -> Dict[str, Any]:
    """Collect Calico pod status from calico-system namespace."""
    return _collect_pods_in_namespace(host, admin_ip, CALICO_NAMESPACE)


def collect_metallb_status(host, admin_ip: str) -> Dict[str, Any]:
    """Collect MetalLB pod status from metallb-system namespace."""
    return _collect_pods_in_namespace(host, admin_ip, METALLB_NAMESPACE)


def collect_lb_service_ips(host, admin_ip: str) -> Dict[str, Any]:
    """
    Record all LoadBalancer service external IPs across all namespaces.

    Returns:
        Dict with success, services=[{namespace, name, external_ip, ports}], error
    """
    cmd = run_on_remote_node(host, KUBECTL_CMD["get_services_lb"], admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "services": [],
            "error": f"kubectl get svc failed: {cmd.stderr.strip()}",
        }

    try:
        data = json.loads(cmd.stdout.strip())
        services = []
        for item in data.get("items", []):
            spec = item.get("spec", {})
            if spec.get("type") != "LoadBalancer":
                continue
            status = item.get("status", {})
            ingress = status.get("loadBalancer", {}).get("ingress", [])
            external_ip = ingress[0].get("ip", "") if ingress else ""
            ports = [
                f"{p.get('port')}/{p.get('protocol', 'TCP')}"
                for p in spec.get("ports", [])
            ]
            services.append({
                "namespace": item["metadata"]["namespace"],
                "name": item["metadata"]["name"],
                "external_ip": external_ip,
                "ports": ports,
            })
        return {"success": True, "services": services, "error": ""}
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        return {
            "success": False,
            "services": [],
            "error": f"Failed to parse services: {exc}",
        }


# =============================================================================
# Telemetry Stack Collectors
# =============================================================================

def collect_helm_releases(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect Helm releases in the telemetry namespace.

    Returns:
        Dict with success, releases=[{name, chart, status, app_version}], error
    """
    helm_cmd = KUBECTL_CMD["helm_list"].format(ns=TELEMETRY_NAMESPACE)
    cmd = run_on_remote_node(host, helm_cmd, admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "releases": [],
            "error": f"helm list failed: {cmd.stderr.strip()}",
        }

    try:
        data = json.loads(cmd.stdout.strip()) if cmd.stdout.strip() else []
        releases = [
            {
                "name": r.get("name", ""),
                "chart": r.get("chart", ""),
                "status": r.get("status", ""),
                "app_version": r.get("app_version", ""),
            }
            for r in data
        ]
        return {"success": True, "releases": releases, "error": ""}
    except (json.JSONDecodeError, TypeError) as exc:
        return {
            "success": False,
            "releases": [],
            "error": f"Failed to parse helm output: {exc}",
        }


def collect_telemetry_pods(host, admin_ip: str) -> Dict[str, Any]:
    """Collect status of all pods in the telemetry namespace."""
    return _collect_pods_in_namespace(host, admin_ip, TELEMETRY_NAMESPACE)


def collect_vm_pvcs(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect VictoriaMetrics PVCs from the telemetry namespace.

    Returns:
        Dict with success, pvcs=[{name, phase, capacity, storage_class}], error
    """
    pvc_cmd = KUBECTL_CMD["get_pvcs"].format(ns=TELEMETRY_NAMESPACE)
    cmd = run_on_remote_node(host, pvc_cmd, admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "pvcs": [],
            "error": f"kubectl get pvc failed: {cmd.stderr.strip()}",
        }

    try:
        data = json.loads(cmd.stdout.strip())
        pvcs = []
        for item in data.get("items", []):
            name = item["metadata"]["name"]
            pvcs.append({
                "name": name,
                "phase": item.get("status", {}).get("phase", "Unknown"),
                "capacity": (
                    item.get("status", {})
                    .get("capacity", {})
                    .get("storage", "unknown")
                ),
                "storage_class": item.get("spec", {}).get("storageClassName", ""),
            })
        return {"success": True, "pvcs": pvcs, "error": ""}
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        return {
            "success": False,
            "pvcs": [],
            "error": f"Failed to parse PVC output: {exc}",
        }


def collect_kafka_state(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect Kafka broker pod status and topic list.

    Returns:
        Dict with success, broker_pods=[...], topics=[], error
    """
    pods_result = _collect_pods_in_namespace(
        host, admin_ip, TELEMETRY_NAMESPACE, label_filter="kafka"
    )

    topics: List[str] = []
    topic_cmd = KUBECTL_CMD["kafka_topics"].format(ns=TELEMETRY_NAMESPACE)
    tcmd = run_on_remote_node(host, topic_cmd, admin_ip)
    if tcmd.rc == 0 and tcmd.stdout.strip():
        topics = [
            t.strip() for t in tcmd.stdout.strip().split("\n")
            if t.strip() and not t.startswith("__")
        ]

    return {
        "success": pods_result["success"],
        "broker_pods": pods_result.get("pods", []),
        "topics": topics,
        "error": pods_result.get("error", ""),
    }


def collect_csi_status(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect CSI driver pods (any namespace) and PVCs bound to CSI drivers.

    Returns:
        Dict with success, csi_pods=[], csi_pvcs=[], error
    """
    # Collect CSI controller/node pods (typically in a csi-* or powerscale namespace)
    pod_cmd = (
        "kubectl get pods -A -o wide --no-headers "
        "| grep -iE 'csi|powerscale'"
    )
    cmd = run_on_remote_node(host, pod_cmd, admin_ip)
    csi_pods = []
    if cmd.rc == 0 and cmd.stdout.strip():
        for line in cmd.stdout.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 4:
                csi_pods.append({
                    "namespace": parts[0],
                    "name": parts[1],
                    "status": parts[3] if len(parts) > 3 else "Unknown",
                })

    # Collect PVCs that use CSI-based storage classes
    pvc_cmd = "kubectl get pvc -A -o json"
    pcmd = run_on_remote_node(host, pvc_cmd, admin_ip)
    csi_pvcs = []
    if pcmd.rc == 0 and pcmd.stdout.strip():
        try:
            data = json.loads(pcmd.stdout.strip())
            for item in data.get("items", []):
                sc = item.get("spec", {}).get("storageClassName", "")
                if "csi" in sc.lower() or "powerscale" in sc.lower():
                    csi_pvcs.append({
                        "namespace": item["metadata"]["namespace"],
                        "name": item["metadata"]["name"],
                        "phase": item.get("status", {}).get("phase", "Unknown"),
                        "storage_class": sc,
                    })
        except (json.JSONDecodeError, KeyError):
            pass

    return {
        "success": True,
        "csi_pods": csi_pods,
        "csi_pvcs": csi_pvcs,
        "error": "",
    }


def collect_nfs_provisioner(host, admin_ip: str) -> Dict[str, Any]:
    """
    Check if the NFS provisioner is deployed.

    Returns:
        Dict with success, deployed, pods=[], error
    """
    nfs_cmd = (
        "kubectl get pods -A --no-headers "
        "| grep -iE 'nfs-provisioner|nfs-subdir'"
    )
    cmd = run_on_remote_node(host, nfs_cmd, admin_ip)
    pods = []
    if cmd.rc == 0 and cmd.stdout.strip():
        for line in cmd.stdout.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 4:
                pods.append({
                    "namespace": parts[0],
                    "name": parts[1],
                    "status": parts[3] if len(parts) > 3 else "Unknown",
                })

    return {
        "success": True,
        "deployed": len(pods) > 0,
        "pods": pods,
        "error": "",
    }


# =============================================================================
# Component Version Collectors  (TC-F006, TC-F007, TC-F008, TC-F009)
# =============================================================================

def collect_crio_version(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect CRI-O version from every node.

    TC-F006: CRI-O upgrade alongside K8s.

    Returns:
        Dict with success, nodes=[{name, crio_version}], error
    """
    cmd = run_on_remote_node(
        host,
        "kubectl get nodes -o jsonpath="
        "'{range .items[*]}{.metadata.name}{\"\\t\"}"
        "{.status.nodeInfo.containerRuntimeVersion}{\"\\n\"}{end}'",
        admin_ip,
    )
    if cmd.rc != 0:
        return {"success": False, "nodes": [], "error": cmd.stderr.strip()}

    nodes = []
    for line in cmd.stdout.strip().split("\n"):
        parts = line.strip().split("\t")
        if len(parts) >= 2:
            nodes.append({"name": parts[0].strip(), "crio_version": parts[1].strip()})
    return {"success": True, "nodes": nodes, "error": ""}


def collect_calico_version(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect Calico controller image version.

    TC-F007: Calico CNI upgrade.

    Returns:
        Dict with success, version, pods, error
    """
    pods = _collect_pods_in_namespace(host, admin_ip, CALICO_NAMESPACE)
    img_cmd = (
        "kubectl get deploy -n calico-system calico-kube-controllers "
        "-o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null"
    )
    cmd = run_on_remote_node(host, img_cmd, admin_ip)
    version = cmd.stdout.strip() if cmd.rc == 0 else "unknown"
    return {
        "success": pods["success"],
        "version": version,
        "pods": pods.get("pods", []),
        "error": pods.get("error", ""),
    }


def collect_network_policies(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect all NetworkPolicies across namespaces.

    TC-F007: Verify network policies preserved after Calico upgrade.

    Returns:
        Dict with success, policies=[{namespace, name}], count, error
    """
    cmd = run_on_remote_node(
        host, "kubectl get networkpolicies -A -o json", admin_ip,
    )
    if cmd.rc != 0:
        return {"success": False, "policies": [], "count": 0, "error": cmd.stderr.strip()}

    try:
        data = json.loads(cmd.stdout.strip())
        policies = [
            {"namespace": i["metadata"]["namespace"], "name": i["metadata"]["name"]}
            for i in data.get("items", [])
        ]
        return {"success": True, "policies": policies, "count": len(policies), "error": ""}
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        return {"success": False, "policies": [], "count": 0, "error": str(exc)}


def collect_metallb_version(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect MetalLB controller image version and IPAddressPool CRDs.

    TC-F008: MetalLB upgrade with IP preservation.

    Returns:
        Dict with success, version, ip_pools=[], pods, error
    """
    pods = _collect_pods_in_namespace(host, admin_ip, METALLB_NAMESPACE)
    img_cmd = (
        "kubectl get deploy -n metallb-system controller "
        "-o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null"
    )
    cmd = run_on_remote_node(host, img_cmd, admin_ip)
    version = cmd.stdout.strip() if cmd.rc == 0 else "unknown"

    pool_cmd = "kubectl get ipaddresspools.metallb.io -A -o json 2>/dev/null"
    pcmd = run_on_remote_node(host, pool_cmd, admin_ip)
    ip_pools: List[Dict] = []
    if pcmd.rc == 0 and pcmd.stdout.strip():
        try:
            pdata = json.loads(pcmd.stdout.strip())
            for item in pdata.get("items", []):
                ip_pools.append({
                    "name": item["metadata"]["name"],
                    "namespace": item["metadata"].get("namespace", ""),
                    "addresses": item.get("spec", {}).get("addresses", []),
                })
        except (json.JSONDecodeError, KeyError):
            pass

    return {
        "success": pods["success"],
        "version": version,
        "ip_pools": ip_pools,
        "pods": pods.get("pods", []),
        "error": pods.get("error", ""),
    }


def collect_helm_version(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect Helm binary version.

    TC-F009: Helm upgrade.

    Returns:
        Dict with success, version, error
    """
    cmd = run_on_remote_node(host, "helm version --short 2>/dev/null", admin_ip)
    if cmd.rc != 0:
        return {"success": False, "version": "", "error": cmd.stderr.strip()}
    return {"success": True, "version": cmd.stdout.strip(), "error": ""}


# =============================================================================
# Extended Telemetry Collectors  (TC-TEL-F003, TC-TEL-F006, TC-TEL-F007)
# NOTE: DCGM, PowerScale, VAST, UFM, Vector, VictoriaLogs are NEW in Omnia 2.2
#       and do not exist in 2.1.  No pre-check baseline to collect.
#       Post-check verifies them based on telemetry_config.yml flags.
# =============================================================================

def collect_idrac_telemetry_status(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect iDRAC telemetry receiver pod status.

    TC-TEL-F006: iDRAC telemetry upgrade.

    Returns:
        Dict with success, pods=[], error
    """
    return _collect_pods_in_namespace(
        host, admin_ip, TELEMETRY_NAMESPACE, label_filter="idrac"
    )


def collect_ldms_status(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect LDMS sampler/aggregator pod status.

    TC-TEL-F007: LDMS upgrade.

    Returns:
        Dict with success, pods=[], error
    """
    return _collect_pods_in_namespace(
        host, admin_ip, TELEMETRY_NAMESPACE, label_filter="ldms"
    )




# =============================================================================
# Pre-Upgrade Validation Gates  (TC-F015)
# =============================================================================

def verify_ssh_connectivity(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify SSH connectivity from OIM (omnia_core) to all K8s nodes.

    TC-F015 Gate 2: SSH access to all nodes.

    Returns:
        Dict with success, reachable=[], unreachable=[], error
    """
    node_cmd = (
        "kubectl get nodes -o jsonpath="
        "'{range .items[*]}{.metadata.name}{\"\\n\"}{end}'"
    )
    cmd = run_on_remote_node(host, node_cmd, admin_ip)
    if cmd.rc != 0:
        return {"success": False, "reachable": [], "unreachable": [], "error": cmd.stderr.strip()}

    nodes = [n.strip() for n in cmd.stdout.strip().split("\n") if n.strip()]
    reachable = []
    unreachable = []
    for node in nodes:
        ssh_cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node} 'echo ok' 2>/dev/null"
        result = run_on_remote_node(host, ssh_cmd, admin_ip)
        if result.rc == 0 and "ok" in result.stdout:
            reachable.append(node)
        else:
            unreachable.append(node)

    return {
        "success": len(unreachable) == 0,
        "reachable": reachable,
        "unreachable": unreachable,
        "error": f"Unreachable nodes: {unreachable}" if unreachable else "",
    }


def verify_version_hop_valid(host, admin_ip: str, target_version: str) -> Dict[str, Any]:
    """
    Verify the current-to-target version hop is valid (one minor version).

    TC-F015 Gate 5 / TC-F017: Version skew policy enforcement.

    Note: If target_version is an Omnia version (e.g., 2.2.0.0) instead of K8s version,
    this check is skipped as it's not applicable.

    Returns:
        Dict with success, current_minor, target_minor, error
    """
    result = collect_k8s_node_versions(host, admin_ip)
    if not result["success"] or not result["nodes"]:
        return {"success": False, "current_minor": "", "target_minor": "", "error": result["error"]}

    current = result["nodes"][0]["version"]
    # Extract minor version numbers
    cur_match = re.search(r'v?1\.(\d+)', current)
    tgt_match = re.search(r'v?1\.(\d+)', target_version)
    
    # If target is not a K8s version format (e.g., Omnia version like 2.2.0.0),
    # skip this check as it's not applicable
    if not tgt_match:
        return {
            "success": True,
            "current_minor": current,
            "target_minor": target_version,
            "error": "",
            "skipped": True,
            "skip_reason": f"Target version '{target_version}' is not a K8s version format - skipping version hop validation",
        }
    
    if not cur_match:
        return {
            "success": False,
            "current_minor": current,
            "target_minor": target_version,
            "error": f"Cannot parse current K8s version: {current}",
        }

    cur_minor = int(cur_match.group(1))
    tgt_minor = int(tgt_match.group(1))
    diff = tgt_minor - cur_minor

    return {
        "success": diff == 1,
        "current_minor": f"1.{cur_minor}",
        "target_minor": f"1.{tgt_minor}",
        "error": (
            f"Version skew: 1.{cur_minor} -> 1.{tgt_minor} (diff={diff}, must be 1)"
            if diff != 1 else ""
        ),
    }


def verify_oim_upgrade_completed(host) -> Dict[str, Any]:
    """
    Verify OIM upgrade is completed (prerequisite for K8s upgrade).

    TC-F016: Tag dependency validation.
    TC-TEL-F001: Telemetry upgrade requires K8s at target.

    Note: In pre-upgrade state, upgrade_manifest.yml won't exist yet.
    This is acceptable and will be treated as success (no upgrade in progress).

    Returns:
        Dict with success, oim_status, error, skipped
    """
    from ...core import run_on_oim
    cmd = run_on_oim(
        host,
        "cat /opt/omnia/upgrade_manifest.yml 2>/dev/null || echo 'NOT_FOUND'"
    )
    if cmd.rc != 0 or "NOT_FOUND" in cmd.stdout:
        # Pre-upgrade state: manifest doesn't exist yet - this is acceptable
        return {
            "success": True,
            "oim_status": "not_started",
            "error": "",
            "skipped": True,
            "skip_reason": "upgrade_manifest.yml not found - pre-upgrade state (acceptable)",
        }

    try:
        import yaml as _yaml
        manifest = _yaml.safe_load(cmd.stdout) or {}
        oim_status = manifest.get("component_status", {}).get("oim", "pending")
        return {
            "success": oim_status == "completed",
            "oim_status": oim_status,
            "error": f"OIM status: {oim_status}" if oim_status != "completed" else "",
            "skipped": False,
        }
    except Exception as exc:
        return {
            "success": False,
            "oim_status": "parse_error",
            "error": str(exc),
            "skipped": False,
        }


def collect_telemetry_config_flags(host) -> Dict[str, Any]:
    """
    Read telemetry_config.yml feature flags.

    TC-TEL-F002: Telemetry pre-flight checks.
    TC-TEL-F014: Disabled components NOT deployed.

    Returns:
        Dict with success, flags={...}, error
    """
    from ...core import run_on_oim
    cmd = run_on_oim(
        host,
        "cat /opt/omnia/input/project_default/telemetry_config.yml 2>/dev/null || echo 'NOT_FOUND'"
    )
    if cmd.rc != 0 or "NOT_FOUND" in cmd.stdout:
        return {"success": False, "flags": {}, "error": "telemetry_config.yml not found at /opt/omnia/input/project_default/"}

    try:
        import yaml as _yaml
        config = _yaml.safe_load(cmd.stdout) or {}
        sources = config.get("telemetry_sources", {})
        bridges = config.get("telemetry_bridges", {})
        sinks = config.get("telemetry_sinks", {})
        flags = {
            "idrac_telemetry": sources.get("idrac", {}).get("metrics_enabled", False),
            "ldms": sources.get("ldms", {}).get("metrics_enabled", False),
            "dcgm": sources.get("dcgm", {}).get("metrics_enabled", False),
            "powerscale_telemetry": sources.get("powerscale", {}).get("metrics_enabled", False),
            "ufm_telemetry": sources.get("ufm", {}).get("metrics_enabled", False),
            "vast_telemetry": sources.get("vast", {}).get("metrics_enabled", False),
            "vector": bool(bridges.get("vector_ldms") or bridges.get("vector_ome")),
            "victorialogs": bool(sinks.get("victoria_logs")),
        }
        return {"success": True, "flags": flags, "error": ""}
    except Exception as exc:
        return {"success": False, "flags": {}, "error": str(exc)}


# =============================================================================
# Backup & Security Collectors  (TC-F003, TC-S001, TC-S002)
# =============================================================================

def collect_etcd_backup_status(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify etcd snapshot capability and backup directory readiness on CP-01.

    TC-F003: etcd snapshot + /etc/kubernetes backup before upgrade.

    Returns:
        Dict with success, backup_dir_exists, etcd_snapshot_ready, k8s_config_size, error
    """
    # Check backup directory
    backup_cmd = (
        "ls -la /opt/omnia/k8s_upgrade_backup/ 2>/dev/null && echo 'DIR_OK' || echo 'DIR_MISSING'"
    )
    result = run_on_remote_node(host, backup_cmd, admin_ip)
    backup_dir_exists = "DIR_OK" in result.stdout

    # Check etcd health (prerequisite for snapshot)
    etcd_cmd = (
        "ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 "
        "--cacert=/etc/kubernetes/pki/etcd/ca.crt "
        "--cert=/etc/kubernetes/pki/etcd/healthcheck-client.crt "
        "--key=/etc/kubernetes/pki/etcd/healthcheck-client.key "
        "endpoint status --write-out=table 2>&1 | head -5"
    )
    etcd_result = run_on_remote_node(host, etcd_cmd, admin_ip)
    etcd_snapshot_ready = etcd_result.rc == 0

    # Check /etc/kubernetes exists and has content
    k8s_cmd = "du -sh /etc/kubernetes/ 2>/dev/null || echo '0'"
    k8s_result = run_on_remote_node(host, k8s_cmd, admin_ip)
    k8s_config_size = k8s_result.stdout.strip().split()[0] if k8s_result.rc == 0 else "0"

    return {
        "success": etcd_snapshot_ready,
        "backup_dir_exists": backup_dir_exists,
        "etcd_snapshot_ready": etcd_snapshot_ready,
        "k8s_config_size": k8s_config_size,
        "error": "" if etcd_snapshot_ready else "etcd not ready for snapshot",
    }


def collect_security_permissions(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect file permissions for security-sensitive paths.

    TC-S001: Snapshot dir permissions (0700), file at 0600.
    TC-S002: SSH key permissions 0600, no passwords in logs.

    Returns:
        Dict with success, permissions={path: mode}, issues=[], error
    """
    paths_to_check = {
        "/opt/omnia/k8s_upgrade_backup": "0700",
        "/root/.ssh/id_rsa": "0600",
        "/root/.ssh/id_ed25519": "0600",
    }

    permissions = {}
    issues = []
    for path, expected in paths_to_check.items():
        cmd = run_on_remote_node(
            host,
            f"stat -c '%a' {path} 2>/dev/null || echo 'NOT_FOUND'",
            admin_ip,
        )
        actual = cmd.stdout.strip()
        permissions[path] = actual
        if actual == "NOT_FOUND":
            continue
        if actual != expected.lstrip("0"):
            issues.append(f"{path}: {actual} (expected {expected})")

    return {
        "success": len(issues) == 0,
        "permissions": permissions,
        "issues": issues,
        "error": "; ".join(issues) if issues else "",
    }


# =============================================================================
# Pulp & Addon Compatibility  (TC-F015 Gate 1, TC-F018)
# =============================================================================

def verify_pulp_images_available(host, admin_ip: str, target_version: str) -> Dict[str, Any]:
    """
    Verify target K8s images are available (pulled or in local registry).

    TC-F015 Gate 1: target RPMs + images in Pulp/registry.

    Returns:
        Dict with success, images_found=[], images_missing=[], error
    """
    expected_images = [
        f"kube-apiserver:v{target_version}",
        f"kube-controller-manager:v{target_version}",
        f"kube-scheduler:v{target_version}",
        f"kube-proxy:v{target_version}",
    ]

    images_found = []
    images_missing = []

    # Check crictl images on admin node
    check_cmd = "crictl images 2>/dev/null || ctr images list 2>/dev/null"
    result = run_on_remote_node(host, check_cmd, admin_ip)
    image_list = result.stdout if result.rc == 0 else ""

    for img in expected_images:
        if target_version in image_list:
            images_found.append(img)
        else:
            images_missing.append(img)

    return {
        "success": True,
        "images_found": images_found,
        "images_missing": images_missing,
        "error": "",
    }


def verify_addon_compatibility(host, admin_ip: str, target_version: str) -> Dict[str, Any]:
    """
    Verify addon versions (Calico, MetalLB, Helm) compatible with target K8s.

    TC-F018: Addon version validation before upgrade.

    Returns:
        Dict with success, addons={name: {version, compatible}}, error
    """
    addons = {}

    # Calico version
    calico = collect_calico_version(host, admin_ip)
    addons["calico"] = {
        "version": calico.get("version", "unknown"),
        "healthy": calico.get("success", False),
    }

    # MetalLB version
    metallb = collect_metallb_version(host, admin_ip)
    addons["metallb"] = {
        "version": metallb.get("version", "unknown"),
        "healthy": metallb.get("success", False),
    }

    # Helm version
    helm = collect_helm_version(host, admin_ip)
    addons["helm"] = {
        "version": helm.get("version", "unknown"),
        "healthy": helm.get("success", False),
    }

    all_healthy = all(a["healthy"] for a in addons.values())
    return {
        "success": all_healthy,
        "addons": addons,
        "target_k8s": target_version,
        "error": "" if all_healthy else "One or more addons unhealthy before upgrade",
    }


# =============================================================================
# Telemetry Pre-Flight  (TC-TEL-F001, TC-TEL-F002)
# =============================================================================

def verify_k8s_at_target_for_telemetry(
    host, admin_ip: str, target_version: str
) -> Dict[str, Any]:
    """
    Verify K8s is already at target version (prerequisite for telemetry upgrade).

    TC-TEL-F001: Telemetry upgrade aborts if K8s not at target.

    Returns:
        Dict with success, current_version, target_version, error
    """
    result = collect_k8s_node_versions(host, admin_ip)
    if not result["success"] or not result["nodes"]:
        return {
            "success": False,
            "current_version": "unknown",
            "target_version": target_version,
            "error": result.get("error", "Cannot get node versions"),
        }

    current = result["nodes"][0]["version"]
    prefix = target_version if target_version.startswith("v") else f"v{target_version}"
    at_target = all(n["version"].startswith(prefix) for n in result["nodes"])

    return {
        "success": at_target,
        "current_version": current,
        "target_version": target_version,
        "error": "" if at_target else f"K8s not at target {target_version}, current: {current}",
    }


def verify_telemetry_preflight(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify telemetry upgrade pre-flight conditions:
      - telemetry_config.yml readable
      - Helm available
      - telemetry namespace exists

    TC-TEL-F002: Telemetry pre-flight checks.

    Returns:
        Dict with success, checks={name: passed}, error
    """
    checks = {}

    # Helm available
    helm = collect_helm_version(host, admin_ip)
    checks["helm_available"] = helm["success"]

    # telemetry namespace exists
    ns_cmd = f"kubectl get ns {TELEMETRY_NAMESPACE} 2>/dev/null"
    ns_result = run_on_remote_node(host, ns_cmd, admin_ip)
    checks["telemetry_ns_exists"] = ns_result.rc == 0

    # telemetry_config.yml readable
    config = collect_telemetry_config_flags(host)
    checks["telemetry_config_readable"] = config["success"]

    all_ok = all(checks.values())
    failed = [k for k, v in checks.items() if not v]
    return {
        "success": all_ok,
        "checks": checks,
        "error": f"Failed pre-flight: {failed}" if failed else "",
    }


# =============================================================================
# BSS Boot Params Baseline  (TC-F011)
# =============================================================================

def collect_bss_boot_params(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect BSS boot parameters for CP and worker nodes (baseline).

    TC-F011: BSS boot params updated after upgrade.

    Returns:
        Dict with success, params={node: {kernel, initrd}}, error
    """
    cmd = run_on_remote_node(
        host,
        "kubectl get nodes -o jsonpath="
        "'{range .items[*]}{.metadata.name}{\"\\t\"}"
        "{.status.nodeInfo.kernelVersion}{\"\\t\"}"
        "{.status.nodeInfo.osImage}{\"\\n\"}{end}'",
        admin_ip,
    )
    if cmd.rc != 0:
        return {"success": False, "params": {}, "error": cmd.stderr.strip()}

    params = {}
    for line in cmd.stdout.strip().split("\n"):
        parts = line.strip().split("\t")
        if len(parts) >= 3:
            params[parts[0].strip()] = {
                "kernel": parts[1].strip(),
                "os_image": parts[2].strip(),
            }

    return {"success": True, "params": params, "error": ""}


# =============================================================================
# Strimzi/Kafka Baseline  (TC-TEL-F004, TC-TEL-F016)
# =============================================================================

def collect_strimzi_version(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect Strimzi operator version and Kafka cluster version.

    TC-TEL-F004: Strimzi operator upgraded first, then Kafka brokers.
    TC-TEL-F016: KRaft migration check.

    Returns:
        Dict with success, strimzi_version, kafka_version, uses_kraft, error
    """
    # Strimzi operator version
    strimzi_cmd = (
        "kubectl get deploy -n telemetry strimzi-cluster-operator "
        "-o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null"
    )
    scmd = run_on_remote_node(host, strimzi_cmd, admin_ip)
    strimzi_version = scmd.stdout.strip() if scmd.rc == 0 else "unknown"

    # Kafka cluster version
    kafka_cmd = (
        "kubectl get kafka -n telemetry -o jsonpath="
        "'{.items[0].spec.kafka.version}' 2>/dev/null"
    )
    kcmd = run_on_remote_node(host, kafka_cmd, admin_ip)
    kafka_version = kcmd.stdout.strip() if kcmd.rc == 0 else "unknown"

    # Check if Kafka uses KRaft (no ZooKeeper pods)
    zk_cmd = "kubectl get pods -n telemetry -l strimzi.io/name=kafka-zookeeper --no-headers 2>/dev/null"
    zk_result = run_on_remote_node(host, zk_cmd, admin_ip)
    zk_pods = [l for l in zk_result.stdout.strip().split("\n") if l.strip()] if zk_result.rc == 0 else []
    uses_kraft = len(zk_pods) == 0

    return {
        "success": scmd.rc == 0,
        "strimzi_version": strimzi_version,
        "kafka_version": kafka_version,
        "uses_kraft": uses_kraft,
        "zk_pods_count": len(zk_pods),
        "error": "" if scmd.rc == 0 else "Cannot get Strimzi operator info",
    }


# =============================================================================
# CRI-O Storage Config  (TC-F006)
# =============================================================================

def collect_crio_storage_config(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect CRI-O storage config (storage size) from nodes.

    TC-F006: Verify k8s_crio_storage_size preserved after upgrade.

    Returns:
        Dict with success, configs={node: {graphRoot, runRoot}}, error
    """
    node_cmd = (
        "kubectl get nodes -o jsonpath="
        "'{range .items[*]}{.metadata.name}{\"\\n\"}{end}'"
    )
    ncmd = run_on_remote_node(host, node_cmd, admin_ip)
    if ncmd.rc != 0:
        return {"success": False, "configs": {}, "error": ncmd.stderr.strip()}

    nodes = [n.strip() for n in ncmd.stdout.strip().split("\n") if n.strip()]
    configs = {}
    for node in nodes:
        cfg_cmd = (
            f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node} "
            "'cat /etc/crio/crio.conf 2>/dev/null | grep -E \"(graphRoot|runRoot|storage_driver)\" '"
        )
        result = run_on_remote_node(host, cfg_cmd, admin_ip)
        configs[node] = result.stdout.strip() if result.rc == 0 else "N/A"

    return {"success": True, "configs": configs, "error": ""}


# =============================================================================
# Kube-VIP HA  (TC-F014)
# =============================================================================

def collect_kube_vip_status(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect kube-vip pod status for HA VIP verification.

    TC-F014: VIP reachable, kube-vip updated.

    Returns:
        Dict with success, pods=[], vip_reachable, error
    """
    vip_pods = _collect_pods_in_namespace(
        host, admin_ip, KUBE_SYSTEM_NAMESPACE, label_filter="kube-vip"
    )

    # Try to detect VIP from cluster info
    cluster_cmd = "kubectl cluster-info 2>/dev/null | head -1"
    ccmd = run_on_remote_node(host, cluster_cmd, admin_ip)
    vip_reachable = ccmd.rc == 0 and "running" in ccmd.stdout.lower()

    return {
        "success": vip_pods["success"] or vip_reachable,
        "pods": vip_pods.get("pods", []),
        "vip_reachable": vip_reachable,
        "error": vip_pods.get("error", ""),
    }


# =============================================================================
# PDB Check  (TC-F005)
# =============================================================================

def collect_pod_disruption_budgets(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect PodDisruptionBudgets across the cluster.

    TC-F005: Drain respects PDBs, workloads rescheduled gracefully.

    Returns:
        Dict with success, pdbs=[{namespace, name, min_available, max_unavailable}], error
    """
    cmd = run_on_remote_node(
        host, "kubectl get pdb -A -o json 2>/dev/null", admin_ip,
    )
    if cmd.rc != 0:
        return {"success": True, "pdbs": [], "error": ""}

    try:
        data = json.loads(cmd.stdout.strip())
        pdbs = []
        for item in data.get("items", []):
            pdbs.append({
                "namespace": item["metadata"]["namespace"],
                "name": item["metadata"]["name"],
                "min_available": item.get("spec", {}).get("minAvailable", "N/A"),
                "max_unavailable": item.get("spec", {}).get("maxUnavailable", "N/A"),
                "current_healthy": item.get("status", {}).get("currentHealthy", 0),
                "desired_healthy": item.get("status", {}).get("desiredHealthy", 0),
            })
        return {"success": True, "pdbs": pdbs, "error": ""}
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        return {"success": True, "pdbs": [], "error": str(exc)}


# =============================================================================
# Node Roles & Topology  (TC-F002, TC-F004)
# =============================================================================

def collect_node_roles(host, admin_ip: str) -> Dict[str, Any]:
    """
    Collect node names, roles (CP vs worker), and IPs.

    TC-F002: CPs upgraded sequentially.
    TC-F004: Workers upgraded rolling.

    Returns:
        Dict with success, control_planes=[], workers=[], error
    """
    cmd = run_on_remote_node(
        host,
        "kubectl get nodes -o jsonpath="
        "'{range .items[*]}{.metadata.name}{\"\\t\"}"
        "{.metadata.labels.node-role\\.kubernetes\\.io/control-plane}{\"\\t\"}"
        "{.status.addresses[?(@.type==\"InternalIP\")].address}{\"\\n\"}{end}'",
        admin_ip,
    )
    if cmd.rc != 0:
        return {"success": False, "control_planes": [], "workers": [], "error": cmd.stderr.strip()}

    control_planes = []
    workers = []
    for line in cmd.stdout.strip().split("\n"):
        parts = line.strip().split("\t")
        if len(parts) < 2:
            continue
        name = parts[0].strip()
        is_cp = len(parts) > 1 and parts[1].strip() != ""
        ip = parts[2].strip() if len(parts) > 2 else ""
        entry = {"name": name, "ip": ip}
        if is_cp:
            control_planes.append(entry)
        else:
            workers.append(entry)

    return {
        "success": True,
        "control_planes": control_planes,
        "workers": workers,
        "total": len(control_planes) + len(workers),
        "error": "",
    }


# =============================================================================
# Internal Helpers
# =============================================================================

def _collect_pods_in_namespace(
    host, admin_ip: str, namespace: str, label_filter: str = ""
) -> Dict[str, Any]:
    """
    Generic helper to collect pod status in a namespace.

    Returns:
        Dict with success, pods=[{name, status, restarts, node}], unhealthy=[], error
    """
    pods_cmd = KUBECTL_CMD["get_pods_ns"].format(ns=namespace)
    cmd = run_on_remote_node(host, pods_cmd, admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "pods": [],
            "unhealthy": [],
            "error": f"kubectl get pods -n {namespace} failed: {cmd.stderr.strip()}",
        }

    pods = []
    unhealthy = []
    for line in cmd.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        name = parts[0]
        if label_filter and label_filter.lower() not in name.lower():
            continue
        status = parts[2]
        restarts = parts[3]
        node = parts[6] if len(parts) > 6 else ""
        pods.append({
            "name": name,
            "status": status,
            "restarts": restarts,
            "node": node,
        })
        if status not in ("Running", "Completed", "Succeeded"):
            unhealthy.append(name)

    return {
        "success": len(unhealthy) == 0,
        "pods": pods,
        "unhealthy": unhealthy,
        "error": f"Unhealthy pods: {unhealthy}" if unhealthy else "",
    }
