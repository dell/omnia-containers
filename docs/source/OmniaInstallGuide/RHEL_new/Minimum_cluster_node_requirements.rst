Omnia Minimum Cluster Node Requirements
========================================

This section describes the minimum number of cluster nodes required for deployments supported by Omnia, categorized by functional role.

Complete Deployment Supported by Omnia (Slurm and Service Kubernetes Cluster) – x86_64 and aarch64
---------------------------------------------------------------------------------------------------

The following table lists the minimum cluster node requirements for the complete deployment supported by Omnia with Slurm and Service Kubernetes Clusters, using both x86_64 and aarch64. 

**Node Requirements**

+-----------------------------------+--------------+----------+
| Role                              | Architecture | Quantity |
+===================================+==============+==========+
| Omnia Infrastructure Manager (OIM)| x86_64       | 1        |
+-----------------------------------+--------------+----------+
| Service Kubernetes Control Plane  | x86_64       | 3        |
+-----------------------------------+--------------+----------+
| Service Kubernetes Node           | x86_64       | 1        |
+-----------------------------------+--------------+----------+
| Slurm Control Node                | x86_64       | 1        |
+-----------------------------------+--------------+----------+
| Slurm Node                        | aarch64      | 1        |
+-----------------------------------+--------------+----------+
| Login Node                        | aarch64      | 1        |
+-----------------------------------+--------------+----------+
| Login Compiler Node               | aarch64      | 1        |
+-----------------------------------+--------------+----------+

Complete Deployment Supported by Omnia (Slurm and Service Kubernetes Cluster) – x86_64 Only
------------------------------------------------------------------------------------

The following table lists the minimum cluster node requirements for complete deployment supported by Omnia with Slurm and Service Kubernetes Clusters, using only x86_64 servers.

**Node Requirements**

+-----------------------------------+--------------+----------+
| Role                              | Architecture | Quantity |
+===================================+==============+==========+
| Omnia Infrastructure Manager (OIM)| x86_64       | 1        |
+-----------------------------------+--------------+----------+
| Service Kubernetes Control Plane  | x86_64       | 3        |
+-----------------------------------+--------------+----------+
| Service Kubernetes Node           | x86_64       | 1        |
+-----------------------------------+--------------+----------+
| Slurm Control Node                | x86_64       | 1        |
+-----------------------------------+--------------+----------+
| Slurm Node                        | x86_64       | 1        |
+-----------------------------------+--------------+----------+
| Login Node                        | x86_64       | 1        |
+-----------------------------------+--------------+----------+
| Login Compiler Node               | x86_64       | 1        |
+-----------------------------------+--------------+----------+

Slurm-Only Deployment Supported by Omnia – x86_64
-----------------------------------------------------

The following table lists the minimum cluster node requirements for Slurm-only deployment supported by Omnia.

**Node Requirements**

+------------------------------------+--------------+----------+
| Role                               | Architecture | Quantity |
+====================================+==============+==========+
| Omnia Infrastructure Manager (OIM) | x86_64       | 1        |
+------------------------------------+--------------+----------+
| Slurm Control Node                 | x86_64       | 1        |
+------------------------------------+--------------+----------+
| Slurm Node                         | x86_64       | 1        |
+------------------------------------+--------------+----------+
| Login Node                          | x86_64       | 1        |
+------------------------------------+--------------+----------+
| Login Compiler Node                | x86_64       | 1        |
+------------------------------------+--------------+----------+

Service Kubernetes Cluster-Only Deployment Supported by Omnia (iDRAC Telemetry) – x86_64
---------------------------------------------------------------------------------------------

The following table lists the minimum cluster node requirements for Service Kubernetes Cluster-only deployment supported by Omnia. This deployment is intended for iDRAC telemetry collection.

**Node Requirements**

+----------------------------------+--------------+----------+
| Role                             | Architecture | Quantity |
+==================================+==============+==========+
| Omnia Infrastructure Manager     | x86_64       | 1        |
+----------------------------------+--------------+----------+
| Service Kubernetes Control Plane | x86_64       | 3        |
+----------------------------------+--------------+----------+
| Service Kubernetes Node          | x86_64       | 1        |
+----------------------------------+--------------+----------+
