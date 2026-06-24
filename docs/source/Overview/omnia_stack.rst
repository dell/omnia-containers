Omnia Stack
============

Omnia provides two distinct deployment models tailored to different workload requirements: the Kubernetes Stack for containerized applications and the Slurm Stack for high-performance computing (HPC) workloads. These stacks can be deployed independently or in a converged configuration where both Kubernetes and Slurm coexist on the same infrastructure, enabling organizations to support diverse workload types within a single management framework.

The following diagrams illustrate the architectural layers and component relationships for each deployment model.

Omnia Kubernetes Stack
----------------------

.. image::  ../images/omnia-k8s.png

The Kubernetes stack provides a complete container orchestration platform for deploying and managing containerized applications. Key components include:

- **Infrastructure Layer**: Bare-metal or virtualized Dell PowerEdge servers with iDRAC management
- **Operating System**: RHEL-based provisioning with cloud-init configuration
- **Container Runtime**: Containerd for running containerized workloads
- **Orchestration**: Kubernetes cluster with control plane and worker nodes
- **Networking**: Calico CNI for pod networking, MetalLB for load balancing
- **Storage**: CSI drivers for PowerScale and other storage backends
- **Monitoring and Telemetry**: VictoriaMetrics for metrics collection, Kafka for telemetry data streaming
- **Application Layer**: User-deployed containerized workloads

Omnia Slurm Stack
-----------------

.. image:: ../images/omnia-slurm.png

The Slurm stack provides a workload manager optimized for HPC and batch job scheduling. Key components include:

- **Infrastructure Layer**: Bare-metal or virtualized Dell PowerEdge servers with iDRAC management
- **Operating System**: RHEL-based provisioning with cloud-init configuration
- **Resource Management**: Slurm Workload Manager with control and compute nodes
- **Networking**: InfiniBand for high-performance interconnects, Ethernet for management
- **Storage**: NFS mounts for shared filesystem access
- **GPU Support**: NVIDIA GPU provisioning with CUDA Toolkit and DCGM for GPU-enabled nodes
- **Monitoring and Telemetry**: LDMS and other HPC-specific monitoring tools
- **Application Layer**: Batch jobs, MPI workloads, and other HPC applications

Virtual Deployment Considerations
---------------------------------

The diagrams show Virtual OS and Virtual Hardware blocks to represent scenarios where Omnia can be deployed on virtualized infrastructure. However, Omnia is primarily designed and tested for bare-metal deployments to ensure optimal performance for both Kubernetes and Slurm workloads. Virtual deployments may be supported for specific test or development scenarios, but production environments should use bare-metal hardware to avoid performance limitations and ensure full compatibility with all Omnia features.
