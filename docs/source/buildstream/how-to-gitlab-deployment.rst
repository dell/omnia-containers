.. _how-to-buildstream-gitlab-deployment:

GitLab Deployment for BuildStreaM
==================================

Deploy GitLab as part of BuildStreaM integration to enable automated pipeline execution, catalog management, and build monitoring. This procedure covers GitLab installation, project setup, runner verification, and service validation.

Prerequisites
-------------

Before deploying GitLab for BuildStreaM:

* BuildStreaM configuration completed (see :doc:`how-to-prepare-buildstream`)
* prepare.yaml playbook completed successfully
* Sufficient system resources for GitLab (minimum 4 GB RAM, 2 CPU cores)
* Network connectivity for GitLab services
* Administrator access on the target server

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

   The configuration should include:

   .. code-block:: yaml

      # Project settings
      # Name of the GitLab project Omnia will create/manage
      gitlab_project_name: "omnia-catalog"
      # Visibility options: private | internal | public
      gitlab_project_visibility: "private"
      # Default branch used for repository and API operations
      gitlab_default_branch: "main"

3. Navigate to the GitLab directory.

   .. code-block:: bash

      cd /omnia/build_stream/gitlab

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

5. Check that GitLab is running and accessible:

.. code-block:: bash

   curl -I https://gitlab.example.com

Expected response shows GitLab is accessible:

.. code-block:: text

   HTTP/1.1 200 OK
   Server: nginx
   Date: Wed, 01 Mar 2026 12:00:00 GMT

6. Verify you can access the GitLab project URL.

Navigate to the GitLab project URL to verify project creation:

.. code-block:: text

   https://gitlab.example.com/omnia-catalog

The project should contain:
- **README.MD** - Project documentation
- **catalog_rhel.json** - Default catalog file
- **.gitlab-ci.yml** - Pipeline configuration file

7. Verify GitLab runner status.

Check that the GitLab runner is running as a Podman container:

.. code-block:: bash

   podman ps | grep gitlab-runner

Expected output shows the runner container:

.. code-block:: text

   gitlab-runner      Up   5 minutes ago

Alternatively, verify runner status through GitLab web interface:

   1. Navigate to **Settings** → **CI/CD**
   2. Expand **Runners** section
   3. Verify the runner shows a **green** status indicator
   4. Confirm runner is set to **Running Always** with **Podman Container**

Next Steps
----------

After completing GitLab deployment:

* **Update catalog files** - Modify catalog_rhel.json to define your build requirements
* **Trigger first pipeline** - Make catalog changes to test automated pipeline execution
