Kernel Version Override Support in Omnia
==========================================

Omnia supports a kernel version override capability, allowing you to deploy a newer, validated kernel without requiring a full base operating system upgrade. This feature helps accelerate the adoption of critical security fixes and bug patches while maintaining OS stability.

.. note::
   The build image process automatically selects the **latest kernel version available across all configured repositories**. This is not user-configurable. The ``kernel_version_override`` parameter in ``provision_config.yml`` controls only the **provisioning flow** — it determines which kernel from S3 is used when installing the OS on cluster nodes.

Prerequisites
-------------

* Omnia Infrastructure Manager (OIM) is deployed and ``omnia_core`` container is running.
* ``prepare_oim.yml`` is executed successfully.
* Network connectivity from the OIM to the RHEL repository source (Red Hat CDN or internal mirror).
* For RHEL subscription-based repositories: Valid RHEL subscription entitlement certificates are required to authenticate with Red Hat CDN.

Configuration and Deployment
----------------------------

This section describes how to add RHEL repositories, configure kernel version override, and execute the complete build and provisioning workflow.

Overview
~~~~~~~~

The following tasks are covered:

* Adding RHEL repositories (BaseOS, AppStream, CRB) to ``local_repo_config.yml``
* Configuring ``kernel_version_override`` in ``provision_config.yml``
* Executing the full build and provisioning process
* Validating repository sync and kernel image availability

Adding RHEL Repositories
~~~~~~~~~~~~~~~~~~~~~~~~

Update the local repository configuration file:

.. code-block:: bash

   /opt/omnia/input/project_default/local_repo_config.yml

Choose **one** of the following options based on your environment.

Option A: RHEL Subscription (EUS Repositories)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your environment has an active RHEL subscription, you can configure Extended Update Support (EUS) repositories using ``rhel_subscription_repo_config_x86_64``. EUS repositories provide longer support cycles for specific RHEL minor releases and are recommended for production HPC environments.

.. note::
   * Copy the RHEL subscription entitlement certificates to ``/opt/omnia/rhel_repo_certs/`` on the omnia core container before running ``local_repo.yml``.
   * The certificate files (CA certificate, client key, and client certificate) are obtained from your RHEL subscription entitlement.
   * Ensure the ``sslcacert``, ``sslclientkey``, and ``sslclientcert`` paths point to valid certificate files on the omnia core container.

**Example Configuration (EUS):**

.. code-block:: yaml

   rhel_subscription_repo_config_x86_64:
     - { url: "https://cdn.redhat.com/content/eus/rhel10/10.0/x86_64/appstream/os", gpgkey: "", sslcacert: "/opt/omnia/rhel_repo_certs/redhat-uep.pem", sslclientkey: "/opt/omnia/rhel_repo_certs/<entitlement-key>.pem", sslclientcert: "/opt/omnia/rhel_repo_certs/<entitlement-cert>.pem", name: "x86_64_appstream-eus" }
     - { url: "https://cdn.redhat.com/content/eus/rhel10/10.0/x86_64/baseos/os", gpgkey: "", sslcacert: "/opt/omnia/rhel_repo_certs/redhat-uep.pem", sslclientkey: "/opt/omnia/rhel_repo_certs/<entitlement-key>.pem", sslclientcert: "/opt/omnia/rhel_repo_certs/<entitlement-cert>.pem", name: "x86_64_baseos-eus" }
     - { url: "https://cdn.redhat.com/content/eus/rhel10/10.0/x86_64/codeready-builder/os", gpgkey: "", sslcacert: "/opt/omnia/rhel_repo_certs/redhat-uep.pem", sslclientkey: "/opt/omnia/rhel_repo_certs/<entitlement-key>.pem", sslclientcert: "/opt/omnia/rhel_repo_certs/<entitlement-cert>.pem", name: "x86_64_crb-eus" }

   rhel_subscription_repo_config_aarch64:
     - { url: "https://cdn.redhat.com/content/eus/rhel10/10.0/aarch64/appstream/os", gpgkey: "", sslcacert: "/opt/omnia/rhel_repo_certs/redhat-uep.pem", sslclientkey: "/opt/omnia/rhel_repo_certs/<entitlement-key>.pem", sslclientcert: "/opt/omnia/rhel_repo_certs/<entitlement-cert>.pem", name: "x86_64_appstream-eus" }
     - { url: "https://cdn.redhat.com/content/eus/rhel10/10.0/aarch64/baseos/os", gpgkey: "", sslcacert: "/opt/omnia/rhel_repo_certs/redhat-uep.pem", sslclientkey: "/opt/omnia/rhel_repo_certs/<entitlement-key>.pem", sslclientcert: "/opt/omnia/rhel_repo_certs/<entitlement-cert>.pem", name: "x86_64_baseos-eus" }
     - { url: "https://cdn.redhat.com/content/eus/rhel10/10.0/aarch64/codeready-builder/os", gpgkey: "", sslcacert: "/opt/omnia/rhel_repo_certs/redhat-uep.pem", sslclientkey: "/opt/omnia/rhel_repo_certs/<entitlement-key>.pem", sslclientcert: "/opt/omnia/rhel_repo_certs/<entitlement-cert>.pem", name: "x86_64_crb-eus" }

.. note::
   * Replace ``<entitlement-key>.pem`` and ``<entitlement-cert>.pem`` with the actual filenames of your RHEL entitlement certificate and key files.
   * The ``gpgkey`` field can be left empty when using subscription certificates for authentication.

Option B: User-Provided Repositories (No Subscription)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your environment does not have an active RHEL subscription, you can configure user-provided repository mirrors using ``user_repo_url_x86_64``. This is suitable for air-gapped environments or when using internal RHEL mirrors.

**Example Configuration:**

.. code-block:: yaml

   user_repo_url_x86_64:
     - { url: "http://<mirror-server>/rhel10/10.0/x86_64/CRB/os/", gpgkey: "http://<mirror-server>/rhel10/10.0/x86_64/CRB/os/RPM-GPG-KEY-redhat-release", name: "additional-codeready-builder" }
     - { url: "http://<mirror-server>/rhel10/10.0/x86_64/BaseOS/os/", gpgkey: "http://<mirror-server>/rhel10/10.0/x86_64/BaseOS/os/RPM-GPG-KEY-redhat-release", name: "additional-baseos" }
     - { url: "http://<mirror-server>/rhel10/10.0/x86_64/AppStream/os/", gpgkey: "http://<mirror-server>/rhel10/10.0/x86_64/AppStream/os/RPM-GPG-KEY-redhat-release", name: "additional-appstream" }

   user_repo_url_aarch64:
     - { url: "http://<mirror-server>/rhel10/10.0/aarch64/CRB/os/", gpgkey: "http://<mirror-server>/rhel10/10.0/aarch64/CRB/os/RPM-GPG-KEY-redhat-release", name: "additional-codeready-builder" }
     - { url: "http://<mirror-server>/rhel10/10.0/aarch64/BaseOS/os/", gpgkey: "http://<mirror-server>/rhel10/10.0/aarch64/BaseOS/os/RPM-GPG-KEY-redhat-release", name: "additional-baseos" }
     - { url: "http://<mirror-server>/rhel10/10.0/aarch64/AppStream/os/", gpgkey: "http://<mirror-server>/rhel10/10.0/aarch64/AppStream/os/RPM-GPG-KEY-redhat-release", name: "additional-appstream" }

.. note::
   * Replace ``<mirror-server>`` with the hostname or IP address of your internal RHEL mirror.
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

* Empty value (``""``): The provisioning flow automatically selects the latest available kernel from S3 for OS installation.
* Set value: The provisioning flow selects the exact specified kernel version from S3 (even from a different RHEL minor version) for OS installation.
* This parameter does not affect the build image process. The build image playbook always picks the latest kernel available across all configured repositories.
* Only the kernel and initrd are overridden during provisioning; the OS and root filesystem remain unchanged.
* Validation fails if the specified kernel is not found in S3.
* The specified kernel version applies to both Intel/AMD (x86_64) and ARM (aarch64) processor architectures.

**Example:**

.. code-block:: yaml

   kernel_version_override: "6.12.0-55.76.1.el10_0"

Execution Workflow
~~~~~~~~~~~~~~~~~

Step 1: Sync Repositories
^^^^^^^^^^^^^^^^^^^^^^^^^^

Run the local repository playbook to sync repositories to Pulp:

.. code-block:: bash

   cd /omnia/local_repo
   ansible-playbook local_repo.yml

Verify that all repositories show a successful status.

Step 2: Validate Repository Sync
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After ``local_repo.yml`` completes, validate that the kernel packages are available in the Pulp repository. Execute the following commands from within the ``omnia_core`` container.

1. List the synced repository distributions to identify the repository name:

.. code-block:: bash

   pulp rpm distribution list

2. Verify kernel packages are available in the repository by querying the Pulp content endpoint. Replace ``<oim_admin_ip>`` with the OIM admin IP address and ``<repo_name>`` with the repository name from the previous step:

.. code-block:: bash

   curl -k https://<oim_admin_ip>:2225/pulp/content/opt/omnia/offline_repo/cluster/x86_64/rhel/10.0/rpms/<repo_name>/Packages/k/ | grep kernel

3. Confirm that the expected kernel RPM packages (``kernel``, ``kernel-core``, ``kernel-modules``) are listed in the output.

.. note::
   If no kernel packages are found, verify the repository URLs in ``local_repo_config.yml`` and re-run ``local_repo.yml``.

Step 3: Build Images
^^^^^^^^^^^^^^^^^^^^

Build the kernel, initrd, and rootfs images:

.. code-block:: bash

   cd /omnia/build_image_x86_64
   ansible-playbook build_image_x86_64.yml

This playbook builds the images and uploads them to S3. The build process automatically selects the **latest kernel version** available across all configured repositories.

Step 4: Validate Kernel Image in S3
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After the build completes, verify that the new kernel image was created and uploaded to S3:

.. code-block:: bash

   s3cmd ls -Hr s3://boot-images

Look for entries matching your functional group and the expected kernel version. For example:

.. code-block:: text

   s3://boot-images/efi-images/<functional_group>/rhel-<functional_group>_omnia_<version>/vmlinuz-<kernel_version>
   s3://boot-images/efi-images/<functional_group>/rhel-<functional_group>_omnia_<version>/initramfs-<kernel_version>.img

Confirm that the kernel version in S3 matches the expected version before proceeding to provisioning.

Step 5: Provision Cluster
^^^^^^^^^^^^^^^^^^^^^^^^^

Provision the cluster with the specified kernel:

.. code-block:: bash

   cd /omnia/provision
   ansible-playbook provision.yml

This playbook validates the kernel and initrd in S3, configures BSS and cloud-init, and prepares nodes for PXE boot.

* If ``kernel_version_override`` is set in ``provision_config.yml``, the provisioning flow selects the exact specified kernel version from S3 for OS installation.
* If ``kernel_version_override`` is empty, the provisioning flow automatically picks the latest available kernel from S3.

Step 6: PXE Boot Nodes
^^^^^^^^^^^^^^^^^^^^^^

Power on the cluster nodes and verify the following:

* Nodes boot successfully
* ``uname -r`` displays the expected kernel version
* Cluster services are operational

Summary
~~~~~~~

To deploy a kernel version override:

1. Add BaseOS, AppStream, and CRB repositories to ``local_repo_config.yml`` (using EUS subscription repos or user-provided mirrors)
2. Run ``local_repo.yml`` to sync repositories to Pulp
3. Validate kernel packages in the Pulp repository
4. Run ``build_image_x86_64.yml`` to build images (latest kernel is selected automatically)
5. Validate the kernel image in S3 using ``s3cmd ls -Hr s3://boot-images``
6. Optionally set ``kernel_version_override`` in ``provision_config.yml``
7. Run ``provision.yml`` to provision the cluster
8. PXE boot the nodes and verify the kernel version
