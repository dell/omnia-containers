# Deploy OpenCHAMI

Deploy OpenCHAMI on the OIM to enable PXE boot orchestration, image resolution, and node management for the cluster.

## Overview

OpenCHAMI is a bare-metal orchestration framework that provides:
- **SMD (Services Management Daemon)** - Service discovery and management
- **BSS (Boot Script Service)** - Boot parameter configuration
- **cloud-init-server** - Cloud-init configuration delivery
- **PXE boot orchestration** - Automated node boot via BMC/iDRAC

The orchestrator domain deploys OpenCHAMI as containerized services on the OIM host. OpenCHAMI is **always required** as it is the foundation for node provisioning.

## Prerequisites

- The [Setup the OIM](../main/setup_oim.md) procedure is complete (main domain setup is complete)
- The [Initialize Domains](../main/initialize_domains.md) procedure is complete (orchestrator domain is initialized)
- The [Configure Repos](../repo_manager/configure_repos.md) procedure is complete (repo_manager domain executed)
- The [Build Images](../image_build_manager/build_images.md) procedure is complete (image_build_manager domain executed)
- The [Discover Nodes](../discovery/discover_nodes.md) procedure is complete (discovery domain executed)

### Input Contract

The orchestrator domain requires the following inputs for OpenCHAMI deployment:

| Input | Location | Purpose |
|-------|----------|---------|
| `build_status.yml` | `/opt/omnia/image_build_manager/output/<project>/build_status.yml` | Boot image paths from image_build_manager |
| `pxe_mapping_file.csv` | `/opt/omnia/discovery/output/<project>/discovery/bmc_pxe_mapping_file.csv` | BMC/PXE mapping from discovery |
| `orchestrator_config.yml` | `/opt/omnia/orchestrator/input/<project>/orchestrator_config.yml` | Main orchestrator configuration |
| `omnia_config_credentials.yml` | `/opt/omnia/orchestrator/input/<project>/omnia_config_credentials.yml` | Vault-encrypted credentials |

**Required Files:**
- `build_status.yml` - Required for S3 access configuration
- `pxe_mapping_file.csv` - Required for functional group generation
- `orchestrator_config.yml` - Always required
- `omnia_config_credentials.yml` - Auto-created if missing

**Input Sources:**
- **image_build_manager** - Provides `build_status.yml` with boot image paths
- **discovery** - Provides `pxe_mapping_file.csv` with BMC/PXE mapping
- **Administrator** - Provides `orchestrator_config.yml`
- **Domain initialization** - Stages input files from samples directory

## Procedure

1. **Initialize the orchestrator domain**:

    ```bash title="Run on: OIM host"
    ./omnia.sh -i orchestrator
    ```

    This stages input files and installs dependencies.

2. **Configure the orchestrator settings**:

    ```bash title="Run on: OIM host"
    vi /opt/omnia/orchestrator/input/project_default/orchestrator_config.yml
    ```

    Configure the following parameters:

    ```yaml title="File: orchestrator_config.yml"
    # Upstream dependency paths
    image_build_manager_output_path: "/opt/omnia/image_build_manager/output/project_default/build_status.yml"
    discovery_output_path: "/opt/omnia/discovery/output/project_default/discovery/bmc_pxe_mapping_file.csv"

    # OpenCHAMI configuration
    domain_name: "example.com"
    admin_nic_ip: "10.20.0.1"
    ```

3. **Run the OpenCHAMI deployment**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run orchestrator --tags deploy_openchami
    ```

    This performs the following:
    - Validates inputs and parameters
    - Configures S3 access from build_status.yml
    - Deploys OpenCHAMI containers (SMD, BSS, cloud-init-server)
    - Validates OpenCHAMI health and readiness

## Verification

1. **Check OpenCHAMI container status**:

    ```bash title="Run on: OIM host"
    podman ps | grep openchami
    ```

    Expected output: Running containers for SMD, BSS, and cloud-init-server.

2. **Verify S3 access**:

    ```bash title="Run on: OIM host"
    s3cmd ls s3://boot-images
    ```

    Should list boot images from the image_build_manager output.

3. **Review the domain logs**:

    ```bash title="Run on: OIM host"
    omnia-cli logs orchestrator
    ```

## Output Contract

After successful execution, the orchestrator domain produces the following output contract for OpenCHAMI:

| Output | Location | Purpose |
|--------|----------|---------|
| `functional_groups_config.yml` | `/opt/omnia/orchestrator/output/<project>/orchestrator/` | Generated functional groups from PXE mapping |
| `orchestrator_state.yml` | `/opt/omnia/orchestrator/output/<project>/orchestrator/` | Support flags for standalone runs |
| BSS configurations | `/opt/omnia/orchestrator/output/<project>/orchestrator/` | Boot parameter configurations |
| Cloud-init configurations | `/opt/omnia/orchestrator/output/<project>/orchestrator/` | Default/group/node cloud-init configs |

This contract is consumed by:
- **Provisioning** - For node boot configuration
- **Cluster workflows** - For ongoing operations

## Next Steps

- [Deploy OpenLDAP](deploy_openldap.md) -- Deploy OpenLDAP authentication service (optional)
- [Provision Nodes](provision_nodes.md) -- Provision cluster nodes using OpenCHAMI

## Troubleshooting

**OpenCHAMI containers not starting**

Check the container logs:
```bash
podman logs <container-name>
```

**S3 access configuration failed**

Verify build_status.yml exists and is accessible:
```bash
cat /opt/omnia/image_build_manager/output/project_default/build_status.yml
```

**PXE mapping file not found**

Verify discovery domain completed successfully:
```bash
cat /opt/omnia/discovery/output/project_default/discovery/bmc_pxe_mapping_file.csv
```
