# OIM Requirements

This section outlines the key requirements for the Omnia Infrastructure Manager (OIM) and Aarch64 nodes used by Omnia to deploy HPC clusters. For more information about the supported devices and software, see [Support Matrix](../index.md#support-matrix).

## Omnia Infrastructure Manager

- Choose a **server outside of your intended cluster** that meets the required [Storage Requirements](disk_space.md) to function as the Omnia Infrastructure Manager (OIM).
- Ensure the OIM has at least 64 GB RAM. To check the free RAM size, use the `free -h` command. To check the disk space, use the `df -h` command.
- Ensure that the OIM has the RHEL operating system installed with the **Server with GUI** Base Environment. For a complete list of supported RHEL versions, see the [supported operating systems](../SupportMatrix/operating_systems.md).
- Ensure that **Podman** container engine is installed on the OIM.
- The OIM must have access to public/internet (for downloading packages and images) network and admin (PXE) network.
- Verify that **Git** is installed. If not, install it using:

    ```bash title="Run on: OIM host"
    dnf install git -y
    ```

- All target bare-metal servers (cluster nodes) must be **reachable from the OIM**.
- Make sure that the required ports are open on the OIM node for cluster deployment. For detailed information on the required ports, refer to [Ports Used by the OIM](../../GetStarted/prerequisites_checklist.md#ports-used-by-the-oim).
- The `omnia_core` and `omnia_auth` container images are deployed on the OIM. For instructions to deploy containers, see [Deploy Omnia Core Container](https://github.com/dell/omnia).

## aarch64 Node Prerequisites

- Ensure that a disk is available to the aarch64 node for Full OS installation and you must install the OS manually.
- Ensure that an IP address is assigned to the aarch64 node and the node has connectivity to the PXE network.
- Ensure that the same NFS share used in OIM is reachable on the aarch64 node.

!!! info

    - [Deploy Omnia core](https://github.com/dell/omnia) -- Deploy Omnia container images on OIM.



















