Step 7: Verify the Status of Omnia Core Container Services
===========================================================

After successfully running the ``prepare.oim.yml``, you can verify if the ``omnia.target`` and
its dependent services are running correctly.

1. Run the following command to check the status of the OMNIA Core service:

   .. code-block:: bash

      systemctl status omnia_core.service

   This command displays whether the ``omnia_core.service`` is active, inactive,
   or has failed. 

2. To view the complete list of dependent services for the OMNIA target, run:

   .. code-block:: bash

      systemctl list-dependencies omnia.target

3. Review the status of the dependent services in the following tree output. 

   .. code-block:: text

      omnia.target
      ● ├─minio.service
      ● ├─omnia_auth.service
      ● ├─omnia_build_stream.service
      ● ├─omnia_core.service
      ● ├─omnia_postgres.service
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
   .. note::  The ``omnia_build_stream.service`` and ``omnia_postgres.service`` run only when BuildStreaM is enabled in the ``/opt/omnia/input/project_default/build_stream_config.yml``.
    

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

