Deploy Additional Packages
==========================

Deploy Additional Packages During First Time Deployment
--------------------------------------------------------

To deploy additional software packages and container images on cluster nodes, do the following:

1. To download and deploy additional software packages and container images using Omnia local repositories, see `Add Additional Packages <../RHEL_new/CreateLocalRepo/AddingAdditionalPackager.html>`_.
2. After the local repositories are created, build the cluster node images and PXE boot the nodes using the images:

* Build images: `Step 12: Build Cluster Node Images <../RHEL_new/build_images.html>`_
* Discover nodes and PXE boot: `Step 13: Discover cluster nodes <../RHEL_new/Provision/index.html>`_

Deploy Additional Packages After Cluster Provisioning
-----------------------------------------------------

To deploy additional packages/images after cluster provisioning, do the following:

1. To download and deploy additional software packages and container images using Omnia local repositories, see `Add Additional Packages <../RHEL_new/CreateLocalRepo/AddingAdditionalPackager.html>`_.
2. Re-run the ``local_repo_.yml`` playbook to download the new packages/images to the Pulp container.
3. After the local repositories are updated, do the following:

    * To install the RPM packages on the required nodes, manually run the following command on each node: ::

        dnf install <package-name>

    * To pull the container images on the required nodes, manually run the following command on each node: ::

        Using tag: crictl pull <image_name>:<tag>

        Using digest: crictl pull <image_name>@<digest>
        
    * To verify the installed packages/images, run the following command on each node: ::

        dnf list installed <package-name>

        crictl images
