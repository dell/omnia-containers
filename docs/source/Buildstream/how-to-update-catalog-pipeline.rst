.. _how-to-buildstream-update-catalog-pipeline:

Step 5: Update Catalog and Execute Omnia BuildStreaM Pipeline
====================================================

Update the ``catalog_rhel.json`` file and monitor pipeline execution through GitLab. This procedure covers catalog modifications, automatic pipeline triggering, and verification of pipeline status and job execution.

Prerequisites
-------------

Before updating catalogs and checking pipelines:

* Deploy and Configure BuildStreaM Container on OIM Node (see :doc:`how-to-prepare-buildstream`)
* GitLab deployment for BuildStreaM is completed (see :doc:`how-to-gitlab-deployment`)
* Confirm that you can access GitLab project repository

Procedure
---------

1. Go to the GitLab project URL::

    https://<gitlab host ip>/<gitlab project name>

2. Go to **Code** → **Repository**.
3. Locate the catalog file ``catalog_rhel.json``.
4. Modify the ``catalog_rhel.json`` file to define your build requirements.

.. note:: Ensure that the catalog file is properly updated with valid functional group names, architecture type, OS types and versions and package types. The pipeline will fail if invalid details are provided.

   For the list of supported values:
   - **Functional group names**: See :ref:`functional-groups-section`.
   - **Architecture type**: Supported types include x86_64 and aarch64 (see functional groups in :doc:`composable_roles_buildstream`)
   - **OS type and version**: RHEL 10.0 (see `Supported OS Versions <../OmniaInstallGuide/RHEL_new/RedHat.html#supported-os-versions>`_)
   - **Package types**: rpm, rpm_repo, image, iso, tarball, pip_module
       

5. To trigger the pipeline, commit and push catalog changes.

.. note:: 
   * Pipelines cannot run parallel jobs. If multiple catalog changes are committed and pushed simultaneously, the pipelines will be queued and executed in sequence.
   * Each pipeline processes the catalog changes independently and builds the specified images according to the catalog requirements.   

The following image shows the BuildStream pipeline is currently running and the stages are being executed:

   .. image:: ../images/buildstream_pipeline_running.png
   
6. Perform the following steps to track the pipeline progress through the GitLab web interface:

      a. Navigate to **Build** → **Pipeline**.
      b. Click on the running pipeline to view details.
      c. Monitor each stage as it progresses:
            - **health-check**: Validates system health and prerequisites
            - **API-registration**: Registers API endpoints
            - **token-generation**: Generates authentication tokens
            - **parse-catalog**: Parses catalog file for build requirements
            - **generate-input-files**: Generates input files for build
            - **create-local-repo**: Creates local repository for artifacts
            - **get-roles**: Retrieves required roles for build
            - **build-images**: Builds the specified images
            - **deploy-and-validate**: Deploys and validates the built images

The following image shows each stage of the BuildStream pipeline and its status:
   .. image:: ../images/buildstream_pipeline_stages.png  

   Expected pipeline status indicators:
      - **Green checkmark**: Stage completed successfully
      - **Red X**: Stage failed (click for error details)
      - **Blue circle**: Stage currently running

The following image shows overall pipeline status:
   .. image:: ../images/buildstream_pipeline_passed.png
      
Verification
------------

After the pipeline is completed, you can check the overall pipeline status and job execution.

1. Navigate to **Build** → **Pipelines**
2. Review the job list and status
3. Click on individual jobs to view:
   - Execution logs
   - Resource usage
   - Error messages (if any)

Next Steps
-----------

After successful execution of the pipeline, set the PXE boot order for the nodes and then run the ``set_pxe_boot.yml`` playbook to configure the boot settings. See :doc:`set_pxe_boot_order_buildstream` for detailed instructions.