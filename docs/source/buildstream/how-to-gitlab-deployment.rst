.. _how-to-buildstream-gitlab-deployment:

Step 4:  Deploy GitLab for BuildStreaM Integration: Automated Pipeline Execution and Build Monitoring
============================================================================================

GitLab serves as the automation engine for BuildStreaM, providing the pipeline execution framework that processes catalog definitions and orchestrates the build workflows. Deploy GitLab to enable automated pipeline execution, catalog management, image building, and cluster node discovery. This procedure covers GitLab installation, project setup, runner verification, and service validation.

Prerequisites
-------------

Before deploying GitLab for BuildStreaM:

* Ensure that Omnia BuildStreaM container, PostgreSQL container, and Playbook Watcher service are deployed on the OIM node (see :doc:`how-to-prepare-buildstream`)
* Sufficient system resources for GitLab (minimum 4 GB RAM, 2 CPU cores, 20GB free disk space)
* GitLab requires a minimum of 2 CPU cores. More cores may be needed for production workloads.
* Network connectivity for GitLab services

.. important::
   Omnia does not support existing customer GitLab. This procedure deploys a new GitLab instance specifically for BuildStreaM.

Procedure
---------

1. Use SSH to connect to the ``omnia_core`` container.

   .. code-block:: bash

      ssh omnia_core

2. Navigate to ``/opt/omnia/input/project_default/gitlab_config.yml`` and update the following parameters.
    
   .. code-block:: bash

      cat /opt/omnia/input/project_default/gitlab_config.yml

   Use the :ref:`GitLab configuration table <buildstream-tables-gitlab-configuration>` for reference.

3. Navigate to the GitLab directory.

   .. code-block:: bash

      cd /omnia/gitlab

4. Run the ``gitlab.yml`` playbook:

.. code-block:: bash

   ansible-playbook gitlab.yml

This ``gitlab.yml`` playbook installs the following:

- GitLab on the specified host with the specified project name, visibility, and default branch in the ``gitlab_config.yml`` file.
- GitLab runner as a Podman container.
- Adds the project with the following files:
   - **README.MD** - Project documentation
   - **catalog_rhel.json** - Default catalog file
   - **.gitlab-ci.yml** - Pipeline configuration file

.. image:: ../images/buildstream_project.png
   :alt: BuildStream project structure
   
.. note::
   The installation may take 10-15 minutes to complete.

Verification
------------
After the installation of GitLab complete, verify the following:

1. Verify you can access the GitLab project URL.

   .. code-block:: text

      https://<gitlab host ip>/<gitlab project name>

 The project should contain:
  * ``README.MD`` — Project documentation with setup instructions and usage guidelines
  * ``catalog_rhel.json`` — Default catalog file containing build definitions for RHEL images
  * ``.gitlab-ci.yml`` — Pipeline configuration file defining automated build stages and execution steps

2. Verify runner status through GitLab web interface:

   1. Navigate to **Settings** → **CI/CD**.
   2. Expand **Runners** section.
   3. Verify the runner shows a **green** status indicator.
   4. Confirm runner is set to **Running Always** with **Podman Container**.

Next Steps
----------

After completing GitLab deployment, update the catalog file and execute the pipeline. See :doc:`how-to-update-catalog-pipeline`.


Troubleshooting
-----------------
