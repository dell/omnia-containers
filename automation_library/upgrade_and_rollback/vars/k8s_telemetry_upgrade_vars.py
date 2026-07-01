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
K8s & Telemetry Upgrade - Configuration Variables.

Loads upgrade-relevant settings from omnia_test_config.yml and defines
constants for namespaces, snapshot paths, and kubectl command templates.
"""

import os
from typing import Dict, Any

import yaml

from ...core import (
    OMNIA_CORE_CONTAINER as _CORE_CONTAINER,
    K8S_CONTROL_PLANE_FUNCTIONAL_GROUP as _K8S_CP_GROUP,
    K8S_WORKER_NODE_FUNCTIONAL_GROUP as _K8S_WORKER_GROUP,
)


# =============================================================================
# Configuration File Paths
# =============================================================================

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
_OMNIA_TEST_CONFIG_FILE = os.path.join(_PROJECT_ROOT, "omnia_test_config.yml")


# =============================================================================
# Configuration Loader
# =============================================================================

def _load_omnia_test_config() -> Dict[str, Any]:
    """Load user configuration from YAML file."""
    if os.path.exists(_OMNIA_TEST_CONFIG_FILE):
        try:
            with open(_OMNIA_TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except (IOError, yaml.YAMLError):
            return {}
    return {}


_omnia_test_config = _load_omnia_test_config()


# =============================================================================
# Kubernetes Namespaces
# =============================================================================

TELEMETRY_NAMESPACE = "telemetry"
KUBE_SYSTEM_NAMESPACE = "kube-system"
CALICO_NAMESPACE = "calico-system"
METALLB_NAMESPACE = "metallb-system"


# =============================================================================
# Snapshot Persistence
# =============================================================================

SNAPSHOT_PATH = _omnia_test_config.get(
    "k8s_upgrade_snapshot_path",
    "/tmp/k8s_telemetry_upgrade_precheck.json",
)


# =============================================================================
# Upgrade section from config
# =============================================================================

_upgrade_config: Dict[str, Any] = _omnia_test_config.get("upgrade", {})


# =============================================================================
# K8S UPGRADE VARIABLES
# =============================================================================

K8S_UPGRADE_VARS: Dict[str, Any] = {

    # OIM Server Connection
    "oim_server_ip": _omnia_test_config.get("oim_server_ip", ""),
    "oim_ssh_user": _omnia_test_config.get("oim_ssh_user", "root"),
    "oim_ssh_password": _omnia_test_config.get("oim_ssh_password", ""),
    "oim_ssh_port": _omnia_test_config.get("oim_ssh_port", 22),

    # Container
    "container_name": _CORE_CONTAINER,

    # K8s functional groups
    "k8s_cp_functional_group": _K8S_CP_GROUP,
    "k8s_worker_functional_group": _K8S_WORKER_GROUP,

    # Upgrade versions (from upgrade section)
    "current_version": _upgrade_config.get("current_version", ""),
    "new_version": _upgrade_config.get("new_version", ""),

    # Namespaces
    "telemetry_namespace": TELEMETRY_NAMESPACE,
    "kube_system_namespace": KUBE_SYSTEM_NAMESPACE,
    "calico_namespace": CALICO_NAMESPACE,
    "metallb_namespace": METALLB_NAMESPACE,

    # Snapshot path
    "snapshot_path": SNAPSHOT_PATH,

    # Timeouts
    "kubectl_timeout": 30,
    "etcd_timeout": 15,
}


# =============================================================================
# kubectl Command Templates
# =============================================================================

KUBECTL_CMD = {
    "get_nodes_version": "kubectl get nodes -o jsonpath="
        "'{range .items[*]}{.metadata.name}{\"\\t\"}"
        "{.status.nodeInfo.kubeletVersion}{\"\\t\"}"
        "{.status.conditions[?(@.type==\"Ready\")].status}{\"\\n\"}{end}'",
    "get_nodes_wide": "kubectl get nodes -o wide",
    "get_pods_ns": "kubectl get pods -n {ns} -o wide --no-headers",
    "get_pods_json": "kubectl get pods -n {ns} -o json",
    "get_pvcs": "kubectl get pvc -n {ns} -o json",
    "get_services_lb": "kubectl get svc -A -o json",
    "helm_list": "helm list -n {ns} -o json",
    "cluster_info": "kubectl cluster-info",
    "etcd_health": "ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 "
        "--cacert=/etc/kubernetes/pki/etcd/ca.crt "
        "--cert=/etc/kubernetes/pki/etcd/healthcheck-client.crt "
        "--key=/etc/kubernetes/pki/etcd/healthcheck-client.key "
        "endpoint health --write-out=json",
    "dns_lookup": "kubectl run dns-check --image=busybox:1.36 --restart=Never "
        "--rm -i --wait=true -- nslookup kubernetes.default.svc.cluster.local",
    "kafka_topics": "kubectl exec -n {ns} kafka-kafka-0 -- "
        "bin/kafka-topics.sh --bootstrap-server localhost:9092 --list",
}
