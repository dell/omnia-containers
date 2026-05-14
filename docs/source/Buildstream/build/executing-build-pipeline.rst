.. _executing-build-pipeline:

Step 5: Execute Build Pipeline
==============================

Update the ``catalog_rhel.json`` file and execute the Omnia BuildStreaM build pipeline through GitLab. This procedure covers catalog modifications, pipeline triggering (automatic and manual), and verification of pipeline status and job execution.

The BuildStream build pipeline automates the creation of diskless images based on catalog specifications. The pipeline consists of four sequential stages:

* **parse-catalog**: Parses and validates the catalog file for build requirements
* **generate-input-files**: Generates input files and configuration data for image building
* **create-local-repository**: Creates and configures the local repository for build artifacts
* **build-image**: Builds the diskless images based on catalog specifications

The build pipeline is automatically triggered when you update the ``catalog_rhel.json`` file in the GitLab repository, or can be manually initiated through the GitLab interface.

Prerequisites
-------------

Before updating catalogs and checking pipelines:

* Deploy and Configure BuildStreaM Container on OIM Node (see :doc:`../setup/preparing-oim-buildstream`)
* GitLab deployment for BuildStreaM is completed (see :doc:`../setup/deploying-gitlab-buildstream`)
* Confirm that you can access GitLab project repository

Procedure
---------

1. Go to the GitLab project URL::

    https://<gitlab_host>:<gitlab_https_port>/root/<gitlab_project_name>

2. Go to **Code** → **Repository**.
3. Locate the catalog file ``catalog_rhel.json``.
4. Modify the ``catalog_rhel.json`` file to define your build requirements.

.. note:: Ensure that the catalog file is updated with valid functional group names, architecture types, operating system types and versions, and package types. The pipeline fails if invalid details are provided.

   The following are the supported values:
      - **Functional group names**: For supported functional group names, see :ref:`functional-groups-section`.
      - **Architecture type**: ``x86_64`` and ``aarch64``.
      - **OS type**: ``RHEL``, see :ref:`supported OS types and versions <redhat-support-matrix>`.
      - **OS version**: ``10.0``, see :ref:`supported OS types and versions <redhat-support-matrix>`.
      - **Package types**: ``rpm``, ``rpm_repo``, ``image``, ``iso``, ``tarball``, ``pip_module``, ``git``, ``manifest``.

5. Trigger the build pipeline by committing and pushing the catalog changes. The pipeline triggers automatically when catalog changes are committed.

   .. image:: ../../../../images/buildstream-build-trigger.png
      :alt: BuildStreaM Build Trigger

6. Monitor the pipeline progress to ensure it completes successfully. See :ref:`Monitor Pipeline Progress <monitor-pipeline-progress>` for detailed instructions.

   .. image:: ../../../../images/buildstream-buid-success.png
      :alt: BuildStreaM Pipeline Execution

.. note:: 
   * Currently, BuildStreaM supports only one catalog file and one pipeline trigger. BuildStreaM pipeline behaviour is controlled by the GitLab CI/CD configuration in your environment.
   * Each pipeline processes the catalog changes independently and builds the specified images according to the catalog requirements.   
   * If the pipeline fails, you can use the manual retry procedure to update input parameters and retry the pipeline.

Manual Pipeline Retry After Failure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the build pipeline fails, you can update the input parameters in the input files and manually retry the pipeline. 

Procedure
---------

#. Identify the failure reason by reviewing the pipeline logs in GitLab.

   a. Navigate to **Build** → **Pipelines**.
   
   b. Click on the failed pipeline.
   
   c. Click on the failed stage to view error logs.

#. Update the input configuration files in the GitLab repository. 
   
   a. Navigate to the ``input/`` folder in the GitLab repository.
   
   b. Edit the relevant configuration file.      
  
   c. Commit and push the changes.

   For detailed descriptions of the configuration parameters in the configuration files, see :doc:`../../../reference/buildstream/configuration-tables`.

#. Manually trigger the pipeline with the updated parameters.

   a. Navigate to **Build** → **Pipelines**.
   
   b. Click **New Pipeline**.
   
   c. In the **Run new pipeline** dialog box, enter the variable name as **PIPELINE_TYPE** and enter the value as **build**.

   .. image:: ../../../../images/gitlab-build-manual-config.png
      :alt: GitLab Build Manual Configuration

   d. Click **Run Pipeline** to execute the build pipeline.

#. Monitor the pipeline progress to ensure it completes successfully. See :ref:`Monitor Pipeline Progress <monitor-pipeline-progress>` for detailed instructions.

For troubleshooting common pipeline issues, see :doc:`../../../troubleshooting/buildstream/common-pipeline-issues`.

.. _monitor-pipeline-progress:

Monitor Pipeline Progress
~~~~~~~~~~~~~~~~~~~~~~~~~

Monitor the build pipeline progress through the GitLab web interface to track stage execution and identify any issues.

1. Navigate to **Build** → **Pipeline**.
   
2. Click on the running pipeline to view details.
   
3. Monitor each stage as it progresses:
     - **parse-catalog**: Parses and validates the catalog file for build requirements
     - **create-local-repository**: Creates and configures the local repository for build artifacts
     - **generate-input-files**: Generates input files and configuration data for image building
     - **build-image**: Builds the diskless images based on catalog specifications

4. Review the stage status indicators:
     - |success| **Green checkmark**: Stage completed successfully
     - |failed| **Red X**: Stage failed (click for error details)
     - |running| **Blue circle**: Stage currently running

5. If any stage fails, review the error logs by clicking on the failed job.

.. |success| image:: ../../../../images/Icons/green_check.png
.. |failed| image:: ../../../../images/Icons/red_x.png
.. |running| image:: ../../../../images/Icons/blue_circle.png

The following image shows the BuildStreaM pipeline is currently running and the stages are being executed:

.. note::
   The build pipeline uses the catalog file to determine which images to build based on functional group assignments.

Verification
------------

After the pipeline is completed, you can check the overall pipeline status and job execution.

1. Navigate to **Build** → **Pipelines**
2. Review the job list and status.

3. Click on individual jobs to view:
      - Execution logs
      - Resource usage
      - Error messages (if any)

Next Steps
-----------

After successful execution of the build pipeline, proceed with deploying the images to cluster nodes. See :doc:`../deploy/executing-deploy-pipeline` for detailed instructions on executing the deploy pipeline.
