# Update Catalog

Update the BuildStreaM catalog file to modify build specifications and trigger new pipeline runs.

## Overview

The `catalog_rhel.json` file defines your build requirements, including functional groups, architecture types, operating systems, and software packages. Modifying this file triggers the build pipeline automatically.

!!! note

    Ensure that the catalog file adheres to the catalog schema. The schema is available at `/omnia/build_stream/core/catalog/resources/CatalogSchema.json`. Invalid catalog entries will cause the pipeline to fail.

## Next Steps

- [Execute Build Pipeline](execute_build_pipeline.md) -- Detailed build pipeline operations
- [Execute Deploy Pipeline](execute_deploy_pipeline.md) -- Detailed deploy pipeline operations
- [Cleanup Operations](cleanup_operations.md) -- Remove old Image Groups
- [Retry Pipelines](retry_pipelines.md) -- Retry failed pipeline operations
