Network Topologies
===================

Omnia supports multiple network topology configurations to accommodate different deployment scenarios, hardware configurations, and operational requirements. The network topology defines how cluster nodes are interconnected through various network segments including Admin (PXE), BMC (iDRAC), Public, and InfiniBand networks.

**Choosing the Right Topology**

Select a network topology based on your infrastructure requirements:

* **Dedicated Setup**: Use when you have dedicated network infrastructure with separate physical connections for BMC (iDRAC) management. This provides the highest level of isolation and security for out-of-band management.

* **Shared LOM Setup**: Ideal for deployments where network port availability is limited. The Administration and BMC networks share the same ethernet segment, reducing cabling requirements while maintaining functionality.

* **Hybrid Setup**: Suitable for environments where the Omnia Infrastructure Manager (OIM) and special nodes (head, login) require public network access, while compute nodes use a shared LOM network for management and BMC.

* **Multi-Rack Multi-Subnet Setup**: Designed for large-scale HPC and AI/ML deployments spanning multiple racks. Each rack has its own /24 subnet for the Admin network, improving scalability, failure isolation, and operational efficiency.

All topologies support classless IP addressing, allowing different subnets for Admin, BMC, Public, and Additional networks. For all topologies, OME-based BMC Discovery is the recommended discovery mechanism.

.. toctree::

    dedicated
    lom
    Hybrid
    multi-rack-multi-subnet
