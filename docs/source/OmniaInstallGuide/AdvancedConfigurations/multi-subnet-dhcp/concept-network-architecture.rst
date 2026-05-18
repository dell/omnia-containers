.. _concept-multi-subnet-dhcp-network-architecture:

Multi-Subnet Network Architecture Guide
========================================

Multi-subnet network architecture defines how rack-based subnets are organized, routed, and configured for large-scale HPC and AI/ML deployments. This guide covers the dual-network model, DHCP relay architecture, ToR switch configuration, IP address planning, and security considerations for implementing multi-subnet DHCP with Omnia.

Network Architecture Model
---------------------------

Dual-Network Model
~~~~~~~~~~~~~~~~~~

Omnia uses a dual-network architecture that separates provisioning infrastructure from out-of-band management:

**Admin (PXE) Network**
- Managed by Omnia's CoreDHCP service
- Used for PXE boot, OS provisioning, and host communication
- Configured with per-rack /24 subnets (254 usable IPs per subnet)
- Each subnet has its own DHCP pool managed by CoreDHCP
- Nodes obtain IPs via DHCP with PXE boot and cloud-init

**OOB/BMC Network**
- Preconfigured externally by the site network team
- Used for iDRAC/BMC management and IPMI
- Not managed by Omnia's DHCP
- Discovered by OME using preconfigured iDRAC IPs
- Typically a separate VLAN or network segment

This separation allows Omnia to focus on the provisioning network while the site team manages the out-of-band management infrastructure independently.

Rack-Based Subnet Allocation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each physical rack is assigned a dedicated /24 subnet for the Admin network:

**Subnet Allocation Strategy**
- Each rack receives a unique /24 subnet (e.g., ``10.40.1.0/24``, ``10.40.3.0/24``, ``10.40.5.0/24``)
- Subnets are typically allocated with odd-numbered third octets to avoid conflicts
- Each subnet provides 254 usable IP addresses (256 total minus network and broadcast addresses)
- DHCP pool ranges are defined within each subnet (e.g., ``10.40.1.100-10.40.1.200``)

**Benefits of Rack-Based Allocation**
- IP addresses directly indicate rack location (``10.40.3.150`` = Rack 2)
- Network failures are isolated to individual racks
- Smaller broadcast domains improve performance
- Clear mapping between physical infrastructure and network addressing
- Simplified troubleshooting and maintenance

**Scalability Considerations**
- Supports up to 100 racks (25,400 nodes) with /24 subnets
- For larger deployments, consider /23 subnets (510 IPs) or additional rack groupings
- Plan for growth by reserving subnet ranges for future rack additions

DHCP Relay Architecture
----------------------

DHCP Relay Overview
~~~~~~~~~~~~~~~~~~~~

DHCP relay agents enable a single CoreDHCP server to manage IP assignment across multiple subnets. Without DHCP relay, DHCP broadcasts are confined to a single Layer-2 domain and cannot cross subnet boundaries.

**How DHCP Relay Works**
1. **Node Request**: A server broadcasts a DHCP request on its local subnet
2. **Relay Forwarding**: The ToR switch receives the broadcast and forwards it to the CoreDHCP server
3. **giaddr Addition**: The relay adds a ``giaddr`` (gateway IP address) field set to the switch's interface IP
4. **Subnet Identification**: CoreDHCP reads ``giaddr`` to identify which subnet the request originated from
5. **IP Assignment**: CoreDHCP assigns an IP from the pool configured for that subnet
6. **Response Routing**: The DHCP response is sent back to the relay, which delivers it to the requesting node

**giaddr-Based Routing**
The ``giaddr`` field is critical for subnet-aware IP assignment:
- ``giaddr`` = Router IP of the subnet where the request originated
- CoreDHCP matches ``giaddr`` to registered ``subnet=`` directives
- IP allocation is routed to the correct subnet pool based on this match
- Enables single CoreDHCP instance to serve dozens of subnets

CoreDHCP Configuration
~~~~~~~~~~~~~~~~~~~~~

Omnia generates CoreDHCP configuration with subnet-aware directives:

**subnet= Directive**
- Registers a subnet with its gateway for giaddr matching
- Format: ``subnet=CIDR,ROUTER``
- Example: ``subnet=10.40.1.0/24,10.40.1.1``
- Repeatable for each additional subnet

**subnet_pool= Directive**
- Defines per-subnet IP allocation pools
- Format: ``subnet_pool=CIDR,START_IP,END_IP``
- Example: ``subnet_pool=10.40.1.0/24,10.40.1.100,10.40.1.200``
- Used by the bootloop plugin for temporary IP allocation

**Configuration Example**
Generated CoreDHCP configuration for 2 subnets:

.. code-block:: text

   # Subnet 1: Rack 1
   subnet=10.40.1.0/24,10.40.1.1
   subnet_pool=10.40.1.0/24,10.40.1.100,10.40.1.200

   # Subnet 2: Rack 2
   subnet=10.40.3.0/24,10.40.3.1
   subnet_pool=10.40.3.0/24,10.40.3.100,10.40.3.200

Network Topology Design Patterns
--------------------------------

Topology A: Routed + DHCP Relay
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**
Each rack is on a routed Layer-3 management network with DHCP relay on ToR switches.

**Characteristics**
- ToR switches configured with VLANs and SVIs for each rack subnet
- DHCP relay helper-address points to CoreDHCP server IP
- Routing between OIM and all rack subnets must be configured
- Most common topology for large-scale deployments

**Advantages**
- Scalable to hundreds of racks
- Clear network segmentation
- Failure isolation at rack level
- Flexible routing and ECMP support

**Requirements**
- Layer-3 capable ToR switches
- Proper routing configuration
- DHCP relay configured on each ToR switch
- CoreDHCP server reachable from all subnets

**Example**
- Rack 1: VLAN 1101, Subnet ``10.40.1.0/24``, Gateway ``10.40.1.1``
- Rack 2: VLAN 1103, Subnet ``10.40.3.0/24``, Gateway ``10.40.3.1``
- OIM: Connected to all subnets via routing

Topology B: Multi-NIC
~~~~~~~~~~~~~~~~~~~

**Description**
OIM has multiple NICs connected to different subnets with direct Layer-2 connectivity.

**Characteristics**
- OIM NICs connected directly to each rack subnet
- No DHCP relay required (direct Layer-2 connectivity)
- Each NIC serves a specific rack or group of racks
- Simpler network configuration but limited scalability

**Advantages**
- No DHCP relay configuration needed
- Direct Layer-2 connectivity
- Simpler troubleshooting
- Lower latency for local racks

**Requirements**
- Sufficient NIC ports on OIM
- Direct Layer-2 connectivity to each subnet
- VLAN trunking if using single NIC with multiple VLANs
- Limited by physical NIC availability

**Example**
- OIM NIC 1: Connected to Rack 1 subnet ``10.40.1.0/24``
- OIM NIC 2: Connected to Rack 2 subnet ``10.40.3.0/24``
- OIM NIC 3: Connected to Rack 3 subnet ``10.40.5.0/24``

Topology C: Hybrid
~~~~~~~~~~~~~~~~~

**Description**
Combination of routed and direct connections for flexibility.

**Characteristics**
- Some racks use DHCP relay (routed topology)
- Some racks use direct connectivity (multi-NIC topology)
- Provides flexibility for complex environments
- Can mix approaches based on rack requirements

**Advantages**
- Maximum flexibility
- Can optimize per-rack based on requirements
- Supports gradual migration from one topology to another
- Adaptable to existing network infrastructure

**Requirements**
- Both routing and direct connectivity configured
- Careful planning to avoid routing loops
- Clear documentation of which racks use which approach

ToR Switch Configuration
-----------------------

VLAN Configuration
~~~~~~~~~~~~~~~~~~

Configure VLANs on ToR switches to isolate rack subnets:

**Example VLAN Configuration**

.. code-block:: text

   # Rack 1 ToR Switch
   vlan 1101
     name Admin-Rack1
     exit

   interface Ethernet1/1
     description Rack 1 Server Port
     switchport access vlan 1101
     exit

   interface Port-channel1
     description Uplink to Core Switch
     switchport trunk allowed vlan add 1101
     exit

SVI Configuration
~~~~~~~~~~~~~~~~

Configure Switched Virtual Interfaces (SVIs) as gateway IPs for each subnet:

**Example SVI Configuration**

.. code-block:: text

   # Rack 1 ToR Switch
   interface Vlan1101
     description Rack 1 Admin Gateway
     ip address 10.40.1.1/24
     no shutdown
     exit

   interface Vlan1102
     description Rack 1 OOB Gateway
     ip address 192.168.1.1/24
     no shutdown
     exit

DHCP Relay Configuration
~~~~~~~~~~~~~~~~~~~~~~

Configure DHCP relay helper-address on each ToR switch:

**Example DHCP Relay Configuration**

.. code-block:: text

   # Rack 1 ToR Switch
   ip dhcp relay
   ip helper-address 172.16.107.254
   interface Vlan1101
     ip helper-address 172.16.107.254
     exit

.. important::
   The helper-address must point to the CoreDHCP server IP (OIM admin IP). Ensure routing is configured so the ToR switch can reach the CoreDHCP server.

Routing Configuration
~~~~~~~~~~~~~~~~~~

Configure routing to enable connectivity between OIM and all rack subnets:

**Example Static Routes on OIM**

.. code-block:: text

   # OIM routing table
   ip route add 10.40.1.0/24 via 172.16.1.1
   ip route add 10.40.3.0/24 via 172.16.3.1
   ip route add 10.40.5.0/24 via 172.16.5.1

**Example ECMP for Redundancy**

.. code-block:: text

   # OIM routing with ECMP
   ip route add 10.40.0.0/16 nexthop 172.16.1.1 weight 1
   ip route add 10.40.0.0/16 nexthop 172.16.2.1 weight 1

ACL Policies and Security
-----------------------

Access Control Lists
~~~~~~~~~~~~~~~~~~

Configure ACLs to restrict access and enforce security policies:

**Example ACL for Rack Subnet**

.. code-block:: text

   # Allow DHCP from rack subnet
   access-list 101 permit udp any eq bootpc any eq bootps
   access-list 101 permit udp any eq bootps any eq bootpc

   # Allow PXE boot
   access-list 101 permit tcp any any eq 69
   access-list 101 permit udp any any eq 69

   # Deny other traffic from rack subnet
   access-list 101 deny ip 10.40.1.0 0.0.0.255 any

   # Apply to interface
   interface Vlan1101
     ip access-group 101 in
     exit

VRF Isolation
~~~~~~~~~~~~~

For enhanced security, consider VRF (Virtual Routing and Forwarding) isolation:

**VRF Configuration Example**

.. code-block:: text

   vrf definition Rack-Mgmt
     rd 65000:1
     route-target import 65000:1
     route-target export 65000:1
     exit

   interface Vlan1101
     vrf forwarding Rack-Mgmt
     ip address 10.40.1.1/24
     exit

iDRAC Access Control
~~~~~~~~~~~~~~~~~~

Configure ACLs to restrict iDRAC access from OOB network:

**Example iDRAC ACL**

.. code-block:: text

   # Allow iDRAC access only from management network
   access-list 102 permit tcp 192.168.0.0 0.0.255.255 any eq 443
   access-list 102 permit tcp 192.168.0.0 0.0.255.255 any eq 5900-5905

   # Deny iDRAC access from other networks
   access-list 102 deny tcp any any eq 443
   access-list 102 deny tcp any any eq 5900-5905

IP Address Planning
------------------

Subnet Allocation Strategy
~~~~~~~~~~~~~~~~~~~~~~~~

Plan subnet allocations systematically to avoid conflicts:

**Allocation Guidelines**
- Use consistent subnet patterns (e.g., odd-numbered third octets)
- Document all allocations in an IPAM system
- Reserve subnet ranges for future growth
- Align subnet allocation with rack numbering scheme

**Example Allocation Table**

| Rack ID | Subnet         | Gateway        | VLAN   | DHCP Pool Range      |
|---------|----------------|----------------|--------|---------------------|
| 1       | 10.40.1.0/24   | 10.40.1.1      | 1101   | 10.40.1.100-10.40.1.200 |
| 2       | 10.40.3.0/24   | 10.40.3.1      | 1103   | 10.40.3.100-10.40.3.200 |
| 3       | 10.40.5.0/24   | 10.40.5.1      | 1105   | 10.40.5.100-10.40.5.200 |
| 4       | 10.40.7.0/24   | 10.40.7.1      | 1107   | 10.40.7.100-10.40.7.200 |

IPAM Considerations
~~~~~~~~~~~~~~~~~~

Maintain an IP Address Management (IPAM) system to track allocations:

**IPAM Best Practices**
- Record all subnet allocations and assignments
- Track static IP assignments (gateways, OIM, service nodes)
- Document DHCP pool ranges and usage
- Monitor IP utilization per subnet
- Plan for subnet exhaustion and expansion

**IPAM Tools**
- Spreadsheet for small deployments
- Dedicated IPAM software (phpIPAdmin, NetBox) for larger deployments
- Integration with configuration management for automation

Performance Considerations
--------------------------

Broadcast Domain Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Smaller broadcast domains improve network performance:

**Benefits**
- Reduced broadcast traffic
- Lower ARP cache size
- Faster network convergence
- Improved troubleshooting

**Metrics**
- /24 subnet: 254 hosts, manageable broadcast domain
- /23 subnet: 510 hosts, larger broadcast domain
- /22 subnet: 1022 hosts, may require optimization

Routing Table Size
~~~~~~~~~~~~~~~~~

Monitor routing table size for scalability:

**Guidelines**
- Each subnet adds one routing entry
- For 100 subnets: ~100 routing entries (manageable)
- For 1000 subnets: Consider route aggregation
- Use route summarization where possible

**Route Aggregation Example**

.. code-block:: text

   # Individual routes (100 subnets)
   ip route add 10.40.1.0/24 via 172.16.1.1
   ip route add 10.40.3.0/24 via 172.16.3.1
   ...

   # Aggregated route (summarized)
   ip route add 10.40.0.0/16 via 172.16.1.1

DHCP Response Latency
~~~~~~~~~~~~~~~~~~~~

Monitor DHCP response times across subnets:

**Factors Affecting Latency**
- Network hops between subnet and CoreDHCP
- CoreDHCP server load
- DHCP relay processing time
- Network congestion

**Optimization**
- Place CoreDHCP server centrally in network topology
- Use ECMP for load balancing
- Monitor CoreDHCP performance metrics
- Consider multiple CoreDHCP instances for very large deployments

Next Steps
----------

For configuration procedures, see :doc:`how-to-configuration`.

For operational guidelines, see :doc:`how-to-best-practices`.

For troubleshooting assistance, see :doc:`../../troubleshootingguide/multi-subnet-dhcp`.

For an overview of multi-subnet DHCP, see :doc:`concept-overview`.
