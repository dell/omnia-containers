Step 5:  Prepare the OIM
========================================================

The ``prepare_oim.yml`` playbook is used to prepare the Omnia Infrastructure Manager (OIM). The playbook performs the following on the OIM:

* Sets up the OpenCHAMI containers.
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

1. ``network_spec.yml``
------------------------

Add necessary inputs to the ``network_spec.yml`` file to configure the network on which the cluster will operate. Use the below table as reference while doing so:

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

Add necessary inputs to the ``provision_config.yml`` file for the provisioning of the cluster. Use the below table as reference while doing so:

.. csv-table:: provision_config.yml
   :file: ../../Tables/Provision_config.csv
   :header-rows: 1
   :keepspace:


Playbook Execution
-------------------

After you have filled in the input files as mentioned above, execute the following commands to trigger the playbook: ::

    ssh omnia_core
    cd /omnia/prepare_oim
    ansible-playbook prepare_oim.yml

.. note:: After ``prepare_oim.yml`` execution, ``ssh omnia_core`` may fail if you switch from a non-root to root user using ``sudo`` command. To avoid this, log in directly as a ``root`` user before executing the playbook or follow the steps mentioned `here <../../Troubleshooting/KnownIssues/Common/Login.html>`_.
