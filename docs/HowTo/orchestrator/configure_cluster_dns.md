
# Configure Cluster DNS

Enable Cluster DNS to provide dynamic hostname resolution for Slurm, login, and Kubernetes nodes using CoreDNS instead of static `/etc/hosts` file management.


## Overview

Cluster DNS replaces per-node `/etc/hosts` synchronization with coresmd, a CoreDNS instance on the OIM that generates DNS records automatically from the OpenCHAMI SMD inventory. For a full explanation of the architecture, DNS ownership boundaries, and failure behavior, see [Cluster DNS](../../Overview/cluster_dns.md).

## Prerequisites

- Omnia is deployed on the OIM node with OpenCHAMI services running.
- The active project's Orchestrator `orchestrator_config.yml` exists and is
  validated.
- The OIM node is accessible on the admin network.


## Procedure

### Enable Cluster DNS

1. Edit the Orchestrator configuration file on the OIM:

    ```bash title="Run on: OIM host"
    source /etc/profile.d/omnia-env.sh
    orchestrator_path="${ORCHESTRATOR_DATA_PATH:-${OMNIA_DATA_PATH}/orchestrator}"
    source "$OMNIA_DATA_PATH/activate-omnia.sh"
    vi "$orchestrator_path/input/$OMNIA_PROJECT_NAME/orchestrator_config.yml"
    ```

2. Set the `dns_enabled` parameter to `true`:

    ```yaml title="File: orchestrator_config.yml"
    dns_enabled: true
    ```

    !!! note
        The default value is `false`. Set it to `true` to enable CoreDNS-based
        cluster name resolution.

    !!! important

        When `dns_enabled` is `true`, all `HOSTNAME` values in the PXE mapping
        file must use the `nidxxx` format (e.g., `nid001`, `nid002`). Formats
        like `nid00001` are not supported and will cause DNS resolution
        failures. See [Cluster DNS Architecture and Hostname Requirements](../../Overview/cluster_dns.md) for details.

3. Deploy or redeploy OpenCHAMI with coresmd (if not already deployed):

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags prepare
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags prepare
        ```

4. Run the provisioning playbook so nodes receive cloud-init with `/etc/resolv.conf` configured:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags provision
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags provision
        ```

5. PXE boot or otherwise reprovision every affected Slurm and service
   Kubernetes node to apply the new cloud-init configuration.

    !!! important
        Nodes must be reprovisioned after setting `dns_enabled: true` for the
        change to take effect. A normal operating-system reboot does not apply
        newly generated cloud-init metadata; existing nodes retain their
        previous resolver configuration until they are reprovisioned.

### Disable Cluster DNS (Revert to /etc/hosts)

1. Edit `orchestrator_config.yml` and set `dns_enabled` to `false`:

    ```yaml title="File: orchestrator_config.yml"
    dns_enabled: false
    ```

2. Re-run the provisioning playbook to regenerate cloud-init configuration:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags provision
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags provision
        ```

3. PXE boot or otherwise reprovision every affected Slurm and service
   Kubernetes node to apply the new cloud-init configuration.

    !!! note
        No coresmd or OpenCHAMI changes are needed for this configuration
        change. coresmd continues running but newly provisioned compute nodes
        no longer query it. Setting `dns_enabled: false` does not restore a
        resolver file that was previously changed on the OIM; review and
        restore the OIM resolver settings manually when required.


## Verification

1. **Verify the Slurm-node resolver configuration**:

    ```bash title="Run on: Slurm controller, compute, or login node"
    cat /etc/resolv.conf
    ```

    ```text title="Expected entries"
    search <domain_name>
    nameserver <admin_nic_ip>
    options timeout:1 attempts:2
    ```

    Slurm controller, compute, and login-node cloud-init replaces the resolver
    content with the three entries shown above and marks the file immutable.
    Kubernetes-node cloud-init instead preserves the existing search line and
    resolver entries, adds the configured upstream nameservers, removes exact
    duplicate lines, and then marks the file immutable. On the OIM,
    Orchestrator prepends the cluster search domain and OIM nameserver while
    preserving the other resolver entries, then marks the file immutable.
    Account for this protection before making later manual resolver changes.

2. **Verify that Orchestrator did not add peer mappings to `/etc/hosts`**:

    ```bash title="Run on: compute node"
    cat /etc/hosts
    ```

    Base-image or operator-managed entries may remain. With Cluster DNS
    enabled, Orchestrator omits its generated cluster peer mappings rather than
    replacing or sanitizing the file.

3. **Verify forward DNS resolution** for a cluster hostname:

    ```bash title="Run on: compute node"
    getent hosts <hostname>.<domain>
    ```

    ```text title="Expected output"
    172.16.0.1 nid001.hpc.cluster
    ```

4. **Query coresmd directly** from the OIM node or any node with network access to it:

    ```bash title="Run on: OIM host"
    dig <hostname>.<domain> @<admin_nic_ip>
    ```

    Expected output includes an `ANSWER SECTION` with the node's admin IP address.

5. **Verify Kubernetes CoreDNS patching** (if Kubernetes is deployed). Confirm the ConfigMap contains the forward zone:

    ```bash title="Run on: kube_control_plane"
    kubectl -n kube-system get configmap coredns -o yaml
    ```

    ```text title="Expected output"
    hpc.cluster:53 {
        errors
        cache 30
        forward . 172.16.107.254
    }
    ```

6. **Verify Kubernetes pod resolution** (if Kubernetes is deployed):

    ```bash title="Run on: kube_control_plane"
    kubectl exec -it <pod> -- getent hosts <hostname>.<domain>
    ```

7. **Verify Slurm and MPI functionality**:

    ```bash title="Run on: Slurm controller or login node"
    sinfo
    srun -N <N> hostname
    mpirun -np 4 -host <host1>,<host2> hostname
    ```

    All nodes should show as `IDLE` or `ALLOCATED` in `sinfo`, and jobs should complete without DNS errors or timeouts.

8. **Verify new node auto-resolution**. After adding a node by running the Orchestrator `provision` phase (`./omnia.sh --run orchestrator --tags provision`), wait up to 30 seconds for coresmd to refresh its cache, then confirm resolution without any playbook re-run:

    ```bash title="Run on: compute node"
    getent hosts <new_hostname>
    ```

### Best Practices

- **Plan DNS mode before deployment** -- Decide on DNS mode before the initial cluster deployment. Changing mode afterward requires reprovisioning all nodes.
- **Monitor coresmd health** -- Track coresmd container status and logs, and use Prometheus metrics (port 9153) to monitor DNS query performance.
- **Configure reliable upstream DNS** -- Configure at least two reliable upstream DNS servers in `admin_network.dns` and test connectivity before enabling Cluster DNS.
- **Test resolution before production** -- Verify DNS resolution, Slurm/MPI job execution, and Kubernetes pod resolution before running production workloads.
- **Document domain configuration** -- Record the cluster domain name and hostname pattern (`cluster_shortname`, `cluster_nidlength`) for reference.
- **Plan for high availability** -- The OIM node is a single point of failure for DNS in the current implementation. Plan for OIM HA deployment and monitor OIM node health.
- **Use short-name resolution** -- Leverage the `search <domain_name>` directive so users can reference short hostnames instead of FQDNs.
- **Validate after node changes** -- After adding or removing nodes, verify DNS resolution within 30 seconds using `dig` or `getent hosts`.

## Next steps

- [Configure InfiniBand](configure_infiniband.md) -- Configure the high-speed interconnect network.

## Troubleshooting

**Custom hostnames not resolving**

Custom hostnames are not supported while `dns_enabled: true`; coresmd is
configured for the `nid` prefix and three-digit suffix. Use hostnames such as
`nid001`, or disable Cluster DNS and reprovision the nodes to use
Orchestrator-managed `/etc/hosts` entries.

**Mixed-state cluster**

If some nodes resolve via DNS while others use `/etc/hosts`, only some nodes were reprovisioned after changing `dns_enabled`. Check `/etc/resolv.conf` on the affected nodes to determine which mode they are using, then reprovision and reboot all nodes for a consistent configuration.


!!! info "Related pages"

    - [Cluster DNS](../../Overview/cluster_dns.md) -- Architecture, DNS ownership boundaries, and failure scenarios.
    - [Orchestrator configuration](../../Reference/Configuration/orchestrator_config.md) -- Reference for the `dns_enabled` parameter and input path.
    - [Known Limitations](../../Troubleshooting/known_limitations.md) -- Cluster DNS constraints.
