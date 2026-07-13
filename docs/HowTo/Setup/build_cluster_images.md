
# Build Cluster Node Images


The `build_image_x86_64.yml` and `build_image_aarch64.yml` playbooks are used to build diskless images for `x86_64` and `aarch64` cluster nodes, respectively.
Each image is created based on the functional groups defined in the mapping file.

!!! caution

    Limited validation has been performed on the aarch64 platform.


## Prerequisites


- The OIM has internet access.
- The [Create Mapping File](create_mapping_file.md) procedure is complete and the mapping file
  contains nodes with the functional groups required for your environment.
- `local_repo.yml` is executed with software packages matching the target architecture.
  If the build is for `x86_64`, include software defined with `x86_64`.
  If the build is for `aarch64`, include software with `aarch64`.
  If the build needs to support both architectures, ensure `local_repo.yml` is executed with
  `software_config.json` that includes both `x86_64` and `aarch64`.
- Note the compatibility between cluster OS and OIM OS:

| OIM OS | Cluster Node OS | Compatibility |
|--------|-----------------|---------------|
| RHEL   | RHEL            | Yes           |

## Procedure
### Build Images for x86_64 Cluster Nodes


1. **Enter the omnia_core container**:

    ```bash title="Run on: OIM host"
    ssh omnia_core
    ```

2. **Navigate to the image build directory**:

    ```bash title="Run on: omnia_core container"
    cd /omnia/build_image_x86_64
    ```

3. **Run the build playbook**:

    ```bash title="Run on: omnia_core container"
    ansible-playbook build_image_x86_64.yml
    ```

4. **Verify that images are created** for each functional group defined in the mapping file:

    ```bash title="Run on: omnia_core container"
    s3cmd ls -Hr s3://boot-images
    ```

    The images created for each functional group are listed in the `boot-images` directory.


### Build Images for aarch64 Cluster Nodes


#### Prepare the aarch64 Node

Before building aarch64 images, you must install RHEL 10 on one of the aarch64 nodes:

1. Ensure a disk is available to the aarch64 node for OS installation.

2. Manually install the **full Red Hat Enterprise Linux 10 OS** on one of the aarch64 nodes with the root password enabled.

3. Use the **host IP address** of the node in the `admin_aarch64` inventory file.

!!! note

    - The root password must be at least 8 characters long, contain alphanumeric characters, and must not include commas (`,`), hyphens (`-`), single quotes (`'`), double quotes (`"`), or backslashes (`\`).
    - The password set during RHEL installation on the aarch64 node must be supplied as `provision_password` when running `provision.yml`.


#### Build the aarch64 Images

1. **Enter the omnia_core container**:

    ```bash title="Run on: OIM host"
    ssh omnia_core
    ```

2. **Navigate to the image build directory**:

    ```bash title="Run on: omnia_core container"
    cd /omnia/build_image_aarch64
    ```

3. **Run the build playbook** with the aarch64 inventory:

    ```bash title="Run on: omnia_core container"
    ansible-playbook build_image_aarch64.yml -i inventory
    ```

    **Sample aarch64 inventory:**

    ```ini
    [admin_aarch64]
    10.0.0.1
    ```

4. **Verify that images are created** for each functional group defined in the mapping file:

    ```bash title="Run on: omnia_core container"
    s3cmd ls -Hr s3://boot-images
    ```

    The images created for each functional group are listed in the `boot-images` directory.


## Next Steps


- [Discover Nodes](discover_nodes.md) -- Run node discovery using the built images.
