# Orchestrator

The orchestrator domain manages OpenCHAMI deployment, OpenLDAP authentication, PXE boot orchestration, image resolution, node provisioning, and service deployment (K8s, Slurm, storage, LDAP).

## Overview

The orchestrator domain (collection: `omnia.orchestrator`) manages the full post-discovery lifecycle. It is fully decoupled from shared utilities and owns its own library, validation framework, credential management, and cleanup lifecycle. OpenCHAMI and OpenLDAP have independent lifecycle management with dedicated precheck, prepare, deploy, cleanup, upgrade, and rollback playbooks.

**Note**: The orchestrator configures telemetry client-side integration on nodes (via telemetry_config.yml and iDRAC telemetry service). The full telemetry server stack is deployed by the separate telemetry domain.

## System Context

```
  build_status.yml                          functional_groups_config.yml
  pxe_mapping_file.csv                      orchestrator_state.yml
  orchestrator_config.yml                      +---------------------+
  omnia_config_credentials.yml               |    Orchestrator     |
  +---------------------+     +-----------------+ |                     |
  |  image_build_manager  |---->|                     |---->  cluster workflows
  |  discovery           |     |  (openchami, ldap,  |     |
  |  (upstream)           |     |   k8s, slurm, etc)  |     |
  +---------------------+     +-----------------+ +---------------------+
                                       |
                                  OpenCHAMI + OpenLDAP
                                 (containers on OIM)
```

## When to Use This Domain

- Use when deploying OpenCHAMI for node orchestration
- Use when deploying OpenLDAP for authentication
- Use when configuring Kubernetes services
- Use when configuring Slurm job scheduler
- Use when configuring networking (InfiniBand, DNS)
- Use when configuring storage (NFS, PowerScale)
- Use when provisioning nodes via PXE boot
- Fifth domain in execution order (after discovery)

## Domain Workflow

The domain supports the following execution tags (component-specific):

| Tag | OpenCHAMI | OpenLDAP | Description |
|-----|-----------|-----------|-------------|
| `precheck` | ✅ | ✅ | Validate inputs, params, boot images, config vars |
| `prepare` | ✅ | ✅ | Credential management, configuration preparation |
| `deploy` | ✅ | ✅ | Deploy services + validate readiness |
| `provision` | ✅ | — | Node provisioning (K8s, Slurm, OS, custom FGs) |
| `validate` | ✅ | ✅ | Health checks + post-provision verification |
| `pxeboot` | ✅ | — | PXE boot on iDRAC nodes (opt-in) |
| `cleanup` | ✅ | ✅ | Remove services, containers, config, artifacts |
| `upgrade` | ✅ | ✅ | In-place upgrade (opt-in) |
| `rollback` | ✅ | ✅ | Revert to previous state (opt-in) |

## Execution Flow

1. **Setup** - Upgrade guard, input directory, OIM group, vars, functional group generation
2. **Precheck** - L1 schema + L2 logic validation, boot image validation, OIM timezone check
3. **Prepare** - Credential prompt/encrypt/vault, S3 access, OpenLDAP dirs/TLS/config
4. **Deploy** - OpenCHAMI containers, OpenLDAP container, validate readiness
5. **Provision** - SSH key distribution, OpenCHAMI auth, K8s/Slurm/OS/custom FG provisioning
6. **PXE Boot** - BMC inventory, reboot, phone-home verify (opt-in)
7. **Cleanup** - Stop services, remove containers/config/artifacts (opt-in)
8. **Upgrade/Rollback** - In-place upgrade or rollback (opt-in)

## Key Inputs

- `build_status.yml` - From image_build_manager (boot image paths)
- `pxe_mapping_file.csv` - From discovery (BMC/PXE mapping)
- `orchestrator_config.yml` - Main configuration
- `omnia_config_credentials.yml` - Vault-encrypted credentials

## Key Outputs

- BSS/cloud-init boot configurations
- Functional groups configuration
- Deployed OpenCHAMI services
- Deployed OpenLDAP service (if enabled)
- Provisioned cluster nodes

## Output Contract

The orchestrator domain produces the following output contract:

| Output | Location | Purpose |
|--------|----------|---------|
| `functional_groups_config.yml` | `/opt/omnia/orchestrator/output/<project>/orchestrator/` | Generated functional groups from PXE mapping |
| `orchestrator_state.yml` | `/opt/omnia/orchestrator/output/<project>/orchestrator/` | Support flags for standalone runs |
| BSS configurations | `/opt/omnia/orchestrator/output/<project>/orchestrator/` | Boot parameter configurations |
| Cloud-init configurations | `/opt/omnia/orchestrator/output/<project>/orchestrator/` | Default/group/node cloud-init configs |
| `/opt/omnia/hosts` | `/opt/omnia/hosts` | Ansible inventory for cluster nodes |

This contract is consumed by:
- **Cluster workflows** - For ongoing operations
- **Administrators** - For manual cluster management
- **Telemetry domain** - For metrics collection (client-side integration)

## Related Guides

### Core Deployment
- [Deploy OpenCHAMI](deploy_openchami.md) -- Deploy OpenCHAMI for node orchestration
- [Deploy OpenLDAP](deploy_openldap.md) -- Deploy OpenLDAP authentication service
- [Deploy Slurm](deploy_slurm.md) -- Deploy Slurm job scheduler
- [Deploy Kubernetes](deploy_kubernetes.md) -- Deploy Kubernetes services

### Node Management
- [Provision Nodes](provision_nodes.md) -- Provision cluster nodes
- [Add Nodes](add_nodes.md) -- Add nodes to the cluster
- [Remove Nodes](remove_nodes.md) -- Remove nodes from the cluster

### Getting Started
- [Getting Started: Full Deployment](../../GetStarted/full_deployment.md)
- [Domain Contract](../../Reference/domain_contracts/orchestrator_contract.md)

### Related Domains
- [Discovery](../discovery/index.md) -- Upstream mapping file provider
- [Image Build Manager](../image_build_manager/index.md) -- Upstream boot image provider

### Configuration Guides
For detailed configuration options, see [Configure](../Configure/index.md) for:
- Authentication (LDAP)
- Networking (InfiniBand, DNS, Multi-Subnet DHCP)
- Storage
- High Availability
- Kernel Version Override
- Advanced Setup (UCX, OpenMPI, NVIDIA HPC SDK, GPU, Apptainer)




