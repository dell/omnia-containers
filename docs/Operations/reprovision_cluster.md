# Re-provision Cluster Nodes

Re-provisioning replaces the diskless image on existing cluster nodes. Since Omnia uses stateless (diskless) provisioning, nodes load their OS entirely from network-delivered images. Re-provisioning is performed by PXE booting the target nodes so they receive the latest image from the OIM.

!!! warning

    If you deploy a fresh Slurm or Service Kubernetes cluster, ensure the NFS server share path used by the cluster is cleared manually. NFS details are configured in `storage_config.yml`.

!!! danger

    Re-provisioning the Slurm Control Node or Kube Control Plane requires the entire cluster to be reprovisioned.

## Prerequisites

- The OIM is healthy and all OIM services are running (verify with [Verify OIM Services](../HowTo/Setup/verify_oim_services.md)).
- NFS or PowerScale shared storage is accessible from the OIM and all cluster nodes.

## Re-provision without modifications

If no changes have been made to the mapping file, `software_config.json`, or input configuration files, PXE boot the target nodes. The OS is automatically installed on every PXE boot. This can be done using the [PXE Boot Playbook](../HowTo/Setup/configure_pxe_boot.md).

```bash title="Run on: OIM host"
ssh omnia_core
cd /omnia/utils
ansible-playbook set_pxe_boot.yml -i inventory
```

## Re-provision with modifications

Use this procedure when you have updated the mapping file, `software_config.json`, or any input configuration files.

1. Update the PXE mapping file (for mapping file discovery) or ensure nodes are configured in OME (for OME-based provisioning). Update `software_config.json` as required.

2. If `software_config.json` has been modified, run `local_repo.yml` and then build new images:

    ```bash title="Run on: omnia_core container"
    cd /omnia/local_repo
    ansible-playbook local_repo.yml
  
    cd /omnia/build_image_x86_64
    ansible-playbook build_image_x86_64.yml

    # For aarch64 images
    cd /omnia/build_image_aarch64
    ansible-playbook build_image_aarch64.yml -i inventory
    ```

3. After images are created, run `provision.yml`:

    ```bash title="Run on: omnia_core container"
    cd /omnia/provision
    ansible-playbook provision.yml
    ```

4. PXE boot the target nodes using the [PXE Boot Playbook](../HowTo/Setup/configure_pxe_boot.md).

## NFS share cleanup

When deploying a fresh cluster, you must clear the NFS share paths before re-provisioning. [OIM Cleanup](oim_cleanup.md) can be used to clear the NFS share paths. Choose one of the following approaches based on your requirements.

### Reuse the same share paths

1. Power off all servers except the OIM.
2. From the OIM, delete all contents in the nfs share used by the cluster (identified in `storage_config.yml`):

    ```bash title="Run on: OIM host"
    rm -rf <mounted_share_path>/*
    ```

3. Run `provision.yml`:

    ```bash title="Run on: omnia_core container"
    ssh omnia_core
    cd /omnia/provision
    ansible-playbook provision.yml
    ```

4. PXE boot the target nodes using the [PXE Boot Playbook](../HowTo/Setup/configure_pxe_boot.md).

### Use new share paths

1. Update `mounts` in [storage_config.yml](../Reference/Configuration/storage_config.md) corresponding to `nfs_storage_name` under `slurm_cluster` or `service_k8s_cluster` in [omnia_config.yml](../Reference/Configuration/omnia_config.md).

2. Run `provision.yml`:

    ```bash title="Run on: omnia_core container"
    cd /omnia/provision
    ansible-playbook provision.yml
    ```

3. PXE boot the target nodes using the [PXE Boot Playbook](../HowTo/Setup/configure_pxe_boot.md).

## Verification

```bash title="Run on: Slurm control node"
sinfo
```

```bash title="Run on: Kubernetes control plane"
kubectl get nodes
```

!!! info

    - [Add/Remove Nodes](add_remove_nodes.md) -- Add or remove nodes without re-imaging.
    - [OIM Cleanup](oim_cleanup.md) -- Full teardown and rebuild of the OIM itself.
    - [Build Cluster Images](../HowTo/Setup/build_cluster_images.md) -- Image build procedure.
    - [Configure Mounts](../HowTo/Storage/configure_mounts.md) -- NFS mount configuration for cluster nodes.
    - [Configure PXE Boot](../HowTo/Setup/configure_pxe_boot.md) -- PXE boot configuration for cluster nodes.

