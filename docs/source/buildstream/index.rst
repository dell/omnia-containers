.. _concept-buildstream-overview:

Automate with BuildStreaM
==========================
Omnia BuildStreaM provides a comprehensive automation solution for managing infrastructure build workflows. It uses a catalog-driven approach where you define your build requirements in a structured catalog file, and BuildStreaM executes automated pipelines to create and deploy images according to your specifications.

BuildStreaM addresses the key challenges in HPC cluster image management:

   - **Automation**: Eliminates manual build and deployment processes
   - **Integration**: Works seamlessly with existing Omnia deployments
   - **Traceability**: Provides complete audit trails for all build operations
   
To build your own custom workflows, you can use the BuildStreaM REST API. The BuildStreaM API documentation is available at `Omnia BuildStreaM API Documentation <https://developer.dell.com/apis/ea677050-f49b-49e1-a4b9-1cdd563415d9/versions/2.1.0/docs/Introduction.md>`_.

Perform the following steps to configure BuildStreaM for automated pipeline execution to create and deploy images:

1. Deploy and Configure BuildStreaM Container on OIM Node (see :doc:`how-to-prepare-buildstream`)
2. Deploy GitLab for BuildStreaM Integration: Automated Pipeline Execution and Build Monitoring (see :doc:`how-to-gitlab-deployment`)
3. Update the catalog file and execute the pipeline (see :doc:`how-to-update-catalog-pipeline`)

.. toctree::
   :maxdepth: 2
   :caption: BuildStreaM Documentation
   
   how-to-prepare-buildstream
   how-to-gitlab-deployment
   how-to-update-catalog-pipeline
