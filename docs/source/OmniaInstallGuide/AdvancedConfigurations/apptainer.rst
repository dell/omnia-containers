Apptainer
==============

Apptainer pulls the container images from configured container registries on all cluster nodes. The method used to retrieve an image depends on the system registry configuration and image availability. Always start with the standard Apptainer pull command. Additional methods should only be used when required.

Verify if Apptainer is installed using the following command: ::

    apptainer --version

General Apptainer pull command is the default command to pull container images: ::

    apptainer pull \
        --name <image_name>.sif \
        --dir <image_directory> \
        --tmpdir <temporary_directory> \
        docker://<registry>/<repository>:<tag>

.. note:: 

    * --dir specifies the output directory for the final .sif image.
    * --tmpdir specifies the temporary working directory used during the pull.
    * Both directories should be located on an NFS-backed filesystem to avoid failures due to limited local disk space.

**Method 1: Standard image pull (Pulp-integrated and preferred)**

Create the directory used for both image storage and temporary files. This directory must be on an NFS-backed filesystem. ::

    mkdir -p /hpc_tools/container_images

Pull the image using the standard Apptainer workflow. This method automatically leverages Pulp when available and requires no changes to user behavior. ::

    apptainer pull \
        --name ubuntu_22.04.sif \
        --dir /hpc_tools/container_images \
        --tmpdir /hpc_tools/container_images \
        docker://docker.io/library/ubuntu:22.04

Behavior:

Registry mirror behavior is controlled by configuration files under: ::

        /etc/containers/registries.conf.d/

When a Pulp registry mirror is configured and the image is present, the pull is transparently served from Pulp.

In environments where Pulp usage is required and the image is known to exist, the Pulp registry may be specified explicitly: ::

        docker://<pulp-registry>/<namespace>/ubuntu:22.04

Replace <pulp-registry> and <namespace> with site-specific values.


**Method 2: Pulling an Image directly from the internet (Exception only)**


.. caution:: Use this method only when absolutely necessary.

This method should be used only if:

* A Pulp registry mirror is configured, and
* The image is not available in Pulp or the mirror is unavailable.

1. Temporarily disable the container registry configuration that enforces mirroring to Pulp. This configuration is typically located under: ::

        /etc/containers/registries.conf.d/

.. caution:: Administrative privileges are required. Do not delete the configuration—disable it temporarily.

2. Pull the image directly from the public registry. Use the same NFS-backed directory for both image storage and temporary files. ::

    apptainer pull --disable-cache \
        --name ubuntu_22.04.sif \
        --dir /hpc_tools/container_images \
        --tmpdir /hpc_tools/container_images \
        docker://docker.io/library/ubuntu:22.04

**Verification (All methods)**

Run the command. ::

        ls -lh /hpc_tools/container_images/ubuntu_22.04.sif
        apptainer inspect /hpc_tools/container_images/ubuntu_22.04.sif


After pulling directly from the internet, restore the registry mirror configuration so that future pulls again route through Pulp.

.. note:: For detailed guidance on using Apptainer and NVIDIA HPC Benchmarks, refer to:
    
    Apptainer User Documentation: https://apptainer.org/docs/user/main/



















