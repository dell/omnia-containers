Update the Input Parameters for Discovering the Nodes
========================================================

Specify the required parameters in the following input files: 

 * ``/opt/omnia/input/project_default/provision_config.yml``
 * ``/opt/omnia/input/project_default/omnia_config_credentials.yml``
 * ``/opt/omnia/input/project_default/software_config.json``
 * ``/opt/omnia/input/project_default/storage_config.yml``
 * ``/opt/omnia/input/project_default/omnia_config.yml``
 * ``/opt/omnia/input/project_default/telemetry_config.yml``

.. caution:: Do not remove or comment any lines in the above mentioned ``.yml`` files.

.. csv-table:: provision_config.yml
   :file: ../../../Tables/Provision_config.csv
   :header-rows: 1
   :keepspace:

.. [1] Boolean parameters do not need to be passed with double or single quotes.

.. note::

    The ``/opt/omnia/input/project_default/omnia_config_credentials.yml`` file is encrypted on the first execution of the ``discovery.yml`` or ``local_repo.yml`` playbooks.

      * To view the encrypted parameters: ::

          ansible-vault view omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key

      * To edit the encrypted parameters: ::

          ansible-vault edit omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key
      
      * If user is decrypting the file, then it must be encrypted again: ::

          ansible-vault encrypt omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key
      
.. csv-table:: software_config.json
   :file: ../../../Tables/software_config_rhel.csv
   :header-rows: 1
   :keepspace:



.. csv-table:: storage_config.yml
   :file: ../../../Tables/storage_config.csv
   :header-rows: 1
   :keepspace:

.. note::  
   
    When PowerScale is configured as an NFS server, ensure that the following CSI-PowerScale driver entry is present in the ``software_config.json`` file::

     {"name": "csi_driver_powerscale", "version": "v2.15.0", "arch": ["x86_64"]}

    For more information on deploying the Dell CSI-PowerScale driver, see `Deploy CSI drivers for Dell PowerScale Storage Solutions <../../AdvancedConfigurations/PowerScale_CSI.html>`_.


The following table lists the parameters that must be configured in ``omnia_config.yml`` for slurm cluster.

.. csv-table:: omnia_config.yml
   :file: ../../../Tables/scheduler_slurm.csv
   :header-rows: 1
   :keepspace:

The following table lists the parameters that must be configured in ``omnia_config.yml`` for service Kubernetes cluster.

.. csv-table:: omnia_config.yml
   :file: ../../../Tables/omnia_config_service_cluster.csv
   :header-rows: 1
   :keepspace:


.. csv-table:: network_spec.yml
   :file: ../../../Tables/network_spec.csv
   :header-rows: 1
   :keepspace:


.. csv-table:: telemetry_config.yml
   :file: ../../../Tables/telemetry_config.csv
   :header-rows: 1
   :keepspace:


.. caution::
    * All provided network ranges and NIC IP addresses should be distinct with no overlap in the ``/opt/omnia/input/project_default/network_spec.yml``.
    * Ensure that all the iDRACs are reachable from the OIM.

A sample of the ``/opt/omnia/input/project_default/network_spec.yml`` where nodes are discovered using a mapping file is provided below: ::

    
   Networks:
   - admin_network:
      oim_nic_name: "eno1"
      netmask_bits: "24"
      primary_oim_admin_ip: "172.16.107.254"
      primary_oim_bmc_ip: "" 
      dynamic_range: "172.16.107.201-172.16.107.250"
      dns: []