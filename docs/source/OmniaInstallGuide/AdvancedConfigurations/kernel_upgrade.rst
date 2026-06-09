Kernel Version Override Support in Omnia
==========================================

Omnia now supports a kernel version override capability, allowing you to deploy a newer, validated kernel without requiring a full base operating system upgrade. This feature helps accelerate the adoption of critical security fixes and bug patches while maintaining OS stability.

Configuration and Deployment
----------------------------

This section describes how to add RHEL repositories, configure kernel version override, and execute the complete build and provisioning workflow.

Overview
~~~~~~~~

The following tasks are covered:

* Adding RHEL 10.x repositories (BaseOS, AppStream, CRB) to ``local_repo_config.yml``
* Configuring ``kernel_version_override`` in ``provision_config.yml``
* Executing the full build and provisioning process

Adding RHEL Repositories
~~~~~~~~~~~~~~~~~~~~~~~~

Update the local repository configuration file:

.. code-block:: bash

   /opt/omnia/input/project_default/local_repo_config.yml

Add the required BaseOS, AppStream, and CRB repository URLs for both architectures.

**Example Configuration:**

.. code-block:: yaml

   user_repo_url_x86_64:
     - { url: "http://crb.com/CRB/x86_64/os/", gpgkey: "http://crb.com/CRB/x86_64/os/RPM-GPG-KEY", name: "additional-codeready-builder"}
     - { url: "http://BaseOS.com/BaseOS/x86_64/os/", gpgkey: "http://BaseOS.com/BaseOS/x86_64/os/RPM-GPG-KEY", name: "additional-baseos"}
     - { url: "http://AppStream.com/AppStream/x86_64/os/", gpgkey: "http://AppStream.com/AppStream/x86_64/os/RPM-GPG-KEY", name: "additional-appstream"}
   user_repo_url_aarch64:
     - { url: "http://crb.com/CRB/aarch64/os/", gpgkey: "http://crb.com/CRB/aarch64/os/RPM-GPG-KEY", name: "additional-codeready-builder"}
     - { url: "http://BaseOS.com/BaseOS/aarch64/os/", gpgkey: "http://BaseOS.com/BaseOS/aarch64/os/RPM-GPG-KEY", name: "additional-baseos"}
     - { url: "http://AppStream.com/AppStream/aarch64/os/", gpgkey: "http://AppStream.com/AppStream/aarch64/os/RPM-GPG-KEY", name: "additional-appstream"}

.. note::
   * Replace the example URLs with your internal RHEL mirror URLs.
   * Ensure that the repositories are accessible from the ``omnia_core`` container.

Configuring Kernel Version Override
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Update the provision configuration file:

.. code-block:: bash

   /opt/omnia/input/project_default/provision_config.yml

Set the ``kernel_version_override`` parameter:

.. code-block:: yaml

   kernel_version_override: ""

**Behavior:**

* **Empty value (``""``)**: Omnia automatically selects the latest available kernel from S3.
* **Set value**: Omnia selects the exact specified kernel version (even from a different RHEL minor version).
* Only the kernel and initrd are overridden; the OS and root filesystem remain unchanged.
* Validation fails if the specified kernel is not found in S3.

**Example:**

.. code-block:: yaml

   kernel_version_override: "6.12.0-55.76.1.el10_0.x86_64"

Execution Workflow
~~~~~~~~~~~~~~~~~

Step 1: Sync Repositories
^^^^^^^^^^^^^^^^^^^^^^^^^^

Run the local repository playbook to sync repositories to Pulp:

.. code-block:: bash

   cd /omnia/local_repo
   ansible-playbook local_repo.yml

Verify that all repositories show a successful status.

Step 2: Build Images
^^^^^^^^^^^^^^^^^^^^

Build the kernel, initrd, and rootfs images:

.. code-block:: bash

   cd /omnia/build_image_x86_64
   ansible-playbook build_image_x86_64.yml

This playbook builds the images and uploads them to S3.

Step 3: Provision Cluster
^^^^^^^^^^^^^^^^^^^^^^^^^

Provision the cluster with the specified kernel:

.. code-block:: bash

   cd /omnia/provision
   ansible-playbook provision.yml

This playbook validates the kernel and initrd in S3, configures BSS and cloud-init, and prepares nodes for PXE boot.

Step 4: PXE Boot Nodes
^^^^^^^^^^^^^^^^^^^^^^

Power on the cluster nodes and verify the following:

* Nodes boot successfully
* ``uname -r`` displays the expected kernel version
* Cluster services are operational
* CUDA and DOCA-OFED status are validated (if applicable)

Troubleshooting
~~~~~~~~~~~~~~~

**Repository Issues**

Check mirror accessibility and network connectivity to ensure the repositories are reachable from the ``omnia_core`` container.

**Kernel Not Found**

Verify that the specified kernel version exists in S3 and matches the expected naming convention.

**PXE Boot Issues**

Validate the following components:

* BSS configuration
* Network connectivity
* DHCP and TFTP services
* Node console logs for boot errors

Summary
~~~~~~~

To deploy a kernel version override:

1. Add BaseOS, AppStream, and CRB repositories to ``local_repo_config.yml``
2. Optionally set ``kernel_version_override`` in ``provision_config.yml``
3. Run the playbooks in sequence: ``local_repo.yml``, ``build_image_x86_64.yml``, ``provision.yml``
4. PXE boot the nodes and verify the kernel version
