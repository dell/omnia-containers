.. _performing-cleanup-operations:

Perform Cleanup Operations
============================

BuildStream supports a maximum of 50 build images. When the build image count exceeds this limit, you must manually perform cleanup operations to remove old images before creating new ones.

.. note:: Do not cancel a running GitLab pipeline or stage. Cancellation prevents some pipeline steps from executing, which leaves the BuildStreaM job in an intermediate, inconsistent state. Note that backend BuildStreaM tasks already in progress will continue running to completion regardless of the cancellation.

Prerequisites
------------

Before performing cleanup operations, ensure the following:

* You have administrative access to the OIM
* BuildStream API server is running
* PostgreSQL database is accessible

Procedure
---------

1. Navigate to the GitLab project URL::

    https://<gitlab_host>:<gitlab_https_port>/root/<gitlab_project_name>

2. Navigate to **Build** → **Pipelines**.

3. Click **New Pipeline**.

4. In the **Run new pipeline** dialog box, enter the variable name as **PIPELINE_TYPE** and enter the value as **cleanup**.

.. image:: ../../images/gitlab-clean-pipeline-variable.png
    :alt: GitLab Clean Pipeline Variable

5. Click **Run Pipeline** to execute the cleanup pipeline.
 
6. In the pipeline, select the image to be cleaned up from the `select_image` stage.

    .. image:: ../../images/gitlab-clean-select-image.png
    :alt: GitLab Clean Select Image

7. Click the **Run Stage** button on the cleanup stage to execute the cleanup.

    .. image:: ../../images/gitlab-clean-run-stage.png
        :alt: GitLab Clean Run Stage

8. Monitor the pipeline progress through the GitLab web interface:

   a. Click on the running pipeline to view details.
   
   b. Monitor the cleanup stage as it progresses to completion.

   .. image:: ../../images/gitlab-clean-monitor-pipeline.png
       :alt: GitLab Clean Monitor Pipeline
 
8. Review the stage status indicators:
    - |success| **Green checkmark**: Stage completed successfully
    - |failed| **Red X**: Stage failed (click for error details)
    - |running| **Blue circle**: Stage currently running

.. |success| image:: ../../images/Icons/green_check.png
.. |failed| image:: ../../images/Icons/red_x.png
.. |running| image:: ../../images/Icons/blue_circle.png

Verification
------------

#. Check the GitLab pipeline status to ensure the cleanup stage passed.

#. Verify the Image Group count is within the configured retention limit.

#. Review the cleanup pipeline logs in GitLab for specific details about which Image Groups were removed.

Related Topics
--------------

* :doc:`../management/retrying-pipelines` - Retry Pipeline Operations
* :doc:`../reference/configuration-tables` - Configuration Reference