.. _deploying-gitlab-buildstream:

Step 4: Deploy GitLab for BuildStream
======================================

Deploy GitLab as the CI/CD automation engine for BuildStream, providing a three-pipeline architecture for build, deploy, and cleanup operations. This procedure covers GitLab installation, project setup with pipeline configuration files, input folder structure, and runner verification.

BuildStream uses a **three-pipeline architecture** in GitLab:

* **Build Pipeline**: Triggered by catalog/config changes, creates images and establishes Job ID to Image Group ID mapping. This pipeline can also be executed manually.
* **Deploy Pipeline**: Triggered by PXE mapping changes, deploys images to cluster nodes. This pipeline can also be executed manually.
* **Cleanup Pipeline**: Triggered manually, removes old Image Groups based on retention policy.

Prerequisites
-------------

Before deploying GitLab for BuildStreaM:

* Ensure that Omnia BuildStreaM container, PostgreSQL container, and Playbook Watcher service are deployed on the OIM node (see :doc:`preparing-oim-buildstream`)
* The node where GitLab will be deployed must have Internet connectivity.
* A dedicated node is required for BuildStreaM GitLab deployment.
* The node must have sufficient system resources for BuildStreaM (minimum 4 GB RAM, 2 CPU cores, 20 GB free disk space)
* GitLab requires a minimum of 2 CPU cores. More cores may be needed for production workloads.
* OIM node must be accessible from the GitLab node.
* Ensure that BuildStream API server (BuildStream container) is reachable from the GitLab node.
* Ensure that appStream and Base OS repositories are configured and accessible from the GitLab node.
* Ensure that on the GitLab node, SELinux is disabled.

.. important::
   Omnia uses a dedicated GitLab instance for BuildStreaM. This procedure provisions a new GitLab instance specifically configured for BuildStreaM. Currently, existing GitLab setups configured for other purposes are not supported.

Procedure
---------

1. Use SSH to connect to the ``omnia_core`` container.

   .. code-block:: bash

      ssh omnia_core

2. Navigate to ``/opt/omnia/input/project_default/gitlab_config.yml`` and update the ``gitlab_config.yml`` file. Use the :doc:`../reference/configuration-tables` for reference.
    
   .. code-block:: bash

      cat /opt/omnia/input/project_default/gitlab_config.yml

3. Ensure that the BuildStream input configuration files are properly configured in ``/opt/omnia/input/project_default/``. 

   For detailed parameter descriptions, see :doc:`../reference/configuration-tables`.

4. Navigate to the GitLab directory.

   .. code-block:: bash

      cd /omnia/gitlab

5. Run the ``gitlab.yml`` playbook:

   .. code-block:: bash

      ansible-playbook gitlab.yml

6. When it prompts you to enter the GitLab password, enter the password. Note the password as it is required to access the GitLab project and instance.

.. note::
   The installation may take 10-15 minutes to complete.


This ``gitlab.yml`` playbook performs the following tasks:

- Installs the GitLab instance on the host specified in the ``gitlab_config.yml`` file.
- In the GitLab instance, creates a project with the specified name, visibility, and default branch as configured in the ``gitlab_config.yml`` file.
- Installs GitLab runner as a Podman container.
- Generates a self-signed CA certificate for GitLab on the GitLab node at ``/root/gitlab-certs/ca.crt``
- Adds the project with the following files:
  - **Pipeline Configuration Files**:
    - ``.gitlab-ci.yml`` - Parent router pipeline that dispatches to child pipelines
    - ``.gitlab-ci-build.yml`` - Build pipeline for creating images
    - ``.gitlab-ci-deploy.yml`` - Deploy pipeline for deploying images to nodes
    - ``.gitlab-ci-cleanup.yml`` - Cleanup pipeline for removing old Image Groups
    - ``.gitlab-ci-deploy-child-template.yml`` - Dynamic child pipeline template for deploy operations
  - **Catalog File**:
    - ``catalog_rhel.json`` - Default catalog file containing build definitions for RHEL images
  - **Input Folder**:
    - ``input/`` - Directory containing all BuildStream input configuration files

      .. image:: ../../images/buildstream_project.png
      
The input folder includes the following configuration files (see :doc:`../reference/configuration-tables` for detailed parameter descriptions):

   - ``build_stream_config.yml`` — BuildStream configuration file
   - ``gitlab_config.yml`` — GitLab configuration file
   - ``high_availability_config.yml`` — High availability configuration file
   - ``local_repo_config.yml`` — Local repository configuration file
   - ``network_config.yml`` — Network configuration file
   - ``omnia_config.yml`` — Omnia configuration file
   - ``provision_config.yml`` — Provision configuration file
   - ``pxe_mapping_file.csv`` — PXE mapping file
   - ``security_config.yml`` — Security configuration file
   - ``storage_config.yml`` — Storage configuration file
   - ``telemetry_config.yml`` — Telemetry configuration file

      .. image:: ../../images/buildstream_project_input_files.png
            :alt: BuildStream project input files structure
   
7. To avoid **Not Secure** warnings when accessing the GitLab instance, download and import the certificate generated in step 4 to the browser.

Verification
------------
After the installation of GitLab complete, verify the following:

* Verify you can access the GitLab project URL.

   .. code-block:: text

      https://<gitlab_host>:<gitlab_https_port>/root/<gitlab_project_name>

* Verify the project contains the expected files and folders.  
* Verify runner status through GitLab web interface:

   1. Navigate to **Settings** → **CI/CD**.
   2. Expand **Runners** section.
   3. Verify the runner shows a **green** status indicator.
   4. Confirm runner is set to **Running Always** with **Podman Container**.

Next Steps
----------

After completing GitLab deployment, update the catalog file to automatically trigger the build pipeline. See :doc:`../build/executing-build-pipeline`.


