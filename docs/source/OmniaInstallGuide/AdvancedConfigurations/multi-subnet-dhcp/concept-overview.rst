.. _concept-multi-subnet-dhcp-overview:

Multi-Subnet DHCP Overview
==========================

Multi-Subnet DHCP enables Omnia to support rack-based network provisioning where each rack has its own /24 subnet for the Admin (PXE) network. This architecture allows large-scale HPC and AI/ML deployments to have per-rack management subnets instead of a single shared subnet, improving scalability, failure isolation, and operational efficiency.

What is Multi-Subnet DHCP
---------------------------

Multi-Subnet DHCP is a network configuration approach where the Omnia Infrastructure Manager (OIM) manages multiple distinct subnets for the Admin (PXE) network, with each subnet typically serving a physical rack of servers. Instead of provisioning all nodes from a single large subnet, each rack receives its own /24 subnet (254 usable IP addresses), and nodes are assigned IPs from their rack-specific subnet during PXE boot.

The system uses DHCP relay agents on Top-of-Rack (ToR) switches to forward DHCP requests from remote subnets to the CoreDHCP server. The DHCP relay adds a ``giaddr`` (gateway IP address) field to each request, which identifies which subnet the request originated from. CoreDHCP then assigns an IP address from the appropriate subnet pool based on this information.

Why Use Multi-Subnet DHCP
---------------------------

Multi-Subnet DHCP addresses key challenges in large-scale HPC and AI/ML deployments:

**Rack Identification**
Admin IP addresses directly indicate rack location. For example, IP ``10.40.3.150`` immediately identifies the server as being in Rack 3 (subnet ``10.40.3.0/24``). This simplifies troubleshooting, maintenance, and physical asset management.

**Failure Isolation**
Network issues are contained to individual racks. If Rack 2 experiences a network problem, Racks 1 and 3 remain unaffected. This improves cluster reliability and reduces the blast radius of failures.

**Reduced Broadcast Traffic**
Smaller broadcast domains (254 nodes per subnet instead of thousands) improve network performance and reduce unnecessary broadcast traffic across the cluster.

**Scalability**
Supports deployments with up to 254 racks (64,516 nodes) while maintaining manageable network segments. Each rack operates as an independent network segment, avoiding the scalability limits of large flat networks.

**Clear Network Organization**
Per-rack subnets provide a logical mapping between physical infrastructure (racks) and network addressing, making the network topology easier to understand and manage.

How Multi-Subnet DHCP Works
----------------------------

Dual-Network Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~~

Omnia uses a dual-network model for multi-subnet deployments:

**Admin (PXE) Network**
- Managed by Omnia's CoreSMD service
- Used for PXE boot, OS provisioning, and host communication
- Configured with per-rack /24 subnets
- Each subnet has its own DHCP pool managed by CoreSMD

**OOB/BMC Network**
- Preconfigured externally by the site network team
- Used for iDRAC/BMC management and IPMI
- Not managed by Omnia's DHCP
- Discovered by OME using preconfigured iDRAC IPs

This separation allows Omnia to focus on the provisioning network while the site team manages the out-of-band management infrastructure.

DHCP Relay and giaddr Routing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The DHCP relay architecture enables CoreDHCP to serve multiple subnets from a single instance:

1. **Node Boot Request**: A server in Rack 2 broadcasts a DHCP request on its local subnet (``10.40.3.0/24``)

2. **DHCP Relay Forwarding**: The ToR switch for Rack 2 receives the broadcast and forwards it to the CoreDHCP server. The relay adds a ``giaddr`` field set to the switch's interface IP (``10.40.3.1``)

3. **Subnet Identification**: CoreDHCP reads the ``giaddr`` field and identifies that the request originated from the ``10.40.3.0/24`` subnet

4. **IP Assignment**: CoreDHCP assigns an IP address from the pool configured for that subnet (e.g., ``10.40.3.100-10.40.3.200``)

5. **Response Routing**: The DHCP response is sent back to the relay agent, which delivers it to the requesting node

.. note::
   In this example, ``10.40.0.0`` is the subnet for the Admin/PXE network. The subnet ``10.40.3.0`` represents the Rack Subnet, where ``10.40.3.1-254`` are the server IP addresses present in the 3rd Rack. The 3rd octet specifies the rack number, while the 4th octet identifies the actual node.

This architecture allows a single CoreDHCP instance to manage IP assignment across dozens or hundreds of subnets without requiring multiple DHCP servers.

Configuration Model
~~~~~~~~~~~~~~~~~~~

Multi-subnet DHCP configuration is specified in the ``/opt/omnia/input/project_default/network_spec.yml`` file using the ``additional_subnets`` field under ``admin_network``. Each subnet entry defines a separate /24 network segment with its own DHCP pool.

For detailed configuration examples and step-by-step procedures, see :doc:`how-to-configuration`.

Use Cases
---------

Multi-Subnet DHCP is designed for the following deployment scenarios:

**HPC/AI Operators with Per-Rack Subnets**
Sites that organize their infrastructure by rack, with each rack having its own management subnet for operational clarity and failure isolation.

**Sites with Routed L3 Management Networks**
Environments where the management network is routed (Layer-3) rather than a single large Layer-2 domain, requiring DHCP relay for PXE boot across subnets.

**Large-Scale Deployments (20+ Racks)**
Deployments where a single /24 subnet (254 IPs) is insufficient for the number of nodes, requiring multiple subnets to scale the cluster.

**Service Nodes Across Multiple Subnets**
Deployments where service nodes (OIM, storage, login nodes) must discover, boot, and collect telemetry across many management subnets.

**Sites Enforcing Network Segmentation**
Organizations with security or operational policies that require network segmentation, with each rack as a separate network segment.

Infrastructure Requirements
---------------------------

Multi-subnet DHCP requires a network infrastructure with:

- Routed Layer-3 management network with per-rack subnets
- DHCP relay agents configured on each subnet's gateway/router
- Network topology documented with rack IDs, subnet allocations, and gateway IPs

For detailed configuration prerequisites and step-by-step setup procedures, see :doc:`how-to-configuration`.

For a complete list of limitations and constraints, see :doc:`/limitations`.
