.. _how-to-buildstream-prepare:

Configure BuildStreaM Settings
===============================

Set up and configure BuildStreaM for automated build and deploymentworkflows. This comprehensive procedure covers prerequisites, enabling BuildStreaM services, configuring BuildStreaM credentials, and ensuring proper PXE mapping setup.

.. contents:: On This Page
   :local:
   :depth: 2

Prerequisites
-------------

Before beginning the BuildStreaM setup:

* Omnia 2.1.0.0 or later with core container 1.1 running
* Administrator access on the Omnia Infrastructure Manager (OIM) node
* PostgreSQL 12 or later for BuildStreaM database
* Network connectivity for external integrations
* Minimum 4 GB RAM and 2 CPU cores for BuildStreaM services
* 10 GB free disk space for BuildStreaM data and logs
* SSH access to omnia_core node for configuration

.. important::
   BuildStreaM requires a separate PostgreSQL database for storing transaction details and job metadata.

Procedure
---------

1. Use SSH to connect to the ``omnia_core`` container.

.. code-block:: bash

   ssh omnia_core

2. Ensure that ``enable_build_stream`` parameter is set to true in build_stream_config.yml and other BuildstreaM parameters are connfigured as per your requirements.

3. Ensure that build_stream_oauth_credential.yml is updated with the required buildstream oauth credentials.

4. Ensure that the PXE mapping file is updated with the required node information.

5. Execute the ``prepare_oim.yaml`` playbook to create BuildStreaM containers:

   .. code-block:: bash

      cd /opt/omnia/playbooks
      ansible-playbook prepare_oim.yml

   This creates:
   - BuildStreaM API container
   - PostgreSQL database container

   The BuildStream API container can now process catalog files and execute build workflows through the automated pipeline system.

 
Verification
-------------

Check that all BuildStreaM services are running:

.. code-block:: bash

   podman ps | grep buildstream

Expected output shows running containers:

.. code-block:: text

   buildstream-api      Up   2 minutes ago
   buildstream-db       Up   2 minutes ago
   buildstream-runner   Up   2 minutes ago

Next Steps
----------

After completing the BuildStreaM configuration:

* **Deploy GitLab** - Install and configure GitLab for pipeline execution
* **Create initial catalog** - Define your first build catalog
* **Test pipeline execution** - Verify end-to-end workflow

