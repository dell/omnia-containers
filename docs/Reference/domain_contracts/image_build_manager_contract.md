# Image Build Manager Domain Contract

**Deployment module**: Image Build Manager | **CLI identifier**: `image_build_manager`

## Upstream domain contract

Image Build Manager consumes `repo_status.yml`, the output contract produced
by Repository Manager. Build-related flows require the file and validate it
against the Repo Manager status schema before loading repository data.

### `repo_status.yml`

**Location**:
`$OMNIA_DATA_PATH/repo_manager/output/$OMNIA_PROJECT_NAME/repo_status.yml`

**Producer**: Repository Manager.

**Consumer**: Image Build Manager build and execute flows.

The path can be overridden by `repo_manager_output_path` in
`image_build_config.yml`. The generated Repository Manager output is the
authoritative contract.

#### Structure

The following example shows the structure of a successful Repository Manager
output. Repository names and artifact entries vary according to the selected
catalog.

```yaml
overall_status: "success"
cluster_os_type: "rhel"
repo_config: "partial"

execution_contexts:
  - context_id: "rhel_10.0"
    os_type: "rhel"
    os_version: "10.0"
    architectures:
      - "x86_64"
      - "aarch64"

overall_status_by_version:
  "10.0": "success"

repo_manager:
  port: 2225
  certificates:
    server_crt: "$OMNIA_DATA_PATH/repo_manager/pulp_config/settings/certs/pulp_webserver.crt"
    certs_dir: "$OMNIA_DATA_PATH/repo_manager/pulp_config/settings/certs"

repositories:
  "10.0":
    x86_64:
      baseos:
        url: "https://192.0.2.10:2225/pulp/content/.../baseos/"
      slurm_custom:
        url: "https://192.0.2.10:2225/pulp/content/.../slurm_custom/"
        priority: 100
    aarch64: {}

registries:
  private_registry:
    base_url: "https://registry.example.com"
    port: 443
    host: "registry.example.com:443"
    tls:
      insecure: false

file_repos:
  x86_64:
    tarball:
      helm_v3_20_1_amd64: "https://192.0.2.10:2225/pulp/content/.../"
    pip_module:
      cffi_1_17_1: "https://192.0.2.10:2225/pypi/.../"
  aarch64: {}

tarball_base_url: "https://192.0.2.10:2225/pulp/content/.../tarball/"
pip_base_url: "https://192.0.2.10:2225/pypi/.../pip_module/"
offline_tarball_path: "https://192.0.2.10:2225/pulp/content/.../tarball/"
offline_pip_module_path: "https://192.0.2.10:2225/pypi/.../pip_module/"
```

Image Build Manager requires `overall_status`, `cluster_os_type`, and at least
one version under `repositories`. `overall_status` must be `success`, and at
least one `x86_64` or `aarch64` repository entry must contain a valid HTTP(S)
URL. Each optional `priority` value must be an integer from 1 through 100.

The `repo_manager` section is optional. When present, Image Build Manager uses
`repo_manager.port` and `repo_manager.certificates.server_crt`; if a certificate
path is specified, the file must exist. Other producer-owned metadata,
including execution contexts, per-version status, registry configuration, and
file-repository URLs, is retained in the contract but is not interpreted by
Image Build Manager. The prepare, validation, precheck, and cleanup flows do
not require this upstream output.

## Output contract

### `build_status.yml`

**Location**:
`$OMNIA_DATA_PATH/image_build_manager/output/<project>/build_status.yml`

**Producer**: The `build_os_images` role's status-writing task.

**Consumer**: The provisioning workflow, for image validation and OpenCHAMI
boot-service configuration rendering.

The current manifest does not contain a `schema_version` or
`contract_version` field. Consumers determine compatibility by validating the
required fields directly.

The producer also writes
`build_status_<OMNIA_VERSION>_<YYYYMMDD_HHMM>.yml` beside the latest file.
The version and timestamp in that filename identify the producing product run;
they are not a manifest schema version.

The latest `build_status.yml` is overwritten only when the workflow reaches
the status-writing step after the selected image builds. If a build fails
before that step, an existing manifest from an earlier run is not replaced or
removed. Verify that the current build completed successfully and that the
manifest references its expected S3 artifacts before using it for
provisioning. Full Image Build Manager cleanup removes both the latest and
versioned status outputs.

| Field | Type | Purpose |
|---|---|---|
| `overall_status` | string | Reports `success` or `failed`. |
| `image_build_type` | string | Records the producing engine: `image-builder` or `image-thrillhouse`. |
| `s3_configurations.endpoint_url` | string | S3 HTTP(S) endpoint without an artifact path. |
| `s3_configurations.bucket` | string | Artifact bucket, currently `boot-images`. |
| `functional_group_images[].functional_group` | string | Functional-group name with its architecture suffix. |
| `functional_group_images[].kernel` | string | Endpoint-relative kernel object path. |
| `functional_group_images[].initrd` | string | Endpoint-relative initramfs object path. |
| `functional_group_images[].image` | string | Endpoint-relative root-filesystem object path. |

Each artifact path includes the bucket name, omits the endpoint and `s3://`
scheme, and ends with the object filename. Consumers construct a download URL
as `<s3_configurations.endpoint_url>/<artifact-path>`.

`image_build_type` records the engine that produced the manifest. Consumers
use this recorded value, rather than current runtime settings, to interpret
the artifact layout.

### S3 artifact layouts

`image-builder` publishes:

```text
boot-images/efi-images/<functional_group>/<image_name>-imgbld/vmlinuz-<kernel-version>
boot-images/efi-images/<functional_group>/<image_name>-imgbld/initramfs-<kernel-version>.img
boot-images/<functional_group>/<image_name>-imgbld/<rootfs-filename>
```

`image-thrillhouse` publishes:

```text
boot-images/<functional_group>/<image_name>-imgth/<release>/vmlinuz
boot-images/<functional_group>/<image_name>-imgth/<release>/initramfs.img
boot-images/<functional_group>/<image_name>-imgth/<release>/rootfs.squashfs
```

The `efi-images` segment is an object-key prefix inside the `boot-images`
bucket, not a separate bucket.

### Deployed services

| Service | Condition | Endpoint |
|---|---|---|
| `minio.service` | S3 provider is not PowerScale | Ports 9000 for the API and 9001 for the console. |
| `registry.service` | Always during preparation | Port 5000 over HTTP. |

Both services are deployed as Podman Quadlets and added to `omnia.target`.

### Cleanup

The full Image Build Manager cleanup removes the MinIO and registry containers
and data, `build_status.yml`, S3 buckets and artifacts, service entries,
credentials, and the `s3cmd` configuration.

## Related documentation

- [Image Build Manager](../../HowTo/image_build_manager/index.md)
- [Build OS Images](../../HowTo/image_build_manager/build_images.md)
- [Repository Manager Contract](repo_manager_contract.md)
