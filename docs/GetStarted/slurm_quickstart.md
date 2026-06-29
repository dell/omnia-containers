# Path A: Slurm Quick Start


Deploy a 4-node Slurm HPC cluster in approximately 2 hours. This is the
fastest path to a working Omnia environment and the recommended starting
point for first-time users.

**What you will build:**

| Role | Functional Group | Purpose |
| --- | --- | --- |
| OIM (management) | -- | Runs the `omnia_core` container; executes all Ansible playbooks. Does **not** join the Slurm cluster. |
| Head node | `slurm_control_node` | Runs `slurmctld` (Slurm controller daemon) and `slurmdbd` (accounting database). |
| Compute node | `slurm_node` | Runs `slurmd`; executes jobs submitted to the cluster. |
| Login node | `login_node` | User-facing SSH gateway for job submission. Does not run `slurmd`. |

**Estimated time:** ~2 hours (varies with network speed and node count).

!!! note

    This tutorial assumes you have completed every item on the
    [Prerequisites Checklist](prerequisites_checklist.md). If you have not, stop here and finish
    that first.

## Step 1 -- Deploy the omnia_core Container


Clone the Omnia repository, build the container images, and install the
`omnia_core` Podman container on the OIM.

```shell title="Run on OIM (as root)"
# Clone the Omnia repository
cd /opt
git clone https://github.com/dell/omnia.git
cd omnia

# Build the required container images
bash build_images.sh
```


!!! tip

    `build_images.sh` creates the `omnia_core` and supporting images.
    It takes 5--10 minutes on a fast connection. Watch for any `FAILED`
    messages in the output.

```shell title="Run on OIM (as root)"
# Install and start the omnia_core container
bash omnia.sh --install

# Verify that the omnia_core container is running
systemctl status omnia_core
```


You should see `active (running)` in the output. If the service is
`failed`, check `journalctl -u omnia_core` for errors.

```shell title="Run on OIM (as root)"
# Verify you can access the container shell
ssh omnia_core
# You should land at a prompt inside the container. Type 'exit' to return.
exit
```



## Step 2 -- Create the Mapping File


The mapping file tells Omnia which physical servers map to which cluster
roles. Create a CSV at `/opt/omnia/input/project_default/mapping.csv`.

```shell title="Run on OIM (as root)"
cat > /opt/omnia/input/project_default/mapping.csv << 'EOF'
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP
slurm_control_node,slurm,ABC1234,,head01,24:6E:96:AA:BB:01,10.5.0.101,,10.3.0.101
slurm_node,slurm,DEF5678,,compute01,24:6E:96:AA:BB:02,10.5.0.102,,10.3.0.102
login_node,slurm,GHI9012,,login01,24:6E:96:AA:BB:03,10.5.0.103,,10.3.0.103
EOF
```


!!! warning

    Replace the placeholder values (`SERVICE_TAG`, `ADMIN_MAC`,
    `ADMIN_IP`, `BMC_IP`) with the actual values from your servers.
    Collect service tags from the server pull-out tab or iDRAC. Collect
    MAC addresses from `iDRAC > Network > NIC Selection` or by running
    `ip link` on each node.

**Field reference:**

- **FUNCTIONAL_GROUP_NAME** -- The Omnia role: `slurm_control_node`,
  `slurm_node`, or `login_node`.
- **GROUP_NAME** -- An arbitrary cluster group label (e.g., `slurm`).
- **SERVICE_TAG** -- The Dell service tag printed on the server chassis.
- **PARENT_SERVICE_TAG** -- Leave empty unless using modular chassis (MX).
- **HOSTNAME** -- Desired hostname; Omnia configures this during provisioning.
- **ADMIN_MAC** -- MAC address of the PXE-boot NIC on the admin network.
- **ADMIN_IP** -- Desired static IP on the admin network.
- **BMC_MAC** -- (Optional) iDRAC MAC address.
- **BMC_IP** -- iDRAC IP on the BMC network.


## Step 3 -- Provide Inputs


Omnia ships example input templates for common deployment patterns. Copy
the bare-metal Slurm template (without service K8s) and customize it.

```shell title="Run on OIM (inside omnia_core container)"
ssh omnia_core

# Copy the template inputs to the active input directory
cp -r /opt/omnia/examples/input_template/bare_metal_slurm/x86_64/without_service_k8s/* \
    /opt/omnia/input/project_default/

# List the copied files
ls -la /opt/omnia/input/project_default/
```


You should see these key input files:

- `network_spec.yml` -- Network CIDRs and interfaces
- `provision_config.yml` -- OS provisioning settings (ISO path, timezone)
- `software_config.json` -- Software stack selections
- `omnia_config.yml` -- Slurm and cluster configuration
- `security_config.yml` -- Authentication settings
- `storage_config.yml` -- NFS mount configuration
- `local_repo_config.yml` -- Repository mirror settings

!!! tip

    Each file is heavily commented with inline documentation. Read the
    comments before changing values. When in doubt, keep the defaults --
    they work for the vast majority of deployments.

## Step 4 -- Set Credentials


Run the `credentials_utility.yml` playbook to securely store passwords
for iDRAC, the provisioning OS, and other services. This playbook prompts
you interactively.

```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook credentials_utility.yml
```


You will be prompted to set:

- **Provisioning OS password** -- root password for provisioned nodes.
- **iDRAC credentials** -- username and password for out-of-band access.
- **MySQL/MariaDB password** -- used by `slurmdbd` for Slurm accounting.

!!! warning

    Store these credentials in a password manager. You will need the iDRAC
    credentials if you ever need to access the BMC console, and the
    provisioning password for emergency SSH access to nodes.

## Step 5 -- Prepare the OIM


Edit the two critical network-related input files, then run
`prepare_oim.yml` to configure the OIM's networking, DHCP, TFTP,
and HTTP services.

### **5a. Edit** `network_spec.yml`


```shell title="Run on OIM (inside omnia_core container)"
vi /opt/omnia/input/project_default/network_spec.yml
```


Set the following values (adjust to match your environment):

```yaml title="Example network_spec.yml excerpt"
admin_network:
  nic: eno2                    # OIM NIC connected to admin switch
  cidr: 10.5.0.0/16            # Admin subnet CIDR
  static_range: 10.5.0.100-10.5.0.200
  gateway: 10.5.0.1

bmc_network:
  nic: eno2                    # Can share NIC if VLANs are used
  cidr: 10.3.0.0/16            # BMC subnet CIDR
  static_range: 10.3.0.100-10.3.0.200
```


### **5b. Edit** `provision_config.yml`


```shell title="Run on OIM (inside omnia_core container)"
vi /opt/omnia/input/project_default/provision_config.yml
```


Key fields to verify or set:

```yaml title="Example provision_config.yml excerpt"
# Path to the RHEL or Rocky Linux ISO on the OIM
iso_path: /opt/isos/RHEL-8.8-x86_64-dvd.iso

# Timezone for provisioned nodes
timezone: America/Chicago

# Domain name for the cluster
domain_name: omnia.local
```


### **5c. Run** `prepare_oim.yml`


```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook prepare_oim.yml -i /opt/omnia/input/project_default/mapping.csv
```


!!! tip

    `prepare_oim.yml` takes 10--15 minutes. It configures DHCP, TFTP,
    HTTP, and NFS services on the OIM. If it fails, re-read the error
    message carefully -- most failures are caused by incorrect NIC names or
    CIDR values in `network_spec.yml`.

## Step 6 -- Verify OIM Services


After `prepare_oim.yml` completes, verify that all Omnia-managed
services are running.

```shell title="Run on OIM (inside omnia_core container)"
systemctl list-dependencies omnia.target
```


Every listed service should show a green dot (`●`) indicating
`active`. Key services to verify:

- `dhcpd.service` -- DHCP server for PXE boot
- `tftp.socket` -- TFTP for PXE boot loader delivery
- `httpd.service` -- HTTP for kickstart/autoinstall files
- `nfs-server.service` -- NFS for shared storage

```shell title="Run on OIM (inside omnia_core container)"
# Quick health check -- all should return 'active'
for svc in dhcpd tftp.socket httpd nfs-server; do
    echo -n "$svc: "; systemctl is-active $svc
done
```



## Step 7 -- Create Local Repositories


Build local mirrors of OS packages, Python packages, and container images
so that node provisioning does not depend on external internet access.

```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook local_repo.yml
```


!!! warning

    `local_repo.yml` can take **30--60 minutes** depending on internet
    bandwidth. It downloads several GB of packages. Ensure the OIM has
    sufficient disk space (see [Prerequisites Checklist](prerequisites_checklist.md)) and a stable
    internet connection.

When the playbook finishes, verify that the local repo is accessible:

```shell title="Run on OIM (inside omnia_core container)"
# Check that the repo metadata exists
ls /opt/omnia/local_repo/
dnf repolist --all | grep omnia
```



## Step 8 -- Build Node Images


Build the provisioning image that Omnia will PXE-boot onto target nodes.

```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook build_image_x86_64.yml
```


This playbook creates a customized OS image with pre-installed Slurm
packages, Omnia agents, and configuration. The image is stored in the
local S3-compatible object store.

```shell title="Run on OIM (inside omnia_core container)"
# Verify the image was uploaded to the local S3 store
s3cmd ls s3://omnia-images/
```


You should see at least one `.qcow2` or `.raw` image file listed.

!!! tip

    If `build_image_x86_64.yml` fails with a disk-space error, free space
    under `/opt` and re-run. The image build process requires ~50 GB of
    temporary space.

## Step 9 -- Discover and Provision Nodes


Power on your target nodes (or ensure they are powered on with PXE boot
priority). Then run the discovery playbook.

```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook discovery.yml
```


`discovery.yml` performs the following:

1. Sends Wake-on-LAN magic packets to MACs listed in `mapping.csv`.
2. Boots each node via PXE from the OIM's TFTP/HTTP services.
3. Installs the base OS image built in Step 8.
4. Configures networking (hostname, admin IP, BMC IP) per the mapping file.
5. Registers each node in the Omnia inventory.

!!! warning

    Discovery can take **20--40 minutes** per node depending on network
    speed and hardware POST time. Monitor progress in the Ansible output.
    If a node fails to PXE boot, verify:

    - The node's BIOS boot order (NIC first).
    - The admin NIC MAC in `mapping.csv` matches the physical NIC.
    - The admin switch port is on the correct VLAN.

After discovery completes, verify all nodes are reachable:

```shell title="Run on OIM (inside omnia_core container)"
# Ping all discovered nodes
ansible all -m ping -i /opt/omnia/inventories/project_default/inventory
```



## Step 10 -- Deploy Slurm


Run the main Omnia playbook to install and configure Slurm across the
cluster.

```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook omnia.yml
```


`omnia.yml` orchestrates:

- Slurm controller (`slurmctld`) installation on the head node.
- Slurm database daemon (`slurmdbd`) setup with MariaDB.
- Slurm compute daemon (`slurmd`) on all compute nodes.
- Munge key distribution for authentication.
- NFS home directory mounts (if configured in `storage_config.yml`).
- Login node configuration (SSH access, `srun`/`sbatch` clients).

!!! tip

    `omnia.yml` typically takes 15--30 minutes. If it fails partway
    through, fix the reported error and **re-run the same command** -- Omnia
    playbooks are idempotent and will skip already-completed tasks.

## Step 11 -- Verify the Cluster


Congratulations! Your Slurm cluster should now be operational. Run these
verification commands.

```shell title="Run on OIM (inside omnia_core container)"
# SSH to the head node
ssh head01
```


```shell title="Run on head node (head01)"
# Check Slurm controller status
systemctl status slurmctld

# View cluster partition and node info
sinfo
```


Expected `sinfo` output:

```text title="Expected output"
PARTITION AVAIL  TIMELIMIT  NODES  STATE NODELIST
normal*      up   infinite      1   idle compute01
```


```shell title="Run on head node (head01)"
# Run a test job across all nodes
srun -N 1 hostname

# Submit a batch job
sbatch --wrap="echo Hello from \$(hostname)" --output=/tmp/hello.out
cat /tmp/hello.out
```


```shell title="Run on login node (login01)"
# Verify login node can submit jobs
ssh login01
srun -N 1 hostname
```


If all commands succeed, your Slurm cluster is fully operational.

!!! tip

    Run `srun -N 1 --pty bash` to get an interactive shell on a compute
    node -- useful for debugging and verifying software installations.

## What's Next?


Your 4-node Slurm cluster is ready for workloads. Here are common next
steps:

**Add more compute nodes**
   Edit `mapping.csv` to add additional `slurm_node` entries, re-run
   `discovery.yml` and then `omnia.yml`.

**Enable telemetry and monitoring**
   Follow [Full Deployment](full_deployment.md) (Path B) starting from the telemetry
   sections to add Grafana dashboards and iDRAC metrics collection.

**Configure authentication (LDAP/FreeIPA)**
   Edit `security_config.yml` to enable FreeIPA or LDAP, then run
   `auth.yml`. See the [Full Deployment](full_deployment.md) guide for details.

**Set up shared storage**
   Edit `storage_config.yml` to configure NFS mounts from PowerScale or
   other storage appliances, then re-run `omnia.yml`.

**Submit real workloads**
   Users can SSH to `login01` and use standard Slurm commands
   (`sbatch`, `srun`, `squeue`, `scancel`) to submit jobs.

!!! info

    - [Index](../Overview/index.md) -- Architecture and component overview
    - [Full Deployment](full_deployment.md) -- Add K8s and telemetry to this cluster
    - [Prerequisites Checklist](prerequisites_checklist.md) -- Return to the master checklist
