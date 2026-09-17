# Kernel Version Override Issues

Issues related to kernel version override functionality, including repository sync, S3 image availability, PXE boot, and EUS subscription certificates.

## Repository Sync Issues

???+ note "Symptom"

    - The Repository Manager `download` phase fails to synchronize the
      additional kernel repositories.
    - Kernel packages are not available in Pulp after sync.

??? note "Cause"

    - Repository URLs in `repo_manager_config.yml` are incorrect or unreachable
    - RHEL subscription (EUS) entitlement certificates are expired or invalid
    - Pulp container cannot access the external repositories due to network or
      firewall issues

??? note "Resolution"

    1. Verify repository URLs are correct and accessible from the OIM:

        ```bash title="Run on: OIM host"
        curl -I <repository_url>
        ```

    2. For RHEL subscription (EUS) repositories, inspect the configured
       `sslcacert`, `sslclientkey`, and `sslclientcert` paths in the active
       Repository Manager project. Verify those exact files rather than
       assuming a fixed certificate directory:

        ```bash title="Run on: OIM host"
        source /etc/profile.d/omnia-env.sh
        repo_manager_path="${OMNIA_DATA_PATH}/repo_manager"
        vi "$repo_manager_path/input/$OMNIA_PROJECT_NAME/repo_manager_config.yml"
        ```

    3. Validate kernel packages are available in the synced Pulp repository:

        ```bash title="Run on: OIM host"
        source /etc/profile.d/omnia-env.sh
        source "$OMNIA_DATA_PATH/activate-omnia.sh"
        pulp rpm distribution list
        ```

    4. Query the Pulp content endpoint to check for kernel packages. Replace `<oim_admin_ip>` with the OIM admin IP and `<repo_name>` with the distribution name from the previous step:

        ```bash title="Run on: OIM host"
        curl -k https://<oim_admin_ip>:2225/pulp/content/opt/omnia/offline_repo/cluster/x86_64/rhel/10.0/rpms/<repo_name>/Packages/k/ | grep kernel
        ```

    5. If no kernel packages are found, correct the repository URLs in
       `$repo_manager_path/input/$OMNIA_PROJECT_NAME/repo_manager_config.yml`,
       then rerun the Repository Manager `download` and `status` phases.

## Kernel Image Not Found in S3

???+ note "Symptom"

    - The Orchestrator `precheck` phase fails with a kernel validation error.
    - The specified `kernel_version_override` does not match the kernel recorded
      for the functional group in `build_status.yml`.

??? note "Cause"

    - The kernel image was not built or uploaded to S3 during the build image step
    - The kernel version specified in `orchestrator_config.yml` does not match any
      available kernel images in S3
    - The Image Build Manager build flow was not executed or failed

??? note "Resolution"

    1. Verify that the build image step completed successfully and uploaded images to S3:

        ```bash title="Run on: OIM host"
        s3cmd ls -Hr s3://boot-images
        ```

    2. Look for kernel and initramfs entries matching your functional group:

        ```text title="Expected output"
        s3://boot-images/efi-images/<functional_group>/rhel-<functional_group>_omnia_<version>/vmlinuz-<kernel_version>
        s3://boot-images/efi-images/<functional_group>/rhel-<functional_group>_omnia_<version>/initramfs-<kernel_version>.img
        ```

    3. If the expected kernel is missing, verify that the kernel packages were
       available in the Pulp repository before running the Image Build Manager.
       The build process selects the latest kernel available across all
       configured repositories.

    4. Rerun the Image Build Manager `build` phase:

        === "Using omnia.sh (recommended)"

            ```bash title="Run on: OIM host"
            cd <OMNIA_SOURCE_PATH>/src/main
            ./omnia.sh --run image_build_manager --tags build
            ```

        === "Using ansible-playbook"

            ```bash title="Run on: OIM host"
            source /opt/omnia/activate-omnia.sh
            cd <OMNIA_SOURCE_PATH>/src/image_build_manager/playbooks
            ansible-playbook image_build_manager.yml --tags build
            ```

    5. After the build completes, verify the new kernel image in S3:

        ```bash title="Run on: OIM host"
        s3cmd ls -Hr s3://boot-images
        ```

       Then rerun the Orchestrator `precheck` phase:

        === "Using omnia.sh (recommended)"

            ```bash title="Run on: OIM host"
            cd <OMNIA_SOURCE_PATH>/src/main
            ./omnia.sh --run orchestrator --tags precheck
            ```

        === "Using ansible-playbook"

            ```bash title="Run on: OIM host"
            source /opt/omnia/activate-omnia.sh
            cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
            ansible-playbook orchestrator.yml --tags precheck
            ```

       When the precheck succeeds, return to the applicable Orchestrator
       deployment procedure.

## PXE Boot Issues

???+ note "Symptom"

    - Nodes fail to PXE boot after kernel override.
    - Nodes boot with the old kernel version instead of the overridden version.

??? note "Cause"

    - The OpenCHAMI boot-service configuration was not regenerated with the
      new kernel version
    - The kernel version specified in `orchestrator_config.yml` does not match the
      kernel images available in S3
    - Network connectivity issues between nodes and the OIM prevent fetching
      the correct boot parameters
    - DHCP or TFTP services are not running correctly

??? note "Resolution"

    Validate the following:

    - The functional group's boot-service configuration and
      `provisioning_report.yml` match the expected kernel and initrd paths in
      S3. See [OpenCHAMI Issues](openchami.md) for current service and API
      diagnostics.
    - Network connectivity between nodes and the OIM.
    - DHCP and TFTP services are running.
    - Node console logs for boot errors.

    Verify the booted kernel version on the node:

    ```bash title="Run on: compute node"
    uname -r
    ```

    If the kernel version does not match the expected override, check that `kernel_version_override` in `orchestrator_config.yml` is set correctly and re-run the Orchestrator flow.

## EUS Subscription Certificate Issues

???+ note "Symptom"

    - The Repository Manager `download` phase fails with TLS/SSL errors when
      synchronizing EUS repositories.
    - Pulp reports authentication failures for RHEL CDN URLs.

??? note "Cause"

    - RHEL subscription (EUS) entitlement certificates have expired or are invalid
    - Certificate files are missing or not accessible from the configured paths in
      `repo_manager_config.yml`
    - SSL/TLS certificate trust issues between the Pulp container and RHEL CDN

??? note "Resolution"

    1. Resolve the active Repository Manager configuration and verify that the
       certificate files exist at the paths declared by `sslcacert`,
       `sslclientkey`, and `sslclientcert`:

        ```bash title="Run on: OIM host"
        source /etc/profile.d/omnia-env.sh
        repo_manager_path="${OMNIA_DATA_PATH}/repo_manager"
        vi "$repo_manager_path/input/$OMNIA_PROJECT_NAME/repo_manager_config.yml"
        ls -l <configured-certificate-path>
        ```

    2. Ensure the CA certificate, client key, and client certificate are valid and not expired:

        ```bash title="Run on: OIM host"
        openssl x509 -in <configured-entitlement-certificate> -noout -dates
        ```

    3. Verify the `sslcacert`, `sslclientkey`, and `sslclientcert` paths in
       `repo_manager_config.yml` match the actual file locations on the OIM.

    4. After correcting the certificates, rerun the Repository Manager
       `download` and `status` phases.
