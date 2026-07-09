
# Provision Nodes

Run the `provision.yml` playbook to provision discovered nodes with their OS image, hostname, and cluster services via OpenCHAMI.

## Overview

The `provision.yml` playbook performs the following:

1. Validates provisioning parameters, the OIM timezone, and the boot image for each functional group.
2. Configures passwordless SSH between the OIM and cluster nodes.
3. Authenticates with the OpenCHAMI cluster.
4. Provisions nodes via the `configure_ochami` role -- discovers nodes in the State Management Database (SMD), configures Boot Script Service (BSS) and cloud-init, and sets node hostnames.
5. Applies the `mount_config`, `k8s_config`, `slurm_config`, `openldap`, and `telemetry` roles to configure cluster services on the provisioned nodes.

## Prerequisites

- The pxe mapping file is created or the [Discover Nodes](discover_nodes.md) procedure is complete.
- The [Build Cluster Images](build_cluster_images.md) procedure is complete (boot images are in MinIO).
- The [Create Mapping File](create_mapping_file.md) procedure is complete.
- The [Configure Credentials](configure_credentials.md) procedure is complete.
- OpenCHAMI services are running on the OIM (see [Prepare Oim](prepare_oim.md)).

## Procedure

1. Run the `provision.yml` playbook:

    ```bash title="Run on: omnia_core container"
    cd /omnia/provision
    ansible-playbook provision.yml 
    ```

## Verification

1. Verify nodes are registered as type `Node` in SMD:

    ```bash title="Run on: omnia_core container"
    ochami smd component get | jq '.Components[] | select(.Type == "Node")'
    ```

2. Verify the BSS service is running:

    ```bash title="Run on: omnia_core container"
    ochami bss service status
    ```

3. Verify the cloud-init service is running:

    ```bash title="Run on: omnia_core container"
    ochami cloud-init service status
    ```

## Troubleshooting

- **Node not registered in SMD**: Confirm the `smd` service is running (`systemctl status smd`), then re-run `provision.yml`.
- **cloud-init-server not reachable**: Restart `openchami.target` (`systemctl restart openchami.target`) and re-run the playbook.
- **Hostname not applied to node**: Verify the mapping file entries in [Create Mapping File](create_mapping_file.md), then re-run `provision.yml`.
- **mount_config, k8s_config, or slurm_config role fails**: Verify the corresponding input file (`storage_config.yml`, `omnia_config.yml`) is correctly configured, then re-run `provision.yml`.

!!! info

    - [Provision Config](../../Reference/Configuration/provision_config.md) -- `provision_config.yml` parameter reference.
    - [PXE Boot Playbook](configure_pxe_boot.md) -- Configure PXE boot order for provisioned nodes.
    - [Configure Mounts](../Storage/configure_mounts.md) -- Storage mount configuration applied during provisioning.
    - [Verify Cluster](verify_cluster.md) -- End-to-end cluster verification.
