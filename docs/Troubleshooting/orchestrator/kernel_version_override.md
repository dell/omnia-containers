# Kernel Version Override Issues

Issues related to kernel version override functionality, including repository sync, S3 image availability, PXE boot, and EUS subscription certificates.

## Repository Sync Issues

???+ note "Symptom"

    - `local_repo.yml` fails to sync the additional kernel repositories.
    - Kernel packages are not available in Pulp after sync.

??? note "Cause"

    - Repository URLs in `local_repo_config.yml` are incorrect or unreachable
    - RHEL subscription (EUS) entitlement certificates are expired or invalid
    - Pulp container cannot access the external repositories due to network or
      firewall issues

??? note "Resolution"

    1. Verify repository URLs are correct and accessible from the `omnia_core` container:

        ```bash title="Run on: omnia_core container"
        podman exec -it omnia_core curl -I <repository_url>
        ```

    2. For RHEL subscription (EUS) repositories, verify that the entitlement certificates are valid and correctly placed:

        ```bash title="Run on: OIM host"
        ls -la /opt/omnia/rhel_repo_certs/
        ```

    3. Validate kernel packages are available in the synced Pulp repository:

        ```bash title="Run on: omnia_core container"
        pulp rpm distribution list
        ```

    4. Query the Pulp content endpoint to check for kernel packages. Replace `<oim_admin_ip>` with the OIM admin IP and `<repo_name>` with the distribution name from the previous step:

        ```bash title="Run on: OIM host"
        curl -k https://<oim_admin_ip>:2225/pulp/content/opt/omnia/offline_repo/cluster/x86_64/rhel/10.0/rpms/<repo_name>/Packages/k/ | grep kernel
        ```

    5. If no kernel packages are found, correct the repository URLs in `local_repo_config.yml` and re-run `local_repo.yml`.

## Kernel Image Not Found in S3

???+ note "Symptom"

    - `provision.yml` fails with a kernel validation error.
    - The specified `kernel_version_override` is not found in S3.

??? note "Cause"

    - The kernel image was not built or uploaded to S3 during the build image step
    - The kernel version specified in `provision_config.yml` does not match any
      available kernel images in S3
    - The build image playbook (`build_image_x86_64.yml` or
      `build_image_aarch64.yml`) was not executed or failed

??? note "Resolution"

    1. Verify that the build image step completed successfully and uploaded images to S3:

        ```bash title="Run on: omnia_core container"
        s3cmd ls -Hr s3://boot-images
        ```

    2. Look for kernel and initramfs entries matching your functional group:

        ```text title="Expected output"
        s3://boot-images/efi-images/<functional_group>/rhel-<functional_group>_omnia_<version>/vmlinuz-<kernel_version>
        s3://boot-images/efi-images/<functional_group>/rhel-<functional_group>_omnia_<version>/initramfs-<kernel_version>.img
        ```

    3. If the expected kernel is missing, verify that the kernel packages were available in the Pulp repository before running `build_image_x86_64.yml`. The build process selects the latest kernel available across all configured repositories.

    4. Re-run the build image playbook to rebuild with the correct kernel:

        ```bash title="Run on: omnia_core container"
        cd /omnia/build_image_x86_64
        ansible-playbook build_image_x86_64.yml
        ```

    5. After the build completes, verify the new kernel image in S3 and re-run `provision.yml`.

## PXE Boot Issues

???+ note "Symptom"

    - Nodes fail to PXE boot after kernel override.
    - Nodes boot with the old kernel version instead of the overridden version.

??? note "Cause"

    - BSS boot parameters were not updated with the new kernel version
    - The kernel version specified in `provision_config.yml` does not match the
      kernel images available in S3
    - Network connectivity issues between nodes and the OIM prevent fetching
      the correct boot parameters
    - DHCP or TFTP services are not running correctly

??? note "Resolution"

    Validate the following:

    - BSS configuration matches the expected kernel and initrd paths in S3.
    - Network connectivity between nodes and the OIM.
    - DHCP and TFTP services are running.
    - Node console logs for boot errors.

    Verify the booted kernel version on the node:

    ```bash title="Run on: compute node"
    uname -r
    ```

    If the kernel version does not match the expected override, check that `kernel_version_override` in `provision_config.yml` is set correctly and re-run `provision.yml`.

## EUS Subscription Certificate Issues

???+ note "Symptom"

    - `local_repo.yml` fails with TLS/SSL errors when syncing EUS repositories.
    - Pulp reports authentication failures for RHEL CDN URLs.

??? note "Cause"

    - RHEL subscription (EUS) entitlement certificates have expired or are invalid
    - Certificate files are missing or not accessible from the configured paths in
      `local_repo_config.yml`
    - SSL/TLS certificate trust issues between the Pulp container and RHEL CDN

??? note "Resolution"

    1. Verify the certificate files exist at the configured paths:

        ```bash title="Run on: OIM host"
        ls -la /opt/omnia/rhel_repo_certs/
        ```

    2. Ensure the CA certificate, client key, and client certificate are valid and not expired:

        ```bash title="Run on: OIM host"
        openssl x509 -in /opt/omnia/rhel_repo_certs/<entitlement-cert>.pem -noout -dates
        ```

    3. Verify the `sslcacert`, `sslclientkey`, and `sslclientcert` paths in `local_repo_config.yml` match the actual file locations on the OIM.

    4. After correcting the certificates, re-run `local_repo.yml`.

!!! info

    - [Upgrade Omnia](../../Operations/upgrade_omnia.md) — Upgrade procedure.
    - [Rollback Omnia](../../Operations/rollback_omnia.md) — Rollback procedure.
