# Image Build Manager Input/Output Contract

## Input Contract

### Input Files

| File | Location | Required | Description |
|------|----------|----------|-------------|
| `image_build_manager_config.yml` | `/opt/omnia/image_build_manager/input/project_default/` | Yes | Image build configuration |
| `omnia_config.yml` | `/opt/omnia/image_build_manager/input/project_default/` | Yes | Omnia cluster configuration |
| `network_spec.yml` | `/opt/omnia/image_build_manager/input/project_default/` | Yes | Network configuration |

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `image_type` | string | Yes | - | Image type (x86_64, aarch64) |
| `base_os` | string | Yes | - | Base OS (RHEL 9, RHEL 10) |
| `package_groups` | list | Yes | - | Package groups to install |
| `s3_configurations` | object | Yes | - | S3 storage configuration |

## Output Contract

### Output Files

| File | Location | Description |
|------|----------|-------------|
| `image_build_status.yml` | `/opt/omnia/image_build_manager/output/` | Image build status |
| `image_manifest.yml` | `/opt/omnia/image_build_manager/output/` | Image manifest |

### Output Artifacts

- Diskless images uploaded to S3
- Image build logs
- Image manifest with checksums

## Execution Flow

1. **Validate Configuration**: Check image build configuration
2. **Configure S3**: Configure S3 storage for images
3. **Build Images**: Build diskless images with packages
4. **Upload Images**: Upload images to S3 storage
5. **Generate Manifest**: Create image manifest with checksums

## Related Documentation

- [Domain Overview](../../HowTo/image_build_manager/index.md)
- [Configuration Reference](../../Reference/Configuration/image_build_manager_config.md)







