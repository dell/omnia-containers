
# Prepare the OIM


Prepare the Omnia Infrastructure Manager (OIM) by deploying the core
management services: OpenCHAMI (provisioning), Pulp (repository management),
and optionally BuildStreaM and Omnia Auth containers.

## Overview


The `prepare_oim.yml` playbook configures the OIM host with all services
required for bare-metal provisioning and cluster management. It reads your
`network_spec.yml` and `provision_config.yml` input files and deploys:

- **OpenCHAMI** -- Node discovery, state management, and boot script services.
- **Pulp** -- RPM repository management and synchronization.
- **CoreDHCP** -- DHCP service for PXE boot on the admin network.
- **MinIO** -- S3-compatible object storage for boot images and artifacts.
- **Registry** -- Local container image registry.
- **BuildStreaM** *(optional)* -- CI/CD pipeline services.
- **Omnia Auth** *(optional)* -- Centralized authentication container.


## Prerequisites


- The [Deploy Omnia Core](deploy_omnia_core.md) procedure is complete.
- The [Configure Inputs](configure_inputs.md) procedure is complete (`network_spec.yml` and
  `provision_config.yml` are configured).
- The [Configure Credentials](configure_credentials.md) procedure is complete (encrypted credentials
  file exists).
- The OIM has at least 2 NICs connected to the admin and BMC networks.
- Network switches are configured with the appropriate VLANs.


## Procedure


1. **Enter the omnia_core container**:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```


2. **Review and edit network_spec.yml** (if not already done):

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/network_spec.yml
   ```


   Ensure the admin and BMC network parameters match your physical network:

   ```yaml title="File: /opt/omnia/input/project_default/network_spec.yml"
   ---
   admin_network:
     nic_name: "eno1"
     static_range: "10.5.0.100-10.5.0.200"
     dynamic_range: "10.5.0.201-10.5.0.254"
     subnet: "10.5.0.0"
     netmask: "255.255.255.0"
     gateway: "10.5.0.1"

   bmc_network:
     nic_name: "eno2"
     static_range: "10.3.0.100-10.3.0.200"
     dynamic_range: "10.3.0.201-10.3.0.254"
     subnet: "10.3.0.0"
     netmask: "255.255.255.0"
   ```


3. **Review and edit provision_config.yml** (if not already done):

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/provision_config.yml
   ```


   ```yaml title="File: /opt/omnia/input/project_default/provision_config.yml"
   ---
   timezone: "America/Chicago"
   language: "en-US"
   iso_file_path: "/opt/omnia/iso/RHEL-8.8-x86_64-dvd.iso"
   default_lease_time: 86400
   pxe_mapping_file_path: "/opt/omnia/input/project_default/pxe_mapping_file.csv"
   ```


4. **Run the prepare_oim playbook**:

   ```bash title="Run on: omnia_core container"
   cd /omnia/prepare_oim
   ansible-playbook prepare_oim.yml
   ```


   !!! note

       If your credentials file is encrypted with Ansible Vault, add the
       `--ask-vault-pass` flag:

       ```bash title="Run on: omnia_core container"
       ansible-playbook prepare_oim.yml --ask-vault-pass
       ```


   The playbook performs the following tasks:

   - Validates input files.
   - Configures network interfaces on the OIM.
   - Deploys OpenCHAMI services (SMD, BSS, CoreDHCP, TFTP).
   - Deploys Pulp for RPM repository management.
   - Deploys MinIO for S3-compatible object storage.
   - Sets up the local container registry.
   - Optionally deploys BuildStreaM and Omnia Auth containers.

   Execution time: **15-30 minutes** depending on network speed and hardware.


## Verification


1. **Check the omnia.target service tree**:

   ```bash title="Run on: OIM host"
   systemctl list-dependencies omnia.target
   ```


   Expected service tree:

   ```text title="Expected output on: OIM host"
   omnia.target
   ├─minio.service
   ├─omnia_auth.service
   ├─omnia_core.service
   ├─pulp.service
   ├─registry.service
   └─openchami.target
     ├─bss.service
     ├─coredhcp.service
     ├─cloud-init-server.service
     ├─dnsmasq.service
     ├─hydra.service
     ├─image-server.service
     ├─opaal.service
     ├─smd.service
     └─tftpd.service
   ```


2. **Verify all services are active**:

   ```bash title="Run on: OIM host"
   systemctl status omnia_core.service
   systemctl status openchami.target
   ```


3. **Test OpenCHAMI CLI**:

   ```bash title="Run on: omnia_core container"
   ochami --help
   ```


   This should display the OpenCHAMI command-line help, confirming the CLI is
   installed and the services are accessible.

4. **Verify Pulp is running**:

   ```bash title="Run on: OIM host"
   podman ps --filter name=pulp
   ```


5. **Verify MinIO is accessible**:

   ```bash title="Run on: omnia_core container"
   s3cmd ls
   ```



## Next Steps


- [Verify Oim Services](verify_oim_services.md) -- Detailed verification of all OIM services.
- [Create Local Repos](create_local_repos.md) -- Sync RPM repositories via Pulp.
- [Build Cluster Images](build_cluster_images.md) -- Build OS images for cluster nodes.


## Troubleshooting


**Playbook fails with "network interface not found"**
   Verify the `nic_name` in `network_spec.yml` matches the actual interface
   names on the OIM:

   ```bash title="Run on: OIM host"
   ip link show
   ```


**OpenCHAMI services fail to start**
   Check the OpenCHAMI container logs:

   ```bash title="Run on: OIM host"
   podman logs smd
   podman logs bss
   podman logs coredhcp
   ```


**Pulp container fails to start**
   Ensure sufficient disk space is available (Pulp requires significant storage
   for repository synchronization):

   ```bash title="Run on: OIM host"
   df -h /var/lib/containers
   ```


**Port conflicts**
   Ensure no other services are listening on ports used by OIM services
   (DHCP: 67, TFTP: 69, HTTP: 80/8080, MinIO: 9000):

   ```bash title="Run on: OIM host"
   ss -tlnp | grep -E ':(67|69|80|8080|9000)\b'
   ```


**Playbook fails at credentials step**
   Ensure you pass `--ask-vault-pass` and enter the correct Vault password.
