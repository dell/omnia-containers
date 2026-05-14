.. _executing-deploy-pipeline:

Step 6: Execute Deploy Pipeline
===============================

Execute the BuildStream deploy pipeline to deploy images to cluster nodes. This procedure covers the three deploy stages: deploy, restart, and validate.

The BuildStream deploy pipeline automates the deployment of built images to target cluster nodes. The pipeline consists of three sequential stages:

* **deploy**: Deploys the built images to the target nodes
* **restart**: Restarts the nodes to load the deployed images
* **validate**: Executes Molecule-based infrastructure tests to verify cluster deployment, network connectivity, and service health

The deploy pipeline is automatically triggered when you update the PXE mapping file (``pxe_mapping_file.csv``) in the GitLab repository, or can be manually initiated through the GitLab interface.

Prerequisites
------------

Before executing the deploy pipeline, ensure the following:

* Build pipeline has completed successfully and images are available
* Target nodes are powered on and accessible via BMC
* PXE mapping file (``pxe_mapping_file.csv``) is correctly configured with target node information
* PXE mapping file is present in the GitLab repository ``input/`` folder for automatic triggering
* GitLab project is accessible and the runner is active
* BuildStream API server is reachable from the GitLab node

Procedure
---------

#. Navigate to the GitLab project URL::

    https://<gitlab_host>:<gitlab_https_port>/root/<gitlab_project_name>

#. Trigger the deploy pipeline by updating the ``pxe_mapping_file.csv`` file in the GitLab repository and committing the changes. 

      .. image:: ../../images/gitlab-deploy-trigger.png
         :alt: GitLab Deploy Trigger

.. note:: If the pipeline fails, you can use the manual retry procedure to update input parameters and retry the pipeline.

#. In the deploy pipeline, select the image from the ``select_image`` stage.

      .. image:: ../../images/gitlab-deploy-select-image.png
         :alt: GitLab Deploy Select Image

#. After selecting the image, click the "Play" button to start the pipeline.

      .. image:: ../../images/gitlab-deploy-play.png
         :alt: GitLab Deploy Play

#. Monitor the pipeline progress to ensure it completes successfully. See :ref:`Monitor Deploy Pipeline Progress <monitor-deploy-pipeline-progress>` for detailed instructions.

Manual Pipeline Retry After Failure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the deploy pipeline fails, you can update the input parameters in the input files and manually retry the pipeline. Use this procedure when you need to modify configuration parameters after a pipeline failure.


Procedure 
~~~~~~~~~~

#. Identify the failure reason by reviewing the pipeline logs in GitLab.

   a. Navigate to **Build** → **Pipelines**.
   
   b. Click on the failed pipeline.
   
   c. Click on the failed stage to view error logs.

#. Update the input parameters in the GitLab repository.

   a. Navigate to the ``input/`` folder in the GitLab repository.
   
   b. Edit the relevant configuration file. For detailed parameter descriptions, see :doc:`../reference/configuration-tables`.
   
   c. Commit and push the changes.

#. Manually trigger the pipeline with the updated parameters.

   a. Navigate to **Build** → **Pipelines**.
   
   b. Click **New Pipeline**.
   
   c.  In the **Run new pipeline** dialog box, enter the variable name as **PIPELINE_TYPE** and enter the value as **deploy**.

    .. image:: ../../images/gitlab-deploy-manual-config.png
       :alt: GitLab Deploy Manual Configuration

   d. Click **Run Pipeline** to execute the deploy pipeline.

#. Monitor the pipeline progress to ensure it completes successfully.  See :ref:`Monitor Deploy Pipeline Progress <monitor-deploy-pipeline-progress>` for detailed instructions.


   .. image:: ../../images/gitlab-deploy-success.png
      :alt: GitLab Deploy Success

.. note::
   When using manual retry, ensure that only the necessary parameters are updated. Unnecessary changes may cause additional pipeline failures.

For troubleshooting common pipeline issues, see :doc:`../troubleshooting/common-pipeline-issues`.

.. _monitor-deploy-pipeline-progress:

Monitor Deploy Pipeline Progress
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Monitor the deploy pipeline progress through the GitLab web interface:

   a. Click on the running pipeline to view details.
   
   b. Monitor each stage as it progresses:

         - **deploy**: Deploys images to target nodes based on catalog specifications
         - **restart**: Restarts nodes to load the deployed images
         - **validate**: Executes Molecule-based infrastructure tests to verify cluster deployment, network connectivity, and service health

#. Review the stage status indicators:
      - |success| **Green checkmark**: Stage completed successfully
      - |failed| **Red X**: Stage failed (click for error details)
      - |running| **Blue circle**: Stage currently running

.. |success| image:: ../../images/Icons/green_check.png
.. |failed| image:: ../../images/Icons/red_x.png
.. |running| image:: ../../images/Icons/blue_circle.png

#. If any stage fails, review the error logs by clicking on the failed job.

.. note::
   The deploy pipeline uses the PXE mapping file to determine which nodes receive which images based on functional group assignments.

Verification
------------

After the deploy pipeline completes, verify the deployment:

#. Check the overall pipeline status in GitLab to ensure all stages passed.

#. Verify that the target nodes have restarted and are accessible.

#. Log in to a sample of deployed nodes to verify the correct image is loaded.

#. Check the BuildStreaM API for deployment status and image group information.

Next Steps
----------

After successful deployment, configure PXE boot for the target nodes to load the deployed images. See :doc:`../management/configuring-pxe-boot`.

