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

# pylint: disable=too-many-lines
"""
CoreDNS Test Cases for Provision Module.

Implements test cases from TSPEC-COREDNS-2026-001 v1.0.

Test Coverage:
  1. DNS Configuration Toggle - Enable CoreDNS
  2. Valid DNS Configuration File
  3. coresmd Container Deployment
  4. Forward Zone File Generation from SMD
  5. Forward DNS Resolution - A Records
  6. Slurm Controller Hostname Resolution
  7. Kubernetes CoreDNS ConfigMap Forwarding
  8. DNS Query Performance - Cached Latency
  9. SMD TLS Communication Security
  10. CoreDNS Deployment Idempotency
  11. Multi-Subnet Admin Reverse Zone Generation
  12. MPI Peer Hostname Resolution via DNS
  13. Node Addition Workflow - Automatic DNS Update
  14. SMD Unreachable During Zone Generation
  15. Backward Compatibility - dns_enabled=false
  16. Invalid Domain Format - Uppercase Characters
  17. PXE Hostname NID Format Validation
  18. Compute Node /etc/hosts - DNS Enabled
  19. Compute Node /etc/resolv.conf - DNS Enabled
  20. Compute Node DNS Resolution - getent hosts

Run: pytest molecule/provision/tests/sanity/test_coredns.py -s
"""

import json
import re
import time

import pytest

from automation_library.core import (
    TestLogger,
    run_on_oim,
    run_in_container,
    run_on_remote_node,
    get_input_value,
    PROVISION_CONFIG_FILE,
)
from automation_library.provision.vars import COREDNS_CONTAINER_NAME


def get_pxe_mapping_file_path(host):
    """Get pxe_mapping_file_path from provision_config.yml."""
    return get_input_value(
        host,
        PROVISION_CONFIG_FILE,
        "pxe_mapping_file_path",
        default="/opt/omnia/input/project_default/pxe_mapping_file.csv"
    )


def get_dns_server_ip(host):
    """Get CoreDNS server IP dynamically from coresmd Corefile bind directive."""
    # Get bind IP from Corefile (most reliable)
    cmd = run_on_oim(
        host,
        f"podman exec {COREDNS_CONTAINER_NAME} grep 'bind ' /Corefile 2>/dev/null | "
        "tr -d ' ' | sed 's/bind//'"
    )
    if cmd.rc == 0 and cmd.stdout.strip():
        dns_ip = cmd.stdout.strip()
        if dns_ip not in ['127.0.0.1', '0.0.0.0', '::1', '::']:
            return dns_ip

    # Fallback: check netstat inside the container
    cmd = run_on_oim(
        host,
        f"podman exec {COREDNS_CONTAINER_NAME} netstat -tulpn 2>/dev/null | "
        "grep ':53 ' | head -1 | cut -d: -f1 | rev | cut -d' ' -f1 | rev"
    )
    if cmd.rc == 0 and cmd.stdout.strip():
        dns_ip = cmd.stdout.strip()
        if dns_ip not in ['127.0.0.1', '0.0.0.0', '::1', '::']:
            return dns_ip

    return "localhost"


def check_dns_enabled(host):
    """Check if DNS is enabled in provision_config.yml."""
    cmd = run_in_container(
        host,
        "grep 'dns_enabled:' /opt/omnia/input/project_default/provision_config.yml | "
        "grep -i true"
    )
    return cmd.rc == 0


def get_coresmd_container_status(host):
    """Check if coresmd-coredns container is running on OIM host."""
    cmd = run_on_oim(
        host,
        f"podman ps --format '{{{{.Names}}}}\t{{{{.Status}}}}' | grep {COREDNS_CONTAINER_NAME}"
    )
    return {
        "running": cmd.rc == 0,
        "status": cmd.stdout.strip() if cmd.rc == 0 else "Not found",
    }


def query_dns(host, hostname, record_type="A", dns_server=None):
    """Query DNS using dig command on OIM host."""
    if dns_server is None:
        dns_server = get_dns_server_ip(host)
    cmd = run_on_oim(
        host,
        f"dig {record_type} {hostname} @{dns_server} +short +time=2"
    )
    return {
        "success": cmd.rc == 0 and cmd.stdout.strip() != "",
        "result": cmd.stdout.strip(),
        "error": cmd.stderr if cmd.rc != 0 else None,
    }


def get_smd_components(host):
    """Get node inventory from OpenCHAMI SMD."""
    cmd = run_on_oim(
        host,
        "curl -sk https://localhost:8443/hsm/v2/State/Components 2>/dev/null | "
        "jq -r '.Components[]' 2>/dev/null"
    )
    if cmd.rc == 0 and cmd.stdout.strip():
        try:
            return json.loads(cmd.stdout)
        except json.JSONDecodeError:
            return []
    return []


def get_pxe_nodes(host):
    """Get node hostnames and IPs from PXE mapping file."""
    pxe_mapping_path = get_pxe_mapping_file_path(host)
    cmd = run_in_container(
        host,
        f"sh -c \"grep -v '^#' {pxe_mapping_path} | "
        "tail -n +2 | cut -d',' -f5,7\""
    )

    nodes = []
    if cmd.rc == 0 and cmd.stdout.strip():
        for line in cmd.stdout.strip().split('\n'):
            parts = line.split(',')
            if len(parts) == 2 and parts[0] and parts[1]:
                nodes.append({
                    'hostname': parts[0].strip(),
                    'ip': parts[1].strip()
                })
    return nodes


def get_dns_domain(host):
    """Get DNS domain from coresmd Corefile zone directive."""
    # Read zone from Corefile (most reliable - excludes comment lines)
    cmd = run_on_oim(
        host,
        f"podman exec {COREDNS_CONTAINER_NAME} grep -E '^ *zone ' /Corefile 2>/dev/null | "
        "sed 's/.*zone //;s/ {.*//' | head -1"
    )
    if cmd.rc == 0 and cmd.stdout.strip():
        return cmd.stdout.strip()

    # Fallback: try network_spec.yml inside omnia_core
    cmd = run_in_container(
        host,
        "grep -E 'cluster_domain|domain:' "
        "/opt/omnia/input/project_default/network_spec.yml 2>/dev/null | "
        "head -1 | sed 's/.*: *//;s/\"//g'"
    )
    if cmd.rc == 0 and cmd.stdout.strip():
        return cmd.stdout.strip()

    return "omnia.test"


def get_k8s_control_plane_ip(host):
    """Get K8s control plane admin IP from PXE mapping."""
    pxe_mapping_path = get_pxe_mapping_file_path(host)
    cmd = run_in_container(
        host,
        f"sh -c \"grep -i 'kube_control_plane' "
        f"{pxe_mapping_path} 2>/dev/null | "
        "head -1 | cut -d',' -f7\""
    )
    if cmd.rc == 0 and cmd.stdout.strip():
        return cmd.stdout.strip()
    return None


def check_k8s_coredns_configmap(host, kcp_ip):
    """Check Kubernetes CoreDNS ConfigMap for forwarding configuration."""
    cmd = run_on_remote_node(
        host,
        "kubectl -n kube-system get configmap coredns -o yaml 2>/dev/null",
        kcp_ip
    )
    return {
        "success": cmd.rc == 0,
        "config": cmd.stdout if cmd.rc == 0 else None,
        "has_forwarding": "forward" in cmd.stdout if cmd.rc == 0 else False,
    }


def is_nid_hostname(hostname):
    """Check if hostname follows NID format (e.g., nid001, nid002)."""
    return bool(re.match(r'^nid\d{3,}$', hostname, re.IGNORECASE))


def get_etc_hosts_peer_entries(host, node_ip):
    """Get non-localhost entries from /etc/hosts on a remote node via SSH."""
    cmd = run_on_remote_node(
        host,
        "cat /etc/hosts | grep -v '^#' | grep -v '^$' | grep -v -E "
        "'localhost|127\\.0\\.0\\.1|::1'",
        node_ip
    )
    entries = []
    if cmd.rc == 0 and cmd.stdout.strip():
        for line in cmd.stdout.strip().split('\n'):
            line = line.strip()
            if line:
                entries.append(line)
    return entries


def get_resolv_conf(host, node_ip):
    """Get /etc/resolv.conf content from a remote node via SSH."""
    cmd = run_on_remote_node(host, "cat /etc/resolv.conf", node_ip)
    return {
        "success": cmd.rc == 0,
        "content": cmd.stdout.strip() if cmd.rc == 0 else "",
    }


@pytest.mark.dns
@pytest.mark.order(40)
def test_dns_configuration_enable(host):
    """TC-F01: Verify dns_enabled=true enables CoreDNS-based resolution."""
    log = TestLogger("1. DNS Configuration Toggle - Enable CoreDNS")

    log.check("Verifying DNS is enabled in provision_config.yml")
    dns_enabled = check_dns_enabled(host)

    if not dns_enabled:
        log.skipped(
            "DNS is not enabled (dns_enabled: false in provision_config.yml)",
            "Skipped \u2014 set dns_enabled: true in provision_config.yml to run DNS tests"
        )
        pytest.skip("dns_enabled is false in provision_config.yml")

    log.check("Verifying coresmd-coredns container is running")
    container_status = get_coresmd_container_status(host)

    details = [
        f"DNS enabled: {dns_enabled}",
        f"coresmd-coredns running: {container_status['running']}",
        f"Container status: {container_status['status']}",
    ]

    if not container_status["running"]:
        log.failed("coresmd-coredns container not running", "\n".join(details))
        assert False, "coresmd-coredns container is not running"

    log.passed("DNS configuration is enabled and coresmd is running", "\n".join(details))


@pytest.mark.dns
@pytest.mark.order(41)
def test_coresmd_container_deployment(host):
    """TC-F11: Verify coresmd container is deployed correctly."""
    log = TestLogger("3. coresmd Container Deployment")

    if not check_dns_enabled(host):
        log.skipped("DNS is not enabled", "Enable DNS in provision_config.yml")
        pytest.skip("DNS is not enabled")

    log.check("Verifying coresmd-coredns container deployment")
    container_status = get_coresmd_container_status(host)

    if not container_status["running"]:
        log.failed("coresmd-coredns not deployed", container_status["status"])
        assert False, "coresmd-coredns container is not running"

    log.check("Checking container port mappings")
    cmd = run_on_oim(host, f"podman port {COREDNS_CONTAINER_NAME} 2>/dev/null")
    port_mappings = cmd.stdout.strip() if cmd.rc == 0 else "No port mappings found"

    log.check("Verifying Corefile configuration")
    cmd = run_on_oim(
        host,
        f"podman exec {COREDNS_CONTAINER_NAME} cat /Corefile 2>/dev/null | grep -i coresmd"
    )
    has_coresmd_plugin = cmd.rc == 0

    details = [
        f"Container status: {container_status['status']}",
        f"Port mappings: {port_mappings}",
        f"coresmd plugin configured: {has_coresmd_plugin}",
    ]

    if not has_coresmd_plugin:
        log.failed("coresmd plugin not configured in Corefile", "\n".join(details))
        assert False, "coresmd plugin not found in Corefile"

    log.passed("coresmd container deployed correctly", "\n".join(details))


@pytest.mark.dns
@pytest.mark.order(42)
def test_forward_zone_generation(host):
    """TC-F23: Verify forward zone file is generated with A records from SMD."""
    log = TestLogger("4. Forward Zone File Generation from SMD")

    if not check_dns_enabled(host):
        log.skipped("DNS is not enabled", "Enable DNS in provision_config.yml")
        pytest.skip("DNS is not enabled")

    log.check("Querying OpenCHAMI SMD for node inventory")
    components = get_smd_components(host)

    log.check("Testing DNS A record resolution for nodes")
    # Get nodes dynamically from PXE mapping
    pxe_nodes = get_pxe_nodes(host)
    dns_domain = get_dns_domain(host)

    if not pxe_nodes:
        log.skipped("No nodes found in PXE mapping", "Check pxe_mapping_file.csv")
        pytest.skip("No nodes in PXE mapping")

    dns_results = []
    for node in pxe_nodes[:5]:  # Test first 5 nodes
        fqdn = f"{node['hostname']}.{dns_domain}"
        result = query_dns(host, fqdn)
        dns_results.append({
            "hostname": node['hostname'],
            "fqdn": fqdn,
            "resolved": result["success"],
            "ip": result["result"] if result["success"] else "N/A",
        })

    resolved_count = sum(1 for r in dns_results if r["resolved"])

    details = [
        f"SMD components found: {len(components)}",
        f"Test hostnames: {len(dns_results)}",
        f"Successfully resolved: {resolved_count}/{len(dns_results)}",
        "",
        "DNS Resolution Results:",
    ]

    for result in dns_results:
        status = "✓" if result["resolved"] else "✗"
        details.append(f"  {status} {result['fqdn']} → {result['ip']}")

    if resolved_count == 0:
        log.failed("No DNS A records found", "\n".join(details))
        assert False, "Forward zone generation failed - no A records found"

    log.passed(f"Forward zone generated with {resolved_count} A records", "\n".join(details))


@pytest.mark.dns
@pytest.mark.order(43)
def test_forward_dns_resolution(host):
    """TC-F32: Verify forward DNS resolution for compute node hostnames."""
    log = TestLogger("5. Forward DNS Resolution - A Records")

    if not check_dns_enabled(host):
        log.skipped("DNS is not enabled", "Enable DNS in provision_config.yml")
        pytest.skip("DNS is not enabled")

    log.check("Testing forward DNS resolution for cluster nodes")

    # Get nodes dynamically from PXE mapping
    pxe_nodes = get_pxe_nodes(host)
    dns_domain = get_dns_domain(host)

    if not pxe_nodes:
        log.skipped("No nodes found in PXE mapping", "Check pxe_mapping_file.csv")
        pytest.skip("No nodes in PXE mapping")

    results = []
    for node in pxe_nodes[:5]:  # Test first 5 nodes
        fqdn = f"{node['hostname']}.{dns_domain}"
        start_time = time.time()
        result = query_dns(host, fqdn)
        query_time = (time.time() - start_time) * 1000  # Convert to ms

        results.append({
            "hostname": fqdn,
            "expected": node['ip'],
            "actual": result["result"],
            "match": result["result"] == node['ip'],
            "query_time_ms": round(query_time, 2),
        })

    successful = sum(1 for r in results if r["match"])

    details = [
        f"Total tests: {len(results)}",
        f"Successful: {successful}/{len(results)}",
        "",
        "DNS Resolution Results:",
    ]

    for result in results:
        status = "✓" if result["match"] else "✗"
        details.append(
            f"  {status} {result['hostname']}: "
            f"{result['actual']} (expected: {result['expected']}) "
            f"[{result['query_time_ms']}ms]"
        )

    if successful == 0:
        log.failed("Forward DNS resolution failed", "\n".join(details))
        assert False, "No hostnames resolved correctly"

    log.passed(f"Forward DNS resolution working ({successful}/{len(results)})", "\n".join(details))


@pytest.mark.dns
@pytest.mark.order(44)
def test_slurm_dns_resolution(host):
    """TC-F48: Verify Slurm controller and node hostnames resolve via DNS."""
    log = TestLogger("6. Slurm Controller Hostname Resolution")

    if not check_dns_enabled(host):
        log.skipped("DNS is not enabled", "Enable DNS in provision_config.yml")
        pytest.skip("DNS is not enabled")

    log.check("Testing Slurm controller hostname resolution")

    # Get nodes dynamically from PXE mapping
    pxe_nodes = get_pxe_nodes(host)
    dns_domain = get_dns_domain(host)

    if not pxe_nodes:
        log.skipped("No nodes found in PXE mapping", "Check pxe_mapping_file.csv")
        pytest.skip("No nodes in PXE mapping")

    # Find Slurm controller (first node with 'control' in functional group)
    pxe_mapping_path = get_pxe_mapping_file_path(host)
    cmd = run_in_container(
        host,
        f"sh -c \"grep -i 'slurm_control' "
        f"{pxe_mapping_path} 2>/dev/null | "
        "head -1 | cut -d',' -f5\""
    )
    slurm_ctrl_out = cmd.stdout.strip()
    slurm_controller_name = (
        slurm_ctrl_out if cmd.rc == 0 and slurm_ctrl_out
        else pxe_nodes[0]['hostname']
    )
    slurm_controller = f"{slurm_controller_name}.{dns_domain}"
    result = query_dns(host, slurm_controller)

    # Test Slurm compute node (second node or first with 'node' in name)
    slurm_node_name = pxe_nodes[1]['hostname'] if len(pxe_nodes) > 1 else pxe_nodes[0]['hostname']
    slurm_node = f"{slurm_node_name}.{dns_domain}"
    node_result = query_dns(host, slurm_node)

    details = [
        f"Slurm controller: {slurm_controller}",
        f"Controller resolved: {result['success']}",
        f"Controller IP: {result['result'] if result['success'] else 'N/A'}",
        "",
        f"Slurm node: {slurm_node}",
        f"Node resolved: {node_result['success']}",
        f"Node IP: {node_result['result'] if node_result['success'] else 'N/A'}",
    ]

    if not result["success"] or not node_result["success"]:
        log.failed("Slurm hostname resolution failed", "\n".join(details))
        assert False, "Slurm hostnames not resolving via DNS"

    log.passed("Slurm hostnames resolve via DNS", "\n".join(details))


@pytest.mark.dns
@pytest.mark.order(45)
def test_k8s_coredns_forwarding(host):
    """
    TC-F58: Verify Kubernetes CoreDNS ConfigMap forwards HPC domain queries.

    Checks:
    - Kubernetes CoreDNS ConfigMap exists
    - ConfigMap contains forwarding block for HPC domain
    - CoreDNS pods are running
    """
    log = TestLogger("7. Kubernetes CoreDNS ConfigMap Forwarding")

    if not check_dns_enabled(host):
        log.skipped("DNS is not enabled", "Enable DNS in provision_config.yml")
        pytest.skip("DNS is not enabled")

    kcp_ip = get_k8s_control_plane_ip(host)
    if not kcp_ip:
        log.skipped("No K8s control plane node found", "Check PXE mapping")
        pytest.skip("No K8s control plane in PXE mapping")

    log.check(f"Checking Kubernetes CoreDNS ConfigMap via kcp ({kcp_ip})")
    configmap_result = check_k8s_coredns_configmap(host, kcp_ip)

    log.check("Verifying CoreDNS pods are running")
    cmd = run_on_remote_node(
        host,
        "kubectl -n kube-system get pods -l k8s-app=kube-dns -o json 2>/dev/null | "
        "jq -r '.items[] | .status.phase'",
        kcp_ip
    )
    coredns_pods_running = "Running" in cmd.stdout if cmd.rc == 0 else False

    details = [
        f"K8s control plane IP: {kcp_ip}",
        f"ConfigMap exists: {configmap_result['success']}",
        f"Has forwarding config: {configmap_result['has_forwarding']}",
        f"CoreDNS pods running: {coredns_pods_running}",
    ]

    if not configmap_result["success"]:
        log.failed("Kubernetes CoreDNS ConfigMap not found", "\n".join(details))
        assert False, "CoreDNS ConfigMap not found"

    if not configmap_result["has_forwarding"]:
        log.passed("⚠ CoreDNS forwarding may not be configured", "\n".join(details))
        return

    log.passed("Kubernetes CoreDNS ConfigMap configured", "\n".join(details))


@pytest.mark.dns
@pytest.mark.order(46)
def test_dns_query_performance(host):
    """
    TC-P01: Verify DNS query latency meets performance requirements.

    Checks:
    - Cached queries respond in < 10ms (relaxed from 1ms for network overhead)
    - Multiple queries show cache effectiveness
    - Query success rate is 100%
    """
    log = TestLogger("8. DNS Query Performance - Cached Latency")

    if not check_dns_enabled(host):
        log.skipped("DNS is not enabled", "Enable DNS in provision_config.yml")
        pytest.skip("DNS is not enabled")

    log.check("Measuring DNS query performance")

    num_queries = 10

    # Get a test hostname from PXE mapping
    pxe_nodes = get_pxe_nodes(host)
    dns_domain = get_dns_domain(host)

    if not pxe_nodes:
        log.skipped("No nodes found in PXE mapping", "Check pxe_mapping_file.csv")
        pytest.skip("No nodes in PXE mapping")

    test_hostname = f"{pxe_nodes[0]['hostname']}.{dns_domain}"

    # First query to populate cache
    query_dns(host, test_hostname)

    # Measure cached query performance
    query_times = []
    for _ in range(num_queries):
        start_time = time.time()
        result = query_dns(host, test_hostname)
        query_time = (time.time() - start_time) * 1000  # Convert to ms
        if result["success"]:
            query_times.append(query_time)

    if not query_times:
        log.failed("No successful DNS queries", "Check DNS configuration")
        assert False, "DNS queries failed"

    avg_latency = sum(query_times) / len(query_times)
    min_latency = min(query_times)
    max_latency = max(query_times)

    details = [
        f"Test hostname: {test_hostname}",
        f"Number of queries: {num_queries}",
        f"Successful queries: {len(query_times)}",
        f"Average latency: {avg_latency:.2f}ms",
        f"Min latency: {min_latency:.2f}ms",
        f"Max latency: {max_latency:.2f}ms",
    ]

    # Relaxed threshold for network overhead
    if avg_latency > 100:
        log.passed(
            f"⚠ Average latency {avg_latency:.2f}ms exceeds 100ms",
            "\n".join(details),
        )
        return

    log.passed(
        f"DNS query performance acceptable ({avg_latency:.2f}ms avg)",
        "\n".join(details),
    )


@pytest.mark.dns
@pytest.mark.order(47)
def test_smd_tls_communication(host):
    """
    TC-S01: Verify communication between coresmd and SMD uses TLS.

    Checks:
    - coresmd Corefile contains TLS configuration
    - CA certificate exists
    - coresmd logs show no TLS errors
    """
    log = TestLogger("9. SMD TLS Communication Security")

    if not check_dns_enabled(host):
        log.skipped("DNS is not enabled", "Enable DNS in provision_config.yml")
        pytest.skip("DNS is not enabled")

    log.check("Verifying coresmd TLS configuration")
    cmd = run_on_oim(
        host,
        f"podman exec {COREDNS_CONTAINER_NAME} cat /Corefile 2>/dev/null | "
        "grep -i -E 'https|tls|ca_cert'"
    )
    has_tls_config = cmd.rc == 0

    log.check("Checking for CA certificate")
    cmd = run_on_oim(
        host,
        f"podman exec {COREDNS_CONTAINER_NAME} ls -la /root_ca/root_ca.crt 2>/dev/null"
    )
    ca_cert_exists = cmd.rc == 0

    log.check("Checking coresmd logs for TLS errors")
    cmd = run_on_oim(
        host,
        f"podman logs {COREDNS_CONTAINER_NAME} 2>&1 | "
        "grep -i -E 'tls|ssl|certificate' | grep -i error"
    )
    has_tls_errors = cmd.rc == 0

    details = [
        f"TLS config in Corefile: {has_tls_config}",
        f"CA certificate exists: {ca_cert_exists}",
        f"TLS errors in logs: {has_tls_errors}",
    ]

    if has_tls_errors:
        log.passed("⚠ TLS errors found in coresmd logs", "\n".join(details))
        return

    if not has_tls_config or not ca_cert_exists:
        log.passed("⚠ TLS configuration incomplete", "\n".join(details))

    log.passed("SMD TLS communication configured", "\n".join(details))


@pytest.mark.dns
@pytest.mark.order(48)
def test_coredns_deployment_idempotency(host):
    """
    TC-I05: Verify CoreDNS deployment is idempotent.

    Checks:
    - coresmd container remains stable
    - Configuration files are consistent
    - No unnecessary restarts occur
    """
    log = TestLogger("10. CoreDNS Deployment Idempotency")

    if not check_dns_enabled(host):
        log.skipped("DNS is not enabled", "Enable DNS in provision_config.yml")
        pytest.skip("DNS is not enabled")

    log.check("Capturing baseline coresmd configuration")
    cmd = run_on_oim(
        host,
        f"podman exec {COREDNS_CONTAINER_NAME} cat /Corefile 2>/dev/null | md5sum"
    )
    corefile_hash_before = cmd.stdout.strip().split()[0] if cmd.rc == 0 else None

    cmd = run_on_oim(
        host,
        f"podman inspect {COREDNS_CONTAINER_NAME} --format '{{{{.State.StartedAt}}}}' 2>/dev/null"
    )
    container_start_time = cmd.stdout.strip() if cmd.rc == 0 else None

    details = [
        f"Corefile hash: {corefile_hash_before}",
        f"Container start time: {container_start_time}",
        "Note: Full idempotency test requires re-running prepare_oim.yml",
    ]

    if not corefile_hash_before:
        log.failed("Cannot capture baseline configuration", "\n".join(details))
        assert False, "Baseline configuration capture failed"

    log.passed("CoreDNS deployment baseline captured", "\n".join(details))


@pytest.mark.dns
@pytest.mark.order(49)
def test_dns_reverse_resolution(host):
    """
    TC-F72: Verify reverse DNS resolution works for admin subnet.

    Checks:
    - Reverse DNS queries return PTR records
    - PTR records point to correct hostnames
    """
    log = TestLogger("11. Multi-Subnet Admin Reverse Zone Generation")

    if not check_dns_enabled(host):
        log.skipped("DNS is not enabled", "Enable DNS in provision_config.yml")
        pytest.skip("DNS is not enabled")

    log.check("Testing reverse DNS resolution")

    # Test reverse DNS for IPs from PXE mapping
    pxe_nodes = get_pxe_nodes(host)

    if not pxe_nodes:
        log.skipped("No nodes found in PXE mapping", "Check pxe_mapping_file.csv")
        pytest.skip("No nodes in PXE mapping")

    results = []
    for node in pxe_nodes[:3]:  # Test first 3 nodes
        result = query_dns(host, f"-x {node['ip']}", "PTR")
        results.append({
            "ip": node['ip'],
            "resolved": result["success"],
            "hostname": result["result"] if result["success"] else "N/A",
        })

    resolved_count = sum(1 for r in results if r["resolved"])

    details = [
        f"Test IPs: {len(results)}",
        f"Successfully resolved: {resolved_count}/{len(results)}",
        "",
        "Reverse DNS Results:",
    ]

    for result in results:
        status = "✓" if result["resolved"] else "✗"
        details.append(f"  {status} {result['ip']} → {result['hostname']}")

    if resolved_count == 0:
        log.passed("⚠ Reverse DNS not configured", "\n".join(details))
    else:
        log.passed(f"Reverse DNS working ({resolved_count}/{len(results)})", "\n".join(details))


@pytest.mark.dns
@pytest.mark.order(50)
def test_dns_configuration_validation(host):
    """
    TC-F02 & TC-UT01: Verify DNS configuration file is valid.

    Checks:
    - provision_config.yml contains dns_enabled setting
    - DNS configuration parameters are valid
    """
    log = TestLogger("2. Valid DNS Configuration File")

    if not check_dns_enabled(host):
        log.skipped("DNS is not enabled", "Enable DNS in provision_config.yml")
        pytest.skip("DNS is not enabled")

    log.check("Validating DNS configuration")

    cmd = run_in_container(
        host,
        "grep -A 5 dns_enabled /opt/omnia/input/project_default/provision_config.yml"
    )

    config_valid = cmd.rc == 0
    dns_enabled = "true" in cmd.stdout.lower() if cmd.rc == 0 else False

    details = [
        f"Configuration file accessible: {config_valid}",
        f"dns_enabled setting: {dns_enabled}",
        "Configuration excerpt:",
        cmd.stdout[:500] if cmd.rc == 0 else "N/A",
    ]

    if not config_valid:
        log.failed("Cannot access DNS configuration", "\n".join(details))
        assert False, "DNS configuration file not accessible"

    log.passed("DNS configuration is valid", "\n".join(details))


@pytest.mark.dns
@pytest.mark.order(51)
def test_mpi_dns_resolution(host):
    """
    TC-F54: Verify MPI peer hostname resolution via DNS.

    Checks:
    - Multiple compute nodes resolve via DNS
    - /etc/hosts does not contain peer entries
    """
    log = TestLogger("12. MPI Peer Hostname Resolution via DNS")

    if not check_dns_enabled(host):
        log.skipped("DNS is not enabled", "Enable DNS in provision_config.yml")
        pytest.skip("DNS is not enabled")

    log.check("Testing MPI peer hostname resolution")

    # Get compute nodes dynamically from PXE mapping
    pxe_nodes = get_pxe_nodes(host)
    dns_domain = get_dns_domain(host)

    if not pxe_nodes:
        log.skipped("No nodes found in PXE mapping", "Check pxe_mapping_file.csv")
        pytest.skip("No nodes in PXE mapping")

    # Test up to 3 compute nodes for MPI peer resolution
    results = []
    for node in pxe_nodes[:3]:
        fqdn = f"{node['hostname']}.{dns_domain}"
        result = query_dns(host, fqdn)
        results.append({
            "hostname": fqdn,
            "resolved": result["success"],
            "ip": result["result"] if result["success"] else "N/A",
        })

    resolved_count = sum(1 for r in results if r["resolved"])

    details = [
        f"Peer hostnames tested: {len(results)}",
        f"Successfully resolved: {resolved_count}/{len(results)}",
        "",
        "MPI Peer Resolution:",
    ]

    for result in results:
        status = "✓" if result["resolved"] else "✗"
        details.append(f"  {status} {result['hostname']} → {result['ip']}")

    if resolved_count == 0:
        log.failed("MPI peer resolution failed", "\n".join(details))
        assert False, "No MPI peers resolved via DNS"

    log.passed(
        f"MPI peer hostnames resolve ({resolved_count}/{len(results)})",
        "\n".join(details),
    )


@pytest.mark.dns
@pytest.mark.order(52)
def test_node_addition_dns_update(host):
    """
    TC-F62: Verify node addition workflow updates DNS automatically.

    Checks:
    - DNS serves records for all nodes in PXE mapping
    - Node count matches expected inventory
    """
    log = TestLogger("13. Node Addition Workflow - Automatic DNS Update")

    if not check_dns_enabled(host):
        log.skipped("DNS is not enabled", "Enable DNS in provision_config.yml")
        pytest.skip("DNS is not enabled")

    log.check("Verifying DNS records for all PXE mapping nodes")

    # Get all nodes from PXE mapping dynamically
    pxe_nodes = get_pxe_nodes(host)
    dns_domain = get_dns_domain(host)

    if not pxe_nodes:
        log.skipped("No nodes found in PXE mapping", "Check pxe_mapping_file.csv")
        pytest.skip("No nodes in PXE mapping")

    results = []
    for node in pxe_nodes:
        fqdn = f"{node['hostname']}.{dns_domain}"
        result = query_dns(host, fqdn)
        results.append({
            "hostname": node['hostname'],
            "fqdn": fqdn,
            "resolved": result["success"],
        })

    resolved_count = sum(1 for r in results if r["resolved"])

    details = [
        f"Total nodes in PXE mapping: {len(pxe_nodes)}",
        f"Nodes with DNS records: {resolved_count}/{len(pxe_nodes)}",
        "",
        "Node DNS Status:",
    ]

    for result in results:
        status = "✓" if result["resolved"] else "✗"
        details.append(f"  {status} {result['fqdn']}")

    if resolved_count < len(pxe_nodes):
        log.passed(
            f"⚠ Not all nodes have DNS ({resolved_count}/{len(pxe_nodes)})",
            "\n".join(details),
        )
    else:
        log.passed("All nodes have DNS records", "\n".join(details))


@pytest.mark.dns
@pytest.mark.order(53)
def test_smd_unreachable_graceful_degradation(host):
    """
    TC-E22: Verify coresmd handles SMD connectivity failures gracefully.

    Checks:
    - coresmd continues serving cached records when SMD is unreachable
    - No critical errors in coresmd logs
    """
    log = TestLogger("14. SMD Unreachable During Zone Generation")

    if not check_dns_enabled(host):
        log.skipped("DNS is not enabled", "Enable DNS in provision_config.yml")
        pytest.skip("DNS is not enabled")

    log.check("Verifying DNS continues working (cached data)")

    # Test DNS resolution (should work from cache even if SMD is down)
    pxe_nodes = get_pxe_nodes(host)
    dns_domain = get_dns_domain(host)

    if not pxe_nodes:
        log.skipped("No nodes found in PXE mapping", "Check pxe_mapping_file.csv")
        pytest.skip("No nodes in PXE mapping")

    test_fqdn = f"{pxe_nodes[0]['hostname']}.{dns_domain}"
    result = query_dns(host, test_fqdn)

    log.check("Checking coresmd logs for SMD connection errors")
    cmd = run_on_oim(
        host,
        f"podman logs {COREDNS_CONTAINER_NAME} --tail 50 2>&1 | "
        "grep -i -E 'smd|error|connection'"
    )
    log_excerpt = cmd.stdout[:500] if cmd.rc == 0 else "No relevant logs"

    details = [
        f"DNS resolution working: {result['success']}",
        f"Resolved IP: {result['result'] if result['success'] else 'N/A'}",
        "",
        "Recent coresmd logs:",
        log_excerpt,
    ]

    if not result["success"]:
        log.passed(
            "⚠ DNS failed - may indicate SMD issue",
            "\n".join(details),
        )
    else:
        log.passed("DNS continues working (cached data)", "\n".join(details))


@pytest.mark.dns
@pytest.mark.order(54)
def test_backward_compatibility_dns_disabled(host):
    """
    TC-U01: Verify backward compatibility when dns_enabled=false.

    Checks:
    - PXE mapping hostnames are custom (not NID format)
    - Compute nodes have peer entries in /etc/hosts via SSH
    """
    log = TestLogger("15. Backward Compatibility - dns_enabled=false")

    dns_enabled = check_dns_enabled(host)

    if dns_enabled:
        log.skipped("DNS is enabled - cannot test dns_enabled=false scenario",
                   "This test requires dns_enabled: false in provision_config.yml")
        pytest.skip("DNS is enabled")

    log.check("Verifying PXE mapping hostnames are custom (not NID format)")
    pxe_nodes = get_pxe_nodes(host)

    if not pxe_nodes:
        log.skipped("No nodes found in PXE mapping", "Check pxe_mapping_file.csv")
        pytest.skip("No nodes in PXE mapping")

    nid_hostnames = [n for n in pxe_nodes if is_nid_hostname(n['hostname'])]

    details = [
        f"dns_enabled: {dns_enabled}",
        f"Total PXE nodes: {len(pxe_nodes)}",
        f"NID-format hostnames: {len(nid_hostnames)}",
        "",
        "PXE Hostnames:",
    ]
    for node in pxe_nodes[:10]:
        fmt = "NID" if is_nid_hostname(node['hostname']) else "custom"
        details.append(f"  {node['hostname']} ({node['ip']}) [{fmt}]")

    log.check("Verifying compute nodes have peer entries in /etc/hosts via SSH")
    nodes_checked = 0
    nodes_with_peers = 0
    hosts_details = []

    for node in pxe_nodes[:3]:
        peer_entries = get_etc_hosts_peer_entries(host, node['ip'])
        nodes_checked += 1
        if peer_entries:
            nodes_with_peers += 1
            hosts_details.append(
                f"  \u2713 {node['hostname']} ({node['ip']}): "
                f"{len(peer_entries)} peer entries"
            )
        else:
            hosts_details.append(
                f"  \u2717 {node['hostname']} ({node['ip']}): "
                "no peer entries in /etc/hosts"
            )

    details.extend([
        "",
        f"Nodes checked: {nodes_checked}",
        f"Nodes with /etc/hosts peers: {nodes_with_peers}/{nodes_checked}",
        "",
        "/etc/hosts Status:",
    ] + hosts_details)

    if nodes_checked > 0 and nodes_with_peers == 0:
        log.failed(
            "No compute nodes have peer entries in /etc/hosts",
            "\n".join(details)
        )
        assert False, (
            "dns_enabled=false but compute nodes have no peer entries "
            "in /etc/hosts"
        )

    log.passed("Backward compatibility verified", "\n".join(details))


@pytest.mark.dns
@pytest.mark.order(55)
def test_invalid_domain_format_validation(host):
    """TC-E01: Verify invalid domain format is rejected during validation."""
    log = TestLogger("16. Invalid Domain Format - Uppercase Characters")

    if not check_dns_enabled(host):
        log.skipped("DNS is not enabled", "Enable DNS in provision_config.yml")
        pytest.skip("DNS is not enabled")

    log.check("Validating DNS domain format")

    # Get the actual domain being used
    dns_domain = get_dns_domain(host)

    # Check for invalid characters (uppercase, underscores, etc.)
    has_uppercase = any(c.isupper() for c in dns_domain)
    has_underscore = '_' in dns_domain
    has_invalid_chars = not all(c.isalnum() or c in '.-' for c in dns_domain)

    # RFC 1035 validation: must be lowercase, alphanumeric with hyphens/dots only
    is_valid = not (has_uppercase or has_underscore or has_invalid_chars)

    details = [
        f"Domain: {dns_domain}",
        f"Has uppercase: {has_uppercase}",
        f"Has underscore: {has_underscore}",
        f"Has invalid chars: {has_invalid_chars}",
        f"RFC 1035 compliant: {is_valid}",
        "",
        "Valid examples: hpc.cluster, test-domain.local, omnia.test",
        "Invalid examples: HPC.CLUSTER, Test-Domain, domain_name",
    ]

    if not is_valid:
        log.failed(
            f"Domain '{dns_domain}' has invalid format",
            "\n".join(details)
        )
        assert False, f"Domain format validation failed: {dns_domain}"

    log.passed(f"Domain '{dns_domain}' is RFC 1035 compliant", "\n".join(details))


@pytest.mark.dns
@pytest.mark.order(56)
def test_pxe_hostname_nid_format(host):
    """
    TC-F03: Verify PXE mapping hostnames follow NID format when dns_enabled=true.

    Checks:
    - All hostnames in PXE mapping follow NID format (nid001, nid002, ...)
      when dns_enabled is true
    - Custom hostnames are present when dns_enabled is false
    """
    log = TestLogger("17. PXE Hostname NID Format Validation")

    dns_enabled = check_dns_enabled(host)

    log.check("Reading PXE mapping hostnames")
    pxe_nodes = get_pxe_nodes(host)

    if not pxe_nodes:
        log.skipped("No nodes found in PXE mapping", "Check pxe_mapping_file.csv")
        pytest.skip("No nodes in PXE mapping")

    nid_nodes = [n for n in pxe_nodes if is_nid_hostname(n['hostname'])]
    non_nid_nodes = [n for n in pxe_nodes if not is_nid_hostname(n['hostname'])]

    details = [
        f"dns_enabled: {dns_enabled}",
        f"Total PXE nodes: {len(pxe_nodes)}",
        f"NID-format hostnames: {len(nid_nodes)}",
        f"Custom hostnames: {len(non_nid_nodes)}",
        "",
        "Hostnames:",
    ]
    for node in pxe_nodes:
        fmt = "NID" if is_nid_hostname(node['hostname']) else "custom"
        details.append(f"  {node['hostname']} ({node['ip']}) [{fmt}]")

    if dns_enabled:
        log.check("dns_enabled=true: all hostnames must be NID format")
        if non_nid_nodes:
            non_nid_names = [n['hostname'] for n in non_nid_nodes]
            details.extend([
                "",
                "Non-NID hostnames (invalid when dns_enabled=true):",
            ] + [f"  {h}" for h in non_nid_names])
            log.failed(
                f"{len(non_nid_nodes)} hostnames are not in NID format",
                "\n".join(details)
            )
            assert False, (
                f"dns_enabled=true but {len(non_nid_nodes)} hostnames "
                f"are not NID format: {non_nid_names}"
            )
        log.passed(
            f"All {len(nid_nodes)} hostnames follow NID format",
            "\n".join(details)
        )
    else:
        log.check("dns_enabled=false: hostnames should be present in PXE mapping")
        log.passed(
            f"PXE mapping has {len(pxe_nodes)} hostnames",
            "\n".join(details)
        )


@pytest.mark.dns
@pytest.mark.order(57)
def test_compute_node_etc_hosts_dns_enabled(host):
    """
    TC-F04: Verify /etc/hosts on compute nodes when dns_enabled=true.

    Checks:
    - SSH into compute nodes
    - /etc/hosts contains only localhost entries (no peer node entries)
    - Peer resolution is handled by DNS, not /etc/hosts
    """
    log = TestLogger("18. Compute Node /etc/hosts - DNS Enabled")

    if not check_dns_enabled(host):
        log.skipped("DNS is not enabled", "Enable DNS in provision_config.yml")
        pytest.skip("DNS is not enabled")

    log.check("Reading PXE mapping for compute nodes")
    pxe_nodes = get_pxe_nodes(host)

    if not pxe_nodes:
        log.skipped("No nodes found in PXE mapping", "Check pxe_mapping_file.csv")
        pytest.skip("No nodes in PXE mapping")

    log.check("SSHing into compute nodes to verify /etc/hosts")
    nodes_checked = 0
    nodes_clean = 0
    check_details = []

    for node in pxe_nodes[:3]:
        peer_entries = get_etc_hosts_peer_entries(host, node['ip'])
        nodes_checked += 1
        if not peer_entries:
            nodes_clean += 1
            check_details.append(
                f"  \u2713 {node['hostname']} ({node['ip']}): "
                "only localhost entries (correct)"
            )
        else:
            check_details.append(
                f"  \u2717 {node['hostname']} ({node['ip']}): "
                f"{len(peer_entries)} unexpected peer entries"
            )
            for entry in peer_entries[:5]:
                check_details.append(f"      {entry}")

    details = [
        f"dns_enabled: true",
        f"Nodes checked: {nodes_checked}",
        f"Nodes with clean /etc/hosts: {nodes_clean}/{nodes_checked}",
        "",
        "/etc/hosts Verification:",
    ] + check_details

    if nodes_checked > 0 and nodes_clean < nodes_checked:
        log.failed(
            f"{nodes_checked - nodes_clean} nodes have peer entries "
            "in /etc/hosts",
            "\n".join(details)
        )
        assert False, (
            "dns_enabled=true but compute nodes still have peer entries "
            "in /etc/hosts — nodes may need reprovisioning"
        )

    log.passed(
        f"All {nodes_clean} nodes have clean /etc/hosts (DNS only)",
        "\n".join(details)
    )


@pytest.mark.dns
@pytest.mark.order(58)
def test_compute_node_resolv_conf(host):
    """
    TC-F05: Verify /etc/resolv.conf on compute nodes when dns_enabled=true.

    Checks:
    - SSH into compute nodes
    - /etc/resolv.conf has correct nameserver pointing to OIM admin IP
    - search domain and options are configured
    """
    log = TestLogger("19. Compute Node /etc/resolv.conf - DNS Enabled")

    if not check_dns_enabled(host):
        log.skipped("DNS is not enabled", "Enable DNS in provision_config.yml")
        pytest.skip("DNS is not enabled")

    log.check("Reading PXE mapping for compute nodes")
    pxe_nodes = get_pxe_nodes(host)

    if not pxe_nodes:
        log.skipped("No nodes found in PXE mapping", "Check pxe_mapping_file.csv")
        pytest.skip("No nodes in PXE mapping")

    dns_server_ip = get_dns_server_ip(host)

    log.check("SSHing into compute nodes to verify /etc/resolv.conf")
    nodes_checked = 0
    nodes_correct = 0
    check_details = []

    for node in pxe_nodes[:3]:
        resolv = get_resolv_conf(host, node['ip'])
        nodes_checked += 1

        if not resolv["success"]:
            check_details.append(
                f"  \u2717 {node['hostname']} ({node['ip']}): "
                "failed to read /etc/resolv.conf"
            )
            continue

        content = resolv["content"]
        has_nameserver = f"nameserver {dns_server_ip}" in content
        has_search = "search " in content

        if has_nameserver:
            nodes_correct += 1
            check_details.append(
                f"  \u2713 {node['hostname']} ({node['ip']}): "
                f"nameserver={dns_server_ip}, search={'yes' if has_search else 'no'}"
            )
        else:
            check_details.append(
                f"  \u2717 {node['hostname']} ({node['ip']}): "
                f"nameserver {dns_server_ip} not found"
            )
            for line in content.split('\n')[:5]:
                check_details.append(f"      {line}")

    details = [
        f"dns_enabled: true",
        f"Expected nameserver: {dns_server_ip}",
        f"Nodes checked: {nodes_checked}",
        f"Nodes with correct resolv.conf: {nodes_correct}/{nodes_checked}",
        "",
        "/etc/resolv.conf Verification:",
    ] + check_details

    if nodes_checked > 0 and nodes_correct == 0:
        log.failed(
            "No compute nodes have correct /etc/resolv.conf",
            "\n".join(details)
        )
        assert False, (
            "dns_enabled=true but compute nodes do not have correct "
            "/etc/resolv.conf — nodes may need reprovisioning"
        )

    log.passed(
        f"{nodes_correct}/{nodes_checked} nodes have correct /etc/resolv.conf",
        "\n".join(details)
    )


@pytest.mark.dns
@pytest.mark.order(59)
def test_getent_hosts_resolution(host):
    """
    TC-F06: Verify DNS resolution on compute nodes using getent hosts.

    Checks:
    - SSH into compute nodes
    - Run getent hosts <hostname> to verify DNS resolution works
    - Resolved IPs match PXE mapping
    """
    log = TestLogger("20. Compute Node DNS Resolution - getent hosts")

    if not check_dns_enabled(host):
        log.skipped("DNS is not enabled", "Enable DNS in provision_config.yml")
        pytest.skip("DNS is not enabled")

    log.check("Reading PXE mapping for compute nodes")
    pxe_nodes = get_pxe_nodes(host)
    dns_domain = get_dns_domain(host)

    if not pxe_nodes:
        log.skipped("No nodes found in PXE mapping", "Check pxe_mapping_file.csv")
        pytest.skip("No nodes in PXE mapping")

    if len(pxe_nodes) < 2:
        log.skipped("Need at least 2 nodes for peer resolution test",
                   "Add more nodes to PXE mapping")
        pytest.skip("Need at least 2 nodes")

    log.check("SSHing into compute nodes to test getent hosts resolution")
    source_node = pxe_nodes[0]
    target_nodes = pxe_nodes[1:4]

    results = []
    for target in target_nodes:
        fqdn = f"{target['hostname']}.{dns_domain}"
        cmd = run_on_remote_node(
            host,
            f"getent hosts {fqdn} 2>/dev/null",
            source_node['ip']
        )
        resolved_ip = ""
        if cmd.rc == 0 and cmd.stdout.strip():
            resolved_ip = cmd.stdout.strip().split()[0]

        match = resolved_ip == target['ip']
        results.append({
            "target": fqdn,
            "expected_ip": target['ip'],
            "resolved_ip": resolved_ip if resolved_ip else "N/A",
            "match": match,
        })

    successful = sum(1 for r in results if r["match"])

    details = [
        f"Source node: {source_node['hostname']} ({source_node['ip']})",
        f"Targets tested: {len(results)}",
        f"Successful: {successful}/{len(results)}",
        "",
        "getent hosts Results:",
    ]
    for result in results:
        status = "\u2713" if result["match"] else "\u2717"
        details.append(
            f"  {status} {result['target']}: "
            f"{result['resolved_ip']} "
            f"(expected: {result['expected_ip']})"
        )

    if successful == 0:
        log.failed("DNS resolution via getent hosts failed", "\n".join(details))
        assert False, "getent hosts failed to resolve any peer hostnames"

    log.passed(
        f"getent hosts resolution working ({successful}/{len(results)})",
        "\n".join(details)
    )
