.. _concept-buildstream-overview:

Omnia BuildStreaM: Catalog-Driven Build Automation
==================================================

Omnia BuildStreaM provides a comprehensive automation solution for managing infrastructure build workflows. It uses a catalog-driven approach where you define your build requirements in a structured catalog file, and BuildStreaM executes automated pipelines to create and deploy images according to your specifications.

BuildStreaM supports three pipeline types that can be executed through GitLab:

* **Build Pipeline**: Creates diskless images based on catalog specifications. This pipeline is automatically triggered when the catalog is committed, but can also be executed manually.
* **Deploy Pipeline**: Deploys built images to target cluster nodes. This pipeline is automatically triggered when the PXE mapping file is updated, but can also be executed manually.
* **Clean Pipeline**: Removes old Image Groups based on retention policy. This pipeline can be executed only manually.

BuildStreaM addresses the key challenges in HPC cluster image management:

* **Automation**: Eliminates manual build and deployment processes
* **Integration**: Works seamlessly with existing Omnia deployments
* **Traceability**: Provides complete audit trails for all build operations

To build your own custom workflows, you can use the BuildStreaM REST API. The BuildStreaM API documentation is available at `Omnia BuildStreaM API Documentation <https://developer.dell.com/apis/ea677050-f49b-49e1-a4b9-1cdd563415d9/versions/2.1.0/docs/Introduction.md>`_.

.. toctree::
   :maxdepth: 1
   :caption: BuildStreaM Documentation

   setup/deploying-omnia-core
   setup/creating-pxe-mapping-file
   setup/preparing-oim-buildstream
   setup/deploying-gitlab-buildstream
   build/executing-build-pipeline
   deploy/executing-deploy-pipeline
   management/configuring-pxe-boot
   monitoring/initializing-telemetry
   monitoring/verifying-telemetry-services
   management/performing-cleanup-operations
   management/retrying-pipelines
   reference/configuration-tables
   troubleshooting/common-pipeline-issues
   


