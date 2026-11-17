# Ingest OCI Boot Images from a Registry

## Overview

Use the Utils `oci_image_ingest` workflow to publish boot images that are
stored as Open Container Initiative (OCI) images in a Harbor registry. For each
configured image, the workflow:

1. Pins the image to its digest and checks that its architecture matches the
   functional group.
2. Exports the image and extracts one complete boot set: the kernel, the
   initramfs, and the root filesystem.
3. Packs the root filesystem into a SquashFS image.
4. Uploads the kernel, initramfs, and SquashFS image to the `boot-images` S3
   bucket.
5. Writes `build_status.yml`, which the Orchestrator uses to provision PXE boot.

The workflow is an alternative to building images with Image Build Manager. It
does not push images to Harbor. Only Harbor registries and the
`repo_to_bucket` operation are supported.

The Orchestrator does not read OCI images directly. It reads the
`build_status.yml` manifest, which points to the boot artifacts in S3. See the
[Image Build Manager Contract](../../Reference/domain_contracts/image_build_manager_contract.md)
for the manifest structure.

## Prerequisites

- Complete the [OIM setup](../main/setup_oim.md).
- Initialize Utils with `./omnia.sh -i utils`.
- Run Image Build Manager with `--tags prepare` first. It provides the
  `regctl` and `s3cmd` clients and the S3 configuration file (`~/.s3cfg`) that
  the ingestion uses. The ingestion verifies these and does not install them.
- Install the `squashfs-tools` package on the OIM. The ingestion verifies
  `mksquashfs` and does not install operating system packages.
- Install the `zstd` package if an image contains zstd-compressed layers.
- A Harbor registry that is reachable from the OIM, with a project (namespace)
  that holds the images and that your registry account can read.
- An S3 endpoint that accepts public-read ACLs on the `boot-images` bucket, or
  a bucket policy that grants anonymous read. Nodes download the boot
  artifacts without credentials.
- Free space in `$OMNIA_DATA_PATH/utils/workdir/$OMNIA_PROJECT_NAME/oci-image-ingest`
  of at least three times the compressed size of the image layers.

## Configure the ingestion

The configuration file is:

```text
$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/oci_image_ingest_config.yml
```

The file contains connection and mapping settings only. Do not add
credentials to it. The shipped template has empty `registries` and
`image_mappings` lists, which you must fill in before the first run.

```yaml title="oci_image_ingest_config.yml"
registries:
  - registry_name: harbor-local
    registry_type: harbor
    registry_protocol: https
    registry_hostname: harbor.example.com
    registry_port: 443

image_mappings:
  - mapping_name: slurm_node
    registry_name: harbor-local
    namespace_name: hpc-images
    image: rhel-slurm-node:10.2
    functional_group: slurm_node_rhel_10_2_x86_64
    operation: repo_to_bucket
```

### Registry settings

| Parameter | Type | Required | Description |
|---|---|---|---|
| `registry_name` | string | Yes | Unique label that `image_mappings` refer to. |
| `registry_type` | string | Yes | Only `harbor` is supported. |
| `registry_protocol` | string | Yes | `http` or `https`. |
| `registry_hostname` | string | Yes | Host name or IP address of the registry. |
| `registry_port` | integer | No | 1 through 65535. Defaults to 443 for `https` and 80 for `http`. |

### Image mapping settings

| Parameter | Type | Required | Description |
|---|---|---|---|
| `mapping_name` | string | Yes | Unique label for the mapping. |
| `registry_name` | string | Yes | Must match a `registry_name` in `registries`. |
| `namespace_name` | string | Yes | Harbor project that holds the image. Lowercase letters, digits, `.`, `_`, and `-`. |
| `image` | string | Yes | `<repository>:<tag>` or `<repository>@sha256:<digest>`. |
| `functional_group` | string | Yes | Predefined functional-group name that ends in `_x86_64` or `_aarch64`. The suffix selects the architecture the image must match. |
| `kernel_version` | string | No | Required only when the image holds more than one complete boot set. |
| `operation` | string | Yes | Only `repo_to_bucket` is supported. |

The workflow validates the file against its schema before it performs any
action. It rejects unsupported values, duplicate `registry_name` or
`mapping_name` values, and mappings that refer to a registry that is not
defined.

## Set up credentials

On the first run, the workflow prompts for the registry user name and password
and asks you to confirm the password. It stores them Vault-encrypted in:

```text
$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/oci_image_ingest_credentials.yml
$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/.oci_image_ingest_credentials_key
```

Both files are created with mode `0600`. Later runs reuse them without
prompting. To enter new credentials, delete both files, or run the
[cleanup](#clean-up) and then rerun the workflow.

### Registry TLS verification

For `https` registries, the workflow does not verify the registry certificate
by default (`oci_ingest_registry_tls: insecure`). To verify it, trust the
registry certificate authority on the OIM and pass the setting for the run:

```bash title="Run on: OIM"
./omnia.sh --run utils --tags oci_image_ingest -e oci_ingest_registry_tls=enabled
```

!!! warning

    With the default setting, the registry credentials and the boot images are
    exchanged over a connection whose certificate is not verified. Use
    `enabled` in production environments.

## Run the ingestion

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags oci_image_ingest
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils/playbooks
    export ANSIBLE_CONFIG=../ansible.cfg
    ansible-playbook utils.yml --tags oci_image_ingest
    ```

The workflow takes a per-project lock, so only one ingestion runs at a time for
a project. It always removes its working data and releases the lock when it
finishes, whether it succeeds or fails.

If a mapping's image digest is already completely published, the workflow skips
that mapping. Running the workflow again with unchanged images therefore does
not upload anything.

## Verify the result

The workflow uploads each image to its own release prefix:

```text
boot-images/<functional_group>/<repository>-ingest/<release>/
├── vmlinuz-<kernel-version>
├── initramfs-<kernel-version>.img
├── rootfs.squashfs
└── ingest.json
```

`<release>` is `<tag>-<first 12 characters of the digest>`, or
`sha256-<first 12 characters of the digest>` when the image is referenced by
digest. `ingest.json` records the digest, kernel version, publication time, and
artifact checksums, and marks the prefix as completely published.

The workflow writes the manifest to:

```text
$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/build_status.yml
```

It also writes a timestamped copy named `build_status_<run-id>.yml` in the same
folder. The manifest has `image_build_type: oci-image-ingest`, the S3 endpoint
and bucket, one entry per functional group with its kernel, initrd, and image
paths, and an `oci_sources` section that records the registry, repository,
digest, platform, and artifact checksums of each ingested image. A run updates
the entries of the functional groups it ingested and keeps the entries of other
functional groups.

The workflow does not update `build_status.yml` if any step fails, and it does
not modify an existing file at that path that another producer wrote.

## Use the ingested images

The Orchestrator reads the manifest from the file that
`image_build_manager_output_path` in `orchestrator_config.yml` points to. By
default, that is the Image Build Manager manifest. Use one of the following
methods to make the ingested images available:

- Set `image_build_manager_output_path` to the Utils manifest file:

    ```yaml title="orchestrator_config.yml"
    image_build_manager_output_path: "<OMNIA_DATA_PATH>/utils/output/<project>/build_status.yml"
    ```

- Copy the Utils `build_status.yml` to the path that
  `image_build_manager_output_path` resolves to.

!!! note

    Copying the file overwrites a `build_status.yml` that Image Build Manager
    created at the destination. Back up the existing file first.

The Orchestrator accepts the manifest only when `overall_status` is `success`,
`image_build_type` is `image-thrillhouse` or `oci-image-ingest`, and the S3
endpoint is usable.

## Clean up

Use the dedicated cleanup tag to remove the ingestion working data and the
stored credentials:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags cleanup_oci_image_ingest
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils/playbooks
    export ANSIBLE_CONFIG=../ansible.cfg
    ansible-playbook utils.yml --tags cleanup_oci_image_ingest
    ```

The cleanup removes the working directories (including a stale lock) and the
credential and Vault key files. To keep the credentials, add
`-e cleanup_credentials=false`. It does not remove `build_status.yml` or the
boot artifacts published to S3.

!!! warning

    The general Utils `cleanup` tag also runs `cleanup_oci_image_ingest`, which
    removes the stored registry credentials by default.

Make sure that no `oci_image_ingest` run is active before you run the cleanup.
It removes the lock and working data of a running ingestion and only displays a
warning.

## Limitations

- A functional group is served either by Image Build Manager or by OCI
  ingestion, not by both.
- An Image Build Manager cleanup removes ingested releases. To recover, run
  the `oci_image_ingest` workflow again.
- Only Harbor registries and the `repo_to_bucket` operation are supported.
- Published boot artifacts are readable by anyone who can reach the S3
  endpoint.

## Troubleshooting

- **`regctl` or `s3cmd` is not found**: Run Image Build Manager with
  `--tags prepare`, and then rerun the ingestion.
- **`.s3cfg` is not found**: Run Image Build Manager with `--tags prepare` to
  create the S3 configuration file for the user that runs Omnia.
- **`mksquashfs` is not found**: Install the `squashfs-tools` package on the
  OIM.
- **Another run holds the project lock**: Wait for the other run to finish. If
  you confirm that the earlier run is no longer active, remove the lock
  directory
  `$OMNIA_DATA_PATH/utils/workdir/$OMNIA_PROJECT_NAME/oci-image-ingest/.lock`,
  or run the cleanup tag.
- **The existing `build_status.yml` was written by another producer**: Use a
  separate output path for OCI image ingestion. The workflow does not modify
  the file.
- **Configuration validation fails**: Fill in the `registries` and
  `image_mappings` lists, which are empty in the template. Check that
  `functional_group` ends in `_x86_64` or `_aarch64`, that names are unique,
  and that each mapping refers to a defined `registry_name`.
- **The registry cannot be reached**: Confirm the host name, port, protocol, and
  network path from the OIM.
- **TLS verification fails**: Trust the registry certificate authority on the
  OIM, or use a registry certificate that the OIM trusts.
- **Registry authentication fails**: Delete the stored credential and Vault key
  files, and rerun the workflow to enter the credentials again.
- **The namespace is inaccessible or the image is not found**: Confirm the
  Harbor project, the image name and tag, and that the account can read them.
- **Architecture mismatch**: The image architecture does not match the
  `functional_group` suffix. Use an `amd64` image for `_x86_64` and an `arm64`
  image for `_aarch64`.
- **Insufficient free space**: Free space in the working directory. The
  workflow requires three times the compressed layer size.
- **zstd is not installed**: Install the `zstd` package and rerun the
  workflow.
- **The S3 endpoint rejects the public-read ACL**: Enable ACLs on the
  `boot-images` bucket, or grant anonymous read with a bucket policy.
- **The S3 upload fails or the uploaded sizes do not match**: Confirm S3
  reachability, bucket permissions, and free space. The workflow removes the
  partial objects and does not update `build_status.yml`.
- **Nodes do not boot the ingested image**: Confirm that
  `image_build_manager_output_path` points to the Utils `build_status.yml` and
  that the functional group is not also served by Image Build Manager.
- **Ingested images disappear after a cleanup**: An Image Build Manager cleanup
  removed them. Rerun `oci_image_ingest`.

## Related documentation

- [Utilities](index.md)
- [Utils Domain Contract](../../Reference/domain_contracts/utils_contract.md)
- [Image Build Manager Contract](../../Reference/domain_contracts/image_build_manager_contract.md)
