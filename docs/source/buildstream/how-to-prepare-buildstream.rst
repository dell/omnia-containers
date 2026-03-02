.. _how-to-buildstream-prepare:

Deploy and Configure BuildStreaM Container on OIM Node
=======================================================

Set up and configure BuildStreaM container on OIM node for automated build and deploymentworkflows. This comprehensive procedure covers prerequisites, enabling BuildStreaM services, configuring BuildStreaM credentials, and ensuring proper PXE mapping setup.

Prerequisites
-------------

Before beginning the BuildStreaM setup:

* Ensure that Omnia core container is upgraded to Omnia 2.1.0.0 or later.
* Administrator access on the Omnia Infrastructure Manager (OIM) node
* Minimum 4 GB RAM and 2 CPU cores for BuildStreaM services
* 10 GB free disk space for BuildStreaM data and logs

.. important::
   BuildStreaM requires a separate PostgreSQL database for storing transaction details and job metadata.

Procedure
---------

1. Use SSH to connect to the ``omnia_core`` container.

.. code-block:: bash

   ssh omnia_core

2. Ensure that ``enable_build_stream`` parameter is set to true in build_stream_config.yml and other BuildstreaM parameters are configured as per your requirements. For more information about preparing OIM, see :doc:`../OmniaInstallGuide/RHEL_new/prepare_oim`.

3. Ensure that ``build_stream_oauth_credential.yml`` is updated with the required BuildStreaM OAuth credentials. For more details on configuration of BuildStreaM OAuth credentials, see :doc:`../OmniaInstallGuide/RHEL_new/credentials_utility`.

4. Ensure that the PXE mapping file is updated with the required node information. For more details on adding node information to the PXE mapping file, see :doc:`../OmniaInstallGuide/RHEL_new/composable_roles`.

5. Execute the ``prepare_oim.yaml`` playbook to create and deploy BuildStreaM container on the OIM node:

   .. code-block:: bash

      cd /opt/omnia/playbooks
      ansible-playbook prepare_oim.yml

   This playbook deploys the following containers on the OIM node:
   - BuildStreaM API container
   - PostgreSQL database container

   The BuildStream API container can now process catalog files and execute build workflows through the automated pipeline system.

 
Verification
-------------

1 Run the following command to the complete list of dependendent services for the Omnia target.

.. code-block:: bash

  systemctl list-dependencies omnia.target

2. Check the status of the BuildStreaM API container.

.. code-block:: bash

  systemctl status omnia_build_stream.service

3. Check the status of the PostgreSQL database container.

.. code-block:: bash

  systemctl status omnia_postgresql.service

* A green circle indicates that the service is running.
* A grey circle indicates that the service is not running.
* A circle with a cross indicates that the service failed to start

Next Steps
----------

After completing the BuildStreaM configuration, deploy GitLab for BuildStreaM pipeline integration.

