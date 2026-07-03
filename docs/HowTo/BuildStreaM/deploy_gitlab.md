# Deploy GitLab for BuildStream

This page provides a quick reference for deploying GitLab as the CI/CD automation engine for BuildStream.

For the complete step-by-step tutorial with detailed instructions, see [Step 4: Deploy GitLab for BuildStream](../../GetStarted/buildstream_deployment.md#step-4-deploy-gitlab-for-buildstream) in the BuildStreaM deployment guide.

## Quick Reference

BuildStream uses a **three-pipeline architecture** in GitLab:

- **Build Pipeline**: Triggered by catalog changes, creates images and establishes Job ID to Image Group ID mapping. This pipeline can also be executed manually.
- **Deploy Pipeline**: Triggered by PXE mapping changes, deploys images to cluster nodes. This pipeline can also be executed manually.
- **Cleanup Pipeline**: Triggered manually, allows users to delete selected Image Groups.

## Related Topics

- [Update Catalog Pipeline](update_catalog_pipeline.md)
- [Cleanup Operations](cleanup_operations.md)
- [Retry Pipelines](retry_pipelines.md)
