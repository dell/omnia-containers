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
K8s & Telemetry Upgrade - Test Messages.

Centralised strings for test names, log messages, assert messages, and skip
reasons used by both pre-check and post-check test files.
"""

from typing import Dict


# =============================================================================
# PRE-CHECK TEST NAMES
# =============================================================================

PRECHECK_TEST_NAMES: Dict[str, str] = {
    "k8s_version": "Pre-Check: K8s node versions (current: {version})",
    "node_readiness": "Pre-Check: All nodes Ready",
    "kube_system_pods": "Pre-Check: kube-system pods healthy",
    "etcd_health": "Pre-Check: etcd cluster healthy",
    "calico_status": "Pre-Check: Calico pods running",
    "metallb_status": "Pre-Check: MetalLB pods running",
    "lb_service_ips": "Pre-Check: LoadBalancer service IPs recorded",
    "helm_releases": "Pre-Check: Helm releases in telemetry namespace",
    "telemetry_pods": "Pre-Check: Telemetry pods running",
    "vm_pvcs": "Pre-Check: VictoriaMetrics PVCs Bound",
    "kafka_state": "Pre-Check: Kafka brokers healthy and topics recorded",
    "csi_status": "Pre-Check: CSI driver pods and PVCs",
    "nfs_provisioner": "Pre-Check: NFS provisioner deployed",
    "crio_version": "Pre-Check: CRI-O version (TC-F006)",
    "calico_version": "Pre-Check: Calico controller version (TC-F007)",
    "network_policies": "Pre-Check: Network policies snapshot (TC-F007)",
    "metallb_version": "Pre-Check: MetalLB version + IPAddressPool CRDs (TC-F008)",
    "helm_version": "Pre-Check: Helm binary version (TC-F009)",
    "idrac_status": "Pre-Check: iDRAC telemetry status (TC-TEL-F006)",
    "ldms_status": "Pre-Check: LDMS status (TC-TEL-F007)",
    "ssh_connectivity": "Pre-Check: SSH connectivity to all nodes (Gate 2)",
    "version_hop": "Pre-Check: Version hop validation (Gate 5 / TC-F017)",
    "etcd_backup": "Pre-Check: etcd backup readiness (TC-F003)",
    "security": "Pre-Check: Security permissions (TC-S001/S002)",
    "pulp_images": "Pre-Check: Pulp/registry images available (TC-F015 Gate 1)",
    "addon_compat": "Pre-Check: Addon version compatibility (TC-F018)",
    "bss_params": "Pre-Check: BSS boot params baseline (TC-F011)",
    "strimzi_version": "Pre-Check: Strimzi/Kafka version (TC-TEL-F004/F016)",
    "crio_storage": "Pre-Check: CRI-O storage config (TC-F006)",
    "kube_vip": "Pre-Check: kube-vip HA status (TC-F014)",
    "pdbs": "Pre-Check: PodDisruptionBudgets (TC-F005)",
    "node_roles": "Pre-Check: Node roles topology (TC-F002/F004)",
    "telemetry_preflight": "Pre-Check: Telemetry pre-flight (TC-TEL-F002)",
    "oim_status": "Pre-Check: OIM upgrade status (TC-F016)",
    "save_snapshot": "Pre-Check: Save pre-upgrade snapshot",
}


# =============================================================================
# PRE-CHECK LOG MESSAGES
# =============================================================================

PRECHECK_LOG_MSGS: Dict[str, str] = {
    "collecting_versions": "Collecting K8s versions from all nodes",
    "node_version": "  {name}: {version} (Ready={ready})",
    "collecting_readiness": "Checking all nodes are in Ready state",
    "collecting_pods": "Collecting pod status in {ns}",
    "checking_etcd": "Checking etcd endpoint health on control plane",
    "checking_calico": "Collecting Calico pod status",
    "checking_metallb": "Collecting MetalLB pod status",
    "collecting_lb_ips": "Recording LoadBalancer service external IPs",
    "lb_service": "  {namespace}/{name}: {external_ip}",
    "collecting_helm": "Collecting Helm releases in telemetry namespace",
    "helm_release": "  {name}: chart={chart} status={status}",
    "collecting_telemetry": "Collecting telemetry pod status",
    "collecting_pvcs": "Collecting VictoriaMetrics PVCs",
    "pvc_entry": "  {name}: {phase} ({capacity})",
    "collecting_kafka": "Collecting Kafka broker state and topics",
    "kafka_topic": "  topic: {topic}",
    "collecting_csi": "Collecting CSI driver pod and PVC status",
    "collecting_nfs": "Checking NFS provisioner deployment",
    "saving_snapshot": "Saving pre-upgrade snapshot to {path}",
    "snapshot_saved": "Snapshot saved ({count} keys)",
    "admin_ip_found": "Admin IP: {ip}",
}


# =============================================================================
# PRE-CHECK ASSERT MESSAGES
# =============================================================================

PRECHECK_ASSERT_MSGS: Dict[str, str] = {
    "version_mismatch": (
        "Node {name} is at {actual}, expected {expected}.\n\n"
        "HOW TO FIX:\n"
        "  1. Run: kubectl get nodes -o wide\n"
        "  2. Verify all nodes are at the expected version\n"
        "  3. Resolve version inconsistencies before upgrade"
    ),
    "nodes_not_ready": (
        "Not all nodes are Ready. NotReady nodes: {nodes}\n\n"
        "HOW TO FIX:\n"
        "  1. Run: kubectl get nodes\n"
        "  2. Check: kubectl describe node <name>\n"
        "  3. Fix NotReady nodes before attempting upgrade"
    ),
    "pods_not_running": (
        "Unhealthy pods in {ns}: {pods}\n\n"
        "HOW TO FIX:\n"
        "  1. Run: kubectl get pods -n {ns}\n"
        "  2. Check: kubectl describe pod <pod> -n {ns}\n"
        "  3. Ensure all pods are Running before upgrade"
    ),
    "etcd_unhealthy": (
        "etcd cluster is not healthy: {error}\n\n"
        "HOW TO FIX:\n"
        "  1. SSH to CP node and run etcdctl endpoint health\n"
        "  2. Check etcd logs: journalctl -u etcd\n"
        "  3. Ensure etcd quorum before upgrade"
    ),
    "snapshot_save_failed": (
        "Failed to save pre-upgrade snapshot: {error}\n\n"
        "HOW TO FIX:\n"
        "  1. Check disk space on OIM server\n"
        "  2. Verify write permission to {path}"
    ),
    "admin_ip_not_found": (
        "Failed to get admin IP from PXE mapping file.\n\n"
        "HOW TO FIX:\n"
        "  1. Check provision_config.yml for pxe_mapping_file_path\n"
        "  2. Ensure the PXE mapping file exists and contains K8s CP entries"
    ),
}


# =============================================================================
# POST-CHECK TEST NAMES
# =============================================================================

POSTCHECK_TEST_NAMES: Dict[str, str] = {
    "load_snapshot": "Post-Check: Load pre-upgrade snapshot",
    "k8s_target_version": "Post-Check: All nodes at target K8s {version}",
    "node_readiness": "Post-Check: All nodes Ready",
    "kube_system_pods": "Post-Check: kube-system pods healthy",
    "etcd_health": "Post-Check: etcd cluster healthy",
    "api_server": "Post-Check: API server reachable via cluster-info",
    "dns_resolution": "Post-Check: DNS resolution working in cluster",
    "calico_healthy": "Post-Check: Calico pods running",
    "metallb_ips": "Post-Check: MetalLB LB IPs preserved",
    "telemetry_pods": "Post-Check: Telemetry pods running after upgrade",
    "vm_pvcs": "Post-Check: VictoriaMetrics PVCs preserved (TC-TEL-R002)",
    "vm_data": "Post-Check: VictoriaMetrics historical data accessible",
    "kafka_topics": "Post-Check: Kafka topics preserved (TC-TEL-R003)",
    "csi_pvcs": "Post-Check: CSI PVCs remain Bound (TC-F019)",
    "helm_releases": "Post-Check: Helm releases present after upgrade",
    "crio_version": "Post-Check: CRI-O at target version (TC-F006)",
    "calico_version": "Post-Check: Calico version upgraded (TC-F007)",
    "network_policies": "Post-Check: Network policies preserved (TC-F007)",
    "metallb_version": "Post-Check: MetalLB version + IP pools (TC-F008)",
    "helm_version": "Post-Check: Helm binary version (TC-F009)",
    "nfs_provisioner": "Post-Check: NFS provisioner running (TC-F010)",
    "idrac_telemetry": "Post-Check: iDRAC telemetry running (TC-TEL-F006)",
    "ldms_status": "Post-Check: LDMS collecting (TC-TEL-F007)",
    "upgrade_manifest": "Post-Check: upgrade_manifest.yml status (TC-F013)",
    "cps_at_target": "Post-Check: CPs at target version (TC-F002)",
    "workers_at_target": "Post-Check: Workers at target version (TC-F004)",
    "etcd_backup": "Post-Check: etcd backup artifacts exist (TC-F003)",
    "pdbs_healthy": "Post-Check: PDBs satisfied after upgrade (TC-F005)",
    "crio_storage": "Post-Check: CRI-O storage config preserved (TC-F006)",
    "bss_params": "Post-Check: BSS boot params updated (TC-F011)",
    "kube_vip_ha": "Post-Check: kube-vip HA / VIP reachable (TC-F014)",
    "strimzi_upgraded": "Post-Check: Strimzi/Kafka upgraded (TC-TEL-F004)",
    "kraft_migration": "Post-Check: KRaft migration (TC-TEL-F016)",
    "phase1_gate": "Post-Check: Telemetry Phase 1 gate (TC-TEL-F008)",
    "security": "Post-Check: Security permissions (TC-S001/S002)",
    "idempotency": "Post-Check: Cluster idempotency (TC-I001/I002)",
    "rollback_source": "Post-Rollback: Nodes at source version (TC-R001)",
    "rollback_etcd": "Post-Rollback: etcd restored (TC-R002/R003)",
    "rollback_helm": "Post-Rollback: Helm restored (TC-R012)",
    "rollback_telemetry": "Post-Rollback: Telemetry healthy (TC-R007/TEL-R001)",
    "rollback_metallb": "Post-Rollback: MetalLB cleaned (TC-R009)",
    "rollback_csi": "Post-Rollback: CSI VolumeAttachments cleaned (TC-R010)",
}


# =============================================================================
# POST-CHECK LOG MESSAGES
# =============================================================================

POSTCHECK_LOG_MSGS: Dict[str, str] = {
    "loading_snapshot": "Loading pre-upgrade snapshot from {path}",
    "snapshot_loaded": "Snapshot loaded ({count} keys, saved at {ts})",
    "checking_version": "Verifying all nodes at target version {version}",
    "version_ok": "  {name}: {version} OK",
    "version_fail": "  {name}: {actual} (expected {expected})",
    "checking_readiness": "Verifying all nodes are Ready",
    "checking_pods": "Verifying pods in {ns}",
    "checking_etcd": "Verifying etcd health post-upgrade",
    "checking_api": "Verifying API server reachable",
    "checking_dns": "Verifying DNS resolution in cluster",
    "checking_calico": "Verifying Calico pods healthy",
    "comparing_lb_ips": "Comparing LB service IPs with pre-upgrade snapshot",
    "ip_preserved": "  {namespace}/{name}: {ip} (preserved)",
    "ip_changed": "  {namespace}/{name}: was {old}, now {new}",
    "ip_missing": "  {namespace}/{name}: was {old}, now MISSING",
    "checking_telemetry": "Verifying telemetry pods post-upgrade",
    "checking_vm_pvcs": "Verifying VictoriaMetrics PVCs preserved",
    "checking_vm_data": "Querying VictoriaMetrics for historical data",
    "checking_kafka": "Verifying Kafka topics preserved",
    "topic_ok": "  topic: {topic} (preserved)",
    "topic_missing": "  topic: {topic} (MISSING)",
    "checking_csi": "Verifying CSI PVCs remain Bound",
    "checking_helm": "Verifying Helm releases present",
}


# =============================================================================
# POST-CHECK ASSERT MESSAGES
# =============================================================================

POSTCHECK_ASSERT_MSGS: Dict[str, str] = {
    "snapshot_not_found": (
        "Pre-upgrade snapshot not found at {path}.\n\n"
        "HOW TO FIX:\n"
        "  1. Run the Pre_check/K8s_telemetry scenario first\n"
        "  2. Ensure snapshot was saved before running the upgrade\n"
        "  3. Check k8s_upgrade_snapshot_path in omnia_test_config.yml"
    ),
    "snapshot_load_failed": (
        "Failed to load pre-upgrade snapshot: {error}\n\n"
        "HOW TO FIX:\n"
        "  1. Check that {path} is valid JSON\n"
        "  2. Re-run Pre_check/K8s_telemetry to regenerate"
    ),
    "version_mismatch": (
        "Nodes not at target version {expected}: {nodes}\n\n"
        "HOW TO FIX:\n"
        "  1. Run: kubectl get nodes -o wide\n"
        "  2. Check upgrade logs for failed nodes\n"
        "  3. Re-run upgrade.yml --tags k8s if needed"
    ),
    "nodes_not_ready": (
        "NotReady nodes after upgrade: {nodes}\n\n"
        "HOW TO FIX:\n"
        "  1. Run: kubectl describe node <name>\n"
        "  2. Check kubelet: journalctl -u kubelet on the node\n"
        "  3. Verify kubelet was restarted after upgrade"
    ),
    "pods_not_running": (
        "Unhealthy pods in {ns} after upgrade: {pods}\n\n"
        "HOW TO FIX:\n"
        "  1. Run: kubectl get pods -n {ns}\n"
        "  2. kubectl describe pod <pod> -n {ns}\n"
        "  3. kubectl logs <pod> -n {ns}"
    ),
    "etcd_unhealthy": (
        "etcd unhealthy after upgrade: {error}\n\n"
        "HOW TO FIX:\n"
        "  1. SSH to each CP and check etcd: etcdctl endpoint health\n"
        "  2. Verify etcd quorum: etcdctl member list"
    ),
    "api_unreachable": (
        "API server unreachable after upgrade.\n\n"
        "HOW TO FIX:\n"
        "  1. Run: kubectl cluster-info\n"
        "  2. Check kube-apiserver pod in kube-system\n"
        "  3. Check kube-vip if using HA"
    ),
    "dns_failed": (
        "DNS resolution failed inside cluster.\n\n"
        "HOW TO FIX:\n"
        "  1. Check CoreDNS pods: kubectl get pods -n kube-system -l k8s-app=kube-dns\n"
        "  2. Run: kubectl logs -n kube-system -l k8s-app=kube-dns"
    ),
    "lb_ips_changed": (
        "LoadBalancer IPs changed after upgrade:\n{details}\n\n"
        "HOW TO FIX:\n"
        "  1. Check MetalLB speaker pods\n"
        "  2. Reassign IPs via MetalLB CRDs if needed"
    ),
    "vm_pvcs_lost": (
        "VictoriaMetrics PVCs not preserved after upgrade:\n{details}\n\n"
        "HOW TO FIX:\n"
        "  1. Run: kubectl get pvc -n telemetry\n"
        "  2. Check PV reclaim policy"
    ),
    "vm_data_lost": (
        "VictoriaMetrics historical data not accessible: {error}\n\n"
        "HOW TO FIX:\n"
        "  1. Verify vmstorage pods are Running\n"
        "  2. Check PVCs are Bound\n"
        "  3. Query: curl http://vmselect:8481/select/0/prometheus/api/v1/query?query=up"
    ),
    "kafka_topics_missing": (
        "Kafka topics lost after upgrade: {topics}\n\n"
        "HOW TO FIX:\n"
        "  1. Check Kafka broker pods: kubectl get pods -n telemetry\n"
        "  2. Verify Strimzi Cluster Operator"
    ),
    "csi_pvcs_lost": (
        "CSI PVCs not Bound after upgrade: {details}\n\n"
        "HOW TO FIX:\n"
        "  1. kubectl get pvc -A\n"
        "  2. kubectl describe pvc <name> -n <ns>\n"
        "  3. Check CSI driver DaemonSet"
    ),
    "helm_releases_missing": (
        "Helm releases missing after upgrade: {releases}\n\n"
        "HOW TO FIX:\n"
        "  1. Run: helm list -n telemetry\n"
        "  2. Re-deploy missing releases"
    ),
}


# =============================================================================
# SKIP MESSAGES
# =============================================================================

SKIP_MSGS: Dict[str, str] = {
    "snapshot_not_found": (
        "Pre-upgrade snapshot not found at {path} — "
        "run Pre_check/K8s_telemetry first"
    ),
    "no_lb_services": "No LoadBalancer services found in pre-upgrade snapshot",
    "no_kafka_topics": "No Kafka topics found in pre-upgrade snapshot",
    "no_csi_pvcs": "No CSI PVCs found in pre-upgrade snapshot",
    "no_vm_pvcs": "No VictoriaMetrics PVCs found in pre-upgrade snapshot",
    "kafka_not_deployed": "Kafka not deployed in telemetry namespace",
    "csi_not_deployed": "No CSI driver detected",
    "vm_not_deployed": "VictoriaMetrics not deployed",
    "upgrade_not_configured": (
        "upgrade section not configured in omnia_test_config.yml"
    ),
}
