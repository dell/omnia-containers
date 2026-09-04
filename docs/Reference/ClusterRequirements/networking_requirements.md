# Networking Requirements

This section outlines the key networking requirements for the components used by Omnia to deploy HPC clusters. For more information about the supported devices and software, see [Support Matrix](../index.md#support-matrix).

## Networking

- Ensure admin and BMC switches are configured and reachable.

## InfiniBand

- Before deploying Omnia on clusters using InfiniBand (IB) networking, ensure that the Subnet Manager (SM) service is enabled and running on the InfiniBand switch or host.

!!! note

    Failure to meet this prerequisite may result in InfiniBand ports on hosts remaining in the Initializing state and prevent IB communication between nodes.

!!! info

    - [Networking Config](../Configuration/network_spec.md) -- Networking configuration.
    - [Configure Cluster DNS](../../HowTo/orchestrator/configure_cluster_dns.md) -- Cluster DNS configuration.
    - [Network Topology](../../Overview/network_topologies.md) -- Network topology configuration.


















