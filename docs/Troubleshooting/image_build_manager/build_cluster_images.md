 
# Build Cluster Image Issues
 
 
Issues related to building diskless cluster node images, S3/MinIO image
storage, and architecture-specific build failures.
 
## S3 Upload Fails
 
 
???+ note "Symptom"
 
    The `build_image_x86_64.yml` or `build_image_aarch64.yml` playbook fails
    during the image upload stage. The built image is not visible in the
    `boot-images` S3 bucket.
 
??? note "Cause"
 
    - The MinIO service on the OIM is not running or is unreachable.
    - S3 credentials are misconfigured.
    - Insufficient disk space on the MinIO storage volume.
 
??? note "Resolution"
 
    1. Verify MinIO is running and accessible:
 
        ```bash title="Run on: omnia_core container"
        s3cmd ls
        ```
 
 
    2. If MinIO is unreachable, restart it on the OIM host:
 
        ```bash title="Run on: OIM host"
        systemctl restart minio.service
        ```
 
 
    3. Verify the `boot-images` bucket exists:
 
        ```bash title="Run on: omnia_core container"
        s3cmd ls s3://boot-images
        ```
 
 
    4. After resolving the issue, re-run the build image playbook.
 
## Kernel Image Not Found in S3
 
 
???+ note "Symptom"
 
    - `provision.yml` fails with a kernel validation error.
    - The specified `kernel_version_override` is not found in S3.
 
??? note "Cause"
 
    The build image step did not complete successfully, or the kernel packages
    were not available in the Pulp repository when the image was built.
 
??? note "Resolution"
 
    1. Verify that the build image step completed successfully and uploaded
       images to S3:
 
        ```bash title="Run on: omnia_core container"
        s3cmd ls -Hr s3://boot-images
        ```
 
 
    2. Look for kernel and initramfs entries matching your functional group:
 
        ```text
         s3://boot-images/efi-images/<functional_group>/rhel-<functional_group>_omnia_<version>/vmlinuz-<kernel_version>
         s3://boot-images/efi-images/<functional_group>/rhel-<functional_group>_omnia_<version>/initramfs-<kernel_version>.img
        ```
 
 
    3. If the expected kernel is missing, verify that the kernel packages were
       available in the Pulp repository before running `build_image_x86_64.yml`.
       The build process selects the latest kernel available across all
       configured repositories.
 
    4. Re-run the build image playbook to rebuild with the correct kernel:
 
        ```bash title="Run on: omnia_core container"
        cd /omnia/build_image_x86_64
        ansible-playbook build_image_x86_64.yml
        ```
 
 
    5. After the build completes, verify the new kernel image in S3 using
       `s3cmd ls -Hr s3://boot-images` and then re-run `provision.yml`.
 
## Build Image Fails for aarch64 — Missing Inventory
 
 
???+ note "Symptom"
 
    The `build_image_aarch64.yml` playbook fails with:
    *"aarch64 functional groups detected in pxe_mapping_file but no hosts
    found in 'admin_aarch64' inventory group"* or *"The inventory group
    'admin_aarch64' does not exist or has no hosts."*
 
??? note "Cause"
 
    The PXE mapping file contains aarch64 functional groups, but the playbook
    was run without an inventory file containing the `[admin_aarch64]` group.
 
??? note "Resolution"
 
    1. Create an inventory file with the `[admin_aarch64]` group containing
       exactly one ARM admin node:
 
        ```ini
        [admin_aarch64]
        <arm_admin_node_ip>
        ```
 
 
    2. Re-run the build image playbook with the inventory file:
 
        ```bash title="Run on: omnia_core container"
        cd /omnia/build_image_aarch64
        ansible-playbook build_image_aarch64.yml -i inventory
        ```
 
 
    !!! note
 
        The `[admin_aarch64]` group must have exactly one host. NFS must be
        configured on the OIM for aarch64 image building.
 
## Repository Sync Issues
 
 
???+ note "Symptom"
 
    - `local_repo.yml` fails to sync the additional kernel repositories.
    - Kernel packages are not available in Pulp after sync.
    - `build_image_x86_64.yml` builds an image with an older kernel than
      expected.
 
??? note "Cause"
 
    Repository URLs in `local_repo_config.yml` are incorrect or
    unreachable, or RHEL subscription certificates are invalid or expired.
 
??? note "Resolution"
 
    1. Verify repository URLs are correct and accessible from the
       `omnia_core` container:
 
        ```bash title="Run on: OIM host"
        podman exec -it omnia_core curl -I <repository_url>
        ```
 
 
    2. For RHEL subscription (EUS) repositories, verify that the
       entitlement certificates are valid and correctly placed:
 
        ```bash title="Run on: omnia_core container"
        ls -la /opt/omnia/rhel_repo_certs/
        ```
 
 
    3. Validate kernel packages are available in the synced Pulp
       repository. From within the `omnia_core` container, list the
       repository distributions:
 
        ```bash title="Run on: omnia_core container"
        pulp rpm distribution list
        ```
 
 
    4. Query the Pulp content endpoint to check for kernel packages.
       Replace `<oim_admin_ip>` with the OIM admin IP and `<repo_name>`
       with the distribution name from the previous step:
 
        ```bash title="Run on: omnia_core container"
        curl -k https://<oim_admin_ip>:2225/pulp/content/opt/omnia/offline_repo/cluster/x86_64/rhel/10.0/rpms/<repo_name>/Packages/k/ | grep kernel
        ```
 
 
    5. If no kernel packages are found, correct the repository URLs in
       `local_repo_config.yml` and re-run `local_repo.yml`.
 
## Images Not Created for All Functional Groups
 
 
???+ note "Symptom"
 
    After running the build image playbook, `s3cmd ls -Hr s3://boot-images`
    shows images for some functional groups but not all groups defined in the
    mapping file.
 
??? note "Cause"
 
    - The mapping file contains functional groups that do not match the
      target architecture of the playbook being run.
    - `local_repo.yml` was not executed with software packages for all
      required functional groups.
 
??? note "Resolution"
 
    1. Verify which functional groups are defined in the mapping file:
 
        ```bash title="Run on: omnia_core container"
        cat /opt/omnia/input/project_default/pxe_mapping_file.csv
        ```
 
 
    2. Ensure `local_repo.yml` was executed with `software_config.json`
       that includes software for all required architectures and functional
       groups.
 
    3. Re-run the appropriate build image playbook and verify images:
 
        ```bash title="Run on: omnia_core container"
        s3cmd ls -Hr s3://boot-images
        ```
 
 
!!! info
 
    - [Build Cluster Node Images](../HowTo/Setup/build_cluster_images.md) -- Full image build procedure.
    - [Create Local Repos](../HowTo/Setup/create_local_repos.md) -- Local repository setup.
    - [Create Mapping File](../HowTo/Setup/create_mapping_file.md) -- Mapping file configuration.
