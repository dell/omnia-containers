# Repository Manager

## Overview

Repo Manager deploys an HTTPS Pulp content server and synchronizes catalog
content for offline Omnia clusters. It supports RPM repositories and packages,
container images, Python packages, files, and source artifacts for `x86_64` and
`aarch64`. All Repo Manager playbooks run locally on the Omnia Infrastructure
Manager (OIM).

Repo Manager validates catalog sources, deploys Pulp, synchronizes the selected
content, and generates `repo_status.yml` for downstream Omnia components.
Before configuring repositories, [select or update the catalog](../main/update_catalog.md)
for the required workload, architecture, and VAST option.

```text
catalog JSON + repository configuration + endpoint configuration
                              + Vault credentials
                              + RHEL subscription
                                       |
                                       v
                        validate -> prepare -> synchronize
                                       |
                                       v
                         HTTPS Pulp + repo_status.yml
                                       |
                                       v
                             downstream consumers
```

## Prerequisites

| Requirement | Minimum | Validated |
|---|---|---|
| OIM operating system | RHEL 10.x | RHEL 10.0 |
| Python | 3.12+ | 3.12.8 |
| Ansible | `ansible-core` 2.20+ | 2.20.0 |
| Podman | 5.0+ | 5.3.1 |
| Privileges | Root or equivalent | Root |
| Storage | Sized for retained catalog content | Deployment-specific |

## Choose a task

| Task | Use it to |
|---|---|
| [Select or update the catalog](../main/update_catalog.md) | Choose the catalog file that Repo Manager will consume through `CATALOG_FILE_PATH`. |
| [Create Local Repositories](configure_repos.md) | Configure Repo Manager inputs, deploy Pulp, synchronize catalog content, and generate `repo_status.yml`. |
| [Configure VAST Storage and Build VAST RPMs](../../Operations/repo_manager/configure_vast.md) | Prepare the VAST appliance, build the VAST NFS RPMs, and host them for use as a Repo Manager user repository. |
| [Build Slurm RPMs](../../Operations/repo_manager/build_slurm_repo.md) | Build Slurm RPMs from source for `x86_64` or `aarch64` nodes before adding the hosted repository to Repo Manager. |
| [Configure Catalog Content](adding_additional_packages.md) | Define functional groups, connect packages to functional layers, resolve package sources, and add or update catalog content. |
| [Add an RPM Repository and Packages](adding_additional_repositories.md) | Map a catalog RPM source to a repository by OS version, architecture, and `reponame`. |
| [Update Local Repositories after Catalog Changes](../../Operations/repo_manager/updating_local_repositories.md) | Validate and synchronize changed catalog content, then regenerate `repo_status.yml`. |
| [Resynchronize Local RPM Repositories](../../Operations/repo_manager/local_repository_resync.md) | Force all or selected catalog-required RPM repositories to check their upstream remotes. |

## Contract reference

See the [Repository Manager Domain Contract](../../Reference/domain_contracts/repo_manager_contract.md)
for the required environment and input files, their schemas, the generated
`repo_status.yml` structure, managed Pulp resources, and runtime state.

After Repo Manager produces a successful `repo_status.yml`, downstream
components such as [Image Build Manager](../image_build_manager/build_images.md)
can consume its repository URLs and certificate paths.
