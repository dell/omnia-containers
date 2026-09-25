# Author BuildStreaM Catalogs with NERSC AI Skills

## Overview

NERSC AI Skills for BuildStreaM Catalog Authoring assist operators with
creating, editing, validating, analyzing, and reviewing BuildStreaM catalogs.
The skills operate on Git-managed catalog files and use the existing GitLab and
BuildStreaM workflow for review, validation, and image building.

AI-generated changes remain subject to operator review. Git is the catalog
source of truth, and the existing BuildStreaM workflow continues to operate
without the AI skills.

### Capabilities

| Capability | Result |
|---|---|
| Catalog generation | Creates a catalog from operator requirements and the supplied catalog reference data. |
| Catalog editing | Adds, removes, or changes packages while preserving catalog structure and package metadata. |
| Cross-catalog bulk editing | Applies a requested change, such as a base OS version update, across the selected catalogs. |
| Pre-submission validation | Checks catalog structure, package resolution, architecture values, metadata, and identifier requirements before submission. |
| Impact analysis | Identifies catalogs, functional layers, package groups, architectures, and adapter policies affected by a requested change. |
| Compatibility and dependency analysis | Evaluates relationships represented by the catalog and supplied reference data. |
| Merge Request risk review | Produces a structured review of catalog changes, affected areas, validation results, and unresolved risks. |
| Semantic catalog diff | Produces a machine-readable forward and reverse change set. |
| Changelog and release-note generation | Produces separate human-readable descriptions of reviewed catalog changes. |

The skills do not introduce a separate catalog database, image-build path, or
catalog-management portal. GitLab retains catalog and Merge Request state,
while BuildStreaM and its GitLab pipelines retain build and pipeline state.

The catalog-authoring capabilities do not perform post-build image scanning,
EOL or security-advisory recommendations, image-level software inventory or
BOM generation, or natural-language catalog search.

## Prerequisites

- Access to the BuildStreaM GitLab catalog project.
- A working branch containing the catalogs to generate, edit, or analyze.
- The catalog schema, master catalogs, adapter policies, and package-reference
  files that match the target Omnia source revision.
- The target operating system, architectures, functional layers, package
  groups, and catalog files.
- Access to the coding-agent environment configured and approved by the site.
- Permission to read or modify the selected catalog files.

Review the current [catalog sample](../../Reference/SampleFiles/catalog_json.md)
and the catalog schema delivered with the matching Omnia source revision before
authoring a catalog.

Do not include passwords, access tokens, keytabs, private keys, customer
identifiers, or other site secrets in prompts, skill inputs, or catalog
reference data.

## Procedure

1. Create or select a working branch in the BuildStreaM catalog project.
2. Select the required operation: generate, edit, bulk edit, validate, analyze,
   review, diff, or generate a changelog or release note.
3. Identify the catalog files and requested scope. Include the required OS,
   architecture, package source, version, tag, package group, and functional
   layer when known.
4. Request an analysis of the change before modifying files.
5. Review the reported input files, reference sources, affected catalogs, and
   unresolved metadata.
6. Apply the catalog changes to the working branch.
7. Validate the resulting catalogs with the schema and package-resolution rules
   used by the matching BuildStreaM version.
8. Review the machine-readable diff separately from the human-readable
   changelog.
9. Resolve every validation error, incomplete cross-catalog change, and
   unverified metadata item.
10. Commit the reviewed changes to the working branch and submit a Merge
    Request.
11. Review the Merge Request risk report and resolve its findings before
    merging the change.
12. Monitor the existing BuildStreaM pipeline after the catalog change is
    committed or merged according to the project workflow.

Changing the root `catalog_rhel.json` in the managed GitLab project uses the
existing BuildStreaM build-pipeline trigger. AI-assisted authoring does not
bypass pipeline validation.

### Generate a catalog

Provide the required functional layers, architectures, OS version, package
groups, and reference catalogs. For example:

> Create a RHEL catalog for the specified functional layers and architectures.
> Use only the supplied master catalogs and package-reference files. Report any
> required package metadata that cannot be resolved, and validate the result
> before changing files.

### Edit a catalog

Identify the package, target groups, functional layers, architectures, and
catalogs. For example:

> Add the requested package to the specified package group and functional
> layers. Preserve existing metadata and ordering conventions. Show the
> affected catalogs and semantic diff before applying the change.

### Analyze impact

Identify the package and requested removal, version change, or metadata change.
For example:

> Analyze the effect of removing or changing the requested package. Report
> direct references from catalogs, package groups, functional layers,
> architectures, and adapter policies. Identify dependency relationships that
> could not be evaluated from the supplied data.

### Update multiple catalogs

Identify every catalog in scope and the value that must remain consistent. For
example:

> Update the requested base OS version across the selected catalogs. List every
> affected file, preserve architecture-specific values, stop if a catalog
> cannot be updated consistently, and produce forward and reverse diffs.

## Verification

Confirm that:

- each modified catalog is valid JSON and conforms to the matching catalog
  schema;
- required catalog fields remain present;
- a catalog used for a new build has a unique identifier;
- package name, type, version, tag, source, OS, and architecture values come
  from the supplied reference data;
- packages are placed in the intended groups and functional layers;
- every requested cross-catalog change was applied consistently;
- unresolved or inferred metadata is identified in the result;
- the reverse diff restores the original catalog; and
- the human-readable changelog agrees with the machine-readable change set.

Impact and compatibility results cover relationships declared in the inspected
catalogs, adapter policies, and supplied reference files. Unless a package
dependency or compatibility data source is supplied, the result does not
establish transitive RPM dependencies, kernel-to-driver compatibility, or
upstream compatibility-matrix status.

Do not use model knowledge alone as evidence for package versions, repository
locations, compatibility claims, or product-support statements.

## Next Steps

- Review [Update the BuildStreaM Catalog](../../Operations/build_stream/update_catalog.md).
- Run [Execute Build Pipeline](execute_build_pipeline.md) after the catalog
  change is reviewed and approved.
- See [BuildStreaM Issues](../../Troubleshooting/build_stream/build_stream.md)
  when catalog validation or pipeline processing fails.

## Troubleshooting

### Required package metadata is unavailable

Do not accept fabricated package versions, repository locations,
architectures, tags, or compatibility information. Supply an approved metadata
source or provide the missing information, then repeat the operation. Do not
present an incomplete catalog entry as valid.

### The request is ambiguous

Identify the target catalog, package, functional layer, architecture, and
requested operation before modifying files. Review the requested scope and
affected files before applying the change.

### Catalog validation fails

Do not merge the catalog or start a new build from it. Compare the catalog with
the schema and samples delivered with the same Omnia source revision, correct
the unsupported or unresolved values, and repeat validation.

### Cross-catalog changes are inconsistent

Review the list of requested catalogs and the generated diff. Correct or revert
the operation if any selected catalog was skipped or contains a conflicting OS,
architecture, version, or package value.

### Impact or compatibility analysis is incomplete

Review the evidence sources identified in the result. Treat unverified
transitive dependencies as unresolved risk and provide an approved package
dependency or compatibility data source before repeating the analysis.

### The reverse diff does not restore the original catalog

Do not use the change set for automated application. Preserve the original
catalog, regenerate the forward and reverse operations, and verify both
directions before submitting the catalog change.
