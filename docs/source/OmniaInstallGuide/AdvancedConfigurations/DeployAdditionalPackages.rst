Deploy Additional Packages
==========================

Deploy Additional Packages During First Time Deployment
--------------------------------------------------------

To deploy additional software packages and container images on cluster nodes, do the following:

1. Open ``/opt/omnia/input/project_default/software_config.json``.
2. Under ``softwares``, add the ``additional_packages`` entry. Ensure the architecture list matches your cluster: ::

    {"name": "additional_packages", "arch": ["x86_64","aarch64"]}

3. Update ``/opt/omnia/input/project_default/additional_packages.json`` with the required packages/images.

4. Ensure you provide the correct package type (``rpm`` or ``image``) and the repository name/tag/digest, based on your requirement.

5. Execute the ``local_repo.yml`` playbook from inside the ``omnia_core`` container: ::

    ssh omnia_core
    cd /omnia/local_repo
    ansible-playbook local_repo.yml

6. After the local repositories are created, build the cluster node images and PXE boot the nodes using the images:

* Build images: `Step 12: Build Cluster Node Images <../RHEL_new/build_images.html>`_
* Discover nodes and PXE boot: `Step 13: Discover cluster nodes <../RHEL_new/Provision/index.html>`_

Deploy Additional Packages After Cluster Provisioning
-----------------------------------------------------

To deploy additional packages/images after cluster provisioning, do the following:

1. Update ``/opt/omnia/input/project_default/additional_packages.json`` with the new packages/images.
2. Re-run the ``local_repo.yml`` playbook to download the new packages/images to the Pulp container.
3. After the local repositories are updated, do the following:

    * To install the RPM packages on the required nodes, manually run the following command on each node: ::

        dnf install <package-name>

    * To pull the container images on the required nodes, manually run the following command on each node: ::

        Using tag: crictl pull <image_name>:<tag>

        Using digest: crictl pull <image_name>@<digest>
        
    * To verify the installed packages/images, run the following command on each node: ::

        dnf list installed <package-name>

        crictl images
