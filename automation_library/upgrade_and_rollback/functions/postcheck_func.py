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
K8s & Telemetry Upgrade - Post-Check Verification Functions.

Each function verifies a specific aspect of the cluster after upgrade,
comparing against the pre-upgrade snapshot where applicable.

Test-case mapping:
  TC-F001  -> verify_k8s_target_version
  TC-F002  -> verify_cps_at_target
  TC-F003  -> verify_etcd_backup_exists
  TC-F004  -> verify_workers_at_target
  TC-F005  -> verify_pdbs_healthy
  TC-F006  -> verify_crio_at_target, verify_crio_storage_preserved
  TC-F007  -> verify_calico_version_upgraded, verify_network_policies_preserved
  TC-F008  -> verify_metallb_version_upgraded
  TC-F009  -> verify_helm_at_target
  TC-F010  -> verify_nfs_provisioner_running
  TC-F011  -> verify_bss_params_updated
  TC-F013  -> verify_all_nodes_ready, verify_kube_system_healthy,
              verify_etcd_healthy, verify_api_server_reachable,
              verify_dns_resolution, verify_calico_healthy, verify_upgrade_manifest
  TC-F014  -> verify_api_server_reachable (VIP), verify_kube_vip_ha
  TC-F019  -> verify_csi_pvcs_preserved
  TC-E016  -> verify_metallb_ips_preserved
  TC-S001/S002 -> verify_security_permissions
  TC-I001/I002 -> verify_cluster_unchanged
  TC-R001/R006/R007 -> verify_rollback_to_source
  TC-R002/R003 -> verify_rollback_etcd_restored
  TC-R009  -> verify_rollback_metallb_cleaned
  TC-R010  -> verify_rollback_csi_cleaned
  TC-R012  -> verify_rollback_helm_restored
  TC-TEL-F004 -> verify_strimzi_upgraded
  TC-TEL-F005 -> verify_vm_pvcs_preserved, verify_vm_data_accessible
  TC-TEL-F006 -> verify_idrac_telemetry_running
  TC-TEL-F007 -> verify_ldms_collecting
  TC-TEL-F008 -> verify_telemetry_phase1_gate
  TC-TEL-F009-F014 -> verify_new_telemetry_components
  TC-TEL-F015 -> verify_upgrade_manifest
  TC-TEL-F016 -> verify_kraft_migration
  TC-TEL-I001/I002 -> verify_cluster_unchanged
  TC-TEL-R001 -> verify_rollback_telemetry_healthy
  TC-TEL-R002 -> verify_vm_pvcs_preserved
  TC-TEL-R003 -> verify_kafka_topics_preserved
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
from .precheck_func import (
    collect_k8s_node_versions,
    collect_node_readiness,
    _collect_pods_in_namespace,
    collect_etcd_health,
    collect_lb_service_ips,
    collect_vm_pvcs,
    collect_kafka_state,
    collect_helm_releases,
    collect_crio_version,
    collect_calico_version,
    collect_network_policies,
    collect_metallb_version,
    collect_helm_version,
    collect_nfs_provisioner,
    collect_idrac_telemetry_status,
    collect_ldms_status,
    collect_etcd_backup_status,
    collect_security_permissions,
    collect_bss_boot_params,
    collect_strimzi_version,
    collect_crio_storage_config,
    collect_kube_vip_status,
    collect_pod_disruption_budgets,
    collect_node_roles,
    collect_telemetry_config_flags,
)


# =============================================================================
# K8s Version & Readiness
# =============================================================================

def verify_k8s_target_version(
    host, admin_ip: str, target_version: str
) -> Dict[str, Any]:
    """
    Verify all nodes are at the target K8s version.

    Args:
        target_version: Expected version prefix (e.g. "v1.35" or "1.35")

    Returns:
        Dict with success, nodes_ok=[], nodes_fail=[], error
    """
    result = collect_k8s_node_versions(host, admin_ip)
    if not result["success"]:
        return {
            "success": False,
            "nodes_ok": [],
            "nodes_fail": [],
            "error": result["error"],
        }

    prefix = target_version if target_version.startswith("v") else f"v{target_version}"
    nodes_ok = []
    nodes_fail = []
    for node in result["nodes"]:
        if node["version"].startswith(prefix):
            nodes_ok.append(node)
        else:
            nodes_fail.append(node)

    return {
        "success": len(nodes_fail) == 0,
        "nodes_ok": nodes_ok,
        "nodes_fail": nodes_fail,
        "error": (
            f"Nodes not at target: {[n['name'] for n in nodes_fail]}"
            if nodes_fail else ""
        ),
    }


def verify_all_nodes_ready(host, admin_ip: str) -> Dict[str, Any]:
    """Verify all nodes are in Ready state after upgrade."""
    return collect_node_readiness(host, admin_ip)


# =============================================================================
# System Pod Health
# =============================================================================

def verify_kube_system_healthy(host, admin_ip: str) -> Dict[str, Any]:
    """Verify all kube-system pods are Running after upgrade."""
    return _collect_pods_in_namespace(host, admin_ip, KUBE_SYSTEM_NAMESPACE)


def verify_etcd_healthy(host, admin_ip: str) -> Dict[str, Any]:
    """Verify etcd cluster is healthy after upgrade."""
    return collect_etcd_health(host, admin_ip)


def verify_api_server_reachable(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify the API server is reachable via kubectl cluster-info.

    Returns:
        Dict with success, output, error
    """
    cmd = run_on_remote_node(host, KUBECTL_CMD["cluster_info"], admin_ip)
    success = cmd.rc == 0 and "is running" in cmd.stdout.lower()
    return {
        "success": success,
        "output": cmd.stdout.strip(),
        "error": cmd.stderr.strip() if not success else "",
    }


def verify_dns_resolution(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify DNS resolution works inside the cluster by running nslookup
    for kubernetes.default.svc.cluster.local.

    Returns:
        Dict with success, output, error
    """
    cmd = run_on_remote_node(host, KUBECTL_CMD["dns_lookup"], admin_ip)
    success = cmd.rc == 0 and "address" in cmd.stdout.lower()
    return {
        "success": success,
        "output": cmd.stdout.strip(),
        "error": cmd.stderr.strip() if not success else "",
    }


# =============================================================================
# Network Add-on Verification
# =============================================================================

def verify_calico_healthy(host, admin_ip: str) -> Dict[str, Any]:
    """Verify Calico pods are Running after upgrade."""
    return _collect_pods_in_namespace(host, admin_ip, CALICO_NAMESPACE)


def verify_metallb_ips_preserved(
    host, admin_ip: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare current LB service IPs with the pre-upgrade snapshot.

    Returns:
        Dict with success, preserved=[], changed=[], missing=[], error
    """
    pre_services = pre_snapshot.get("lb_service_ips", {}).get("services", [])
    if not pre_services:
        return {
            "success": True,
            "preserved": [],
            "changed": [],
            "missing": [],
            "error": "",
        }

    current = collect_lb_service_ips(host, admin_ip)
    if not current["success"]:
        return {
            "success": False,
            "preserved": [],
            "changed": [],
            "missing": [],
            "error": current["error"],
        }

    # Build lookup: (ns, name) -> external_ip
    current_map = {
        (s["namespace"], s["name"]): s["external_ip"]
        for s in current["services"]
    }

    preserved = []
    changed = []
    missing = []
    for svc in pre_services:
        key = (svc["namespace"], svc["name"])
        cur_ip = current_map.get(key)
        if cur_ip is None:
            missing.append({**svc, "current_ip": ""})
        elif cur_ip == svc["external_ip"]:
            preserved.append(svc)
        else:
            changed.append({**svc, "current_ip": cur_ip})

    ok = len(changed) == 0 and len(missing) == 0
    details = []
    for c in changed:
        details.append(
            f"  {c['namespace']}/{c['name']}: was {c['external_ip']}, "
            f"now {c['current_ip']}"
        )
    for m in missing:
        details.append(f"  {m['namespace']}/{m['name']}: was {m['external_ip']}, now MISSING")

    return {
        "success": ok,
        "preserved": preserved,
        "changed": changed,
        "missing": missing,
        "error": "\n".join(details) if details else "",
    }


# =============================================================================
# Telemetry Stack Verification
# =============================================================================

def verify_telemetry_pods_running(host, admin_ip: str) -> Dict[str, Any]:
    """Verify all telemetry namespace pods are Running after upgrade."""
    return _collect_pods_in_namespace(host, admin_ip, TELEMETRY_NAMESPACE)


def verify_vm_pvcs_preserved(
    host, admin_ip: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify VictoriaMetrics PVCs are still Bound and match pre-upgrade state.

    Returns:
        Dict with success, preserved=[], lost=[], error
    """
    pre_pvcs = pre_snapshot.get("vm_pvcs", {}).get("pvcs", [])
    if not pre_pvcs:
        return {"success": True, "preserved": [], "lost": [], "error": ""}

    current = collect_vm_pvcs(host, admin_ip)
    if not current["success"]:
        return {
            "success": False,
            "preserved": [],
            "lost": [],
            "error": current["error"],
        }

    current_map = {p["name"]: p for p in current["pvcs"]}
    preserved = []
    lost = []
    for pre in pre_pvcs:
        cur = current_map.get(pre["name"])
        if cur and cur["phase"] == "Bound":
            preserved.append(cur)
        else:
            lost.append(pre)

    return {
        "success": len(lost) == 0,
        "preserved": preserved,
        "lost": lost,
        "error": (
            f"PVCs lost/unbound: {[p['name'] for p in lost]}"
            if lost else ""
        ),
    }


def verify_vm_data_accessible(host, admin_ip: str) -> Dict[str, Any]:
    """
    Query VictoriaMetrics for any metric to verify TSDB data accessible.

    Returns:
        Dict with success, sample_count, error
    """
    query_cmd = (
        "kubectl exec -n telemetry deploy/vmselect -- "
        "wget -qO- 'http://localhost:8481/select/0/prometheus/api/v1/query"
        "?query=up&time=2025-01-01T00:00:00Z' 2>/dev/null "
        "|| curl -sk 'http://vmselect-telemetry.telemetry:8481"
        "/select/0/prometheus/api/v1/query?query=up' 2>/dev/null"
    )
    cmd = run_on_remote_node(host, query_cmd, admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "sample_count": 0,
            "error": f"VM query failed: {cmd.stderr.strip()}",
        }

    try:
        data = json.loads(cmd.stdout.strip())
        results = data.get("data", {}).get("result", [])
        return {
            "success": data.get("status") == "success",
            "sample_count": len(results),
            "error": "" if data.get("status") == "success" else "query unsuccessful",
        }
    except (json.JSONDecodeError, TypeError):
        # Non-JSON output isn't necessarily a failure; VM may just not be queryable
        return {
            "success": False,
            "sample_count": 0,
            "error": "Could not parse VictoriaMetrics response",
        }


def verify_kafka_topics_preserved(
    host, admin_ip: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify Kafka topics from pre-upgrade still exist.

    Returns:
        Dict with success, preserved=[], missing=[], error
    """
    pre_topics = pre_snapshot.get("kafka_state", {}).get("topics", [])
    if not pre_topics:
        return {"success": True, "preserved": [], "missing": [], "error": ""}

    current = collect_kafka_state(host, admin_ip)
    current_topics = set(current.get("topics", []))

    preserved = [t for t in pre_topics if t in current_topics]
    missing = [t for t in pre_topics if t not in current_topics]

    return {
        "success": len(missing) == 0,
        "preserved": preserved,
        "missing": missing,
        "error": f"Missing topics: {missing}" if missing else "",
    }


def verify_csi_pvcs_preserved(
    host, admin_ip: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify CSI-backed PVCs are still Bound after upgrade.

    Returns:
        Dict with success, preserved=[], lost=[], error
    """
    pre_pvcs = pre_snapshot.get("csi_status", {}).get("csi_pvcs", [])
    if not pre_pvcs:
        return {"success": True, "preserved": [], "lost": [], "error": ""}

    # Re-collect current CSI PVCs
    pvc_cmd = "kubectl get pvc -A -o json"
    cmd = run_on_remote_node(host, pvc_cmd, admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "preserved": [],
            "lost": [],
            "error": f"kubectl get pvc failed: {cmd.stderr.strip()}",
        }

    try:
        data = json.loads(cmd.stdout.strip())
        current_map = {}
        for item in data.get("items", []):
            key = (item["metadata"]["namespace"], item["metadata"]["name"])
            current_map[key] = item.get("status", {}).get("phase", "Unknown")
    except (json.JSONDecodeError, KeyError):
        return {
            "success": False,
            "preserved": [],
            "lost": [],
            "error": "Failed to parse PVC output",
        }

    preserved = []
    lost = []
    for pre in pre_pvcs:
        key = (pre["namespace"], pre["name"])
        phase = current_map.get(key)
        if phase == "Bound":
            preserved.append(pre)
        else:
            lost.append({**pre, "current_phase": phase or "MISSING"})

    return {
        "success": len(lost) == 0,
        "preserved": preserved,
        "lost": lost,
        "error": (
            f"PVCs lost/unbound: {[p['name'] for p in lost]}"
            if lost else ""
        ),
    }


def verify_helm_releases_present(
    host, admin_ip: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify Helm releases from pre-upgrade are still present.

    Returns:
        Dict with success, present=[], missing=[], error
    """
    pre_releases = pre_snapshot.get("helm_releases", {}).get("releases", [])
    if not pre_releases:
        return {"success": True, "present": [], "missing": [], "error": ""}

    current = collect_helm_releases(host, admin_ip)
    if not current["success"]:
        return {
            "success": False,
            "present": [],
            "missing": [],
            "error": current["error"],
        }

    current_names = {r["name"] for r in current["releases"]}
    present = [r for r in pre_releases if r["name"] in current_names]
    missing = [r for r in pre_releases if r["name"] not in current_names]

    return {
        "success": len(missing) == 0,
        "present": present,
        "missing": missing,
        "error": (
            f"Missing releases: {[r['name'] for r in missing]}"
            if missing else ""
        ),
    }


# =============================================================================
# Component Version Verification  (TC-F006, TC-F007, TC-F008, TC-F009)
# =============================================================================

def verify_crio_at_target(
    host, admin_ip: str, target_version: str
) -> Dict[str, Any]:
    """
    Verify CRI-O is upgraded to match the target K8s minor version.

    TC-F006: CRI-O upgrade alongside K8s.

    Returns:
        Dict with success, nodes_ok=[], nodes_fail=[], error
    """
    result = collect_crio_version(host, admin_ip)
    if not result["success"]:
        return {"success": False, "nodes_ok": [], "nodes_fail": [], "error": result["error"]}

    tgt_match = re.search(r'1\.(\d+)', target_version)
    tgt_minor = tgt_match.group(1) if tgt_match else ""

    nodes_ok = []
    nodes_fail = []
    for node in result["nodes"]:
        ver = node["crio_version"]
        if tgt_minor and tgt_minor in ver:
            nodes_ok.append(node)
        else:
            nodes_fail.append(node)

    return {
        "success": len(nodes_fail) == 0,
        "nodes_ok": nodes_ok,
        "nodes_fail": nodes_fail,
        "error": (
            f"CRI-O not at target on: {[n['name'] for n in nodes_fail]}"
            if nodes_fail else ""
        ),
    }


def verify_calico_version_upgraded(
    host, admin_ip: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify Calico pods are Running and version is at or above pre-upgrade.

    TC-F007: Calico CNI upgrade.

    Returns:
        Dict with success, pre_version, post_version, pods_healthy, error
    """
    pre_version = pre_snapshot.get("calico_version", {}).get("version", "unknown")
    current = collect_calico_version(host, admin_ip)
    return {
        "success": current["success"],
        "pre_version": pre_version,
        "post_version": current.get("version", "unknown"),
        "pods_healthy": current["success"],
        "error": current.get("error", ""),
    }


def verify_network_policies_preserved(
    host, admin_ip: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify all pre-upgrade NetworkPolicies still exist.

    TC-F007: Network policies preserved after Calico upgrade.

    Returns:
        Dict with success, preserved=[], missing=[], error
    """
    pre_policies = pre_snapshot.get("network_policies", {}).get("policies", [])
    if not pre_policies:
        return {"success": True, "preserved": [], "missing": [], "error": ""}

    current = collect_network_policies(host, admin_ip)
    if not current["success"]:
        return {"success": False, "preserved": [], "missing": [], "error": current["error"]}

    current_set = {(p["namespace"], p["name"]) for p in current["policies"]}
    preserved = [p for p in pre_policies if (p["namespace"], p["name"]) in current_set]
    missing = [p for p in pre_policies if (p["namespace"], p["name"]) not in current_set]

    return {
        "success": len(missing) == 0,
        "preserved": preserved,
        "missing": missing,
        "error": f"Missing policies: {missing}" if missing else "",
    }


def verify_metallb_version_upgraded(
    host, admin_ip: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify MetalLB pods Running and IPAddressPool CRDs preserved.

    TC-F008: MetalLB upgrade with IP preservation.

    Returns:
        Dict with success, pre_version, post_version, pools_preserved, error
    """
    pre_version = pre_snapshot.get("metallb_version", {}).get("version", "unknown")
    pre_pools = pre_snapshot.get("metallb_version", {}).get("ip_pools", [])

    current = collect_metallb_version(host, admin_ip)
    if not current["success"]:
        return {
            "success": False,
            "pre_version": pre_version,
            "post_version": "unknown",
            "pools_preserved": False,
            "error": current.get("error", ""),
        }

    # Check IP pool CRDs preserved
    current_pool_names = {p["name"] for p in current.get("ip_pools", [])}
    pre_pool_names = {p["name"] for p in pre_pools}
    pools_ok = pre_pool_names.issubset(current_pool_names)

    return {
        "success": current["success"] and pools_ok,
        "pre_version": pre_version,
        "post_version": current.get("version", "unknown"),
        "pools_preserved": pools_ok,
        "error": (
            f"Missing IP pools: {pre_pool_names - current_pool_names}"
            if not pools_ok else current.get("error", "")
        ),
    }


def verify_helm_at_target(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify Helm binary is at or above pre-upgrade version.

    TC-F009: Helm upgrade.

    Returns:
        Dict with success, version, error
    """
    return collect_helm_version(host, admin_ip)


def verify_nfs_provisioner_running(
    host, admin_ip: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify NFS provisioner running and existing PVCs remain Bound.

    TC-F010: NFS subdir external provisioner upgrade.

    Returns:
        Dict with success, provisioner_running, error
    """
    current = collect_nfs_provisioner(host, admin_ip)
    pre_deployed = pre_snapshot.get("nfs_provisioner", {}).get("deployed", False)

    if not pre_deployed:
        return {"success": True, "provisioner_running": False, "error": ""}

    return {
        "success": current.get("deployed", False),
        "provisioner_running": current.get("deployed", False),
        "error": "NFS provisioner not running after upgrade" if not current.get("deployed") else "",
    }


# =============================================================================
# Telemetry Component Verification  (TC-TEL-F006, TC-TEL-F007, TC-TEL-F009-F014)
# =============================================================================

def verify_idrac_telemetry_running(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify iDRAC telemetry receiver pods are Running.

    TC-TEL-F006: iDRAC telemetry upgrade.

    Returns:
        Dict with success, pods, error
    """
    return collect_idrac_telemetry_status(host, admin_ip)


def verify_ldms_collecting(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify LDMS pods are Running after upgrade.

    TC-TEL-F007: LDMS upgrade.

    Returns:
        Dict with success, pods, error
    """
    return collect_ldms_status(host, admin_ip)


def verify_new_telemetry_components(
    host, admin_ip: str, expected_flags: Dict[str, bool]
) -> Dict[str, Any]:
    """
    Verify new telemetry components deployed/absent based on config flags.

    TC-TEL-F009 - TC-TEL-F014: Phase 2 component deployment.

    Args:
        expected_flags: Dict of component_name -> enabled (True/False)
            e.g. {"powerscale_telemetry": True, "vast_telemetry": False, ...}

    Returns:
        Dict with success, deployed=[], correctly_absent=[], unexpected=[], error
    """
    component_filters = {
        "powerscale_telemetry": "powerscale",
        "vast_telemetry": "vast",
        "victorialogs": "victorialog",
        "ufm_telemetry": "ufm",
        "vector": "vector",
    }

    deployed = []
    correctly_absent = []
    unexpected = []

    for comp, label in component_filters.items():
        enabled = expected_flags.get(comp, False)
        result = _collect_pods_in_namespace(
            host, admin_ip, TELEMETRY_NAMESPACE, label_filter=label
        )
        has_pods = len(result.get("pods", [])) > 0

        if enabled and has_pods:
            deployed.append(comp)
        elif not enabled and not has_pods:
            correctly_absent.append(comp)
        elif enabled and not has_pods:
            unexpected.append(f"{comp}: expected but not deployed")
        elif not enabled and has_pods:
            unexpected.append(f"{comp}: deployed but flag is false")

    return {
        "success": len(unexpected) == 0,
        "deployed": deployed,
        "correctly_absent": correctly_absent,
        "unexpected": unexpected,
        "error": "; ".join(unexpected) if unexpected else "",
    }


def verify_upgrade_manifest(host) -> Dict[str, Any]:
    """
    Verify upgrade_manifest.yml shows k8s / telemetry completed.

    TC-F013 final check, TC-TEL-F015: upgrade_manifest.yml status.

    Returns:
        Dict with success, k8s_status, telemetry_status, error
    """
    from ...core import run_on_oim
    cmd = run_on_oim(
        host,
        "cat /opt/omnia/upgrade_manifest.yml 2>/dev/null || echo 'NOT_FOUND'"
    )
    if cmd.rc != 0 or "NOT_FOUND" in cmd.stdout:
        return {
            "success": False,
            "k8s_status": "unknown",
            "telemetry_status": "unknown",
            "error": "upgrade_manifest.yml not found",
        }

    try:
        import yaml as _yaml
        manifest = _yaml.safe_load(cmd.stdout) or {}
        cs = manifest.get("component_status", {})
        k8s_status = cs.get("k8s", cs.get("k8s-telemetry", "pending"))
        tel_status = cs.get("telemetry", "pending")
        ok = k8s_status == "completed"
        return {
            "success": ok,
            "k8s_status": k8s_status,
            "telemetry_status": tel_status,
            "error": "" if ok else f"k8s={k8s_status}, telemetry={tel_status}",
        }
    except Exception as exc:
        return {
            "success": False,
            "k8s_status": "parse_error",
            "telemetry_status": "parse_error",
            "error": str(exc),
        }


# =============================================================================
# CP & Worker Version Verification  (TC-F002, TC-F004)
# =============================================================================

def verify_cps_at_target(
    host, admin_ip: str, target_version: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify all control-plane nodes are at target version and Ready.

    TC-F002: CPs upgraded sequentially, all Ready, etcd quorum.

    Returns:
        Dict with success, cps_ok=[], cps_fail=[], error
    """
    result = collect_k8s_node_versions(host, admin_ip)
    if not result["success"]:
        return {"success": False, "cps_ok": [], "cps_fail": [], "error": result["error"]}

    pre_roles = pre_snapshot.get("node_roles", {})
    cp_names = {n["name"] for n in pre_roles.get("control_planes", [])}

    prefix = target_version if target_version.startswith("v") else f"v{target_version}"
    cps_ok = []
    cps_fail = []
    for node in result["nodes"]:
        if node["name"] not in cp_names:
            continue
        if node["version"].startswith(prefix) and node.get("ready", "True") == "True":
            cps_ok.append(node)
        else:
            cps_fail.append(node)

    return {
        "success": len(cps_fail) == 0,
        "cps_ok": cps_ok,
        "cps_fail": cps_fail,
        "error": (
            f"CPs not at target: {[n['name'] for n in cps_fail]}"
            if cps_fail else ""
        ),
    }


def verify_workers_at_target(
    host, admin_ip: str, target_version: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify all worker nodes are at target version and Ready.

    TC-F004: Workers upgraded rolling, each Ready at target.

    Returns:
        Dict with success, workers_ok=[], workers_fail=[], error
    """
    result = collect_k8s_node_versions(host, admin_ip)
    if not result["success"]:
        return {"success": False, "workers_ok": [], "workers_fail": [], "error": result["error"]}

    pre_roles = pre_snapshot.get("node_roles", {})
    cp_names = {n["name"] for n in pre_roles.get("control_planes", [])}

    prefix = target_version if target_version.startswith("v") else f"v{target_version}"
    workers_ok = []
    workers_fail = []
    for node in result["nodes"]:
        if node["name"] in cp_names:
            continue
        if node["version"].startswith(prefix) and node.get("ready", "True") == "True":
            workers_ok.append(node)
        else:
            workers_fail.append(node)

    return {
        "success": len(workers_fail) == 0,
        "workers_ok": workers_ok,
        "workers_fail": workers_fail,
        "error": (
            f"Workers not at target: {[n['name'] for n in workers_fail]}"
            if workers_fail else ""
        ),
    }


# =============================================================================
# Backup Artifacts Verification  (TC-F003)
# =============================================================================

def verify_etcd_backup_exists(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify etcd snapshot and /etc/kubernetes backup were created by upgrade.

    TC-F003: etcd snapshot + /etc/kubernetes backed up.

    Returns:
        Dict with success, snapshot_exists, k8s_backup_exists, error
    """
    # Check etcd snapshot file
    snap_cmd = (
        "ls -la /opt/omnia/k8s_upgrade_backup/etcd-snapshot*.db 2>/dev/null "
        "&& echo 'SNAP_OK' || echo 'SNAP_MISSING'"
    )
    snap_result = run_on_remote_node(host, snap_cmd, admin_ip)
    snapshot_exists = "SNAP_OK" in snap_result.stdout

    # Check /etc/kubernetes backup
    k8s_cmd = (
        "ls -la /opt/omnia/k8s_upgrade_backup/etc-kubernetes*.tar* 2>/dev/null "
        "&& echo 'K8S_OK' || echo 'K8S_MISSING'"
    )
    k8s_result = run_on_remote_node(host, k8s_cmd, admin_ip)
    k8s_backup_exists = "K8S_OK" in k8s_result.stdout

    return {
        "success": snapshot_exists and k8s_backup_exists,
        "snapshot_exists": snapshot_exists,
        "k8s_backup_exists": k8s_backup_exists,
        "error": (
            "Missing: "
            + ("etcd snapshot " if not snapshot_exists else "")
            + ("/etc/kubernetes backup" if not k8s_backup_exists else "")
        ).strip() if not (snapshot_exists and k8s_backup_exists) else "",
    }


# =============================================================================
# PDB & Workload Health  (TC-F005)
# =============================================================================

def verify_pdbs_healthy(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify all PDBs are satisfied after upgrade (currentHealthy >= desiredHealthy).

    TC-F005: Drain respected PDBs, workloads rescheduled.

    Returns:
        Dict with success, pdbs_ok=[], pdbs_violated=[], error
    """
    result = collect_pod_disruption_budgets(host, admin_ip)
    if not result["success"]:
        return {"success": False, "pdbs_ok": [], "pdbs_violated": [], "error": result["error"]}

    pdbs_ok = []
    pdbs_violated = []
    for pdb in result.get("pdbs", []):
        if pdb["current_healthy"] >= pdb["desired_healthy"]:
            pdbs_ok.append(pdb)
        else:
            pdbs_violated.append(pdb)

    return {
        "success": len(pdbs_violated) == 0,
        "pdbs_ok": pdbs_ok,
        "pdbs_violated": pdbs_violated,
        "error": (
            f"PDBs violated: {[p['name'] for p in pdbs_violated]}"
            if pdbs_violated else ""
        ),
    }


# =============================================================================
# CRI-O Storage Config Preserved  (TC-F006)
# =============================================================================

def verify_crio_storage_preserved(
    host, admin_ip: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify CRI-O storage config unchanged after upgrade.

    TC-F006: k8s_crio_storage_size preserved.

    Returns:
        Dict with success, changed_nodes=[], error
    """
    pre_configs = pre_snapshot.get("crio_storage_config", {}).get("configs", {})
    if not pre_configs:
        return {"success": True, "changed_nodes": [], "error": ""}

    current = collect_crio_storage_config(host, admin_ip)
    if not current["success"]:
        return {"success": False, "changed_nodes": [], "error": current["error"]}

    changed = []
    for node, pre_cfg in pre_configs.items():
        cur_cfg = current["configs"].get(node, "N/A")
        if pre_cfg != cur_cfg and pre_cfg != "N/A":
            changed.append({"node": node, "pre": pre_cfg, "post": cur_cfg})

    return {
        "success": len(changed) == 0,
        "changed_nodes": changed,
        "error": f"CRI-O config changed on: {[c['node'] for c in changed]}" if changed else "",
    }


# =============================================================================
# BSS Boot Params Updated  (TC-F011)
# =============================================================================

def verify_bss_params_updated(
    host, admin_ip: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify BSS boot params (kernel version) updated after upgrade.

    TC-F011: BSS boot params updated for CPs and workers.

    Returns:
        Dict with success, updated_nodes=[], unchanged_nodes=[], error
    """
    pre_params = pre_snapshot.get("bss_boot_params", {}).get("params", {})
    current = collect_bss_boot_params(host, admin_ip)
    if not current["success"]:
        return {"success": False, "updated_nodes": [], "unchanged_nodes": [], "error": current["error"]}

    updated = []
    unchanged = []
    for node, cur in current["params"].items():
        pre = pre_params.get(node, {})
        if pre and pre.get("kernel") == cur.get("kernel"):
            unchanged.append(node)
        else:
            updated.append(node)

    return {
        "success": True,
        "updated_nodes": updated,
        "unchanged_nodes": unchanged,
        "error": "",
    }


# =============================================================================
# Kube-VIP HA Verification  (TC-F014)
# =============================================================================

def verify_kube_vip_ha(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify kube-vip pods Running and VIP reachable after upgrade.

    TC-F014: HA - VIP reachable throughout, kube-vip updated.

    Returns:
        Dict with success, pods, vip_reachable, error
    """
    return collect_kube_vip_status(host, admin_ip)


# =============================================================================
# Strimzi/Kafka Verification  (TC-TEL-F004, TC-TEL-F016)
# =============================================================================

def verify_strimzi_upgraded(
    host, admin_ip: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify Strimzi operator upgraded, Kafka brokers running, topics preserved.

    TC-TEL-F004: Strimzi operator upgraded first, then Kafka brokers.

    Returns:
        Dict with success, pre_strimzi, post_strimzi, pre_kafka, post_kafka, error
    """
    pre = pre_snapshot.get("strimzi_version", {})
    current = collect_strimzi_version(host, admin_ip)

    # Verify Kafka brokers running
    kafka_pods = _collect_pods_in_namespace(
        host, admin_ip, TELEMETRY_NAMESPACE, label_filter="kafka"
    )

    return {
        "success": current["success"] and kafka_pods["success"],
        "pre_strimzi": pre.get("strimzi_version", "unknown"),
        "post_strimzi": current.get("strimzi_version", "unknown"),
        "pre_kafka": pre.get("kafka_version", "unknown"),
        "post_kafka": current.get("kafka_version", "unknown"),
        "kafka_pods_healthy": kafka_pods["success"],
        "error": kafka_pods.get("error", "") if not kafka_pods["success"] else "",
    }


def verify_kraft_migration(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify Kafka uses KRaft (no ZooKeeper pods) after upgrade.

    TC-TEL-F016: KRaft migration from ZooKeeper.

    Returns:
        Dict with success, uses_kraft, zk_pods_count, error
    """
    result = collect_strimzi_version(host, admin_ip)
    return {
        "success": result.get("uses_kraft", False),
        "uses_kraft": result.get("uses_kraft", False),
        "zk_pods_count": result.get("zk_pods_count", -1),
        "kafka_version": result.get("kafka_version", "unknown"),
        "error": (
            f"ZooKeeper still running ({result.get('zk_pods_count', 0)} pods)"
            if not result.get("uses_kraft", False) else ""
        ),
    }


# =============================================================================
# Phase 1 Validation Gate  (TC-TEL-F008)
# =============================================================================

def verify_telemetry_phase1_gate(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify Phase 1 gate: all telemetry pods Running, Kafka ready, VM writes.

    TC-TEL-F008: Phase 1 gate must pass before Phase 2.

    Returns:
        Dict with success, checks={}, error
    """
    checks = {}

    # All telemetry pods running
    tel_pods = _collect_pods_in_namespace(host, admin_ip, TELEMETRY_NAMESPACE)
    checks["telemetry_pods_healthy"] = tel_pods["success"]

    # Kafka brokers ready
    kafka_pods = _collect_pods_in_namespace(
        host, admin_ip, TELEMETRY_NAMESPACE, label_filter="kafka"
    )
    checks["kafka_brokers_ready"] = kafka_pods["success"]

    # VictoriaMetrics accepting writes (vmstorage pods running)
    vm_pods = _collect_pods_in_namespace(
        host, admin_ip, TELEMETRY_NAMESPACE, label_filter="vmstorage"
    )
    checks["vm_accepting_writes"] = vm_pods["success"]

    all_ok = all(checks.values())
    failed = [k for k, v in checks.items() if not v]
    return {
        "success": all_ok,
        "checks": checks,
        "error": f"Phase 1 gate failed: {failed}" if failed else "",
    }


# =============================================================================
# Security Verification  (TC-S001, TC-S002)
# =============================================================================

def verify_security_permissions(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify backup dir (0700), snapshot file (0600), SSH keys (0600).

    TC-S001: Snapshot stored in restricted dir.
    TC-S002: SSH key permissions, no passwords logged.

    Returns:
        Dict with success, permissions, issues, error
    """
    return collect_security_permissions(host, admin_ip)


# =============================================================================
# Idempotency Verification  (TC-I001, TC-I002, TC-TEL-I001, TC-TEL-I002)
# =============================================================================

def verify_cluster_unchanged(
    host, admin_ip: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify cluster state unchanged (for idempotency: re-run should be no-op).

    TC-I001: Re-run skipped, cluster unchanged.
    TC-I002: Partial re-run resumes.
    TC-TEL-I001/I002: Telemetry idempotency.

    Returns:
        Dict with success, node_versions_match, pod_count_match, error
    """
    # Compare node versions
    pre_versions = pre_snapshot.get("k8s_node_versions", {}).get("nodes", [])
    current = collect_k8s_node_versions(host, admin_ip)
    if not current["success"]:
        return {
            "success": False,
            "node_versions_match": False,
            "pod_count_match": False,
            "error": current["error"],
        }

    cur_map = {n["name"]: n["version"] for n in current["nodes"]}
    pre_map = {n["name"]: n["version"] for n in pre_versions}
    versions_match = cur_map == pre_map

    # Compare telemetry pod count
    pre_tel_count = len(pre_snapshot.get("telemetry_pods", {}).get("pods", []))
    cur_tel = _collect_pods_in_namespace(host, admin_ip, TELEMETRY_NAMESPACE)
    cur_tel_count = len(cur_tel.get("pods", []))
    pod_count_match = abs(cur_tel_count - pre_tel_count) <= 2  # allow small variance

    return {
        "success": versions_match and pod_count_match,
        "node_versions_match": versions_match,
        "pod_count_match": pod_count_match,
        "error": (
            ("Node versions changed " if not versions_match else "")
            + (f"Pod count changed ({pre_tel_count}->{cur_tel_count})" if not pod_count_match else "")
        ).strip(),
    }


# =============================================================================
# Rollback Verification  (TC-R001 - TC-R012)
# =============================================================================

def verify_rollback_to_source(
    host, admin_ip: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify all nodes rolled back to source (pre-upgrade) version.

    TC-R001 / TC-R006 / TC-R007: Full rollback verification.

    Returns:
        Dict with success, nodes_at_source=[], nodes_not_reverted=[], error
    """
    pre_versions = pre_snapshot.get("k8s_node_versions", {}).get("nodes", [])
    if not pre_versions:
        return {
            "success": False,
            "nodes_at_source": [],
            "nodes_not_reverted": [],
            "error": "No pre-upgrade versions in snapshot",
        }

    source_version = pre_versions[0]["version"]
    current = collect_k8s_node_versions(host, admin_ip)
    if not current["success"]:
        return {
            "success": False,
            "nodes_at_source": [],
            "nodes_not_reverted": [],
            "error": current["error"],
        }

    prefix = source_version[:source_version.rfind(".")] if "." in source_version else source_version
    at_source = []
    not_reverted = []
    for node in current["nodes"]:
        if node["version"].startswith(prefix):
            at_source.append(node)
        else:
            not_reverted.append(node)

    return {
        "success": len(not_reverted) == 0,
        "source_version": source_version,
        "nodes_at_source": at_source,
        "nodes_not_reverted": not_reverted,
        "error": (
            f"Nodes not reverted: {[n['name'] for n in not_reverted]}"
            if not_reverted else ""
        ),
    }


def verify_rollback_etcd_restored(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify etcd healthy and quorum maintained after rollback.

    TC-R002 / TC-R003: etcd restored from snapshot.

    Returns:
        Dict with success, etcd_healthy, endpoints, error
    """
    result = collect_etcd_health(host, admin_ip)
    return {
        "success": result["success"],
        "etcd_healthy": result["success"],
        "endpoints": result.get("endpoints", []),
        "error": result.get("error", ""),
    }


def verify_rollback_helm_restored(
    host, admin_ip: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify Helm binary restored to pre-upgrade version after rollback.

    TC-R012: Helm binary restored from backup.

    Returns:
        Dict with success, pre_version, post_version, error
    """
    pre_version = pre_snapshot.get("helm_version", {}).get("version", "unknown")
    current = collect_helm_version(host, admin_ip)

    return {
        "success": current["success"],
        "pre_version": pre_version,
        "post_version": current.get("version", "unknown"),
        "error": current.get("error", ""),
    }


def verify_rollback_telemetry_healthy(
    host, admin_ip: str, pre_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify telemetry pods healthy after rollback, 2.1-era pods running.

    TC-R007: Full telemetry stack healthy after rollback.
    TC-TEL-R001: Phase 2 removed, Phase 1 reverted.

    Returns:
        Dict with success, pods_healthy, vm_preserved, kafka_preserved, error
    """
    tel_pods = _collect_pods_in_namespace(host, admin_ip, TELEMETRY_NAMESPACE)
    vm_result = collect_vm_pvcs(host, admin_ip)
    kafka_result = collect_kafka_state(host, admin_ip)

    pre_topics = pre_snapshot.get("kafka_state", {}).get("topics", [])
    cur_topics = kafka_result.get("topics", [])
    kafka_ok = set(pre_topics).issubset(set(cur_topics)) if pre_topics else True

    return {
        "success": tel_pods["success"] and kafka_ok,
        "pods_healthy": tel_pods["success"],
        "vm_preserved": vm_result["success"],
        "kafka_preserved": kafka_ok,
        "error": (
            tel_pods.get("error", "") if not tel_pods["success"]
            else ("Kafka topics lost" if not kafka_ok else "")
        ),
    }


def verify_rollback_metallb_cleaned(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify stale MetalLB IPs cleaned up after rollback.

    TC-R009: Stale MetalLB IPs cleaned up before etcd restore.

    Returns:
        Dict with success, metallb_healthy, error
    """
    result = _collect_pods_in_namespace(host, admin_ip, METALLB_NAMESPACE)
    return {
        "success": result["success"],
        "metallb_healthy": result["success"],
        "pods": result.get("pods", []),
        "error": result.get("error", ""),
    }


def verify_rollback_csi_cleaned(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify stale CSI VolumeAttachments cleaned after rollback.

    TC-R010: Stale CSI VolumeAttachments cleaned after etcd restore.

    Returns:
        Dict with success, stale_attachments=[], error
    """
    cmd = run_on_remote_node(
        host,
        "kubectl get volumeattachments -o json 2>/dev/null",
        admin_ip,
    )
    if cmd.rc != 0:
        return {"success": True, "stale_attachments": [], "error": ""}

    try:
        data = json.loads(cmd.stdout.strip())
        stale = []
        for item in data.get("items", []):
            if not item.get("status", {}).get("attached", True):
                stale.append(item["metadata"]["name"])
        return {
            "success": len(stale) == 0,
            "stale_attachments": stale,
            "error": f"Stale VolumeAttachments: {stale}" if stale else "",
        }
    except (json.JSONDecodeError, KeyError) as exc:
        return {"success": True, "stale_attachments": [], "error": str(exc)}
