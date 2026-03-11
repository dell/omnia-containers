Types of Clusters Deployed by Omnia
======================================

Omnia can deploy and configure PowerEdge servers (nodes), and build clusters that use Slurm or Kubernetes (or both) for workload management. Apart from the general compute nodes of the cluster, a cluster deployed by Omnia has the following node:

**Omnia Infrastructure Manager (OIM)**: The OIM functions as a central management node in a cluster, separate from the actual computing nodes. It acts as the main hub of the cluster, hosting the Omnia provisioning and monitoring tool. When setting up the cluster, the Omnia repository is cloned and downloaded to the OIM.


Service Kubernetes Cluster
----------------------------

Components of a Kubernetes cluster are:

* **Head node**: In a Kubernetes cluster deployed by Omnia, the head node is the ``kube_control_plane`` used to manage Kubernetes jobs on the cluster.
* **Compute nodes**: In a Kubernetes cluster, the ``kube_node`` function as the compute nodes.

Slurm Cluster
----------------

Components of a Slurm cluster are:

* **Head node**: In an HPC cluster, the head node is a  ``slurm_control_node`` used to manage slurm jobs on the cluster.
* **Compute nodes**: In an HPC cluster, a compute node is a ``slurm_node``.
* **[Optional] Login node**: In Omnia, a login node serves as an extra layer of authentication. Users are required to authenticate themselves through this additional login node, which is configured by Omnia. This setup allows the cluster administrator to restrict direct access to the head node (also referred to as ``slurm_control_node``) by users. The login node acts as a gateway for users to securely access the cluster.
* **[Optional] Login/Compiler node**: In Omnia, a login/compiler node is an optional node that provides users with access to the cluster and a development environment to compile and build applications. It is configured with compilers, libraries, and development tools, allowing users to prepare their applications before submitting jobs to the compute nodes.