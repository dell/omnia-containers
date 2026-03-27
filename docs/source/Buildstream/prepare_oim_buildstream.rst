.. _prepare-oim-buildstream:

Step 3:  Prepare the Omnia Infrastructure Manager 
========================================================

To enable BuildStreaM functionality, you must prepare the Omnia Infrastructure Manager (OIM) by deploying the required containers and services. This procedure installs the OpenCHAMI containers, BuildStreaM container, Omnia Auth container, Pulp container, and Playbook watcher service that are essential for automated build workflows and cluster management. 

Prerequisites
---------------

Before beginning the BuildStreaM setup:

* Ensure that the Omnia core container is installed with Omnia 2.1.0.0
* Administrator access on the Omnia Infrastructure Manager (OIM) node
* Minimum 4 GB RAM and 2 CPU cores for BuildStreaM services
* 10 GB free disk space for BuildStreaM data and logs
* Ensure that the system time is synchronized across all compute nodes and the OIM. Time mismatch can lead to certificate-related issues during or after the ``prepare_oim.yml`` playbook execution.

.. important::
   BuildStreaM requires a separate PostgreSQL database for storing transaction details and job metadata.

Procedure
------------

1. Update the following input files.

   * ``build_stream_config.yml``: contains the details about the BuildStreaM pipeline.
   * ``gitlab_config.yml``: contains the details about the BuildStreaM GitLab configuration.
   * ``high_availability_config.yml``: contains the details about the high availability configuration.
   * ``local_repo_config.yml``: contains the details about the local repository configuration.
   * ``network_spec.yml``: contains the details about the network configuration.
   * ``omnia_config.yml``: contains the details about the Omnia configuration.
   * ``provision_config.yml``: contains the details about the provision configuration.
   * ``security_config.yml``: contains the details about the security configuration.
   * ``storage_config.yml``: contains the details about the storage configuration.
   * ``telemetry_config.yml``: contains the details about the telemetry configuration.
   * ``user_registry_credential.yml``: contains the details about the user registry credentials.
  
``build_stream_config.yml``
---------------------------

Add necessary inputs to the ``build_stream_config.yml`` file for the BuildStreaM pipeline. Use the :ref:`BuildStreaM configuration table <buildstream-tables-buildstream-configuration>` for guidance when configuring these parameters.

.. note:: Ensure that the ``build_stream_port`` (BuildStreaM port) is correctly configured in the ``build_stream_config.yml`` file.
   The BuildStreaM port cannot be modified after preparing the OIM. To modify the port after preparing the OIM, you need to cleanup the OIM first (using ``cleanup_oim.yml``),
   and then prepare the OIM again with the required port number (using ``prepare_oim.yml``).

``gitlab_config.yml``
-----------------------

Add necessary inputs to the ``gitlab_config.yml`` file for the BuildStreaM GitLab configuration. Use the :ref:`GitLab configuration table <buildstream-tables-gitlab-configuration>` for guidance when configuring these parameters.


``high_availability_config.yml``
--------------------------------

Add necessary inputs to the ``high_availability_config.yml`` file for the high availability configuration. Use the :ref:`high availability configuration table <buildstream-tables-high-availability-configuration>` for guidance when configuring these parameters.

``local_repo_config.yml``
-------------------------

Add necessary inputs to the ``local_repo_config.yml`` file for the local repository configuration. Use the :ref:`local repository configuration table <buildstream-tables-local-repository-configuration>` for guidance when configuring these parameters.


``network_spec.yml``
---------------------
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
          
``omnia_config.yml``
------------------

Add necessary inputs to the ``omnia_config.yml`` file for the OMNIA configuration. Use the :ref:`OMNIA configuration table <buildstream-tables-oma-configuration>` for guidance when configuring these parameters.


``provision_config.yml``
------------------------

Add necessary inputs to the ``provision_config.yml`` file for the provisioning of the cluster. Use the :ref:`provisioning configuration table <buildstream-tables-provisioning-configuration>` for guidance when configuring these parameters.


``security_config.yml``
-----------------------

Add necessary inputs to the ``security_config.yml`` file for the security configuration. Use the :ref:`security configuration table <buildstream-tables-security-configuration>` for guidance when configuring these parameters. 

``storage_config.yml``
----------------------

Add necessary inputs to the ``storage_config.yml`` file for the storage configuration. Use the :ref:`storage configuration table <buildstream-tables-storage-configuration>` for guidance when configuring these parameters. 


``telemetry_config.yml``
------------------------

Add necessary inputs to the ``telemetry_config.yml`` file for the telemetry configuration. Use the :ref:`telemetry configuration table <buildstream-tables-telemetry-configuration>` for guidance when configuring these parameters. 


2. After updating the input files, run the ``prepare_oim.yml`` playbook::

    ssh omnia_core
    cd /omnia/prepare_oim
    ansible-playbook prepare_oim.yml

The ``prepare_oim.yml`` deploys the following on the OIM node:

* OpenCHAMI containers
* PostgreSQL database container
* Omnia Auth container
* Pulp container
* BuildStreaM API container 
* Playbook watcher service

.. note:: After ``prepare_oim.yml`` execution, ``ssh omnia_core`` may fail if you switch from a non-root to root user using ``sudo`` command. To avoid this, log in directly as a ``root`` user before executing the playbook or follow the steps mentioned `here <../KnownIssues/Login.html>`_.

Verification
--------------

After successfully running the ``prepare.oim.yml``, you can verify if the ``omnia.target`` and
its dependent services are running correctly.

1. Run the following command to check the status of the OMNIA Core service:

   .. code-block:: bash

      systemctl status omnia_core.service

   This command displays whether the ``omnia_core.service`` is active, inactive,
   or has failed. 

2. Check the status of the BuildStreaM API container.

.. code-block:: bash

  systemctl status omnia_build_stream.service

3. Check the status of the playbook watcher service.

.. code-block:: bash

  systemctl status playbook_watcher.service

3. Check the status of the PostgreSQL database container.

.. code-block:: bash

  systemctl status omnia_postgres.service

4. To view the complete list of dependent services for the OMNIA target, run:

   .. code-block:: bash

      systemctl list-dependencies omnia.target

5. Review the status of the dependent services in the following tree output. 

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

   .. note::  The ``omnia_auth.service`` runs only when OpenLDAP is specified in the ``/opt/omnia/input/project_default/software_config.json``.
   .. note::  The ``omnia_build_stream.service``, ``omnia_postgres.service``, and ``playbook_watcher_service`` run only when BuildStreaM is enabled in the ``/opt/omnia/input/project_default/build_stream_config.yml``.
    

View Usage Instructions for OpenCHAMI Containers
--------------------------------------------------

The ``ochami --help`` command provides usage instructions for interacting with **OpenCHAMI services**.  
The help menu lists the supported commands you can use for node discovery, provisioning, and service management.

1. Access the OpenCHAMI container via Podman.

2. On the Omnia Infrastructure Manager (OIM), run the following command::

       ochami --help

The help menu includes:

* ``bss``: Communicate with the Boot Script Service (BSS).
* ``cloud-init``: Interact with the cloud-init service.
* ``completion``: Generate the autocompletion script for the specified shell.
* ``config``: View or modify configuration options.
* ``discover``: Perform static or dynamic discovery of nodes.
* ``pcs``: Interact with the Power Control Service (PCS).
* ``smd``: Communicate with the State Management Database (SMD).
* ``version``: Display detailed version information and exit.
* ``help``: Display help for a specific command.

For more details about a specific command, run::

   ochami [command] --help


