# image_build_manager Config Reference

The `image_build_manager_config.yml` file configures image building and S3 storage.

## Location

```
/opt/omnia/image_build_manager/input/project_default/image_build_manager_config.yml
```

## Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `image_type` | string | Yes | - | Image type (x86_64, aarch64) |
| `base_os` | string | Yes | - | Base OS (RHEL 9, RHEL 10) |
| `package_groups` | list | Yes | - | Package groups to install |
| `s3_configurations` | object | Yes | - | S3 storage configuration |

## Usage Example

```yaml title="File: /opt/omnia/image_build_manager/input/project_default/image_build_manager_config.yml"
image_type: x86_64
base_os: RHEL 9
package_groups:
  - slurm
  - kubernetes
s3_configurations:
  provider: minio
  endpoint: http://minio:9000
  bucket: omnia-images
```

## Related Configuration

- [storage_config.md](storage_config.md)
- [Domain Contract](../domain_contracts/image_build_manager_contract.md)





