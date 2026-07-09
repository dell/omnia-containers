# Prepare the OIM

The `prepare_oim.yml` playbook prepares the Omnia Infrastructure Manager (OIM) by deploying the core management services required for bare-metal provisioning and cluster management. The playbook performs the following on the OIM:

- Sets up the OpenCHAMI containers for node discovery, state management, and boot script services.
- Sets up the Pulp container for RPM repository management and synchronization.
- Sets up the BuildStreaM container if BuildStreaM is enabled in `/opt/omnia/input/project_default/build_stream_config.yml`.
- Sets up the Omnia Auth container if `"name": "openldap", "arch": ["x86_64"]` entry is present in `/opt/omnia/input/project_default/software_config.json`.
- Sets up MinIO for S3-compatible object storage for boot images and artifacts.
- Sets up the local container image registry.

## Prerequisites

- The [Deploy Omnia Core](deploy_omnia_core.md) procedure is complete.
- The [Configure Inputs](configure_inputs.md) procedure is complete.
- The [Configure Credentials](configure_credentials.md) procedure is complete (encrypted credentials file exists).
- The OIM has at least 2 NICs connected to the admin and BMC networks.
- Network switches are configured with the appropriate VLANs.
- System time is synchronized across all compute nodes and the OIM. Time mismatch can lead to certificate-related issues during or after the `prepare_oim.yml` playbook execution.

## Procedure

1. Update the following input files in `/opt/omnia/input/project_default/`:

    - `network_spec.yml` -- Contains the necessary configurations for the cluster network.
    - `provision_config.yml` -- Contains the details about provisioning of clusters.
    - `build_stream_config.yml` -- Contains the details about the BuildStreaM pipeline.
    - `storage_config.yml` -- Contains the details about the storage configuration.

2. Enter the `omnia_core` container:

    ```bash title="Run on: OIM host"
    ssh omnia_core
    ```

3. Run the `prepare_oim.yml` playbook:

    ```bash title="Run on: omnia_core container"
    cd /omnia/prepare_oim
    ansible-playbook prepare_oim.yml
    ```

The `prepare_oim.yml` playbook deploys the following on the OIM node:

- OpenCHAMI containers
- PostgreSQL database container
- Omnia Auth container
- Pulp container
- BuildStreaM API container (if BuildStreaM is enabled)
- Playbook watcher service (if BuildStreaM is enabled)

!!! note

    After `prepare_oim.yml` execution, `ssh omnia_core` may fail if you switch from a non-root to root user using the `sudo` command. To avoid this, log in directly as the `root` user before executing the playbook.

## Input file configuration

### network_spec.yml

Add necessary inputs to the `network_spec.yml` file to configure the network on which the cluster will operate. Refer to [Network Spec](../../Reference/Configuration/network_spec.md) for guidance on configuring these parameters.

!!! warning

    - All provided network ranges and NIC IP addresses must be distinct with no overlap.
    - All iDRACs must be reachable from the OIM.

A sample of the `network_spec.yml` where nodes are discovered using a mapping file:

```yaml title="File: /opt/omnia/input/project_default/network_spec.yml"
Networks:
- admin_network:
    oim_nic_name: "eno1"
    netmask_bits: "24"
    primary_oim_admin_ip: "172.16.107.67"
    primary_oim_bmc_ip: ""
    dynamic_range: "172.16.107.201-172.16.107.250"
    dns: []
```

### provision_config.yml

Add necessary inputs to the `provision_config.yml` file for provisioning the cluster. Refer to [Provision Config](../../Reference/Configuration/provision_config.md) for guidance on configuring these parameters.

### build_stream_config.yml

Add necessary inputs to the `build_stream_config.yml` file for the BuildStreaM pipeline. Refer to [BuildStreaM Config](../../Reference/Configuration/build_stream_config.md) for guidance on configuring these parameters.

### storage_config.yml

Add necessary inputs to the `storage_config.yml` file for the storage configuration. Refer to [Storage Config](../../Reference/Configuration/storage_config.md) for guidance on configuring these parameters.

### Configure PowerScale as S3 storage

PowerScale provides scalable, high-performance object storage for the OpenCHAMI image repository. Using PowerScale as S3-compatible storage enables efficient storage and retrieval of boot images across the cluster, with support for HTTP access and robust authentication mechanisms.

!!! note

    - PowerScale cluster must be deployed within the admin subnet and be accessible from all cluster nodes.
    - Omnia uses HTTP access only when connecting to PowerScale, using the default port 9020.
    - Both S3 and HTTP services must be enabled in the S3 bucket configuration.
    - Valid S3 Access Key ID and S3 Secret Access Key are required for authentication.
    - S3 Access Key ID and S3 Secret Access Key are tightly associated with the S3 buckets. You need these keys to access the S3 buckets created using the key.

**Enable S3 service on PowerScale:**

1. Log in to the PowerScale OneFS web interface.
2. Navigate to **Protocol** > **Object storage (S3)**.
3. On the **Object Storage (S3)** page, click the **Global Settings** tab.
4. Select the **Enable S3 service** checkbox.
5. Select the **Enable S3 HTTP** checkbox.
6. Set the HTTP port for S3 (default: `9020`).
7. Click **Save** to apply the changes.

**Obtain S3 Access ID and Secret Key:**

1. Log in to the PowerScale OneFS web interface.
2. Navigate to **Protocol** > **Object storage (S3)**.
3. On the **Object Storage (S3)** page, click the **My Keys** tab.
4. Click **Create new key**.
5. Note down the **Access ID** and **Secret Key**.

!!! warning

    The S3 Access ID and Secret Key are required during the OIM credential setup process. The cluster nodes cannot access boot images without these keys.

**Configure storage_config.yml:**

1. Open `/opt/omnia/input/project_default/storage_config.yml`.
2. Update the `s3_configurations` section:

    ```yaml title="File: /opt/omnia/input/project_default/storage_config.yml"
    s3_configurations:
      provider: "powerscale"
      endpoint_url: "http://<powerscale-ip>:<port>"
    ```

    Replace `<powerscale-ip>` with the actual PowerScale IP address and `<port>` with the S3 port (default: `9020`).

    ```yaml title="Example"
    s3_configurations:
      provider: "powerscale"
      endpoint_url: "http://192.168.1.100:9020"
    ```

3. Save the file.

**Configure credentials during prepare OIM:**

When running `prepare_oim.yml`, you are prompted for S3 credentials. Enter the S3 Access ID and Secret Key obtained from PowerScale.

!!! note

    - For `powerscale` provider, the `s3_access_id` is prompted as a conditional mandatory parameter.
    - The `s3_secret_key` is always prompted during credential setup.

## Verification

1. Check the status of the Omnia Core service:

    ```bash title="Run on: OIM host"
    systemctl status omnia_core.service
    ```

2. Check the status of the PostgreSQL database container (if BuildStreaM is enabled):

    ```bash title="Run on: OIM host"
    systemctl status omnia_postgres.service
    ```

3. Check the status of the BuildStreaM API container (if BuildStreaM is enabled):

    ```bash title="Run on: OIM host"
    systemctl status omnia_build_stream.service
    ```

4. Check the status of the playbook watcher service (if BuildStreaM is enabled):

    ```bash title="Run on: OIM host"
    systemctl status playbook_watcher.service
    ```

5. View the complete list of dependent services for the Omnia target:

    ```bash title="Run on: OIM host"
    systemctl list-dependencies omnia.target
    ```

    Expected service tree:

    ```text title="Expected output"
    omnia.target
    ● ├─minio.service
    ● ├─omnia_auth.service
    ● ├─omnia_build_stream.service
    ● ├─omnia_core.service
    ● ├─omnia_postgres.service
    ● ├─playbook_watcher.service
    ● ├─pulp.service
    ● ├─registry.service
    ● ├─network-online.target
    ● │ └─NetworkManager-wait-online.service
    ● └─openchami.target
    ●   ├─acme-deploy.service
    ●   ├─acme-register.service
    ●   ├─bss-init.service
    ●   ├─bss.service
    ●   ├─cloud-init-server.service
    ●   ├─coresmd.service
    ●   ├─haproxy.service
    ●   ├─hydra-gen-jwks.service
    ●   ├─hydra-migrate.service
    ●   ├─hydra.service
    ●   ├─opaal-idp.service
    ●   ├─opaal.service
    ●   ├─openchami-cert-trust.service
    ●   ├─postgres.service
    ●   ├─smd.service
    ●   └─step-ca.service
    ```

    - A **green circle** indicates the service is running.
    - A **grey circle** indicates the service is not running.
    - A **circle with a cross** indicates the service failed to start.

!!! note

    The `omnia_auth.service` runs only when OpenLDAP is specified in `/opt/omnia/input/project_default/software_config.json`.

!!! note

    The `omnia_build_stream.service`, `omnia_postgres.service`, and `playbook_watcher.service` run only when BuildStreaM is enabled in `/opt/omnia/input/project_default/build_stream_config.yml`.

## Next Steps

- [Verify OIM Services](verify_oim_services.md) -- Detailed verification of all OIM services.
- [Create Local Repos](create_local_repos.md) -- Sync RPM repositories via Pulp.
- [Build Cluster Images](build_cluster_images.md) -- Build OS images for cluster nodes.

!!! info "Related References"

    - [Network Spec](../../Reference/Configuration/network_spec.md) -- Network configuration parameters.
    - [Provision Config](../../Reference/Configuration/provision_config.md) -- Provisioning configuration parameters.
    - [Storage Config](../../Reference/Configuration/storage_config.md) -- Storage configuration parameters.
    - [Security Configuration Guide](../../SecurityConfigurationGuide/network_security.md#firewall-settings) -- Firewall port requirements.
