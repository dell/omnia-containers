
# Build Cluster Images


Build operating system boot images for cluster nodes using the Omnia image
build playbooks. These images are stored in MinIO (S3) and served to nodes
during PXE boot.

## Overview


Omnia provides architecture-specific playbooks to build cluster boot images:

- `build_image_x86_64.yml` -- For Intel/AMD x86_64 servers.
- `build_image_aarch64.yml` -- For ARM-based (aarch64) servers.

The build process:

1. Extracts the OS ISO specified in `provision_config.yml`.
2. Installs packages from the local Pulp repositories.
3. Applies the software stack defined in `software_config.json`.
4. Creates a bootable image and uploads it to MinIO (S3 `boot-images` bucket).
5. Registers the image with OpenCHAMI's Boot Script Service (BSS).


## Prerequisites


- The [Create Local Repos](create_local_repos.md) procedure is complete (local repositories are
  synced).
- The [Create Mapping File](create_mapping_file.md) procedure is complete (mapping file defines
  target nodes).
- The OS ISO file is available at the path specified in
  `provision_config.yml` (`iso_file_path`).
- MinIO is running and accessible (verified via [Verify Oim Services](verify_oim_services.md)).


## Procedure


1. **Enter the omnia_core container**:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```


2. **Verify the OS ISO is accessible**:

   ```bash title="Run on: omnia_core container"
   ls -lh /opt/omnia/iso/
   ```


   Ensure the ISO file listed in `provision_config.yml` exists.

3. **Build images for x86_64 nodes**:

   ```bash title="Run on: omnia_core container"
   cd /omnia
   ansible-playbook build_image_x86_64.yml
   ```


   !!! note

       Add `--ask-vault-pass` if credentials are encrypted:

       ```bash title="Run on: omnia_core container"
       ansible-playbook build_image_x86_64.yml --ask-vault-pass
       ```


4. **(If applicable) Build images for aarch64 nodes**:

   ```bash title="Run on: omnia_core container"
   cd /omnia
   ansible-playbook build_image_aarch64.yml
   ```


   !!! note

       You can build both architectures. Each playbook produces a separate
       image in MinIO.

5. **Wait for the build to complete**. Image building typically takes
   **20-45 minutes** depending on the software stack size and hardware.


## Verification


1. **List images in the S3 boot-images bucket**:

   ```bash title="Run on: omnia_core container"
   s3cmd ls -Hr s3://boot-images
   ```


   Expected output shows the image files with their sizes:

   ```text title="Expected output on: omnia_core container"
   2024-01-15 10:30  3145728000  s3://boot-images/x86_64/rhel-8.8/rootfs.img
   2024-01-15 10:30     8388608  s3://boot-images/x86_64/rhel-8.8/vmlinuz
   2024-01-15 10:30    52428800  s3://boot-images/x86_64/rhel-8.8/initrd.img
   ```


2. **Verify the image is registered with BSS**:

   ```bash title="Run on: omnia_core container"
   ochami bss list
   ```


   The output should show boot configurations referencing the newly built
   images.

3. **Check the image size is reasonable**:

   ```bash title="Run on: omnia_core container"
   s3cmd du s3://boot-images
   ```


   A typical RHEL 8.8 image with Slurm and basic packages is 2-4 GB.
   Images with CUDA or large software stacks can be 5-10 GB.


## Next Steps


- [Discover Nodes](discover_nodes.md) -- Run node discovery using the built images.
- [Pxe Boot Nodes](pxe_boot_nodes.md) -- PXE boot target servers with the new images.


## Troubleshooting


**Build fails with "ISO not found"**
   Verify the `iso_file_path` in `provision_config.yml` points to a valid
   ISO:

   ```bash title="Run on: omnia_core container"
   cat /opt/omnia/input/project_default/provision_config.yml | grep iso_file_path
   ls -lh /opt/omnia/iso/
   ```


**Build fails with "repository not found"**
   Ensure `local_repo.yml` completed successfully. Check Pulp repositories:

   ```bash title="Run on: OIM host"
   curl -s http://localhost:8080/pulp/api/v3/distributions/rpm/rpm/ | python3 -m json.tool
   ```


**S3 upload fails**
   Verify MinIO is running and accessible:

   ```bash title="Run on: omnia_core container"
   s3cmd ls
   ```


   If MinIO is unreachable, restart it:

   ```bash title="Run on: OIM host"
   systemctl restart minio.service
   ```


**Image build is very slow**
   - Ensure the OIM has sufficient RAM (64 GB minimum).
   - Check disk I/O performance (SSD recommended for image builds).
   - Reduce the software stack in `software_config.json` if building a
     minimal test image.

**Wrong architecture image built**
   Ensure you run the correct playbook for your target hardware:

   - Intel/AMD servers: `build_image_x86_64.yml`
   - ARM servers: `build_image_aarch64.yml`
