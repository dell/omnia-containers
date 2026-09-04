# Provision Nodes

Provision bare-metal cluster nodes using the orchestrator domain. This process reads the PXE mapping file, configures boot scripts and cloud-init based on functional groups, and prepares all target servers for PXE boot.

## Overview

The orchestrator domain provisions nodes by functional group (Kubernetes, Slurm, OS, or custom). It reads the PXE mapping file from discovery, configures BSS boot parameters and cloud-init configurations, and prepares all target servers for PXE boot.

## Prerequisites

- The [Setup the OIM](../main/setup_oim.md) procedure is complete (main domain setup is complete)
- The [Initialize Domains](../main/initialize_domains.md) procedure is complete (orchestrator domain is initialized)
- The [Configure Repos](../repo_manager/configure_repos.md) procedure is complete (repo_manager domain executed)
- The [Build Images](../image_build_manager/build_images.md) procedure is complete (image_build_manager domain executed)
- The [Discover Nodes](../discovery/discover_nodes.md) procedure is complete (discovery domain executed)
- The [Deploy OpenCHAMI](deploy_openchami.md) procedure is complete (OpenCHAMI containers are running)
- The [Deploy OpenLDAP](deploy_openldap.md) procedure is complete (if authentication is enabled)

### Input Contract

The orchestrator domain requires the following inputs for node provisioning:

| Input | Location | Purpose |
|-------|----------|---------|
| `build_status.yml` | `/opt/omnia/image_build_manager/output/<project>/build_status.yml` | Boot image paths from image_build_manager |
| `pxe_mapping_file.csv` | `/opt/omnia/discovery/output/<project>/discovery/bmc_pxe_mapping_file.csv` | BMC/PXE mapping from discovery |
| `orchestrator_config.yml` | `/opt/omnia/orchestrator/input/<project>/orchestrator_config.yml` | Main orchestrator configuration |
| `omnia_config_credentials.yml` | `/opt/omnia/orchestrator/input/<project>/omnia_config_credentials.yml` | Vault-encrypted credentials |

**Required Files:**
- `build_status.yml` - Required for boot image configuration
- `pxe_mapping_file.csv` - Required for functional group generation
- `orchestrator_config.yml` - Always required
- `omnia_config_credentials.yml` - Auto-created if missing

**Input Sources:**
- **image_build_manager** - Provides `build_status.yml` with boot image paths
- **discovery** - Provides `pxe_mapping_file.csv` with BMC/PXE mapping
- **Administrator** - Provides `orchestrator_config.yml`
- **Domain initialization** - Stages input files from samples directory

## Procedure

1. **Verify all prerequisites are complete**:

    - Verify boot images exist:

        ```bash title="Run on: OIM host"
        s3cmd ls -Hr s3://boot-images
        ```

2. **Run the orchestrator provision tag**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run orchestrator --tags provision
    ```

    This performs the following:
    - SSH key distribution and OpenCHAMI authentication
    - Provision Kubernetes functional groups (if present)
    - Provision Slurm+Login functional groups (if present)
    - Provision OS-only functional groups (if present)
    - Provision custom functional groups (if present)
    - Configures BSS boot parameters
    - Configures cloud-init for each node
    - Generates inventories and verifies provisioning

3. **PXE boot the nodes** using one of the following methods:

    - **Manual PXE boot**: Power on target servers and select network boot from the BIOS boot menu
    - **Automated PXE boot**: Use the orchestrator pxeboot tag. For detailed steps, see [Configure PXE Boot](../Configure/configure_pxe_boot.md)

4. **Monitor provisioning progress**:

    ```bash title="Run on: OIM host"
    omnia-cli logs orchestrator
    ```

!!! note

    - Ansible runs concurrently on multiple nodes by default. To change this, update the `forks` value in the orchestrator configuration
    - Omnia does not track the OS installation on the target node. Verify the installation status manually
    - While the `admin_nic` on cluster nodes is configured by Omnia to be static, the public NIC IP address must be configured by the user

!!! caution

    - In case of any IP route conflict between the admin network and an additional NIC (for example, an internet NIC), delete the admin route or configure the IP route priority based on your cluster requirements
    - If internet connectivity is required on the target node, configure it after the node is booted
    - To avoid breaking the password-less SSH channel on the OIM, do not run `ssh-keygen` commands after execution of the provision tag

!!! important

    After running the provision tag, the file `/opt/omnia/orchestrator/input/<project>/omnia_config_credentials.yml` is encrypted. To edit it, use:

    ```bash title="Run on: OIM host"
    ansible-vault edit omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key
    ```

    Post execution of the provision tag, IPs and hostnames cannot be reassigned by changing the mapping file.

## Verification

1. **Check provision logs for errors**:

    ```bash title="Run on: OIM host"
    omnia-cli logs orchestrator
    ```

2. **Check cloud-init output on a provisioned node**:

    ```bash title="Run on: provisioned compute node"
    cat /var/log/cloud-init-output.log | tail -30
    ```

3. **Verify all nodes are reachable**:

    ```bash title="Run on: OIM host"
    ansible all -m ping
    ```

## Output Contract

After successful execution, the orchestrator domain produces the following output contract for provisioning:

| Output | Location | Purpose |
|--------|----------|---------|
| Functional groups configuration | `/opt/omnia/orchestrator/output/<project>/orchestrator/` | Generated functional groups from PXE mapping |
| BSS configurations | `/opt/omnia/orchestrator/output/<project>/orchestrator/` | Boot parameter configurations |
| Cloud-init configurations | `/opt/omnia/orchestrator/output/<project>/orchestrator/` | Default/group/node cloud-init configs |
| `/opt/omnia/hosts` | `/opt/omnia/hosts` | Ansible inventory for cluster nodes |

This contract is consumed by:
- **Cluster workflows** - For ongoing operations
- **Administrators** - For manual cluster management

## Next Steps

- [Configure PXE Boot](../Configure/configure_pxe_boot.md) -- Automate PXE boot for provisioned nodes
- [Add Nodes](add_nodes.md) -- Add new nodes to the cluster
- [Remove Nodes](remove_nodes.md) -- Remove nodes from the cluster

## Troubleshooting

**Provision fails at "Waiting for node registration"**

   Verify the admin network switch is configured and nodes can PXE boot. Check DHCP and TFTP services on the OIM:

   ```bash title="Run on: OIM host"
   systemctl status coredhcp.service
   systemctl status tftpd.service
   ```

**Cloud-init did not complete on provisioned node**

   Check the cloud-init log on the affected node:

   ```bash title="Run on: provisioned compute node"
   cat /var/log/cloud-init-output.log
   journalctl -u cloud-init --no-pager -n 50
   ```

**Nodes not reachable after provisioning**

   Verify admin network connectivity and NIC configuration:

   ```bash title="Run on: OIM host"
   ping -c 3 <admin-ip>
   arping -D -I <admin-nic> <admin-ip>
   ```

   Check for IP route conflicts between admin and public networks on the node.

**omnia_config_credentials.yml is encrypted and cannot be edited**

   Use the vault password file to edit:

   ```bash title="Run on: OIM host"
   ansible-vault edit omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key
   ```



















