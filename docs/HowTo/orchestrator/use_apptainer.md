# Use Apptainer

## Overview

Provisioned Slurm nodes receive
`/etc/containers/registries.conf.d/apptainer_mirror.conf`. The file defines the
OIM Pulp registry as a mirror for supported upstream registries, including
Docker Hub, GHCR, Quay, `registry.k8s.io`, NVCR, ECR Public, and GCR.

An ordinary `apptainer pull docker://...` therefore uses the system registry
configuration. The shared benchmark helper is different: it rewrites every
entry to the OIM Pulp endpoint and never falls back to the internet.

## Prerequisites

- Provision a Slurm functional layer whose catalog includes the `apptainer`
  RPM.
- To pull synchronized content from Pulp, complete Repository Manager and confirm
  that `repo_status.yml` reports `overall_status: success`.
- Select output and temporary directories with enough free space. Use shared
  storage for images needed by multiple nodes; the temporary directory may be
  local or shared.
- For the `/hpc_tools` examples, configure `slurm_cluster.nfs_storage_name`.
  Optionally set `vast_storage_name` to select a separate VAST mount; when it
  is omitted or empty, Orchestrator uses the `nfs_storage_name` entry for
  `/hpc_tools`.
- Run the `/hpc_tools` write operations as `root`, or have an administrator
  grant the calling user write access to the chosen shared directories.

## Procedure

### Pull through the configured registry mirror

1. Verify Apptainer and the generated mirror configuration:

    ```bash title="Run on: Slurm node"
    apptainer --version
    cat /etc/containers/registries.conf.d/apptainer_mirror.conf
    ```

2. Create shared image and temporary directories:

    ```bash title="Run on: Slurm node"
    mkdir -p /hpc_tools/container_images /hpc_tools/apptainer_tmp
    ```

3. Pull an image by its normal upstream name:

    ```bash title="Run on: Slurm node"
    apptainer pull --disable-cache \
      --name ubuntu_22.04.sif \
      --dir /hpc_tools/container_images \
      --tmpdir /hpc_tools/apptainer_tmp \
      docker://docker.io/library/ubuntu:22.04
    ```

    Apptainer consults the generated registry configuration and tries the Pulp
    mirror. Because the configuration also retains each upstream registry as
    its primary location, an ordinary pull can reach the upstream registry
    when the mirror does not satisfy it and the node has external network
    access.

### Require the Pulp copy

Specify Pulp explicitly when the operation must not use an upstream registry.
Pulp stores the image path without the original registry prefix:

```bash title="Run on: Slurm node"
apptainer pull --disable-cache \
  --name ubuntu_22.04.sif \
  --dir /hpc_tools/container_images \
  --tmpdir /hpc_tools/apptainer_tmp \
  docker://<oim-admin-ip>:<pulp-port>/library/ubuntu:22.04
```

The image and tag must already be synchronized. Use the OIM admin address and
Pulp container-registry port recorded by Repository Manager.

### Pull the catalog-selected benchmark images

Slurm provisioning writes
`/hpc_tools/scripts/download_container_image.sh` and
`/hpc_tools/scripts/container_image.list`. The generated list contains
`nvcr.io/nvidia/hpc-benchmarks:25.09` by default.

```bash title="Run on: Slurm login or compiler node"
/hpc_tools/scripts/download_container_image.sh
```

The helper is Pulp-only, uses the OIM admin address on port `2225`, stores SIF
files under `/hpc_tools/container_images`, and uses the same directory for
temporary data. It imposes a 30-minute timeout per image. Run it as `root`
because it writes `/var/log/container_image_download.log` and
`/var/log/apptainer_pull.log`.

## Verification

```bash title="Run on: Slurm node"
ls -lh /hpc_tools/container_images/ubuntu_22.04.sif
apptainer inspect /hpc_tools/container_images/ubuntu_22.04.sif
apptainer exec /hpc_tools/container_images/ubuntu_22.04.sif \
  cat /etc/os-release
```

## Next steps

- [Run HPC benchmarks](run_hpc_benchmarks.md) with the generated Pulp-only
  helper.
- [Configure catalog content and add packages](../repo_manager/adding_additional_packages.md)
  to synchronize another image before requiring a Pulp-only pull.

## Troubleshooting

- **`apptainer` is not found**: Confirm that the applicable catalog functional
  layer includes `apptainer`, then rerun Repository Manager, Image Build Manager, and
  Orchestrator provisioning.
- **An explicit Pulp pull fails**: Confirm the exact repository path and tag in
  Pulp. The Pulp path omits the original registry host.
- **The helper fails but an ordinary pull works**: The helper has no internet
  fallback. Synchronize the image into Pulp and confirm that the OIM registry
  is reachable on port `2225`. The generated helper currently hard-codes that
  port; use a manual explicit Pulp pull if Repository Manager uses another port.
- **A direct registry pull fails**: Confirm network and DNS connectivity from
  the compute node and verify that the requested registry is reachable.
- **A pull runs out of space**: Choose a larger `--tmpdir`. For the supplied
  helper, free space under `/hpc_tools/container_images` or edit a local copy
  of the script to use another temporary directory.
