# image_build_config.yml

This file selects the Image Build Manager engine, S3 backend, upstream Repo
Manager output, functional-group source, build controls, and optional ARM build
host.

## Location

```text
$OMNIA_DATA_PATH/image_build_manager/input/$OMNIA_PROJECT_NAME/image_build_config.yml
```

## Parameters

| Parameter | Type | Required | Source value or constraint |
|---|---|---|---|
| `repo_manager_output_path` | string | Yes | Full path to `repo_status.yml` produced by Repository Manager. |
| `s3_configurations.provider` | string | Yes | `minio` or `powerscale`. |
| `s3_configurations.endpoint_url` | string | Yes | Empty for MinIO; valid HTTP(S) URL for PowerScale. |
| `image_build_type` | string | Yes | `image-builder` or `image-thrillhouse`; source value is `image-thrillhouse`. |
| `functional_groups_source` | string | Yes | `config` or `catalog`; source value is `catalog`. |
| `build_image.max_parallel` | integer | Yes | 0 through 64; `0` means unlimited. |
| `build_image.build_timeout` | integer | Yes | 600 through 86400 seconds. |
| `build_image.force_rebuild` | boolean | Yes | Bypass the package-hash cache. |
| `build_image.backup_s3_images` | boolean | Yes | Back up existing S3 image artifacts before rebuilding. |
| `build_image.repo_ssl_verify` | boolean | Yes | Enable SSL and GPG verification for RPM repositories. |
| `aarch64_inventory_host_ip` | IPv4 string | No | Empty disables aarch64 builds. |
| `aarch64_ssh_user` | string | Conditional | Required when an ARM host IP is provided; source value is `root`. |

Unknown properties are rejected. S3 bucket names are fixed by the source and
are not configuration fields.

## Usage example

```yaml title="File: /opt/omnia/image_build_manager/input/project_default/image_build_config.yml"
repo_manager_output_path: "/opt/omnia/repo_manager/output/project_default/repo_status.yml"

s3_configurations:
  provider: "minio"
  endpoint_url: ""

image_build_type: "image-thrillhouse"

build_image:
  max_parallel: 0
  build_timeout: 7200
  force_rebuild: false
  backup_s3_images: false
  repo_ssl_verify: true

functional_groups_source: "catalog"

aarch64_inventory_host_ip: ""
aarch64_ssh_user: "root"
```

The credential workflow stores S3 and ARM SSH secrets in the encrypted
`image_build_credentials.yml`; do not add them here.

## Related configuration

- [Package groups](package_groups.md)
- [Image Build Manager contract](../domain_contracts/image_build_manager_contract.md)

