# Update Catalog Pipeline

This page provides a quick reference for executing BuildStream build and deploy pipelines.

For the complete step-by-step tutorial with detailed instructions, see:

- [Step 5: Execute Build Pipeline](../../GetStarted/buildstream_deployment.md#step-5-execute-build-pipeline) in the BuildStreaM deployment guide
- [Step 6: Execute Deploy Pipeline](../../GetStarted/buildstream_deployment.md#step-6-execute-deploy-pipeline) in the BuildStreaM deployment guide

## Quick Reference

### Build Pipeline

The BuildStream build pipeline automates the creation of diskless images based on catalog specifications. The pipeline consists of four sequential stages:

- **parse-catalog**: Parses and validates the catalog file for build requirements
- **generate-input-files**: Generates input files and configuration data for image building
- **create-local-repository**: Creates and configures the local repository for build artifacts
- **build-image**: Builds the diskless images based on catalog specifications

### Deploy Pipeline

The BuildStream deploy pipeline automates the deployment of built images to target cluster nodes. The pipeline consists of three sequential stages:

- **deploy**: Deploys the built images to the target nodes
- **restart**: PXE-boots the target nodes to load the deployed images
- **validate**: Executes Molecule-based infrastructure tests to verify cluster deployment, network connectivity, and service health

## Related Topics

- [Deploy GitLab](deploy_gitlab.md)
- [Cleanup Operations](cleanup_operations.md)
- [Retry Pipelines](retry_pipelines.md)
