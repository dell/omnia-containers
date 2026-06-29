
# Supported Operating Systems


Omnia v2.1 requires RHEL 10.0 on both the OIM (management node) and
cluster nodes. This page documents the supported OS versions and installation
profiles.

## OS support matrix


| Operating System | Version | Node Role | Installation Profile |
| --- | --- | --- | --- |
| Red Hat Enterprise Linux | 10.0 | OIM (Omnia Infrastructure Manager) | **Server with GUI** -- full graphical desktop environment and development tools. Required for the OIM management stack. |
| Red Hat Enterprise Linux | 10.0 | Slurm control node | **Minimal Install** -- base system with no GUI. Omnia installs all required packages during provisioning. |
| Red Hat Enterprise Linux | 10.0 | Slurm compute node | **Minimal Install** |
| Red Hat Enterprise Linux | 10.0 | Login node | **Minimal Install** |
| Red Hat Enterprise Linux | 10.0 | Kubernetes control plane | **Minimal Install** |
| Red Hat Enterprise Linux | 10.0 | Kubernetes worker node | **Minimal Install** |
| Red Hat Enterprise Linux | 10.0 | Auth server | **Minimal Install** |

## Architecture-specific requirements


| Architecture | OS Image Build Playbook | Notes |
| --- | --- | --- |
| x86_64 (Intel, AMD) | `build_image_x86_64.yml` | Standard RHEL 10.0 x86_64 ISO. Both Intel and AMD servers use the same image. |
| AArch64 (ARM Grace CPU) | `build_image_aarch64.yml` | RHEL 10.0 AArch64 ISO. ARM nodes **must** be provisioned with a separate image built specifically for AArch64. |

## OIM operating system details


The OIM must be installed with the **Server with GUI** profile before running
any Omnia playbooks. The following packages are expected to be present on the
OIM:

| Package / Group | Purpose |
| --- | --- |
| `podman` | Container runtime for OIM services (OpenCHAMI, Pulp, omnia_core). |
| `ansible-core` | Automation engine (installed inside the omnia_core container). |
| `python3` | Python interpreter for Ansible modules and Omnia utilities. |
| `git` | Cloning the Omnia repository. |
| `NetworkManager` | Network configuration management. |

## RHEL subscription requirements


A valid Red Hat subscription is required on the OIM to access RHEL
repositories. Cluster nodes provisioned by Omnia receive packages from the
local Pulp mirror and do not require individual subscriptions.

| Repository | Required For |
| --- | --- |
| `rhel-10-for-x86_64-baseos-rpms` | Base operating system packages for x86_64 nodes. |
| `rhel-10-for-x86_64-appstream-rpms` | Application stream packages (Python, Podman, development tools). |
| `rhel-10-for-aarch64-baseos-rpms` | Base operating system packages for ARM nodes. |
| `rhel-10-for-aarch64-appstream-rpms` | Application stream packages for ARM nodes. |
| `codeready-builder-for-rhel-10-x86_64-rpms` | Build dependencies and development libraries. |

!!! note

    The `local_repo.yml` playbook mirrors all required repositories to the OIM
    so that cluster nodes can install packages without direct internet access.
    Configure repository URLs in
    [Local Repo Config](../Configuration/local_repo_config.md).

!!! info

    - [Servers](servers.md) -- Supported server models.
    - [Provision Config](../Configuration/provision_config.md) -- Provisioning
      configuration parameters.
    - [Local Repo Config](../Configuration/local_repo_config.md) -- Local repository
      mirror configuration.
