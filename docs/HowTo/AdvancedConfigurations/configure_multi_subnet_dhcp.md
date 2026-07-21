
# Configure Multi-Subnet DHCP

Multi-Subnet DHCP enables Omnia to support rack-based network provisioning where each rack has its own /24 subnet for the Admin (PXE) network. This architecture allows large-scale HPC and AI/ML deployments to have per-rack management subnets instead of a single shared subnet, improving scalability, failure isolation, and operational efficiency.

## Overview

Multi-Subnet DHCP is a network configuration approach where the Omnia Infrastructure Manager (OIM) manages multiple distinct subnets for the Admin (PXE) network, with each subnet typically serving a physical rack of servers. Instead of provisioning all nodes from a single large subnet, each rack receives its own /24 subnet (254 usable IP addresses), and nodes are assigned IPs from their rack-specific subnet during PXE boot.

The system uses DHCP relay agents on Top-of-Rack (ToR) switches to forward DHCP requests from remote subnets to the CoreDHCP server. The DHCP relay adds a `giaddr` (gateway IP address) field to each request, which identifies which subnet the request originated from. CoreDHCP then assigns an IP address from the appropriate subnet pool based on this information.

**Why use Multi-Subnet DHCP:**

- **Rack identification** -- Admin IP addresses directly indicate rack location. For example, IP `10.40.3.150` immediately identifies the server as being in Rack 3 (subnet `10.40.3.0/24`). This simplifies troubleshooting, maintenance, and physical asset management.
- **Failure isolation** -- Network issues are contained to individual racks. If Rack 2 experiences a network problem, Racks 1 and 3 remain unaffected. This improves cluster reliability and reduces the blast radius of failures.
- **Reduced broadcast traffic** -- Smaller broadcast domains (254 nodes per subnet instead of thousands) improve network performance and reduce unnecessary broadcast traffic across the cluster.
- **Scalability** -- Supports deployments with up to 254 racks (64,516 nodes) while maintaining manageable network segments. Each rack operates as an independent network segment, avoiding the scalability limits of large flat networks.
- **Clear network organization** -- Per-rack subnets provide a logical mapping between physical infrastructure (racks) and network addressing, making the network topology easier to understand and manage.

**How Multi-Subnet DHCP works:**

- **Dual-network architecture** -- The Admin (PXE) network is managed by Omnia's CoreSMD service and is used for PXE boot, OS provisioning, and host communication, configured with per-rack /24 subnets (each with its own DHCP pool managed by CoreSMD). The OOB/BMC network is preconfigured externally by the site network team, is used for iDRAC/BMC management and IPMI, is not managed by Omnia's DHCP, and is discovered by OME using preconfigured iDRAC IPs. This separation allows Omnia to focus on the provisioning network while the site team manages the out-of-band management infrastructure.
- **DHCP relay and giaddr routing** -- CoreDHCP (running on the OIM) serves multiple subnets from a single instance:
    1. A server in Rack 2 broadcasts a DHCP request on its local subnet (`10.40.3.0/24`).
    2. The ToR switch for Rack 2 receives the broadcast and forwards it to the CoreDHCP server. The relay adds a `giaddr` field set to the switch's interface IP (`10.40.3.1`).
    3. CoreDHCP reads the `giaddr` field and identifies that the request originated from the `10.40.3.0/24` subnet.
    4. CoreDHCP assigns an IP address from the pool configured for that subnet (for example, `10.40.3.100-10.40.3.200`).
    5. The DHCP response is sent back to the relay agent, which delivers it to the requesting node.

    This architecture allows a single CoreDHCP instance to manage IP assignment across dozens or hundreds of subnets without requiring multiple DHCP servers.

- **Configuration model** -- Multi-subnet DHCP configuration is specified in the `/opt/omnia/input/project_default/network_spec.yml` file using the `additional_subnets` field under `admin_network`. Each subnet entry defines a separate /24 network segment with its own DHCP pool.

!!! note

    In the example above, `10.40.0.0` is the subnet for the Admin/PXE network. The subnet `10.40.3.0` represents the Rack Subnet, where `10.40.3.1-254` are the server IP addresses present in the 3rd Rack. The 3rd octet specifies the rack number, while the 4th octet identifies the actual node.

### Use cases

Multi-Subnet DHCP is designed for the following deployment scenarios:

- **HPC/AI operators with per-rack subnets** -- Sites that organize their infrastructure by rack, with each rack having its own management subnet for operational clarity and failure isolation.
- **Sites with routed L3 management networks** -- Environments where the management network is routed (Layer-3) rather than a single large Layer-2 domain, requiring DHCP relay for PXE boot across subnets.
- **Large-scale deployments (20+ racks)** -- Deployments where a single /24 subnet (254 IPs) is insufficient for the number of nodes, requiring multiple subnets to scale the cluster.
- **Service nodes across multiple subnets** -- Deployments where service nodes (OIM, storage, login nodes) must discover, boot, and collect telemetry across many management subnets.
- **Sites enforcing network segmentation** -- Organizations with security or operational policies that require network segmentation, with each rack as a separate network segment.

### Infrastructure requirements

Multi-subnet DHCP requires a network infrastructure with:

- Routed Layer-3 management network with per-rack subnets.
- DHCP relay agents configured on each subnet's gateway/router.
- Network topology documented with rack IDs, subnet allocations, and gateway IPs.

## Prerequisites

- Omnia cluster deployed and operational.
- Network switches configured with VLANs and DHCP relay helper-address pointing to the OIM CoreSMD server.
- CoreSMD services deployed (CoreSMD v0.6.3+ required for multi-subnet support).
- Network topology documented with rack IDs, subnet allocations, gateway IPs, and VLAN assignments.
- DHCP pool ranges planned and validated to avoid conflicts with static IPs and the OIM admin IP.
- The `pxe_mapping_file.csv` is configured and aligned with your network topology. For sample configurations, see [PXE Mapping File](../../Reference/SampleFiles/pxe_mapping_file.md).

!!! important

    Multi-Subnet DHCP requires DHCP relay agents configured on each subnet's gateway/router. Without proper DHCP relay configuration, DHCP requests from remote subnets will not reach the CoreSMD server.

## Procedure

1. Use SSH to connect to the `omnia_core` container on the OIM node.

    ```bash title="Run on: OIM host"
    ssh omnia_core
    ```

2. Navigate to the input directory and view the current `network_spec.yml` file.

    ```bash title="Run on: omnia_core container"
    cd /opt/omnia/input/project_default/
    cat network_spec.yml
    ```

3. Edit the `network_spec.yml` file to add the `additional_subnets` field under the `admin_network` section.

    ```bash title="Run on: omnia_core container"
    vi network_spec.yml
    ```

4. Add the `additional_subnets` array with subnet entries for each rack. For example, for 2 racks:

    ```yaml title="File: /opt/omnia/input/project_default/network_spec.yml"
    Networks:
    - admin_network:
       oim_nic_name: "eno1"
       subnet: "10.40.1.0"
       netmask_bits: "24"
       primary_oim_admin_ip: "10.40.1.111"
       primary_oim_bmc_ip: ""
       dynamic_range: "10.40.1.201-10.40.1.250"
       dns: []
       ntp_servers: []
    - ib_network:
       subnet: "198.168.0.0"
       netmask_bits: "24"
       dns: []
    - additional_subnets:
      - subnet: "10.40.2.0"
        netmask_bits: "24"
        router: "10.40.2.1"
        dynamic_range: "10.40.2.190-10.40.2.200"
      - subnet: "10.40.3.0"
        netmask_bits: "24"
        router: "10.40.3.1"
        dynamic_range: "10.40.3.190-10.40.3.200"
    ```

    !!! note

        Leave `additional_subnets: []` (empty array) for single-subnet deployments. This maintains backward compatibility with existing configurations.

    For a full description of the `additional_subnets` parameters, see [network_spec.yml Reference](../../Reference/Configuration/network_spec.md).

5. Run the `prepare_oim.yml` playbook:

    ```bash title="Run on: omnia_core container"
    cd /omnia/prepare_oim
    ansible-playbook prepare_oim.yml
    ```

6. Exit the `omnia_core` container and view the CoreDHCP configuration on the OIM host.

    ```bash title="Run on: OIM host"
    exit
    cat /etc/openchami/configs/coredhcp.yaml
    ```

    The file will contain the single-subnet configuration as active, with the multi-subnet configuration commented out below it.

    !!! warning

        The line `# Single-subnet mode: positional argument format (coresmd v0.4.x)` must be commented (have `#` prefix). If this line is uncommented, it will cause CoreSMD and other OpenCHAMI service failures.

7. Stop OpenCHAMI services before modifying the container configuration.

    ```bash title="Run on: OIM host"
    systemctl stop openchami.target
    ```

8. Pull the new CoreSMD image which supports multi-subnet DHCP.

    ```bash title="Run on: OIM host"
    podman pull ghcr.io/openchami/coresmd:v0.6.3
    ```

9. Edit the CoreDHCP configuration to switch from single-subnet to multi-subnet mode.

    ```bash title="Run on: OIM host"
    vi /etc/openchami/configs/coredhcp.yaml
    ```

    Make the following changes:
    - Comment out the single-subnet `coresmd` and `bootloop` lines (add `#` prefix)
    - Uncomment the multi-subnet `coresmd` and `bootloop` blocks (remove `#` prefix)

    The multi-subnet configuration section begins with the comment `# Multi-subnet configuration (requires coresmd v0.6.x+)`. This is a heading within the YAML file, not a hyperlink. Below this heading, uncomment the `coresmd` and `bootloop` blocks to enable multi-subnet DHCP.

    !!! important

        Ensure the CA certificate file exists at `/root_ca/root_ca.crt` on the OIM host. This certificate is required for CoreSMD to communicate with the OIM. If the file is missing, copy it from the appropriate source and ensure it is mounted in the CoreSMD container with proper permissions.

10. Update the CoreSMD CoreDHCP container quadlet file to use the new image version.

    ```bash title="Run on: OIM host"
    vi /etc/containers/systemd/coresmd-coredhcp.container
    ```

    Change the `Image` line from `v0.4.3` to `v0.6.3`:

    ```ini title="File: /etc/containers/systemd/coresmd-coredhcp.container"
    [Unit]
    Description=The CoreSMD CoreDHCP container
    Wants=haproxy.service
    After=haproxy.service
    PartOf=openchami.target

    [Container]
    ContainerName=coresmd-coredhcp
    HostName=coresmd-coredhcp
    Image=ghcr.io/openchami/coresmd:v0.6.3

    # Capabilities
    AddCapability=NET_ADMIN
    AddCapability=NET_RAW

    # Volumes
    Volume=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem:/root_ca/root_ca.crt:ro,Z
    Volume=/etc/openchami/configs/coredhcp.yaml:/etc/coredhcp/config.yaml:ro,Z

    # Networks for the Container to use
    Network=host

    # Unsupported by generator options
    # Proxy settings
    PodmanArgs=--http-proxy=false

    [Service]
    Restart=always
    ```

11. Update the CoreSMD CoreDNS container quadlet file to use the new image version.

    ```bash title="Run on: OIM host"
    vi /etc/containers/systemd/coresmd-coredns.container
    ```

    Change the `Image` line from `v0.4.3` to `v0.6.3`:

    ```ini title="File: /etc/containers/systemd/coresmd-coredns.container"
    [Unit]
    Description=The CoreSMD CoreDNS container
    Wants=haproxy.service
    After=haproxy.service
    PartOf=openchami.target

    [Container]
    ContainerName=coresmd-coredns
    HostName=coresmd-coredns
    Image=ghcr.io/openchami/coresmd:v0.6.3
    Exec=/coredns

    # Capabilities
    AddCapability=NET_ADMIN
    AddCapability=NET_RAW

    # Volumes
    Volume=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem:/root_ca/root_ca.crt:ro,Z
    Volume=/etc/openchami/configs/Corefile:/Corefile:ro,Z

    # Networks for the Container to use
    Network=host

    # Unsupported by generator options
    # Proxy settings
    PodmanArgs=--http-proxy=false

    [Service]
    Restart=always
    ```

12. Reload the systemd daemon and restart the OpenCHAMI target to apply the changes.

    ```bash title="Run on: OIM host"
    systemctl daemon-reload
    systemctl restart openchami.target
    ```

### Example: ten-rack configuration

For a larger deployment with 10 racks:

```yaml title="File: /opt/omnia/input/project_default/network_spec.yml"
Networks:
- admin_network:
    oim_nic_name: "eno1"
    subnet: "10.40.1.0"
    netmask_bits: "24"
    primary_oim_admin_ip: "10.40.1.111"
    primary_oim_bmc_ip: ""
    dynamic_range: "10.40.1.201-10.40.1.250"
    dns: []
    ntp_servers: []
- additional_subnets:
    - subnet: "10.40.2.0"
      netmask_bits: "24"
      router: "10.40.2.1"
      dynamic_range: "10.40.2.190-10.40.2.200"
    - subnet: "10.40.3.0"
      netmask_bits: "24"
      router: "10.40.3.1"
      dynamic_range: "10.40.3.190-10.40.3.200"
    - subnet: "10.40.5.0"
      netmask_bits: "24"
      router: "10.40.5.1"
      dynamic_range: "10.40.5.100-10.40.5.200"
    - subnet: "10.40.7.0"
      netmask_bits: "24"
      router: "10.40.7.1"
      dynamic_range: "10.40.7.100-10.40.7.200"
    - subnet: "10.40.9.0"
      netmask_bits: "24"
      router: "10.40.9.1"
      dynamic_range: "10.40.9.100-10.40.9.200"
    - subnet: "10.40.11.0"
      netmask_bits: "24"
      router: "10.40.11.1"
      dynamic_range: "10.40.11.100-10.40.11.200"
    - subnet: "10.40.13.0"
      netmask_bits: "24"
      router: "10.40.13.1"
      dynamic_range: "10.40.13.100-10.40.13.200"
    - subnet: "10.40.15.0"
      netmask_bits: "24"
      router: "10.40.15.1"
      dynamic_range: "10.40.15.100-10.40.15.200"
    - subnet: "10.40.17.0"
      netmask_bits: "24"
      router: "10.40.17.1"
      dynamic_range: "10.40.17.100-10.40.17.200"
    - subnet: "10.40.19.0"
      netmask_bits: "24"
      router: "10.40.19.1"
      dynamic_range: "10.40.19.100-10.40.19.200"
```

This configuration supports 10 racks with non-overlapping /24 subnets, each with 100 IP addresses available for DHCP allocation.

## Verification

Verify that CoreSMD has registered the additional subnets. Expected output shows a `subnet=` directive for each additional subnet:

```bash title="Run on: OIM host"
podman logs coresmd-coredhcp | grep "subnet="
```

## Next Steps

- [Configure Inputs](../Setup/configure_inputs.md) -- Full input file configuration, including `additional_subnets`.
- [network_spec.yml Reference](../../Reference/Configuration/network_spec.md) -- Full parameter reference for admin, IB, and additional subnets.
- [PXE Mapping File](../../Reference/SampleFiles/pxe_mapping_file.md) -- Sample PXE mapping files for multi-subnet DHCP deployments.
- [Network Topologies](../../Overview/network_topologies.md) -- Multi-rack multi-subnet network topology diagram.

## Troubleshooting

**Core services fail to start after configuring multi-subnet DHCP**
   Ensure that services such as CoreSMD and other dependent services are in an active state. If any of the core services fail to start, use the following commands to check the error logs:

   ```bash title="Run on: OIM host"
   journalctl -xeu coresmd-coredhcp
   journalctl -xeu coresmd-coredns
   ```