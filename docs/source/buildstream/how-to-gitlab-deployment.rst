.. _how-to-buildstream-gitlab-deployment:

Step 4:  Deploy GitLab for BuildStreaM Integration: Automated Pipeline Execution and Build Monitoring
============================================================================================

Deploy GitLab as part of BuildStreaM integration to enable automated pipeline execution, catalog management, build images, and discover cluster nodes. This procedure covers GitLab installation, project setup, runner verification, and service validation.

Prerequisites
-------------

Before deploying GitLab for BuildStreaM:

* Ensure that Omnia BuildStreaM container, PostgreSQL container, and Playbook Watcher service are deployed on the OIM node (see :doc:`how-to-prepare-buildstream`)
* Sufficient system resources for GitLab (minimum 4 GB RAM, 2 CPU cores)
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

   .. csv-table:: gitlab_config.yml
   :file: ../../Tables/build_stream_gitlab_config.csv 
   :header-rows: 1
   :keepspace:

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
   
.. note::
   The installation may take 10-15 minutes to complete.

Verification
------------
After the installation of GitLab complete, verify the following:

1. Verify you can access the GitLab project URL.

   .. code-block:: text

      https://<gitlab host ip>/<gitlap project name>

 The project should contain:
  * **README.MD** - Project documentation
  * **catalog_rhel.json** - Default catalog file
  * **.gitlab-ci.yml** - Pipeline configuration file

2. Verify runner status through GitLab web interface:

   1. Navigate to **Settings** → **CI/CD**.
   2. Expand **Runners** section.
   3. Verify the runner shows a **green** status indicator.
   4. Confirm runner is set to **Running Always** with **Podman Container**.

Next Steps
----------

After completing GitLab deployment, update the catalog file and execute the pipeline. See :doc:`how-to-update-catalog-pipeline`.
