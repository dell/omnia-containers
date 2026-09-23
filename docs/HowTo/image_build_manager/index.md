# Image Build Manager

## Overview

Image Build Manager builds RHEL images for `x86_64` and `aarch64` cluster-node
provisioning by using OpenCHAMI. It uses the configured S3 backend, deploying
MinIO when selected, and deploys a local OCI registry. It builds an image for
each selected functional group and writes `build_status.yml` for the
Orchestrator provisioning workflow.

Image Build Manager runs on the Omnia Infrastructure Manager (OIM). Tasks run
locally except for `aarch64` builds, which use SSH to run on a remote ARM host.

```text
  repo_status.yml                                                       build_status.yml
  catalog_rhel.json (or package_groups.yml)                             S3 artifacts
  +----------------------+     +--------------------------------------+     +----------------------+
  | Repository Manager         |     | Image Build Manager                  |     | Orchestrator         |
  | (upstream)           |---->| setup -> validate -> prepare         |---->| (consumer)           |
  |                      |     |          -> build -> write_status    |     | provision workflow   |
  +----------------------+     +--------------------------------------+     +----------------------+
                                         |              |
                                   S3 storage      OCI Registry
                              (MinIO or PowerScale)  (+ regctl)
```

## Prerequisites

| Requirement | Minimum | Validated |
|---|---|---|
| OIM operating system | RHEL 10.x | RHEL 10.0 |
| Python | 3.12+ | 3.12.8 |
| Ansible | `ansible-core` 2.20+ | 2.20.0 |
| Podman | 5.0+ | 5.3.1 |
| Free disk space | 50 GB | Not specified |

The component source accepts RHEL 10.x inputs, but that implementation range
does not classify every point release for product support. Use the OIM and
cluster-node combination listed as validated in the
[Operating Systems Matrix](../../Reference/SupportMatrix/operating_systems.md).

Build operations also require a successful `repo_status.yml` from Repository Manager.
An `aarch64` build requires a separate, reachable ARM host because
cross-architecture builds are not supported.

When using catalog mode, [select or update the catalog](../main/update_catalog.md)
before configuring the image build. The selected catalog determines the
functional layers and architectures that Image Build Manager builds.

## Choose a task

| Task | Use it to |
|---|---|
| [Select or update the catalog](../main/update_catalog.md) | Choose the workload, architecture, and VAST variant used for catalog-based image builds. |
| [Build OS Images](build_images.md) | Configure the build inputs, prepare storage and registry services, build functional-group images, upload their artifacts, and generate `build_status.yml`. |
| [Clean up built images](../../Operations/cleanup_built_images.md) | Remove selected or all built artifacts from S3 and the local registry without removing Image Build Manager services. |

## Contract reference

See the [Image Build Manager Domain Contract](../../Reference/domain_contracts/image_build_manager_contract.md)
for the configuration, credentials, upstream Repository Manager contract, package
sources, generated `build_status.yml`, services, and S3 artifact layout.

After Image Build Manager produces a successful `build_status.yml`, the
[Orchestrator provisioning workflow](../orchestrator/index.md) can
consume its functional-group image paths.
