Omnia Configuration Tables
=========================

This section contains the configuration tables referenced throughout the Omnia documentation.

.. _buildstream-tables-buildstream-configuration:

BuildStreaM Configuration
--------------------------

.. csv-table:: build_stream_config.yml
   :file: Tables/build_stream_config.csv
   :header-rows: 1
   :keepspace:

.. _buildstream-tables-high-availability-configuration:

High Availability Configuration
-------------------------------

.. csv-table:: high_availability_config.yml
   :file: Tables/service_k8s_high_availability.csv
   :header-rows: 1
   :keepspace:

.. _buildstream-tables-local-repository-configuration:

Local Repository Configuration
------------------------------

.. csv-table:: local_repo_config.yml
   :file: Tables/local_repo_config_rhel.csv
   :header-rows: 1
   :keepspace:


.. _buildstream-tables-network-configuration:

Network Configuration
---------------------

.. csv-table:: network_spec.yml
   :file: Tables/network_spec.csv
   :header-rows: 1
   :keepspace:

**Example: additional_subnets configuration**

.. code-block:: yaml

   additional_subnets:
     - subnet: "10.40.1.0"
       netmask_bits: "24"
       router: "10.40.1.1"
       dynamic_range: "10.40.1.100-10.40.1.200"
     - subnet: "10.40.3.0"
       netmask_bits: "24"
       router: "10.40.3.1"
       dynamic_range: "10.40.3.100-10.40.3.200"

.. important::
   Requires coresmd v0.5+ with multi-subnet support and DHCP relay configuration on each subnet's gateway/router.

.. _buildstream-tables-oma-configuration:

Omnia Configuration
-------------------

.. csv-table:: omnia_config.yml
   :file: Tables/omnia_config_service_cluster.csv
   :header-rows: 1
   :keepspace:


.. _buildstream-tables-provisioning-configuration:

Provisioning Configuration
--------------------------

.. csv-table:: provision_config.yml
   :file: Tables/Provision_config.csv
   :header-rows: 1
   :keepspace:


.. _buildstream-tables-security-configuration:

Security Configuration
----------------------

.. csv-table:: security_config.yml
   :file: Tables/security_config.csv
   :header-rows: 1
   :keepspace:


.. _buildstream-tables-storage-configuration:

Storage Configuration
---------------------

.. csv-table:: storage_config.yml
   :file: Tables/storage_config.csv
   :header-rows: 1
   :keepspace:


.. _buildstream-tables-telemetry-configuration:

Telemetry Configuration
-----------------------

.. csv-table:: telemetry_config.yml
   :file: Tables/telemetry_config.csv
   :header-rows: 1
   :keepspace:

.. _buildstream-tables-telemetry-storage-configuration:

Telemetry Storage Configuration
-------------------------------

.. csv-table:: telemetry_storage_config.yml
   :file: Tables/telemetry_storage_config.csv
   :header-rows: 1
   :keepspace:

.. _buildstream-tables-gitlab-configuration:

GitLab Configuration
--------------------

.. csv-table:: gitlab_config.yml
   :file: Tables/build_stream_gitlab_config.csv
   :header-rows: 1
   :keepspace:
