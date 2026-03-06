.. _concept-buildstream-overview:

Omnia BuildStreaM: Catalog-Driven Build Automation
==================================================

Omnia BuildStreaM provides a comprehensive automation solution for managing infrastructure build workflows. It uses a catalog-driven approach where you define your build requirements in a structured catalog file, and BuildStreaM executes automated pipelines to create and deploy images according to your specifications.

BuildStreaM addresses the key challenges in HPC cluster image management:

   - **Automation**: Eliminates manual build and deployment processes
   - **Integration**: Works seamlessly with existing Omnia deployments
   - **Traceability**: Provides complete audit trails for all build operations
   
To build your own custom workflows, you can use the BuildStreaM REST API. The BuildStreaM API documentation is available at `Omnia BuildStreaM API Documentation <https://developer.dell.com/apis/ea677050-f49b-49e1-a4b9-1cdd563415d9/versions/2.1.0/docs/Introduction.md>`_.

.. toctree::
   :maxdepth: 1
   :caption: BuildStreaM Deployment Workflow

   omnia_startup_buildstream
   composable_roles_buildstream
   prepare_oim_buildstream
   how-to-gitlab-deployment
   how-to-update-catalog-pipeline
   set_pxe_boot_order_buildstream
   buildstream_tables
