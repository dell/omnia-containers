# Configuration

This section contains detailed configuration guides for various aspects of the Omnia cluster.

## Overview

These configuration guides provide detailed instructions for configuring specific components and features of your Omnia cluster. These configurations are typically applied during the provisioning process or as post-deployment customizations.

## Configuration Guides

### Authentication
- [Configure Authentication](configure_authentication.md) -- Configure LDAP authentication for cluster users

### Networking
- [Configure InfiniBand](configure_infiniband.md) -- Configure InfiniBand networking for high-performance interconnects
- [Configure Cluster DNS](configure_cluster_dns.md) -- Configure DNS for cluster name resolution
- [Configure Multi-Subnet DHCP](configure_multi_subnet_dhcp.md) -- Configure DHCP for multiple network subnets
- [Configure PXE Boot](configure_pxe_boot.md) -- Configure PXE boot for node provisioning

### Storage
- [Configure Storage](configure_storage.md) -- Configure storage mounts and file systems
- [Deploy PowerScale CSI](deploy_powerscale_csi.md) -- Deploy PowerScale CSI driver

### High Availability
- [Configure HA](configure_ha.md) -- Configure high availability for cluster services

### Kernel
- [Configure Kernel Version Override](configure_kernel_version_override.md) -- Override default kernel versions for specific nodes

### Advanced Setup
- [Custom UCX and OpenMPI Setup](custom_ucx_openmpi_setup.md) -- Configure UCX and OpenMPI for high-performance networking
- [Setup NVIDIA HPC SDK](setup_nvhpc_sdk.md) -- Install and configure NVIDIA HPC SDK
- [Slurm with GPU](slurm_with_gpu.md) -- Configure Slurm with GPU support
- [Use Apptainer](use_apptainer.md) -- Use Apptainer containers for application deployment

### Cloud-Init
- [Configure Additional Cloud-Init](configure_additional_cloud_init.md) -- Configure custom cloud-init parameters

### Performance
- [Run HPC Benchmarks](run_hpc_benchmarks.md) -- Run HPC benchmarks

## Related Guides

- [Orchestrator](../orchestrator/index.md) -- Core deployment and provisioning
- [Deploy Slurm](../orchestrator/deploy_slurm.md) -- Deploy Slurm job scheduler
- [Deploy Kubernetes](../orchestrator/deploy_kubernetes.md) -- Deploy Kubernetes services
