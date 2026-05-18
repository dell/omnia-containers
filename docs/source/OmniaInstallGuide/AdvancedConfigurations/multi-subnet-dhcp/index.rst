Multi-Subnet DHCP
=================

Multi-Subnet DHCP enables Omnia to support rack-based network provisioning where each rack has its own /24 subnet for the Admin (PXE) network. This architecture allows large-scale HPC and AI/ML deployments to have per-rack management subnets instead of a single shared subnet, improving scalability, failure isolation, and operational efficiency.

.. toctree::
   :maxdepth: 2

   concept-overview
   how-to-configuration
   concept-network-architecture
   how-to-best-practices

For troubleshooting assistance, see :doc:`../../troubleshootingguide/multi-subnet-dhcp`.

For parameter reference, see :doc:`../../Tables/network_spec`.
