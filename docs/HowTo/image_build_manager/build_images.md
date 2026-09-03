# Build OS Images

Build production-ready RHEL images for x86_64 and aarch64 compute nodes using the Image Build Manager domain.

## Overview

The image_build_manager domain (collection: `omnia.image_build_manager`) deploys MinIO S3 storage and an OCI container registry, then builds OS boot images for diskless cluster provisioning. It supports dual-mode package resolution (config or catalog mode) and builds images using OpenCHAMI image-builder or image-thrillhouse.

The image build process reads `repo_status.yml` from the repo_manager domain and writes `build_status.yml` for the orchestrator domain to consume during PXE boot provisioning.

## Prerequisites

- The [Setup the OIM](../main/setup_oim.md) procedure is complete (main domain setup is complete)
- The [Initialize Domains](../main/initialize_domains.md) procedure is complete (image_build_manager domain is initialized)
- The [Configure Repos](../repo_manager/configure_repos.md) procedure is complete (repo_manager domain executed)
- Minimum 50GB free disk space for image builds
- For aarch64 builds: Dedicated ARM64 host with RHEL 10.x and Podman 5.0+

### Input Contract

The image_build_manager domain requires the following inputs:

| Input | Location | Purpose |
|-------|----------|---------|
| `repo_status.yml` | `/opt/omnia/repo_manager/output/<project>/repo_status.yml` | Repository URLs and certificate paths from repo_manager |
| `image_build_config.yml` | `/opt/omnia/image_build_manager/input/<project>/image_build_config.yml` | Main configuration for S3, image builder, and build controls |
| `package_groups.yml` | `/opt/omnia/image_build_manager/input/<project>/package_groups.yml` | Package groups for config mode (when `functional_groups_source: "config"`) |
| `CATALOG_FILE_PATH` | Environment variable | Path to catalog JSON for catalog mode (when `functional_groups_source: "catalog"`) |
| `image_build_credentials.yml` | `/opt/omnia/image_build_manager/input/<project>/image_build_credentials.yml` | S3 access/secret keys and aarch64 SSH password (Ansible Vault encrypted) |

### Required Files

- `image_build_config.yml` - Always required
- `repo_status.yml` - Required for build-related tags
- `package_groups.yml` - Required when `functional_groups_source: "config"`
- `CATALOG_FILE_PATH` - Required when `functional_groups_source: "catalog"`

### Input Sources

- **repo_manager** - Provides `repo_status.yml` with repository URLs and certificates
- **Administrator** - Provides `image_build_config.yml`, `package_groups.yml`, and catalog JSON
- **Domain initialization** - Stages input files from samples directory

## Procedure

1. **Initialize the image_build_manager domain**:

    ```bash title="Run on: OIM host"
    ./omnia.sh -i image_build_manager
    ```

    This stages input files and installs dependencies.

2. **Configure the image build settings**:

    ```bash title="Run on: OIM host"
    vi /opt/omnia/image_build_manager/input/project_default/image_build_config.yml
    ```

    Configure the following parameters:

    ```yaml title="File: image_build_config.yml"
    # Upstream dependency path
    repo_manager_output_path: "/opt/omnia/repo_manager/output/project_default/repo_status.yml"

    # S3 storage backend
    s3_configurations:
      provider: "minio"  # Options: minio, powerscale
      endpoint_url: ""  # Required for powerscale; auto-detected for minio

    # Image builder type
    image_build_type: "image-builder"  # Options: image-builder, image-thrillhouse

    # Build controls
    build_image:
      max_parallel: 0  # 0 = unlimited concurrent builds
      build_timeout: 7200  # Per-build timeout in seconds
      force_rebuild: false  # Bypass package hash cache
      backup_s3_images: false  # Copy S3 artifacts to *_prev before rebuild
      repo_ssl_verify: true  # SSL + GPG check on RPM repos

    # Functional groups source
    functional_groups_source: "catalog"  # Options: config, catalog

    # ARM build host (for aarch64)
    aarch64_inventory_host_ip: ""  # Leave empty to skip aarch64 builds
    aarch64_ssh_user: "root"
    ```

    !!! note
        For aarch64 builds, ensure the remote ARM host is accessible via SSH and has sufficient resources for image building.

3. **Configure package resolution mode**:

    **Catalog Mode (Recommended)**

    Catalog mode automatically resolves package lists from catalog JSON files. Set the catalog file path in your environment:

    ```bash title="Run on: OIM host"
    export CATALOG_FILE_PATH="${OMNIA_DATA_PATH}/catalog/catalog_rhel.json"
    ```

    Ensure `functional_groups_source: "catalog"` is set in `image_build_config.yml`.

    **Config Mode (Package Groups)**

    Config mode uses manual package selection from `package_groups.yml`. Edit the package groups file:

    ```yaml title="File: package_groups.yml"
    os: "rhel"  # OS type
    os_version: "10.0"  # OS version
    base_packages:
      - package1
      - package2
    functional_groups:
      slurm_control_node_x86_64:
        packages:
          - slurm
          - slurm-pam_slurm
      slurm_compute_node_x86_64:
        packages:
          - slurm
          - openmpi
    ```

    Set `functional_groups_source: "config"` in `image_build_config.yml`.

## Procedure

1. **Validate the configuration**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run image_build_manager --tags validate
    ```

    This performs schema validation, logic validation, and catalog structure validation (if using catalog mode). No credentials are required.

2. **Deploy MinIO S3 and OCI container registry**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run image_build_manager --tags prepare
    ```

    This prompts for S3 credentials, deploys MinIO S3 service (if using MinIO), deploys the OCI container registry, and opens firewall ports.

    !!! tip
        When using PowerScale as the S3 backend, ensure IAM credentials are pre-configured and the bucket is manually created before running the prepare step.

3. **Build the OS images**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run image_build_manager --tags build
    ```

    Or run without tags for the default flow (prepare + build):

    ```bash title="Run on: OIM host"
    ./omnia.sh --run image_build_manager
    ```

    The build process resolves packages, builds the base image, builds compute images with concurrency control, uploads artifacts to S3, and writes `build_status.yml`.

    !!! warning
        Initial image builds can take significant time depending on the number of functional groups and network bandwidth.

## Verification

1. **Check the build status file**:

    ```bash title="Run on: OIM host"
    cat /opt/omnia/image_build_manager/output/project_default/build_status.yml
    ```

    ```text title="Expected output"
    overall_status: "success"
    s3_configurations:
      endpoint_url: "http://10.20.0.1:9000"
      bucket: "boot-images"
    functional_group_images:
      - x86_64:
        - functional_group: "slurm_control_node_x86_64"
          kernel: "boot-images/efi-images/.../vmlinuz-<kernel>"
          initrd: "boot-images/efi-images/.../initramfs-<kernel>.img"
          image: "boot-images/slurm_control_node_x86_64/..."
    ```

2. **Review the domain logs**:

    ```bash title="Run on: OIM host"
    omnia-cli logs image_build_manager
    ```

## Output Contract

After successful execution, the image_build_manager domain produces the following output contract:

| Output | Location | Purpose |
|--------|----------|---------|
| `build_status.yml` | `/opt/omnia/image_build_manager/output/<project>/build_status.yml` | S3 artifact paths, kernel/initrd/image URLs for downstream consumers |
| S3 artifacts | MinIO S3 buckets (`boot-images`, `efi-images`) | Boot images, kernels, initramfs for PXE boot |

### build_status.yml Structure

The `build_status.yml` file contains:

- Overall build status
- S3 configuration (endpoint URL, bucket)
- Functional group images with kernel, initrd, and image paths per architecture

This contract is consumed by:

- **discovery** - For PXE boot configuration
- **Cluster workflows** - For OS provisioning
- **Administrators** - For manual image access and verification

## Next Steps

- [Discover Nodes](../discovery/discover_nodes.md) -- Discover and generate BMC/PXE mapping files
- [Deploy Orchestrator](../orchestrator/deploy_slurm.md) -- Use the built images for PXE boot provisioning

## Troubleshooting

- **Build fails with package resolution errors**: Check that `repo_status.yml` exists and is valid. Verify the `repo_manager_output_path` in `image_build_config.yml` points to the correct location.
- **S3 connectivity errors**: Verify S3 credentials and endpoint configuration. For MinIO, ensure the service is running. For PowerScale, verify IAM credentials are pre-configured.
- **aarch64 build fails**: Verify ARM host connectivity with `ping <aarch64_inventory_host_ip>` and ensure SSH access works. Cross-architecture building is not supported.
- **Catalog validation fails**: Check that the catalog JSON structure is valid and that `CATALOG_FILE_PATH` environment variable is set correctly.
- **Build timeout errors**: Increase `build_timeout` in `build_image` configuration or reduce `max_parallel` to limit concurrent builds.
- **SSL verification fails**: Set `repo_ssl_verify: false` in `build_image` configuration for self-signed certificates.


















