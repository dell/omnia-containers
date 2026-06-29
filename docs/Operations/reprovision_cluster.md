
# Re-provision Cluster Nodes


Re-provisioning replaces the operating system and software stack on existing
cluster nodes. This is a full-cycle operation: nodes are re-imaged from the OIM
and then reconfigured with the appropriate Omnia roles (Slurm, Kubernetes, or
both).

## When to re-provision


Re-provisioning is the correct approach when:

- **Operating system update** -- You need to move nodes from one OS version to
  another (for example, RHEL 8.8 to RHEL 9.4).
- **Configuration drift** -- Nodes have accumulated manual changes that diverge
  from the desired state and a clean slate is simpler than incremental fixes.
- **Recovery** -- A node's OS is corrupted or a critical service has been
  misconfigured beyond easy repair.
- **Role change** -- A node is being reassigned from the Slurm cluster to the
  Kubernetes cluster (or vice versa).

!!! warning

    Re-provisioning destroys all data on the target node's local disks. Ensure
    any important data is backed up to shared storage (NFS, PowerScale) before
    proceeding.

## Prerequisites


- The OIM is healthy and all OIM services are running (verify with
  [Verify Oim Services](../HowTo/Setup/verify_oim_services.md)).
- Shared storage (NFS or PowerScale) is accessible for any data that must
  survive the re-provision.
- Updated OS images have been built and are available in the Pulp repository
  (see [Build Cluster Images](../HowTo/Setup/build_cluster_images.md)).
- The mapping file has been updated if node roles are changing.


## Procedure


### Step 1: Drain workloads


Before re-provisioning, gracefully drain all workloads from the target nodes.

**For Slurm nodes:**

```bash title="Run on: Slurm control node"
scontrol update NodeName=compute-03 State=DRAIN Reason="Re-provisioning"
```


Wait for running jobs to complete, or cancel them if immediate action is needed:

```bash title="Run on: Slurm control node"
# Check for running jobs on the node
squeue -w compute-03

# Cancel if necessary
scancel <job_id>
```


**For Kubernetes nodes:**

```bash title="Run on: Kubernetes control plane"
kubectl drain kube-worker-02 --ignore-daemonsets --delete-emptydir-data
```


### Step 2: Update configuration


1. Review and update the input configuration files as needed:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   cd /omnia/input
   ```


   - `mapping_file.csv` -- Update node roles if changing.
   - `provision_config.yml` -- Update OS image or provisioning parameters.
   - `omnia_config.yml` -- Update cluster-level settings.

2. If building a new OS image, run the image-build process:

   ```bash title="Run on: OIM host"
   cd /omnia
   ansible-playbook playbooks/build_cluster_images.yml
   ```


### Step 3: Re-image the nodes


Run `discovery.yml` to re-discover and PXE-boot the target nodes with the
updated OS image:

```bash title="Run on: OIM host"
cd /omnia
ansible-playbook playbooks/discovery.yml
```


The nodes will:

1. Reboot into the PXE environment.
2. Receive the new OS image from the OIM.
3. Complete the cloud-init first-boot configuration.

!!! note

    The re-imaging process typically takes 15--30 minutes per node, depending on
    image size and network speed.

### Step 4: Redeploy cluster software


After the nodes have been re-imaged and are accessible via SSH, redeploy the
Omnia cluster software:

```bash title="Run on: OIM host"
cd /omnia
ansible-playbook playbooks/omnia.yml
```


This playbook applies the full cluster configuration, including:

- Slurm controller and compute daemon setup
- Kubernetes control plane and worker configuration
- GPU drivers (CUDA / ROCm)
- Authentication (OpenLDAP client)
- Telemetry agents


## Verification


After re-provisioning is complete:

```bash title="Run on: OIM host"
# Verify Slurm nodes are back online
sinfo

# Verify Kubernetes nodes are Ready
kubectl get nodes

# Check for any failed Ansible tasks in the log
cat /opt/omnia/log/core/playbooks/omnia.log | grep -i "failed"

# Run a test Slurm job
srun -N 1 hostname
```



!!! info

    - [Add Remove Nodes](add_remove_nodes.md) -- Add or remove nodes without re-imaging.
    - [Oim Cleanup](oim_cleanup.md) -- Full teardown and rebuild of the OIM itself.
    - [Discover Nodes](../HowTo/Setup/discover_nodes.md) -- Detailed node discovery procedure.
