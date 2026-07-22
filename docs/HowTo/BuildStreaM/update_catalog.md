# Update Catalog

Update the BuildStreaM catalog file to modify build specifications and trigger new pipeline runs.

## Overview

The `catalog_rhel.json` file defines your build requirements, including functional groups, architecture types, operating systems, and software packages. Modifying this file triggers the build pipeline automatically.

!!! note

    Ensure that the catalog file adheres to the catalog schema. The schema is available at `/omnia/build_stream/core/catalog/resources/CatalogSchema.json`. Invalid catalog entries will cause the pipeline to fail.

!!! warning

    **Unique Catalog Identifier Required**

    Every catalog must have a unique `identifier` attribute. When you modify `catalog_rhel.json`, always update the `identifier` field with a new unique value. Build pipelines triggered from the GitLab portal rely on this identifier to track catalog versions. If the identifier is not unique, the pipeline will fail during the "Parse Catalog" stage.

## Next Steps

- [Execute Build Pipeline](execute_build_pipeline.md) -- Detailed build pipeline operations
- [Execute Deploy Pipeline](execute_deploy_pipeline.md) -- Detailed deploy pipeline operations
- [Cleanup Operations](cleanup_operations.md) -- Remove old Image Groups
- [Retry Pipelines](retry_pipelines.md) -- Retry failed pipeline operations
