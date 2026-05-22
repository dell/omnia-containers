Cluster DNS
============

Cluster DNS enables Omnia to provide dynamic hostname resolution for compute, Slurm, login, and Kubernetes nodes using CoreDNS-based DNS services instead of static ``/etc/hosts`` file management. This architecture eliminates O(N) SSH-based hosts file updates during provisioning and provides automatic hostname resolution for newly inventoried nodes.

.. toctree::
   :maxdepth: 2

   concept-overview
   how-to-configuration

For parameter reference, see :doc:`../../Tables/provision_config`.
