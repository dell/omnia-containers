.. _how-to-buildstream-update-catalog-pipeline:

Step 5: Update Catalog and Execute Omnia BuildStreaM Pipeline
===============================================================
Update the ``catalog_rhel.json`` file and monitor pipeline execution through GitLab. This procedure covers catalog modifications, automatic pipeline triggering, and verification of pipeline status and job execution.

Prerequisites
-------------

Before updating catalogs and checking pipelines:

* Deploy and Configure BuildStreaM Container on OIM Node (see :doc:`prepare_oim_buildstream`)
* GitLab deployment for BuildStreaM is completed (see :doc:`how-to-gitlab-deployment`)
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
       

5. To trigger the pipeline, commit and push catalog changes.

.. note:: 
   * Currently, BuildStream supports only one catalog file and one pipeline trigger. BuildStream pipeline behaviour is controlled by the GitLab CI/CD configuration in your environment.
   * Each pipeline processes the catalog changes independently and builds the specified images according to the catalog requirements.   

The following image shows the BuildStreaM pipeline is currently running and the stages are being executed:

   .. image:: ../images/buildstream_pipeline_running.png
   
6. Perform the following steps to track the pipeline progress through the GitLab web interface:

      a. Navigate to **Build** → **Pipeline**.
      b. Click on the running pipeline to view details.
      c. Monitor each stage as it progresses:
            - **initialization**: Sets up the build environment.
            - **parse-catalog**: Parses catalog file for build requirements.
            - **generate-input-files**: Generates input files for build.
            - **configure-local-repository**: Configures local repository for artifacts.
            - **build-images**: Builds the specified images.
            - **deploy-and-validate**: Discovers the nodes on which the images need to be deployed.
            - **summary**: Generates summary of pipeline execution.

The following image shows each stage of the BuildStreaM pipeline and its status:
   .. image:: ../images/buildstream_pipeline_stages.png  

   Expected pipeline status indicators:
      - |success| **Green checkmark**: Stage completed successfully
      - |failed| **Red X**: Stage failed (click for error details)
      - |running| **Blue circle**: Stage currently running

.. |success| image:: ../images/Icons/green_check.png
.. |failed| image:: ../images/Icons/red_x.png
.. |running| image:: ../images/Icons/blue_circle.png

The following image shows overall pipeline status:
   .. image:: ../images/buildstream_pipeline_passed.png
      
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

After successful execution of the pipeline, do one of the following:

* Manually PXE boot the nodes to deploy the images. 
* Use the PXE boot utility to deploy the images. See :doc:`set_pxe_boot_order_buildstream` for detailed instructions.
