# Author BuildStreaM Catalogs with NERSC AI Skills

## Overview

NERSC AI Skills for BuildStreaM Catalog Authoring provide optional,
standalone assistance for generating and editing catalogs, applying changes
across catalogs, analyzing impact and compatibility, and comparing catalog
versions. Operators invoke the skills on demand, outside the BuildStreaM
pipeline. BuildStreaM continues to operate without an AI assistant.

AI-generated content is not authoritative by itself. Every catalog-changing
operation is subject to source checks, operator approval, and catalog-schema
validation. Master catalogs remain the authoritative source for the concrete
package sets in shipped configurations.

### Capabilities

| Capability | Result |
|---|---|
| Catalog generation | Creates a schema-valid catalog from the selected base OS, architectures, stack, node roles, GPU, storage, network, and package requirements. |
| Catalog editing | Adds, removes, or changes catalog content while preserving unrelated content and existing package metadata. |
| Cross-catalog bulk editing | Applies a requested change to each matching catalog that passes validation and reports any catalog that is skipped. |
| Impact analysis | Reports the functional layers in one catalog that a proposed package change affects and, when online repository data is available, its transitive package dependents. |
| Compatibility and dependency analysis | Checks catalog selections against approved online upstream and Red Hat compatibility information, with a disclosed offline fallback. |
| Semantic catalog comparison | Produces a deterministic, reversible machine-readable diff and a separate human-readable changelog. |

Pre-submission validation, Merge Request risk review, and post-build release
note generation are not part of these standalone skills. Schema validation
within catalog generation and editing is a required safety check, not a
pipeline-integrated pre-submission validation capability.

### Master reference file

The versioned master reference file is delivered with the skill definitions.
It provides the decision knowledge required when approved online sources are
unavailable. The development team derives and maintains this Markdown file
from master catalogs, repository configuration, and verified external sources;
an operator does not generate it when invoking a skill. It is regenerated as
part of the skill build and release process when master catalogs or repository
configuration change.

The master reference file contains these eight information sets:

1. Selection catalogue
2. Node-role mappings
3. Functional-layer composition
4. Stack and storage compatibility
5. Package-source defaults
6. Pinned versions
7. Supported hardware
8. Constraints and co-requisites

Each entry records its provenance, capture date, and `support_status`. A skill
uses only entries marked `supported` when producing catalog content. It
refuses any other status, reports the recorded status, and presents supported
alternatives without silently substituting one.

### Source and fallback behavior

The skills prefer approved online package repositories, upstream
documentation, and Red Hat compatibility information for package metadata,
dependency, impact, and compatibility checks. If online access is unavailable,
the skills use only the delivered master reference file and disclose the
reduced scope. They do not fabricate packages, versions, repository locations,
dependencies, compatibility results, or changelog entries.

The skills can be invoked through either of these channels:

- A coding agent with repository file access can read and update catalog files
  within the catalog Git repository.
- A browser-based AI assistant without file access accepts pasted catalog
  content and returns a complete edited catalog or an applicable diff for the
  operator to apply.

Both channels use the same source, validation, approval, and output contracts.

## Prerequisites

- Access to the BuildStreaM catalog Git project and a working branch.
- The catalog schema, master catalogs, master reference file, and repository
  configuration delivered for the same Omnia release.
- An approved coding-agent or browser-based AI assistant invocation channel.
- A model identified as certified for the skills in the delivery package.
- Permission to read the selected catalogs and, when direct editing is used,
  to write within the catalog Git repository.
- For online analysis, access through the site-approved endpoint allowlist to
  the required package repositories, upstream documentation, and Red Hat
  compatibility information.
- The functional group or cluster requirements, including the intended base
  OS, architecture, stack, node roles, GPU, storage, and network selections.

Review the current [catalog sample](../../Reference/SampleFiles/catalog_json.md)
and the catalog schema delivered with the matching Omnia source revision
before authoring a catalog.

Do not include passwords, access tokens, keytabs, private keys, customer
identifiers, or other site secrets in prompts, catalogs, skill definitions, or
reference data. Credentials for approved online sources must come from the
invoking platform's secret store.

## Procedure

### Invoke a skill

1. Create or select a working branch in the BuildStreaM catalog project.
2. Choose the invocation channel:
   - In a coding agent, identify the catalog repository and the files in scope.
   - In a browser-based assistant, paste the complete catalog content required
     for the operation and request text or a diff to apply manually.
3. Select one operation: generate a catalog, edit one catalog, apply a bulk
   edit, analyze impact or compatibility, or compare catalog versions.
4. State the requested outcome and all known selection values. Do not provide
   credentials or unrelated customer data.
5. Review the sources, unresolved information, fallback disclosure, and
   proposed output before approving any catalog change.

### Generate a catalog

1. Request the selections in this dependency order when they are not already
   supplied:
   1. OS version
   2. Architecture or architectures
   3. Stack
   4. Node roles
   5. GPU
   6. Storage
   7. Network
   8. Package-source overrides
2. At each decision, select only options recorded as supported and compatible
   with earlier selections. When the operator defers a decision that has a
   recorded default, use that default and disclose it.
3. Review and confirm the complete selection set before catalog generation.
4. Emit one functional layer for each selected node role and architecture,
   using the master reference file's layer-to-group mappings. Include
   conditional groups only when the governing selection is present.
5. Resolve package versions, architectures, repositories, and registries from
   approved online sources or the master reference file.
6. Validate the generated catalog against the catalog JSON schema before it is
   written or returned.
7. Review the output for unresolved packages and outstanding operator-supplied
   repository URLs. Verify that every repository name in the catalog is mapped
   in `repo_manager_config.yml` before catalog synchronization.

If a requested package cannot be resolved, the skill may return a partial
catalog with that package clearly marked for manual review. Treat that output
as incomplete; do not synchronize or build from it. If a repository URL is
recorded as operator-supplied but is unavailable, the catalog can retain the
repository name, but the skill must report that the URL is required before
synchronization and must not invent one.

### Edit a catalog

1. Identify the catalog and the exact package, version, OS, metadata, group, or
   functional-layer change.
2. Run impact analysis and compatibility/dependency analysis when applicable.
   For a metadata-only correction, the skill can skip a non-applicable check
   only if it states which check was skipped and why.
3. Review the affected functional layers, dependencies, compatibility
   findings, sources, and any online/offline disclosure.
4. Explicitly approve or decline the proposed edit. Declining leaves both the
   catalog and its changelog unchanged.
5. After approval, apply the edit only within the catalog repository. Preserve
   the file byte-for-byte outside the targeted section when the operation does
   not require other changes.
6. Validate the result against the catalog schema before writing it. A failed
   validation rejects the edit and leaves the catalog unmodified.
7. Generate a new changelog entry or update the applicable changelog with the
   approved change and its disclosed impact.

### Update multiple catalogs

1. State the original value, replacement value, and catalog scope.
2. Identify only catalogs that contain the original value.
3. Run the applicable impact and compatibility checks, then obtain explicit
   operator approval for the proposed file list and findings.
4. Apply and validate the edit one catalog at a time.
5. Keep each catalog that fails validation unchanged, and report the specific
   violation. Continue with other matching catalogs that pass validation.
6. Report changed, skipped, and unaffected catalogs, and update the changelog
   for each applied change.

No catalog may be left in a partially edited or schema-invalid state.

### Analyze impact and compatibility

For impact analysis, identify the catalog, proposed package removal or change,
and affected functional group. The result covers relationships within that
catalog; it does not trace dependencies between separate catalogs.

When online package-repository access succeeds, the result includes direct
functional-layer references and resolved transitive dependents. When it is
unavailable, the result is limited to relationships in the master reference
file and must include this disclosure:

> This analysis covers relationships declared in the master reference file
> only; transitive package dependencies were not evaluated because online
> access was unavailable.

For compatibility analysis, identify the package or component version, target
OS and architecture, and any other package involved. An online result names
the specific approved source consulted. If Red Hat compatibility information
cannot be reached, the result must include this disclosure:

> Compatibility check is based on master reference file data only. The Red
> Hat Compatibility Matrix was not consulted.

### Compare catalog versions

1. Supply the current and future catalogs or identify their versions.
2. Validate both catalogs against the schema. If either is invalid, correct
   the reported violation before requesting another comparison.
3. Generate a machine-readable `forward_diff` and `reverse_diff`.
4. Verify that applying `forward_diff` to the current catalog reproduces the
   future catalog, and applying `reverse_diff` to the future catalog reproduces
   the current catalog.
5. Review the separate human-readable changelog. It describes package
   additions, removals, version or tag changes, functional-layer and
   architecture impact, base-OS changes, and verified compatibility warnings.

The changelog does not replace the machine-readable diff and is not a
workflow-integrated release note.

## Verification

Confirm that:

- every generated or modified catalog is valid JSON and conforms to the
  matching catalog schema;
- a catalog used for a new build has a unique identifier;
- all catalog-changing operations received explicit operator approval;
- package values, source data, dependencies, and compatibility statements are
  traceable to an identified online source or the master reference file;
- an offline result contains the required reduced-scope disclosure;
- unresolved information is flagged for manual review and is not represented
  as verified content;
- package placement follows the functional-layer composition and constraints
  in the master reference file;
- required operator-supplied repository URLs are identified, and repository
  names are mapped in `repo_manager_config.yml` before synchronization;
- bulk-edit results identify changed, skipped, and unaffected catalogs, and no
  catalog is partially edited or schema-invalid;
- the reverse diff restores the original catalog exactly; and
- the human-readable changelog agrees with, but remains separate from, the
  machine-readable change set.

Catalog writes, rejected edits, degraded offline analyses, and unresolved
packages must produce an invocation record sufficient to determine what was
requested, what was applied or rejected, and why. Use the logging facility of
the approved invocation platform; do not place credentials in logs.

## Next Steps

- Review [Update the BuildStreaM Catalog](../../Operations/build_stream/update_catalog.md).
- Commit the reviewed catalog and changelog changes according to the site's
  Git workflow.
- Run [Execute Build Pipeline](execute_build_pipeline.md) after the catalog
  change is approved.
- See [BuildStreaM Issues](../../Troubleshooting/build_stream/build_stream.md)
  when authoring, validation, or pipeline processing fails.

## Troubleshooting

### Required package metadata is unavailable

Do not accept fabricated package versions, repository locations,
architectures, tags, or compatibility information. If approved online sources
are unavailable, check the delivered master reference file. When neither
source contains the data, flag the item for manual review. Do not synchronize
or build from the partial catalog.

### A selection is not supported

Review its `support_status` in the master reference file. The skill must use
only an option marked `supported` and show recorded supported alternatives
for any other status. Choose an alternative explicitly; do not allow automatic
substitution.

### The request is ambiguous

Identify the target catalog, package, functional layer, architecture, and
requested operation. The skill must ask for clarification instead of guessing
and modifying the catalog.

### Online analysis is unavailable

Confirm that the required endpoint is on the site-approved allowlist and that
credentials are available from the invocation platform. If the operation uses
the master reference file instead, confirm that the result identifies offline
mode and includes the reduced-scope disclosure.

### An operator-supplied repository URL is missing

Provide the approved URL before catalog synchronization. Do not replace the
repository name or invent a URL. Also confirm that the repository name is
mapped in `repo_manager_config.yml`.

### Catalog validation fails

Do not write, synchronize, commit, or build from the invalid result. Correct
the specific schema violation using the schema and reference artifacts from
the same Omnia release, then repeat validation.

### A bulk edit skips a catalog

Review the reported per-catalog schema violation. The skipped catalog remains
unchanged while valid matching catalogs can be updated. Correct the skipped
catalog and request the change again for that catalog.

### A browser-based assistant cannot access catalog files

Paste the complete catalog content needed for the operation. Request either
the complete edited catalog or an applicable diff, then validate and apply it
manually within the catalog repository.

### A requested path is outside the catalog repository

Do not apply the write. Use a path within the known catalog Git repository and
repeat the request. The skill must reject traversal or any destination outside
that repository boundary.

### The reverse diff does not restore the original catalog

Do not apply the change set. Preserve both input catalogs, regenerate the
forward and reverse diffs, and verify both equations before using the result.
