# Clean up built images

Use the Image Build Manager `cleanup_images` operation to delete obsolete OS
image artifacts from S3 and the local OCI registry without removing Image
Build Manager services, credentials, configuration, logs, or output files.

Use this operation for direct Image Build Manager workflows. For images
managed by BuildStreaM, use
[Clean up BuildStreaM image groups](build_stream/cleanup_operations.md).

!!! danger

    Image deletion is permanent. With no pattern, `cleanup_images` defaults to
    `*` and selects all objects in the `boot-images` bucket and all tags in the
    managed registry. Stop provisioning activity and confirm that no deployed
    or pending node operation requires the selected images before continuing.

    The operation does not update or remove `build_status.yml`. After deleting
    an image referenced by that file, do not use the existing status file for
    provisioning. Rebuild the required images to generate a current contract.

## What the operation changes

| Resource | Behavior |
|---|---|
| S3 `boot-images` objects | Deletes objects whose full S3 path matches `cleanup_image_pattern`. The default `*` deletes every object in the bucket. |
| Local OCI registry | Deletes the tagged manifests in repositories whose names match the pattern. Repository metadata and unreferenced blob storage can remain. |
| `minio.service` and `registry.service` | Preserved. |
| S3 buckets | Preserved. The operation deletes matching objects, not the buckets. |
| Configuration, credentials, logs, and output | Preserved, including the latest and versioned `build_status` files. |

When `/root/.s3cfg` identifies an external PowerScale endpoint, matching
objects are deleted from that external backend. Full Image Build Manager
cleanup does not delete external PowerScale objects, but `cleanup_images` can.

## Prerequisites

- Complete [OIM setup](../HowTo/main/setup_oim.md), and keep the shared Omnia
  virtual environment installed.
- Use the same `OMNIA_PROJECT_NAME`, `OMNIA_DATA_PATH`, and
  `IMAGE_BUILD_MANAGER_DATA_PATH` values used for the image build.
- Back up any image artifact that must be retained.
- Identify a deletion pattern by listing the current S3 objects and registry
  repositories.
- For S3 cleanup, ensure `s3cmd` is installed and `/root/.s3cfg` identifies
  the intended S3 endpoint and credentials.
- For registry cleanup, ensure `/usr/local/bin/regctl` exists and the managed
  registry service or storage is available.

!!! warning

    The workflow checks S3 and the registry independently. If `s3cmd`, its
    configuration, `regctl`, or managed registry state is unavailable, the
    corresponding cleanup is skipped. Review the summary and verification
    results to detect partial cleanup.

## Review the available images

Load the installed environment and list the current artifacts:

```bash title="Run on: OIM host"
source /etc/profile.d/omnia-env.sh
s3cmd ls -r s3://boot-images/
/usr/local/bin/regctl repo ls "${SYSTEM_ADMIN_NIC_IPV4}:5000"
```

To inspect the tags for one repository returned by `regctl repo ls`, run:

```bash title="Run on: OIM host"
/usr/local/bin/regctl tag ls \
  "${SYSTEM_ADMIN_NIC_IPV4}:5000/<repository-name>"
```

The cleanup pattern is applied to complete S3 object paths and registry
repository names. It supports `*` and `?` wildcards. Use a pattern narrow
enough to select the same intended image group on both storage systems.

## Delete selected images

Choose one execution method. For example, delete images whose names match
`rhel-slurm_*`:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run image_build_manager --tags cleanup_images \
      -e 'cleanup_image_pattern=rhel-slurm_*'
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/image_build_manager/playbooks
    ansible-playbook image_build_manager.yml --tags cleanup_images \
      -e 'cleanup_image_pattern=rhel-slurm_*'
    ```

The command displays the pattern, matching S3 object count, matching registry
repository count, and registry tag count before prompting. Enter `yes` or `y`
only after reviewing that summary. Any other response aborts deletion.

To target one config-mode functional group, use a more specific pattern:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run image_build_manager --tags cleanup_images \
      -e 'cleanup_image_pattern=rhel-os_x86_64*'
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/image_build_manager/playbooks
    ansible-playbook image_build_manager.yml --tags cleanup_images \
      -e 'cleanup_image_pattern=rhel-os_x86_64*'
    ```

The same pattern can match current artifacts and `_prev` backups. Review the
discovered count before approving the operation.

## Delete all built images

Omitting `cleanup_image_pattern` selects the default `*` pattern:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run image_build_manager --tags cleanup_images
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/image_build_manager/playbooks
    ansible-playbook image_build_manager.yml --tags cleanup_images
    ```

This deletes every object under `s3://boot-images/` and every tag in the
managed registry. It preserves the S3 buckets, registry service, and registry
repository metadata.

## Run without an approval prompt

For reviewed automation only, pass the domain extra variable:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run image_build_manager --tags cleanup_images \
      -e 'cleanup_image_pattern=rhel-slurm_*' \
      -e skip_approval=true
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/image_build_manager/playbooks
    ansible-playbook image_build_manager.yml --tags cleanup_images \
      -e 'cleanup_image_pattern=rhel-slurm_*' \
      -e skip_approval=true
    ```

`skip_approval=true` bypasses the Image Build Manager prompt. Main's
`--skip-approval` option applies only to `./omnia.sh --cleanup` and is not the
option for this domain operation.

## Verification

1. List the remaining S3 objects:

    ```bash title="Run on: OIM host"
    s3cmd ls -r s3://boot-images/
    ```

2. List the remaining tags for each affected registry repository:

    ```bash title="Run on: OIM host"
    /usr/local/bin/regctl tag ls \
      "${SYSTEM_ADMIN_NIC_IPV4}:5000/<repository-name>"
    ```

    A repository can remain visible after all its tags are deleted. This is
    expected because selective cleanup preserves registry metadata and does
    not run registry garbage collection.

3. Review the Image Build Manager log:

    ```text
    /var/log/omnia/image_build_manager/image_build_manager.log
    ```

4. Before the next provisioning operation, confirm that every artifact named
   in the active `build_status.yml` still exists. If an active artifact was
   deleted, run the Image Build Manager build flow again and verify the newly
   generated status file.

## Troubleshooting

- **S3 cleanup is skipped**: Install `s3cmd` and confirm that
  `/root/.s3cfg` is readable by the account running the playbook and identifies
  the intended endpoint.
- **Registry cleanup is skipped**: Confirm that `/usr/local/bin/regctl` exists
  and that `registry.service` is active or the configured registry storage
  directory remains available.
- **No matching images are found**: List S3 objects and registry repositories,
  then adjust `cleanup_image_pattern` to match their complete names.
- **Registry disk usage does not decrease**: The operation deletes manifests
  and tags but does not garbage-collect unreferenced registry blobs. Use full
  Image Build Manager cleanup only when the local registry and all its data can
  be removed.
- **Provisioning fails after cleanup**: The existing `build_status.yml` can
  still reference deleted artifacts. Rebuild the required functional-group
  images and use the regenerated status file.

For removal of Image Build Manager services, runtime data, credentials, and
logs, use the full domain procedure in [Clean up the OIM](oim_cleanup.md).
