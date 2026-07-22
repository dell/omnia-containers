# Prepare aarch64 Node for Image Building

## Overview

Before building aarch64 compute images with `build_image_aarch64.yml`,
you must manually install RHEL 10 on one aarch64 bare-metal node. This
node is used as a build host to create diskless images for all aarch64
functional groups.

!!! caution

    Limited validation has been performed on the aarch64 platform.

## Prerequisites

- A disk is available to the aarch64 node for full OS installation.
- The aarch64 node has network connectivity to the PXE (admin) network.
- The same NFS share used by the OIM is reachable on the aarch64 node.
- The [Deploy Omnia Core](deploy_omnia_core.md) procedure is complete
  (with NFS share option selected during `omnia.sh --install`).
- `prepare_oim.yml` has been executed (downloads the `regctl` binary for
  aarch64).
- `local_repo.yml` has been executed with `software_config.json` that
  includes aarch64 packages (downloads the aarch64 image builder
  container to the local registry).

## Procedure

### 1. Install RHEL 10 on the aarch64 node

Manually install the **full Red Hat Enterprise Linux 10** OS on one of
the aarch64 nodes with root password enabled.

!!! warning

    - The root password must be at least 8 characters long, contain
      alphanumeric characters, and must **not** include commas (`,`),
      hyphens (`-`), single quotes (`'`), double quotes (`"`), or
      backslashes (`\`).
    - The password set during RHEL installation on the aarch64 node must
      be supplied as `provision_password` when running `prepare_oim.yml`.

### 2. Create an inventory file

Create an inventory file with the aarch64 node's admin IP address in the
`admin_aarch64` group:

```ini title="Example: /omnia/build_image_aarch64/inventory"
[admin_aarch64]
<aarch64_node_admin_ip>
```

Replace `<aarch64_node_admin_ip>` with the actual admin IP address of
the node where RHEL 10 was installed.

!!! note

    The `admin_aarch64` inventory group must contain exactly **one** host.
    The `build_image_aarch64.yml` playbook will fail if the group is empty
    or contains more than one host.

### What happens during the build

When you run `build_image_aarch64.yml -i inventory`, the playbook
automatically performs the following on the aarch64 node:

1. Sets up passwordless SSH from `omnia_core` to the aarch64 node.
2. Verifies the target machine architecture is `aarch64`.
3. Adds the OIM PXE IP and hostname to `/etc/hosts`.
4. Installs NFS utilities and mounts the OIM NFS share.
5. Copies the Pulp repository configuration and certificate.
6. Pulls the aarch64 image builder container from the local registry.
7. Copies the `regctl` binary for registry operations.
8. Builds diskless images for all aarch64 functional groups defined in
   the PXE mapping file.
9. Uploads the built images to MinIO (S3).

## Verification

Verify that the aarch64 node is prepared and accessible:

```bash title="Run on: omnia_core container"
ssh <aarch64_node_admin_ip> uname -m
```

The output should return `aarch64`.

## Next Steps

- [Build Cluster Images](build_cluster_images.md) -- Build x86_64 and
  aarch64 images for provisioning.

## Troubleshooting

- **SSH connection to aarch64 node fails**: Verify the admin IP address is correct, the node is powered on, and network connectivity exists between the OIM and the aarch64 node.
- **Build playbook fails with "architecture mismatch"**: Confirm that the target node is running on aarch64 hardware and that RHEL 10 was installed correctly.
