Step 5:  Prepare the OIM
========================================================

The ``prepare_oim.yml`` playbook is used to prepare the Omnia Infrastructure Manager (OIM). The playbook performs the following on the OIM:

* Sets up the OpenCHAMI containers.
* Sets up the BuildStreamM container if BuildStreaM is enabled in ``/opt/omnia/input/project_default/build_stream_config.yml``.
* Sets up the Omnia Auth container if ``"name": "openldap", "arch": ["x86_64"]`` entry is present in ``/opt/omnia/input/project_default/software_config.json``.
* Sets up the Pulp container: ``pulp``


Prerequisite
----------------

Ensure that the system time is synchronized across all compute nodes and the OIM. Time mismatch can lead to certificate-related issues during or after the ``prepare_oim.yml`` playbook execution.

Input files for the playbook
------------------------------

The ``prepare_oim.yml`` playbook is dependent on the inputs provided to the following input files:

* ``network_spec.yml``: This input file is located in the ``/opt/omnia/input/project_default`` folder and contains the necessary configurations for the cluster network.
* ``provision_config.yml``: This input file is located in the ``/opt/omnia/input/project_default`` folder and contains the details about provisioning of clusters.
* ``build_stream_config.yml``: This input file is located in the ``/opt/omnia/input/project_default`` folder and contains the details about the BuildStreamM pipeline.

1. ``network_spec.yml``
------------------------

Add necessary inputs to the ``network_spec.yml`` file to configure the network on which the cluster will operate. Refer to the table below for the required fields:

.. csv-table:: network_spec.yml
   :file: ../../Tables/network_spec.csv
   :header-rows: 1
   :keepspace:

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
          
     
2. ``provision_config.yml``
-------------------------------

Add necessary inputs to the ``provision_config.yml`` file for the provisioning of the cluster. Refer to the table below for the required fields:

.. csv-table:: provision_config.yml
   :file: ../../Tables/Provision_config.csv
   :header-rows: 1
   :keepspace:

3. ``build_stream_config.yml``
-------------------------------

Add necessary inputs to the ``build_stream_config.yml`` file for the BuildStreamMpipeline. Refer to the table below for the required fields:

.. csv-table:: build_stream_config.yml
   :file: ../../Tables/build_stream_config.csv
   :header-rows: 1
   :keepspace:

4. ``storage_config.yml``
--------------------------

Add necessary inputs to the ``storage_config.yml`` file for the storage configuration. Refer to the table below for the required fields:

.. note::
   For detailed instructions on configuring PowerScale as S3 storage, see :ref:`PowerScale S3 configuration <powerscale-s3-config>`.

.. csv-table:: storage_config.yml
   :file: ../../Tables/storage_config.csv
   :header-rows: 1
   :keepspace:


Playbook Execution
-------------------

After you have filled in the input files as mentioned above, execute the following commands to trigger the playbook: ::

    ssh omnia_core
    cd /omnia/prepare_oim
    ansible-playbook prepare_oim.yml

.. note:: After ``prepare_oim.yml`` execution, ``ssh omnia_core`` may fail if you switch from a non-root to root user using ``sudo`` command. To avoid this, log in directly as a ``root`` user before executing the playbook or follow the steps mentioned `here <../../Troubleshooting/KnownIssues/Common/Login.html>`_.


.. _powerscale-s3-config:

Configure PowerScale as S3 Storage
-----------------------------------

PowerScale provides scalable, high-performance object storage for the OpenCHAMI image repository. Using PowerScale as S3-compatible storage enables efficient storage and retrieval of boot images across the cluster, with support for HTTP access and robust authentication mechanisms.

This section describes the end-to-end workflow for configuring PowerScale as S3 storage, including enabling the S3 service on PowerScale, obtaining credentials, configuring the ``storage_config.yml`` file, and setting up credentials during the ``prepare_oim`` playbook execution.

.. note::
   * PowerScale cluster must be deployed within the admin subnet and should be accessible from all cluster nodes.
   * Omnia uses HTTP access only when connecting to PowerScale, using the default port 9020.
   * Both S3 and HTTP services are enabled in the S3 bucket configuration.
   * Valid S3 Access Key ID and S3 Secret Access Key for authentication when accessing the PowerScale S3 service.
   * S3 Access Key ID and S3 Secret Access Key are tightly associated with the S3 buckets. You need S3 Access Key ID and S3 Secret Access Key to access the S3 buckets created using the key.


Enable S3 Service on PowerScale
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When running the ``prepare_oim`` playbook, you will be prompted for S3 credentials:

1. Run the ``prepare_oim.yml`` playbook as described in :doc:`../prepare_oim`.   

2. When prompted, enter the S3 access ID and secret key obtained from PowerScale.

   .. note::
      * For ``powerscale`` provider, the ``s3_access_id`` is prompted as a conditional mandatory parameter.
      * The ``s3_secret_key`` is always prompted during credential setup.

