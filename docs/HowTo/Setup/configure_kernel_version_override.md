
# Configure Kernel Version Override

Deploy a newer, validated kernel without requiring a full base operating system upgrade, to accelerate the adoption of critical security fixes and bug patches while maintaining OS stability.


## Overview

Omnia supports a kernel version override capability through the `kernel_version_override` parameter in `provision_config.yml`. This parameter controls only the **provisioning flow** -- it determines which kernel from S3 is used when installing the OS on cluster nodes.

!!! note
    The build image process always selects the **latest kernel version available across all configured repositories**. This is not user-configurable. `kernel_version_override` only affects which kernel is installed during provisioning, and it applies to both x86_64 and aarch64 architectures.


## Prerequisites

- Omnia Infrastructure Manager (OIM) is deployed and the `omnia_core` container is running.
- `prepare_oim.yml` is executed successfully.
- Network connectivity from the OIM to the RHEL repository source (Red Hat CDN or an internal mirror).
- For RHEL subscription-based repositories: valid RHEL subscription entitlement certificates to authenticate with the Red Hat CDN.


## Procedure

### Step 1: Add RHEL Repositories

Update the local repository configuration file:

```bash title="Run on: omnia_core container"
vi /opt/omnia/input/project_default/local_repo_config.yml
```

Choose **one** of the following options based on your environment.

**Option A: RHEL subscription (EUS repositories)**

If your environment has an active RHEL subscription, configure Extended Update Support (EUS) repositories using `rhel_subscription_repo_config_x86_64`. EUS repositories provide longer support cycles for specific RHEL minor releases and are recommended for production HPC environments.

```yaml title="File: /opt/omnia/input/project_default/local_repo_config.yml"
rhel_subscription_repo_config_x86_64:
  - { url: "https://cdn.redhat.com/content/eus/rhel10/10.0/x86_64/appstream/os", gpgkey: "", sslcacert: "/opt/omnia/rhel_repo_certs/redhat-uep.pem", sslclientkey: "/opt/omnia/rhel_repo_certs/<entitlement-key>.pem", sslclientcert: "/opt/omnia/rhel_repo_certs/<entitlement-cert>.pem", name: "x86_64_appstream-eus" }
  - { url: "https://cdn.redhat.com/content/eus/rhel10/10.0/x86_64/baseos/os", gpgkey: "", sslcacert: "/opt/omnia/rhel_repo_certs/redhat-uep.pem", sslclientkey: "/opt/omnia/rhel_repo_certs/<entitlement-key>.pem", sslclientcert: "/opt/omnia/rhel_repo_certs/<entitlement-cert>.pem", name: "x86_64_baseos-eus" }
  - { url: "https://cdn.redhat.com/content/eus/rhel10/10.0/x86_64/codeready-builder/os", gpgkey: "", sslcacert: "/opt/omnia/rhel_repo_certs/redhat-uep.pem", sslclientkey: "/opt/omnia/rhel_repo_certs/<entitlement-key>.pem", sslclientcert: "/opt/omnia/rhel_repo_certs/<entitlement-cert>.pem", name: "x86_64_crb-eus" }

rhel_subscription_repo_config_aarch64:
  - { url: "https://cdn.redhat.com/content/eus/rhel10/10.0/aarch64/appstream/os", gpgkey: "", sslcacert: "/opt/omnia/rhel_repo_certs/redhat-uep.pem", sslclientkey: "/opt/omnia/rhel_repo_certs/<entitlement-key>.pem", sslclientcert: "/opt/omnia/rhel_repo_certs/<entitlement-cert>.pem", name: "x86_64_appstream-eus" }
  - { url: "https://cdn.redhat.com/content/eus/rhel10/10.0/aarch64/baseos/os", gpgkey: "", sslcacert: "/opt/omnia/rhel_repo_certs/redhat-uep.pem", sslclientkey: "/opt/omnia/rhel_repo_certs/<entitlement-key>.pem", sslclientcert: "/opt/omnia/rhel_repo_certs/<entitlement-cert>.pem", name: "x86_64_baseos-eus" }
  - { url: "https://cdn.redhat.com/content/eus/rhel10/10.0/aarch64/codeready-builder/os", gpgkey: "", sslcacert: "/opt/omnia/rhel_repo_certs/redhat-uep.pem", sslclientkey: "/opt/omnia/rhel_repo_certs/<entitlement-key>.pem", sslclientcert: "/opt/omnia/rhel_repo_certs/<entitlement-cert>.pem", name: "x86_64_crb-eus" }
```

!!! note
    - Copy the RHEL subscription entitlement certificates to `/opt/omnia/rhel_repo_certs/` on the `omnia_core` container before running `local_repo.yml`.
    - The certificate files (CA certificate, client key, and client certificate) are obtained from your RHEL subscription entitlement.
    - Replace `<entitlement-key>.pem` and `<entitlement-cert>.pem` with the actual filenames. The `gpgkey` field can be left empty when using subscription certificates for authentication.

**Option B: User-provided repositories (no subscription)**

If your environment does not have an active RHEL subscription, configure user-provided repository mirrors using `user_repo_url_x86_64`. This is suitable for air-gapped environments or internal RHEL mirrors.

```yaml title="File: /opt/omnia/input/project_default/local_repo_config.yml"
user_repo_url_x86_64:
  - { url: "http://<mirror-server>/rhel10/10.0/x86_64/CRB/os/", gpgkey: "http://<mirror-server>/rhel10/10.0/x86_64/CRB/os/RPM-GPG-KEY-redhat-release", name: "additional-codeready-builder" }
  - { url: "http://<mirror-server>/rhel10/10.0/x86_64/BaseOS/os/", gpgkey: "http://<mirror-server>/rhel10/10.0/x86_64/BaseOS/os/RPM-GPG-KEY-redhat-release", name: "additional-baseos" }
  - { url: "http://<mirror-server>/rhel10/10.0/x86_64/AppStream/os/", gpgkey: "http://<mirror-server>/rhel10/10.0/x86_64/AppStream/os/RPM-GPG-KEY-redhat-release", name: "additional-appstream" }

user_repo_url_aarch64:
  - { url: "http://<mirror-server>/rhel10/10.0/aarch64/CRB/os/", gpgkey: "http://<mirror-server>/rhel10/10.0/aarch64/CRB/os/RPM-GPG-KEY-redhat-release", name: "additional-codeready-builder" }
  - { url: "http://<mirror-server>/rhel10/10.0/aarch64/BaseOS/os/", gpgkey: "http://<mirror-server>/rhel10/10.0/aarch64/BaseOS/os/RPM-GPG-KEY-redhat-release", name: "additional-baseos" }
  - { url: "http://<mirror-server>/rhel10/10.0/aarch64/AppStream/os/", gpgkey: "http://<mirror-server>/rhel10/10.0/aarch64/AppStream/os/RPM-GPG-KEY-redhat-release", name: "additional-appstream" }
```

!!! note
    Replace `<mirror-server>` with the hostname or IP address of your internal RHEL mirror, and ensure the repositories are accessible from the `omnia_core` container.

### Step 2: Configure the Kernel Version Override

Update the provision configuration file:

```bash title="Run on: omnia_core container"
vi /opt/omnia/input/project_default/provision_config.yml
```

Set the `kernel_version_override` parameter:

```yaml title="File: /opt/omnia/input/project_default/provision_config.yml"
kernel_version_override: ""
```

**Behavior:**

- Empty value (`""`) -- The provisioning flow automatically selects the latest available kernel from S3 for OS installation.
- Set value -- The provisioning flow selects the exact specified kernel version from S3 (even from a different RHEL minor version) for OS installation. Validation fails if the specified kernel is not found in S3.
- Only the kernel and initrd are overridden during provisioning; the OS and root filesystem remain unchanged.

**Example:**

```yaml title="File: /opt/omnia/input/project_default/provision_config.yml"
kernel_version_override: "6.12.0-55.76.1.el10_0"
```

### Step 3: Sync Repositories

Run the local repository playbook to sync the repositories to Pulp:

```bash title="Run on: omnia_core container"
cd /omnia/local_repo
ansible-playbook local_repo.yml
```

**Validate that kernel packages are available in Pulp.** List the synced repository distributions to identify the repository name:

```bash title="Run on: omnia_core container"
pulp rpm distribution list
```

Query the Pulp content endpoint to confirm kernel packages are present. Replace `<oim_admin_ip>` with the OIM admin IP address and `<repo_name>` with the repository name from the previous step:

```bash title="Run on: omnia_core container"
curl -k https://<oim_admin_ip>:2225/pulp/content/opt/omnia/offline_repo/cluster/x86_64/rhel/10.0/rpms/<repo_name>/Packages/k/ | grep kernel
```

Confirm that the expected kernel RPM packages (`kernel`, `kernel-core`, `kernel-modules`) are listed. If none are found, verify the repository URLs in `local_repo_config.yml` and re-run `local_repo.yml`.

### Step 4: Build Images

Build the kernel, initrd, and rootfs images. The build process automatically selects the **latest kernel version** available across all configured repositories:

```bash title="Run on: omnia_core container"
cd /omnia/build_image_x86_64
ansible-playbook build_image_x86_64.yml
```

This playbook builds the images and uploads them to S3.

**Validate the kernel image in S3.** After the build completes, verify that the new kernel image was uploaded:

```bash title="Run on: omnia_core container"
s3cmd ls -Hr s3://boot-images
```

Look for entries matching your functional group and the expected kernel version:

```text title="Expected output"
s3://boot-images/efi-images/<functional_group>/rhel-<functional_group>_omnia_<version>/vmlinuz-<kernel_version>
s3://boot-images/efi-images/<functional_group>/rhel-<functional_group>_omnia_<version>/initramfs-<kernel_version>.img
```

Confirm the kernel version in S3 matches the expected version before provisioning.

### Step 5: Provision the Cluster

Provision the cluster with the specified kernel:

```bash title="Run on: omnia_core container"
cd /omnia/provision
ansible-playbook provision.yml
```

This playbook validates the kernel and initrd in S3, configures BSS and cloud-init, and prepares nodes for PXE boot.

- If `kernel_version_override` is set, the provisioning flow selects the exact specified kernel version from S3.
- If `kernel_version_override` is empty, the provisioning flow automatically picks the latest available kernel from S3.

### Step 6: PXE Boot the Nodes

Power on the cluster nodes and confirm that they boot successfully and cluster services are operational.


## Verification

**Verify the booted kernel version** on each node:

```bash title="Run on: compute node"
uname -r
```

The output should match the version specified in `kernel_version_override` (or the latest available version if left empty).


## Next Steps

- [Provision Nodes](provision_nodes.md) -- Continue the provisioning workflow.
- [PXE Boot Playbook](configure_pxe_boot.md) -- PXE boot configuration reference.


## Troubleshooting

- **Repository sync fails or kernel packages missing in Pulp**: Verify repository URLs and EUS certificate paths. See [Kernel Version Override Issues](../../Troubleshooting/kernel_version_override.md#repository-sync-issues) for details.
- **`kernel_version_override` not found in S3**: Verify the build image playbook completed and uploaded the expected kernel. See [Kernel Version Override Issues](../../Troubleshooting/kernel_version_override.md#kernel-image-not-found-in-s3) for details.
- **Nodes fail to PXE boot or boot with the wrong kernel**: Check BSS boot parameters and network connectivity. See [Kernel Version Override Issues](../../Troubleshooting/kernel_version_override.md#pxe-boot-issues) for details.


!!! info "Related pages"

    - [Provision Config](../../Reference/Configuration/provision_config.md) -- Reference for the `kernel_version_override` parameter.
    - [Local Repo Config](../../Reference/Configuration/local_repo_config.md) -- Reference for repository configuration parameters.
