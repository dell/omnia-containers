
# Configure Cluster DNS

Enable Cluster DNS to provide dynamic hostname resolution for Slurm, login, and Kubernetes nodes using CoreDNS instead of static `/etc/hosts` file management.


## Overview

Cluster DNS replaces per-node `/etc/hosts` synchronization with coresmd, a CoreDNS instance on the OIM that generates DNS records automatically from the OpenCHAMI SMD inventory. For a full explanation of the architecture, DNS ownership boundaries, and failure behavior, see [Cluster DNS](../../Overview/cluster_dns.md).

!!! important "Centralized DNS Upgrade"

    `dns_enabled` defaults to `true` only for fresh Omnia 2.2 installations. For upgrades from Omnia 2.1 to 2.2, `dns_enabled` must be set to `false`; enabling Cluster DNS during an upgrade is not supported.


## Prerequisites

- Omnia is deployed on the OIM node with OpenCHAMI services running.
- `/opt/omnia/input/project_default/provision_config.yml` exists and is validated.
- The OIM node is accessible on the admin network.


## Procedure

### Enable Cluster DNS

1. Edit the provision configuration file on the OIM node:

    ```bash title="Run on: OIM host"
    vi /opt/omnia/input/project_default/provision_config.yml
    ```

2. Set the `dns_enabled` parameter to `true`:

    ```yaml title="File: /opt/omnia/input/project_default/provision_config.yml"
    dns_enabled: true
    ```

    !!! note
        The default value is `true`, which enables the CoreDNS-based Cluster DNS behavior.

    !!! important

        When `dns_enabled` is `true`, all `HOSTNAME` values in the PXE mapping
        file must use the `nid00x` format (e.g., `nid001`, `nid002`). Formats
        like `nid00001` are not supported and will cause DNS resolution
        failures. See [Cluster DNS Architecture and Hostname Requirements](../../Overview/cluster_dns.md) for details.

3. Deploy or redeploy OpenCHAMI with coresmd (if not already deployed):

    ```bash title="Run on: omnia_core container"
    cd /omnia/prepare_oim
    ansible-playbook prepare_oim.yml
    ```

4. Run the provisioning playbook so nodes receive cloud-init with `/etc/resolv.conf` configured:

    ```bash title="Run on: omnia_core container"
    cd /omnia/provision
    ansible-playbook provision.yml
    ```

5. Reprovision (reboot) all compute nodes to apply the new cloud-init configuration.

    !!! important
        Nodes must be reprovisioned after setting `dns_enabled: true` for the change to take effect. Existing nodes retain their previous configuration until reprovisioned.

### Disable Cluster DNS (Revert to /etc/hosts)

1. Edit `provision_config.yml` and set `dns_enabled` to `false`:

    ```yaml title="File: /opt/omnia/input/project_default/provision_config.yml"
    dns_enabled: false
    ```

2. Re-run the provisioning playbook to regenerate cloud-init configuration:

    ```bash title="Run on: omnia_core container"
    cd /omnia/provision
    ansible-playbook provision.yml
    ```

3. Reprovision (reboot) all compute nodes to apply the new cloud-init configuration.

    !!! note
        No coresmd or OpenCHAMI changes are needed for rollback. coresmd continues running but compute nodes no longer query it.


## Verification

1. **Verify the compute node resolver configuration**:

    ```bash title="Run on: compute node"
    cat /etc/resolv.conf
    ```

    ```text title="Expected output"
    search <domain_name>
    nameserver <admin_nic_ip>
    options timeout:1 attempts:2
    ```

2. **Verify no peer entries exist in `/etc/hosts`** (only localhost entries should be present):

    ```bash title="Run on: compute node"
    cat /etc/hosts
    ```

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

    ```bash title="Run on: OIM host"
    sinfo
    srun -N <N> hostname
    mpirun -np 4 -host <host1>,<host2> hostname
    ```

    All nodes should show as `IDLE` or `ALLOCATED` in `sinfo`, and jobs should complete without DNS errors or timeouts.

8. **Verify new node auto-resolution**. After adding a node via `provision.yml`, wait up to 30 seconds for coresmd to refresh its cache, then confirm resolution without any playbook re-run:

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

## Next Steps

- [Configure InfiniBand](configure_infiniband.md) -- Configure the high-speed interconnect network.

## Troubleshooting

**Custom hostnames not resolving**

Custom hostnames from the PXE mapping file resolve via `/etc/hosts`, not CoreDNS. If a custom hostname does not resolve, check that it is present in `/etc/hosts`:

```bash title="Run on: compute node"
grep <hostname> /etc/hosts
```

If missing, re-run `provision.yml` to repopulate `/etc/hosts`.

**Mixed-state cluster**

If some nodes resolve via DNS while others use `/etc/hosts`, only some nodes were reprovisioned after changing `dns_enabled`. Check `/etc/resolv.conf` on the affected nodes to determine which mode they are using, then reprovision and reboot all nodes for a consistent configuration.


!!! info "Related pages"

    - [Cluster DNS](../../Overview/cluster_dns.md) -- Architecture, DNS ownership boundaries, and failure scenarios.
    - [Provision Config](../../Reference/Configuration/provision_config.md) -- Reference for the `dns_enabled` parameter.
    - [Known Limitations](../../Troubleshooting/known_limitations.md) -- Cluster DNS constraints.
