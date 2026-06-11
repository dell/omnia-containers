Step 5:  Prepare the OIM
========================================================

The ``prepare_oim.yml`` playbook is used to prepare the Omnia Infrastructure Manager (OIM). The playbook performs the following on the OIM:

* Sets up the OpenCHAMI containers.
* Sets up the BuildStreamM container if BuildStreaM is enabled in ``/opt/omnia/input/project_default/build_stream_config.yml``.
* Sets up the Omnia Auth container if ``"name": "openldap", "arch": ["x86_64"]`` entry is present in ``/opt/omnia/input/project_default/software_config.json``.
* Sets up the Pulp container: ``pulp``


Prerequisites
-------------

Ensure that the system time is synchronized across all compute nodes and the OIM. Time mismatch can lead to certificate-related issues during or after the ``prepare_oim.yml`` playbook execution.

Procedure
----------

1. Update the following input files.

   * ``network_spec.yml``: This input file is located in the ``/opt/omnia/input/project_default`` folder and contains the necessary configurations for the cluster network.
   * ``provision_config.yml``: This input file is located in the ``/opt/omnia/input/project_default`` folder and contains the details about provisioning of clusters.
   * ``build_stream_config.yml``: This input file is located in the ``/opt/omnia/input/project_default`` folder and contains the details about the BuildStreamM pipeline.
   * ``storage_config.yml``: This input file is located in the ``/opt/omnia/input/project_default`` folder and contains the details about the storage configuration.

2. After updating the input files, run the ``prepare_oim.yml`` playbook::

    ssh omnia_core
    cd /omnia/prepare_oim
    ansible-playbook prepare_oim.yml

The ``prepare_oim.yml`` playbook deploys the following on the OIM node:

* OpenCHAMI containers
* PostgreSQL database container
* Omnia Auth container
* Pulp container
* BuildStreaM API container (if BuildStreaM is enabled)
* Playbook watcher service (if BuildStreaM is enabled)

.. note:: After ``prepare_oim.yml`` execution, ``ssh omnia_core`` may fail if you switch from a non-root to root user using ``sudo`` command. To avoid this, log in directly as a ``root`` user before executing the playbook or follow the steps mentioned `here <../../KnownIssues/Login.html>`_.

``network_spec.yml``
-------------------

Add necessary inputs to the ``network_spec.yml`` file to configure the network on which the cluster will operate. Use the :ref:`network configuration table <buildstream-tables-network-configuration>` for guidance when configuring these parameters.

.. caution::
    * All provided network ranges and NIC IP addresses should be distinct with no overlap.
    * All iDRACs must be reachable from the OIM.

A sample of the ``network_spec.yml`` where nodes are discovered using a **mapping file** is provided below: ::

    Networks:
    - admin_network:
       oim_nic_name: "eno1"
       netmask_bits: "24"
       primary_oim_admin_ip: "172.16.107.67"
       primary_oim_bmc_ip: "" 
       dynamic_range: "172.16.107.201-172.16.107.250"
       dns: []

.. note:: For more information about configuring Multi-Subnet DHCP, see :doc:`../AdvancedConfigurations/multi-subnet-dhcp/how-to-configuration`.

``provision_config.yml``
-----------------------

Add necessary inputs to the ``provision_config.yml`` file for the provisioning of the cluster. Use the :ref:`provisioning configuration table <buildstream-tables-provisioning-configuration>` for guidance when configuring these parameters.

``build_stream_config.yml``
---------------------------

Add necessary inputs to the ``build_stream_config.yml`` file for the BuildStreaM pipeline. Use the :ref:`BuildStreaM configuration table <buildstream-tables-buildstream-configuration>` for guidance when configuring these parameters.

``storage_config.yml``
----------------------

Add necessary inputs to the ``storage_config.yml`` file for the storage configuration. Use the :ref:`storage configuration table <buildstream-tables-storage-configuration>` for guidance when configuring these parameters. For configuring PowerScale as S3 storage, refer to :ref:`PowerScale S3 configuration <powerscale-s3-config>`.

.. _powerscale-s3-config:

Configure PowerScale as S3 Storage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PowerScale provides scalable, high-performance object storage for the OpenCHAMI image repository. Using PowerScale as S3-compatible storage enables efficient storage and retrieval of boot images across the cluster, with support for HTTP access and robust authentication mechanisms.

This section describes the end-to-end workflow for configuring PowerScale as S3 storage, including enabling the S3 service on PowerScale, obtaining credentials, configuring the ``storage_config.yml`` file, and setting up credentials during the ``prepare_oim`` playbook execution.

.. note::
   * PowerScale cluster must be deployed within the admin subnet and should be accessible from all cluster nodes.
   * Omnia uses HTTP access only when connecting to PowerScale, using the default port 9020.
   * Both S3 and HTTP services are enabled in the S3 bucket configuration.
   * Valid S3 Access Key ID and S3 Secret Access Key for authentication when accessing the PowerScale S3 service.
   * S3 Access Key ID and S3 Secret Access Key are tightly associated with the S3 buckets. You need S3 Access Key ID and S3 Secret Access Key to access the S3 buckets created using the key.

Enable S3 Service on PowerScale
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Log in to the PowerScale OneFS web interface.

2. Navigate to **Protocol** → **Object storage (S3)**.

   .. image:: ../../images/powerscale_s3_enable.png

3. On the **Object Storage (S3)** page, click the **Global Settings** tab.

4. To enable the S3 bucket service, do the following:

   * Select the **Enable S3 service** checkbox.
   * Select the **Enable S3 HTTP** checkbox.

5. Set the HTTP port for S3 (default: 9020).

6. Click **Save** to apply the changes.

Obtain S3 Access ID and Secret Key
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Log in to the PowerScale OneFS web interface.

2. Navigate to **Protocol** → **Object storage (S3)**.

3. On the **Object Storage (S3)** page, click the **My Keys** tab.

.. image:: ../../images/powerscale_s3_my_keys.png

4. On the **Secret key Details** page, click **Create new key**.

5. Ensure to note the **Access ID** and **Secret Key**.

   .. warning::
      The S3 access ID and secret key are required during the OIM credential setup process.

   .. warning::
      Ensure to note down the S3 access ID and secret key as they are tightly associated with the S3 buckets. The cluster nodes cannot access the bootimages without these keys.

Configure storage_config.yml
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Open the ``storage_config.yml`` file available at ``/opt/omnia/input/project_default``.

2. Update the ``s3_configurations`` section with the following parameters. For detailed instructions on updating the ``storage_config.yml`` file, refer to :doc:`../prepare_oim`.

   .. code-block:: yaml

      s3_configurations:
        provider: "powerscale"
        endpoint_url: "http://<powerscale-ip>:<port>"

   Replace ``<powerscale-ip>`` with the actual PowerScale IP address and ``<port>`` with the S3 port (default: 9020).

   **Sample:**

   .. code-block:: yaml

      s3_configurations:
        provider: "powerscale"
        endpoint_url: "http://192.168.1.100:9020"

3. Save the ``storage_config.yml`` file.

Configure Credentials During Prepare OIM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When running the ``prepare_oim`` playbook, you will be prompted for S3 credentials:

1. Run the ``prepare_oim.yml`` playbook as described in :doc:`../prepare_oim`.

2. When prompted, enter the S3 access ID and secret key obtained from PowerScale.

   .. note::
      * For ``powerscale`` provider, the ``s3_access_id`` is prompted as a conditional mandatory parameter.
      * The ``s3_secret_key`` is always prompted during credential setup.

Verification
------------

After successfully running the ``prepare_oim.yml``, you can verify if the ``omnia.target`` and its dependent services are running correctly.

1. Run the following command to check the status of the OMNIA Core service:

   .. code-block:: bash

      systemctl status omnia_core.service

   This command displays whether the ``omnia_core.service`` is active, inactive, or has failed.

2. Check the status of the PostgreSQL database container (if BuildStreaM is enabled).

   .. code-block:: bash

      systemctl status omnia_postgres.service

3. Check the status of the BuildStreaM API container (if BuildStreaM is enabled).

   .. code-block:: bash

      systemctl status omnia_build_stream.service

4. Check the status of the playbook watcher service (if BuildStreaM is enabled).

   .. code-block:: bash

      systemctl status playbook_watcher.service

5. To view the complete list of dependent services for the OMNIA target, run:

   .. code-block:: bash

      systemctl list-dependencies omnia.target

6. Review the status of the dependent services in the following tree output.

   .. note:: The ``prepare_oim.yml`` deploys the following on the OIM node only when BuildStream is enabled on the ``build_stream_config.yml``.

      * PostgreSQL database container
      * BuildStreaM API container
      * Playbook watcher service

   .. code-block:: text

      omnia.target
      ● ├─minio.service
      ● ├─omnia_auth.service
      ● ├─omnia_build_stream.service
      ● ├─omnia_core.service
      ● ├─omnia_postgres.service
      ● ├─playbook_watcher.service
      ● ├─pulp.service
      ● ├─registry.service
      ● ├─network-online.target
      ● │ └─NetworkManager-wait-online.service
      ● └─openchami.target
      ●   ├─acme-deploy.service
      ●   ├─acme-register.service
      ●   ├─bss-init.service
      ●   ├─bss.service
      ●   ├─cloud-init-server.service
      ●   ├─coresmd.service
      ●   ├─haproxy.service
      ●   ├─hydra-gen-jwks.service
      ●   ├─hydra-migrate.service
      ●   ├─hydra.service
      ●   ├─opaal-idp.service
      ●   ├─opaal.service
      ●   ├─openchami-cert-trust.service
      ●   ├─postgres.service
      ●   ├─smd.service
      ●   └─step-ca.service

   * A **green circle** indicates that the service is running.
   * A **grey circle** indicates that the service is not running.
   * A **circle with a cross** indicates that the service failed to start.

   .. note:: The ``omnia_auth.service`` runs only when OpenLDAP is specified in the ``/opt/omnia/input/project_default/software_config.json``.
   .. note:: The ``omnia_build_stream.service``, ``omnia_postgres.service``, and ``playbook_watcher_service`` run only when BuildStreaM is enabled in the ``/opt/omnia/input/project_default/build_stream_config.yml``.
