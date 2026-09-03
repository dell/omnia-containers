# Repository Manager

The repo_manager domain manages local and remote repositories for air-gapped provisioning, package synchronization, and RPM management.

## Overview

The repo_manager domain (collection: `omnia.repo_manager` v3.0.0) validates catalog sources, deploys a local Pulp server, synchronizes content, and generates `repo_status.yml` for downstream Omnia components. It runs bare-metal on the OIM host with `connection: local`.

## System Context

```text
catalog JSON                  Repo Manager                         downstream consumers
repo_manager_config.yml       +-------------------------------+    +-------------------+
endpoint config              | validate -> prepare -> sync    |    | image_build_manager|
Vault credentials ---------->|          -> status             |--->| cluster workflows  |
RHEL subscription            |                               |    | administrators     |
                               +---------------+---------------+    +-------------------+
                                               |
                                    HTTPS Pulp content server
                              RPM | OCI images | File | Python
```

## When to Use This Domain

- Use when deploying air-gapped clusters without internet access
- Use when mirroring external repositories to local storage
- Required for all deployment paths
- Use when deploying additional packages or custom repositories
- First domain in the execution order (after main setup)

## Domain Workflow

The domain supports the following execution tags:

| Tag | Description | Credentials | Destructive |
|-----|-------------|-------------|-------------|
| `precheck` | Validate environment, input, catalog and subscription sources | No | No |
| `prepare` / `deploy` | Collect credentials and deploy Pulp | Yes | No |
| `download` / `execute` | Resolve catalog and synchronize content | Yes | No |
| `status` | Generate `repo_status.yml` from Pulp | No | No |
| `cleanup_repos` | Selectively remove Pulp RPM, container, File or Python content | No | Yes |
| `cleanup_pulp` / `cleanup` | Remove the Pulp deployment and runtime data | No | Yes |
| `catalog_generate` | Create catalog JSON from text input | No | Writes catalog |
| `catalog_add` | Add or update catalog packages | No | Writes catalog |
| `catalog_delete` | Delete catalog packages | No | Writes catalog |
| `catalog_validate` | Validate catalog JSON | No | No |

## Execution Flow

1. **Environment setup** - Load Omnia environment, resolve paths, require `SYSTEM_ADMIN_NIC_IPV4` and `CATALOG_FILE_PATH`
2. **Precheck** - Validate host environment, YAML syntax, JSON schemas, catalog mappings
3. **Prepare** - Collect credentials, deploy Pulp as Podman Quadlet, generate HTTPS certificate
4. **Download** - Resolve catalog, synchronize RPM, OCI images, File and Python content to Pulp
5. **Status** - Generate `repo_status.yml` with HTTPS repository URLs and certificate paths
6. **Cleanup** - Selective or full Pulp cleanup

## Pulp Deployment

- **Protocol**: HTTPS only
- **Host endpoint**: `https://<pulp_server_ip>:<pulp_server_port>`
- **Service**: `pulp.service` generated from Podman Quadlet
- **Persistence**: `/opt/omnia/repo_manager/pulp_config/`
- **Certificate**: Generated under `pulp_config/settings/certs/`

## Content Model

| Catalog type | Resolution | Pulp content |
|--------------|------------|--------------|
| `rpm` | Package name and mapped `reponame` | RPM repository |
| `rpm_repo` | DNF resolves package and dependencies | RPM repository |
| `rpm_file` | Direct RPM file | RPM repository |
| `image` | Image name, tag and mapped registry | Container repository |
| `pip_module` | Package and version | Python repository |
| `tarball`, `manifest`, `git`, `iso`, `shell`, `ansible_galaxy_collection` | Type-specific source | File repository |

## Output Contract

The repo_manager domain produces the following output contract:

| Output | Location | Purpose |
|--------|----------|---------|
| `repo_status.yml` | `/opt/omnia/repo_manager/output/<project>/repo_status.yml` | Pulp URLs, repositories, file content and certificate paths for downstream consumers |
| Package/group state | `/opt/omnia/repo_manager/log/<os>/<version>/<arch>/` | Per-group CSV and worker results |
| Mirror indexes | `/opt/omnia/repo_manager/log/<os>/<version>/mirror_status/` | Composite catalog and Pulp mirror state |

### repo_status.yml Structure

The `repo_status.yml` file contains:

- HTTPS repository URLs for RPM repositories
- Container registry URLs for OCI images
- File content URLs for additional artifacts
- Certificate paths for HTTPS trust
- Repository status and availability information

This contract is consumed by:
- **image_build_manager** - For accessing OS images and container artifacts
- **Cluster workflows** - For package installation during provisioning
- **Administrators** - For manual repository access and verification

## Related Guides

- [Configure Repos](configure_repos.md) -- Set up and synchronize local repositories
- [Getting Started: Full Deployment](../../GetStarted/full_deployment.md)
- [Domain Contract](../../Reference/domain_contracts/repo_manager_contract.md)
- [Related Domain: image_build_manager](../image_build_manager/index.md)




