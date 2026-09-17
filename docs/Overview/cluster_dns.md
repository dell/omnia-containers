# Cluster DNS

## Overview

Cluster DNS is an optional Orchestrator capability that makes OpenCHAMI SMD
inventory available through the `coresmd` CoreDNS plugin. The current
Orchestrator input sets `dns_enabled: false` by default.

When Cluster DNS is enabled, Orchestrator configures provisioned nodes to query
the OIM admin address for the Omnia cluster domain. For service Kubernetes, the
generated control-plane cloud-init also adds a Kubernetes CoreDNS forward zone
for that domain. When Cluster DNS is disabled, the node cloud-init templates
append the generated peer mapping to `/etc/hosts` instead.

Cluster DNS is owned by the Orchestrator deployment module. See
[Configure Cluster DNS](../HowTo/orchestrator/configure_cluster_dns.md) for the
task-oriented procedure.

## Prerequisites

- Complete the common OIM setup and stage the Orchestrator inputs.
- Provide a valid `pxe_mapping_file.csv` and the successful Repository Manager
  and Image Build Manager outputs required by Orchestrator.
- Configure `SYSTEM_ADMIN_NIC_IPV4` and `SYSTEM_DOMAIN_NAME` for the OIM.
- In `network_spec.yml`, configure reachable DNS forwarders in
  `Networks.admin_network.dns`. The generated Corefile forwards queries outside
  the Omnia cluster zone to these addresses.
- Ensure managed nodes and service Kubernetes nodes can reach TCP and UDP port
  53 on the OIM admin address. The OpenCHAMI deployment opens both ports in
  `firewalld`.

## Source-defined behavior

The generated OpenCHAMI Corefile:

- binds DNS to the cluster boot/admin address;
- exposes CoreDNS Prometheus metrics on port `9153`;
- queries SMD through the configured OpenCHAMI endpoint and CA certificate;
- refreshes the SMD data cache every 30 seconds;
- serves the cluster domain recorded from the OIM environment; and
- generates node records using the fixed `nid` short name and a three-digit
  node identifier.

When `dns_enabled: true`, Orchestrator input validation requires every PXE
mapping hostname to use the `nidNNN` form from `nid001` through `nid999`.
During node registration, each generated per-category file, such as
`nodes_slurm.yaml` or `nodes_kubernetes.yaml`, derives the numeric node ID from
that suffix. Custom hostnames are supported only when Cluster DNS is disabled;
in that mode, node cloud-init uses the generated `/etc/hosts` mapping instead.

When Orchestrator provisions a target category with Cluster DNS enabled, it:

- writes `/etc/resolv.conf` content into applicable node cloud-init with the
  cluster domain search suffix and OIM admin address;
- updates the OIM resolver to place the cluster domain and OIM nameserver first;
- marks the OIM `/etc/resolv.conf` immutable to prevent NetworkManager from
  overwriting it; and
- adds a service Kubernetes CoreDNS forward block for the cluster domain when
  service Kubernetes is selected.

## Enable Cluster DNS

1. Edit the staged Orchestrator configuration:

    ```bash title="Run on: OIM host"
    source /etc/profile.d/omnia-env.sh
    orchestrator_path="${ORCHESTRATOR_DATA_PATH:-${OMNIA_DATA_PATH}/orchestrator}"
    vi "${orchestrator_path}/input/${OMNIA_PROJECT_NAME}/orchestrator_config.yml"
    ```

2. Enable the source-defined option:

    ```yaml
    dns_enabled: true
    ```

3. Validate the complete Orchestrator input contract:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags validate
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags validate
        ```

4. Prepare Orchestrator. This deploys and validates OpenCHAMI and its generated
   CoreDNS configuration:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags prepare
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags prepare
        ```

5. Provision the selected functional groups so that Orchestrator generates the
   updated node metadata and resolver configuration:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags provision
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags provision
        ```

    Use `--tags execute` instead when the same invocation should perform the
    complete provision flow and the conditional iDRAC PXE-boot phase.

6. New resolver content is applied to a stateless node when it consumes the
   updated cloud-init during provisioning. Reprovision existing nodes when they
   must receive the new resolver configuration.

## Verification

1. Verify the OpenCHAMI target on the OIM:

    ```bash title="Run on: OIM host"
    systemctl is-active openchami.target
    systemctl list-dependencies openchami.target
    ```

2. Query an SMD-derived name directly from the OIM DNS address:

    ```bash title="Run on: OIM host"
    dig nid001.<SYSTEM_DOMAIN_NAME> @<SYSTEM_ADMIN_NIC_IPV4>
    ```

    Confirm that the answer contains the expected node admin address.

3. Verify the resolver on a newly provisioned node:

    ```bash title="Run on: provisioned node"
    cat /etc/resolv.conf
    getent hosts nid001.<SYSTEM_DOMAIN_NAME>
    ```

    The resolver content generated by Orchestrator contains the cluster domain
    search suffix, the OIM admin address as nameserver, and
    `options timeout:1 attempts:2`.

4. When service Kubernetes is present, inspect its CoreDNS ConfigMap:

    ```bash title="Run on: service Kubernetes control plane"
    kubectl -n kube-system get configmap coredns -o yaml
    ```

    Confirm that it contains a forward block for `<SYSTEM_DOMAIN_NAME>` whose
    target is `<SYSTEM_ADMIN_NIC_IPV4>`.

## Disable Cluster DNS

1. Set `dns_enabled: false` in the staged `orchestrator_config.yml`.
2. Run Orchestrator validation and provisioning again.
3. Reprovision stateless nodes that must return to the `/etc/hosts` content
   generated by their updated cloud-init.

Disabling the option changes client configuration. The OpenCHAMI deployment
still contains its generated CoreDNS service and firewall rules.

## Troubleshooting

- **The DNS query times out:** Verify `openchami.target`, TCP and UDP port 53,
  and reachability of the OIM admin address from the affected node.
- **The cluster name resolves to an unexpected node:** Compare the mapping
  hostnames with the node IDs registered in SMD. The CoreDNS record is based on
  the SMD node ID, not an arbitrary custom hostname.
- **External names do not resolve:** Check the DNS addresses in
  `Networks.admin_network.dns` and verify that the OIM can reach them.
- **An existing node still uses `/etc/hosts`:** Confirm that the node consumed
  the regenerated cloud-init after `dns_enabled` was changed.
- **Manual changes to the OIM resolver fail:** The provisioning task applies
  the immutable flag to `/etc/resolv.conf`. Manage the setting through the
  Orchestrator flow so that the source-defined resolver content is reapplied.
- **Kubernetes pods cannot resolve the cluster domain:** Verify the CoreDNS
  ConfigMap forward block and confirm that pods can reach port 53 on the OIM
  admin address.
