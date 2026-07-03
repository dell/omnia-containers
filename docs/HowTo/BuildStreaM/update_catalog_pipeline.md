# Update Catalog Pipeline

Update the BuildStreaM catalog file to modify build specifications and trigger new pipeline runs.

## Overview

The `catalog_rhel.json` file defines your build requirements, including functional groups, architecture types, operating systems, and software packages. Modifying this file triggers the build pipeline automatically.

### Build Pipeline Stages

- **parse-catalog**: Parses and validates the catalog file for build requirements
- **generate-input-files**: Generates input files and configuration data for image building
- **create-local-repository**: Creates and configures the local repository for build artifacts
- **build-image**: Builds the diskless images based on catalog specifications

### Deploy Pipeline Stages

- **deploy**: Deploys the built images to the target nodes
- **restart**: PXE-boots the target nodes to load the deployed images
- **validate**: Executes Molecule-based infrastructure tests to verify cluster deployment, network connectivity, and service health

## Next Steps

- [Execute Build Pipeline](execute_build_pipeline.md) -- Detailed build pipeline operations
- [Execute Deploy Pipeline](execute_deploy_pipeline.md) -- Detailed deploy pipeline operations
- [Deploy GitLab](deploy_gitlab.md) -- GitLab deployment procedures
- [Cleanup Operations](cleanup_operations.md) -- Remove old Image Groups
- [Retry Pipelines](retry_pipelines.md) -- Retry failed pipeline operations
