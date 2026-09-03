# Image Build Manager

The image_build_manager domain builds diskless cluster images for PXE boot provisioning using package repositories.

## Overview

The image_build_manager domain (collection: `omnia.image_build_manager`) deploys MinIO S3 storage and an OCI container registry, then builds OS boot images for diskless cluster provisioning. It runs bare-metal on the OIM host with `connection: local`, except for aarch64 builds which SSH to a remote ARM node.

## System Context

```
  repo_status.yml                                                    build_status.yml
  catalog_rhel.json (or package_groups.yml)                          S3 artifacts
  +---------------------+     +-------------------------------------+     +-----------+
  |                     |     |       Image Build Manager            |     |           |
  |  repo_manager       |---->|                                     |---->| provision |
  |  (upstream)         |     |  setup -> validate -> prepare       |     | workflow  |
  |                     |     |         -> build -> write_status    |     | (consumer)|
  +---------------------+     +-------------------------------------+     +-----------+
                                       |              |
                                  MinIO S3      OCI Registry
                                 (boot-images)  (+ regctl)
```

## When to Use This Domain

- Use when provisioning diskless nodes via PXE boot
- Use when building custom images with specific packages
- Required for Slurm and Kubernetes deployments
- Use when rebuilding images after package updates
- Third domain in execution order (after repo_manager)

## Domain Workflow

The domain supports the following execution tags (mutually exclusive - run exactly ONE tag):

| Tag | Description | Credentials | repo_status needed |
|-----|-------------|-------------|-------------------|
| *(none)* | Default: prepare + build + write_status | Yes | Yes |
| `precheck` | Environment and connectivity precheck | No | No |
| `validate` | Validate configuration only | No | No |
| `credentials` | Collect/update credentials only | Yes | No |
| `prepare` | Deploy MinIO + Registry | Yes | No |
| `build` / `execute` | Build images only | Yes | Yes |
| `cleanup` | Remove all infrastructure | No | No |
| `cleanup_images` | Delete built images only | No | No |

## Execution Flow

1. **Setup** - Validate tags, load environment, set project directories, validate prerequisite files
2. **Validate** - Schema validation, logic validation, catalog structure validation
3. **Credentials** - Collect S3 access/secret keys (Ansible Vault encrypted), aarch64 SSH password
4. **Precheck** - Verify env vars, IP address, hostname, omnia.sh setup (opt-in)
5. **Prepare** - Deploy MinIO S3 via Podman Quadlet, deploy OCI registry, install regctl, create S3 buckets
6. **Build** - Dual-mode package resolution (config or catalog), build base OS image, build compute images, upload to S3
7. **Cleanup** - Remove MinIO + Registry containers, build artifacts, credentials (opt-in)

## Deployed Services

| Service | Ports | Purpose |
|---------|-------|---------|
| MinIO S3 (Podman Quadlet) | 9000 (API), 9001 (Console) | Boot image storage |
| OCI Registry (Podman Quadlet) | 5000 (HTTP) | Image verification |

## Output Contract

The image_build_manager domain produces the following output contract:

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

## Related Guides

- [Build Images](build_images.md) -- Build OS boot images using local repos
- [Getting Started: Full Deployment](../../GetStarted/full_deployment.md)
- [Domain Contract](../../Reference/domain_contracts/image_build_manager_contract.md)
- [Related Domain: repo_manager](../repo_manager/index.md) -- Upstream repository management




