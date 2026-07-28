# Deploy the Telemetry Stack

## Overview

Telemetry in Omnia is **not** deployed by a single playbook. After you configure
the telemetry input files, the telemetry stack is deployed as part of the normal
cluster deployment workflow. This page documents the complete playbook sequence
that every telemetry source depends on.

Each telemetry configuration guide (iDRAC, LDMS, DCGM, PowerScale, UFM, VAST, OME,
and the Vector bridges) ends with a **Deploy the Cluster** step that links back to
this page.


### When to Use This Page


- **First-time deployment** -- You are provisioning the cluster for the first time
  and want telemetry enabled from the start. Complete the full sequence below.
- **Enabling telemetry on an existing cluster** -- The cluster is already
  provisioned and you are turning on a new telemetry source. See
  [Update Telemetry on a Running Cluster](#update-telemetry-on-a-running-cluster).


## Prerequisites


- The `omnia_core` container is deployed on the OIM. See
  [Deploy Omnia Core](../Setup/deploy_omnia_core.md).
- The mapping file (`pxe_mapping_file.csv`) is created. See
  [Create Mapping File](../Setup/create_mapping_file.md).
- The telemetry source you want has been configured. See the per-source guides
  under [Telemetry Setup](setup_telemetry.md).


## Procedure


Run the following playbooks **in order** from inside the `omnia_core` container.
Telemetry deployment happens automatically during `provision.yml`; iDRAC telemetry
additionally requires `telemetry.yml`.

| Order | Playbook | Purpose | Telemetry Role |
| --- | --- | --- | --- |
| 1 | `prepare_oim.yml` | Deploys OIM infrastructure (OpenCHAMI, Pulp, registry, MinIO, step-ca) | Foundation for repos and provisioning |
| 2 | `local_repo.yml` | Downloads packages, images, and telemetry container images into Pulp | Pulls telemetry images and RPMs (e.g., `ldms`, `service_k8s`) |
| 3 | `build_image_x86_64.yml` / `build_image_aarch64.yml` | Builds node OS images | Bakes telemetry packages into node images |
| 4 | `provision.yml` | Provisions nodes and **deploys the telemetry stack** to the service K8s cluster | Deploys UFM, VAST, PowerScale, LDMS, OME/Vector, iDRAC infra |
| 5 | `telemetry.yml` | **iDRAC only** -- initiates iDRAC telemetry collection | Triggers iDRAC data collection |

### Step 1: Prepare the OIM

Deploys the OIM infrastructure: OpenCHAMI provisioning stack, Pulp local
repository, container registry, MinIO S3 storage, OpenLDAP, and step-ca.

```bash title="Run on: omnia_core container"
cd /omnia/prepare_oim
ansible-playbook prepare_oim.yml
```

For details, see [Prepare OIM](../Setup/prepare_oim.md){target="_blank"}.

### Step 2: Create Local Repositories

Downloads all RPMs, container images, and tarballs (including telemetry component
images) into the Pulp repository for air-gapped deployment.

```bash title="Run on: omnia_core container"
cd /omnia/local_repo
ansible-playbook local_repo.yml
```

For details, see [Create Local Repos](../Setup/create_local_repos.md){target="_blank"}.

!!! important

    The software and repositories that `local_repo.yml` downloads are driven by
    `software_config.json` and `local_repo_config.yml`. Ensure the telemetry
    software your source requires (for example, `ldms`, `service_k8s`, or
    `csi_driver_powerscale`) and its repositories are listed **before** you run
    this playbook. Each telemetry guide lists the exact entries in its
    **Add Required Software** step.

### Step 3: Build Node Images

Builds the OS images for the node architectures in your cluster.

```bash title="Run on: omnia_core container (x86_64)"
cd /omnia/build_image_x86_64
ansible-playbook build_image_x86_64.yml
```

```bash title="Run on: omnia_core container (aarch64)"
cd /omnia/build_image_aarch64
ansible-playbook build_image_aarch64.yml -i inventory
```

!!! note

    Build only the images for the architectures present in your mapping file. If
    you have aarch64 nodes, ensure the telemetry software has an `aarch64` entry
    in `software_config.json` and the corresponding aarch64 repositories are set
    in `local_repo_config.yml`.

For details, see [Build Cluster Images](../Setup/build_cluster_images.md).

### Step 4: Provision Nodes (Deploys Telemetry)

Provisions the cluster nodes and deploys the telemetry stack to the service
Kubernetes cluster. During this step, Omnia:

- Generates the telemetry deployment manifests and the `telemetry.sh` script.
- Deploys the enabled telemetry sources (UFM, VAST, PowerScale, LDMS aggregator,
  OME/Vector bridges, and iDRAC infrastructure) based on `telemetry_config.yml`.
- Installs node-side telemetry agents (LDMS samplers, DCGM) via cloud-init.

```bash title="Run on: omnia_core container"
cd /omnia/provision
ansible-playbook provision.yml
```

After `provision.yml` completes, PXE boot the nodes. Cloud-init on the service K8s
control plane node then executes `telemetry.sh` automatically to bring up the
telemetry stack. For details, see [Provision Nodes](../Setup/provision_nodes.md)
and [PXE Boot Playbook](../Setup/configure_pxe_boot.md).

### Step 5: Deploy iDRAC Telemetry (iDRAC Only)

If you enabled iDRAC telemetry, run `telemetry.yml` after provisioning to validate
the BMC IPs and initiate iDRAC telemetry collection.

```bash title="Run on: omnia_core container"
cd /omnia/telemetry
ansible-playbook telemetry.yml
```

!!! note

    This step is required **only** for iDRAC telemetry. All other telemetry
    sources are fully deployed by `provision.yml`.


### Update Telemetry on a Running Cluster


If the cluster is already provisioned and you want to enable or
reconfigure a telemetry source:

1. Update `telemetry_config.yml`.
2. If you changed `software_config.json` or repositories, re-run `local_repo.yml`.
3. Re-run `provision.yml` to regenerate the telemetry deployment manifests:

    ```bash title="Run on: omnia_core container"
    cd /omnia/provision
    ansible-playbook provision.yml
    ```

4. Apply the updated telemetry stack by executing `telemetry.sh` on the service
   K8s control plane:

    ```bash title="Run on: K8s control plane"
    <K8s_NFS_mount_point>/telemetry/telemetry.sh
    ```

5. Re-run `telemetry.yml` to validate the BMC IPs and initiate iDRAC data collection:

    ```bash title="Run on: omnia_core container"
    cd /omnia/telemetry
    ansible-playbook telemetry.yml
    ```

    !!! note

        Do not update the `bmc_group_data.csv` file from a previous run. This ensures that iDRAC telemetry metrics are collected for all previously configured iDRAC IPs.


## Verification

Verify that the input files were successfully processed and the telemetry stack is operational. Use the component-specific verification pages listed in Next Steps to confirm each enabled telemetry source is collecting data.


## Next Steps
After deployment, verify that each enabled telemetry source is collecting data.
Each component has its own verification page:

- [Verify iDRAC Telemetry](verify_idrac.md)
- [Verify LDMS Telemetry](verify_ldms.md)
- [Verify PowerScale Telemetry](verify_powerscale.md)
- [Verify UFM Telemetry](verify_ufm.md)
- [Verify VAST Telemetry](verify_vast.md)
- [Verify OME Telemetry](verify_ome.md)
- [Verify Vector-LDMS Bridge](verify_vector_ldms.md)

## Troubleshooting
[Telemetry Troubleshooting](../../Troubleshooting/telemetry.md)
