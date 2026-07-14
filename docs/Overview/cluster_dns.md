
# Cluster DNS

Cluster DNS provides dynamic hostname resolution for Omnia-managed cluster nodes using CoreDNS-based DNS services instead of static `/etc/hosts` file management. This eliminates O(N) SSH-based hosts file updates during provisioning and provides automatic hostname resolution for newly inventoried nodes without requiring playbook re-runs.

For configuration steps, see [Configure Cluster DNS](../HowTo/Networking/configure_cluster_dns.md).


## What Is Cluster DNS

Cluster DNS is a DNS-based hostname resolution system that leverages **coresmd**, the CoreDNS instance deployed as part of the OpenCHAMI stack on the Omnia Infrastructure Manager (OIM) node. coresmd queries the OpenCHAMI State Manager Daemon (SMD) inventory every 30 seconds and automatically generates forward A records for all inventoried nodes.

When enabled, compute nodes resolve hostnames via DNS queries to the OIM instead of reading from local `/etc/hosts` files. This provides a single source of truth for hostname-to-IP mappings and eliminates the need for manual hosts file synchronization across the cluster.

!!! note

    Omnia does not manage InfiniBand fabric DNS. MPI over InfiniBand uses UCX auto-detection for transport selection and does not rely on DNS for IB fabric discovery.


## DNS Ownership Boundaries

### Omnia Cluster-Scoped DNS

Omnia manages and is responsible for the following:

- **Cluster node resolution** -- Forward (A record) hostname resolution for all compute, Slurm controller, login, and Kubernetes nodes.
- **Dynamic record generation** -- DNS records are generated automatically from the OpenCHAMI SMD inventory via coresmd.
- **DNS zone serving** -- coresmd serves the cluster domain (for example, `hpc.cluster`).
- **Cloud-init `/etc/resolv.conf` configuration** -- Compute nodes are configured to use coresmd as their nameserver at boot.
- **Kubernetes CoreDNS forwarding** -- The Kubernetes CoreDNS ConfigMap is patched to forward cluster-domain queries to the OIM coresmd instance.
- **Admin network DNS forwarding** -- coresmd forwards non-cluster DNS queries (for example, `google.com`) to the upstream DNS servers configured in `admin_network.dns` in `network_spec.yml`.

### Enterprise DNS (Site Responsibility)

The site network administrator retains responsibility for:

- **Enterprise DNS infrastructure** -- Upstream DNS server configuration, enterprise-wide DNS zones, and DNS security policies.
- **Out-of-band (OOB) network DNS** -- BMC/iDRAC hostname resolution and switch management interface DNS.
- **InfiniBand fabric DNS** -- InfiniBand-specific hostname records and Subnet Manager (SM) hostname resolution. Omnia does not manage this.


## DNS Architecture

### Legacy Behavior (`dns_enabled: false`)

By default, Omnia uses static `/etc/hosts` file management:

- **At boot (cloud-init)** -- Cloud-init renders the hostname-to-IP mapping for all cluster nodes into `/etc/hosts` as a snapshot at provisioning time. The mapping does not update if nodes are added or removed later.
- **OIM `/etc/hosts` update** -- During `provision.yml` execution, stale entries are removed and fresh entries are added for every node in the PXE mapping file. This is an O(N) operation that takes several minutes for large clusters.
- **Slurm node `/etc/hosts` update** -- Each reachable Slurm node is updated over SSH, an O(N x M) operation.
- **Limitations** -- New nodes are not resolvable until reprovisioned, removed nodes leave stale entries, and races or unreachable nodes can cause inconsistent `/etc/hosts` files across the cluster.

### CoreDNS Behavior (`dns_enabled: true`)

When enabled, Omnia uses dynamic DNS resolution instead:

- **At boot (cloud-init)** -- Cloud-init writes `/etc/resolv.conf` with the OIM IP as the nameserver and does not append peer entries to `/etc/hosts`.
- **OIM and Slurm node `/etc/hosts` updates are skipped** -- Only the localhost entry is ensured. Munge key distribution and Slurm service restart logic continue to function normally.

When `dns_enabled: true`, Omnia configures `/etc/resolv.conf` on both the **OIM host** and **omnia_core** as follows:

```text title="Example: /etc/resolv.conf"
search <domain_name> <existing-search-domains>
nameserver <cluster_boot_ip>
nameserver <existing-nameservers>
```

- `search <domain_name>` allows short hostnames (for example, `nid001`) to resolve as FQDNs (`nid001.hpc.cluster`).
- `nameserver <cluster_boot_ip>` points to coresmd on the cluster boot IP.
- Existing nameservers are preserved as a fallback for external DNS queries.

!!! note

    `resolv.conf` is protected with the immutable attribute (`chattr +i`) on the OIM host to prevent NetworkManager from overwriting it.

### Hybrid Mode: Custom Hostnames with DNS

When `dns_enabled: true`, Omnia supports a hybrid mode that combines DNS-based resolution for NID-based hostnames with static `/etc/hosts` entries for custom hostnames defined in the PXE mapping file.

- CoreDNS generates records automatically from the SMD inventory using a fixed NID-based pattern: `{cluster_shortname}{zero_padded_id}.{cluster_domain}`. For example, with `cluster_shortname=nid` and `cluster_nidlength=3`, node ID 1 produces `nid001.hpc.cluster`.
- CoreDNS does **not** use custom hostnames defined in the PXE mapping file (for example, `headnode`, `compute1`); these resolve via `/etc/hosts`, which is always populated from the PXE mapping regardless of the `dns_enabled` setting.
- Resolution order (defined by `/etc/nsswitch.conf`) checks `/etc/hosts` first, then DNS.

| Hostname | Resolution Source | Example |
|----------|--------------------|---------|
| `nid001.hpc.cluster` | CoreDNS (coresmd) | FQDN from SMD NID pattern |
| `nid001` | CoreDNS (via `search` domain) | Short name appended with cluster domain |
| `headnode` | `/etc/hosts` | Custom name from PXE mapping |

```text title="DNS resolution flow"
Compute Node                    OIM Node
+----------------+             +------------------+
| Application    |             | coresmd          |
| (Slurm/MPI)    |             | (CoreDNS + SMD)  |
|    |           |             |    |             |
|    v           |    DNS      |    v             |
| glibc resolver | ----------> | coresmd plugin   |
| /etc/resolv.conf|   UDP:53   | queries SMD      |
|    |           |             | every 30s        |
|    v           |  A record   |    |             |
| IP address     | <---------- | cached response  |
+----------------+             +------------------+
                                      |
                                      v (non-cluster queries)
                                 upstream DNS forwarders
                                 (admin_network.dns)
```

Every 30 seconds, coresmd queries SMD for the current node inventory and creates a record `{cluster_shortname}{zero_padded_id}.{cluster_domain} -> <admin_ip>` for each node. Non-cluster queries are forwarded to the upstream DNS servers from `admin_network.dns`.


## High Availability and Failure Scenarios

coresmd runs as a single container on the OIM node. No VIP failover or load balancing is currently implemented, so the OIM node is a single point of failure for DNS resolution.

!!! warning

    In the current implementation, the OIM node is a single point of failure for DNS resolution. For production deployments requiring high availability, ensure the OIM node is deployed with appropriate redundancy and monitoring.

| Scenario | Behavior | Mitigation |
|----------|----------|------------|
| **coresmd unreachable** (OIM down or container stopped) | DNS queries time out after 1 second, retry once, then fail. All resolution fails until coresmd is restored. Slurm jobs cannot start. | Restart the coresmd container; monitor coresmd health via Prometheus metrics on port 9153. |
| **SMD unreachable from coresmd** | coresmd continues serving records from its last cached SMD query (up to 30s stale). New nodes are not resolvable until SMD recovers. | Restart the SMD service and monitor SMD connectivity. |
| **Node not in SMD** | coresmd has no record for the node; queries return `NXDOMAIN`. Slurm marks the node as `DOWN`. | Ensure the discovery playbook registered the node in SMD. |
| **Domain misconfiguration** | `domain_name` in OIM metadata does not match the zone configured in coresmd, causing `NXDOMAIN`. | `domain_name` is set once during `prepare_oim.yml` and used consistently; verify OIM metadata if resolution fails. |
| **Upstream DNS failure** | Non-cluster queries (for example, `google.com`) fail, but cluster-internal resolution continues to work. | Configure at least two reliable upstream DNS servers in `admin_network.dns`. |

For a complete list of Cluster DNS limitations and constraints, see [Known Limitations](../Troubleshooting/known_limitations.md).


## Fabric-Aware Resolution

### Ethernet (Admin/PXE Network)

coresmd returns the admin/PXE IP address for each node from SMD. This is the IP address used for Slurm hostname resolution, cluster management, and MPI-over-Ethernet peer discovery. Only forward A records are generated (`nid001.hpc.cluster -> 172.16.0.1`); no reverse DNS (PTR) records or fabric-specific suffixes (for example, `-ib`) are supported.

### InfiniBand Fabric

coresmd does not generate InfiniBand-specific DNS records (for example, `nid001-ib.hpc.cluster`), and reverse DNS for IB addresses is not provided. MPI implementations typically use UCX auto-detection to discover IB interfaces directly via the RDMA/Verbs API, so explicit IB DNS records are rarely required. If your MPI implementation requires IB-specific hostnames, configure them manually in `/etc/hosts` on the relevant nodes.

### Integration with Upstream DNS and Kubernetes

- **Upstream forwarding** -- Non-cluster queries are forwarded to the servers in `admin_network.dns`, used by cluster nodes to resolve external services, internal enterprise services, and by Kubernetes pods to resolve external APIs.
- **Kubernetes CoreDNS patching** -- When DNS is enabled, the first Kubernetes control plane node's cloud-init script patches the Kubernetes CoreDNS ConfigMap with a forward zone (`<domain_name>:53 { errors; cache 30; forward . <admin_nic_ip> }`) and restarts the CoreDNS deployment. This enables MPI-over-Kubernetes workloads and host-network pods to resolve Slurm/compute hostnames from within pods.


## Use Cases and Operational Expectations

Cluster DNS is designed for:

- **Large-scale clusters (100+ nodes)** -- Eliminates O(N x M) SSH operations for `/etc/hosts` management and reduces provisioning time.
- **Dynamic node environments** -- New nodes are automatically resolvable within 30 seconds, with no playbook re-run required.
- **MPI-over-Kubernetes workloads** -- Enables hybrid Slurm/Kubernetes deployments and containerized MPI workloads.
- **Sites with strict network policies** -- Removes the SSH-based `/etc/hosts` configuration push, reducing attack surface; DNS queries use UDP/TCP port 53 only.

**Resolution latency** -- Cached queries are served from coresmd's in-memory cache (30s TTL) with sub-millisecond latency. coresmd refreshes its SMD inventory cache every 30 seconds, so new nodes are resolvable within 30 seconds of registration and removed nodes stop resolving within the same window.

**Node lifecycle** -- Adding a node (registering it in SMD) makes it resolvable within 30 seconds with no playbook re-run. Removing a node from SMD drops its record within 30 seconds and no `/etc/hosts` cleanup is needed. Changing `dns_enabled` requires reprovisioning (reboot) so cloud-init can write the appropriate resolver configuration.


!!! info "Related pages"

    - [Configure Cluster DNS](../HowTo/Networking/configure_cluster_dns.md) -- Enable, verify, and troubleshoot Cluster DNS.
    - [Provision Config](../Reference/Configuration/provision_config.md) -- Reference for the `dns_enabled` parameter.
    - [Known Limitations](../Troubleshooting/known_limitations.md) -- Cluster DNS constraints.
