Deploy Additional Packages
==========================

Deploy Additional Packages During First Time Deployment
--------------------------------------------------------

To deploy additional software packages and container images on cluster nodes, do the following:

1. To download and deploy additional software packages and container images using Omnia local repositories, see `Add Additional Packages <../RHEL_new/CreateLocalRepo/AddingAdditionalPackages.html>`_.
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

    * To pull the container images on the required nodes, see **Pulling images from a user registry via Pulp on a service Kubernetes cluster** in the following section.
        
    * To verify the installed packages/images, run the following command on each node: ::

        dnf list installed <package-name>

        crictl images

Pulling images from a user registry via Pulp on a service Kubernetes cluster
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When the container images from a user registry are specified in the ``additional_packages.json``, running ``local_repo.yml`` thereafter, uploads those images to the configured Pulp registry.
 
After this synchronization:

* All cluster nodes must pull images from Pulp, not directly from the user registry.
* This enables centralized image management and supports offline or air-gapped environments.

Example: Image defined in input additional_packages.json ::

    "additional_packages": {
    "cluster": [
        {
        "package": "100.10.0.76:3445/library/nginx",
        "type": "image",
        "tag": "1.25.2-alpine-slim"
        }
    ]
    }

In this example:

* `100.10.0.76:3445` is the user registry.
* Omnia syncs the image to the Pulp registry.
* Cluster nodes must subsequently pull the image from Pulp.


Retrieve the Pulp registry endpoint
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On the Omnia Core container, run: ::

    pulp status | jq -r '.content_settings.content_origin'

Sample output: ::

    https://172.16.255.254:2225

Remove the `https://` prefix and use only 172.16.255.254:2225


Configure compute nodes to pull from Pulp
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On each Kubernetes compute node:

1. Edit the following file: ::

    vi /etc/containers/registries.conf.d/crio.conf

2. Append this configuration at the end of the file. ::

    [[registry]]
    prefix = "100.10.0.76:3445"
    location = "100.10.0.76:3445"
    
    [[registry.mirror]]
    location = "172.16.255.254:2225"

3. Reload and restart CRI-O. ::
    
    systemctl daemon-reload
    systemctl restart crio


Pull the image
^^^^^^^^^^^^^^^^^

Pull the image using the original registry reference (CRI-O transparently redirects to Pulp). ::

    crictl pull 100.10.0.76:3445/library/nginx:1.25.2-alpine-slim

The image will be retrieved from the Pulp mirror automatically.