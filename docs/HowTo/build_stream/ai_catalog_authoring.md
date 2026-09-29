# Author BuildStreaM Catalogs with AI-Assisted Skills

## Overview

AI-Assisted Catalog Authoring Skills provide optional, standalone assistance
for generating and editing catalogs, applying changes across catalogs,
analyzing impact and compatibility, and comparing catalog versions. Operators
invoke the skills on demand, outside the BuildStreaM pipeline. BuildStreaM
continues to operate without an AI assistant.

AI-generated content is not authoritative by itself. Every catalog-changing
operation is subject to source checks, operator approval, and catalog-schema
validation. Use the catalogs and package metadata provided with the matching
Omnia release as the source for shipped package sets.

### Capabilities

| Capability | Result |
|---|---|
| Catalog generation | Creates a schema-valid catalog from the selected base OS, architectures, stack, node roles, GPU, storage, network, and package requirements. |
| Catalog editing | Adds, removes, or changes catalog content while preserving unrelated content and existing package metadata. |
| Cross-catalog bulk editing | Applies a requested change to each matching catalog that passes validation and reports any catalog that is skipped. |
| Impact analysis | Evaluates a package, group, functional layer, or OS change within one catalog. Reports package, role, cluster, and user or workload impact with evidence tags and a severity rating. |
| Compatibility and dependency analysis | Checks catalog selections against approved online upstream and Red Hat compatibility information, with a disclosed offline fallback. |
| Semantic catalog comparison | Uses the deterministic catalog comparison command to produce reversible forward and reverse JSON diffs and a separate Markdown or optional HTML changelog. |

### Master reference file

Use the versioned master reference file provided with the matching Omnia
release. It contains the selection, constraint, source, and version information
required when approved online sources are unavailable. Do not generate or
modify the file during a skill invocation. The master reference file does not
replace the release-matched catalogs as the source for shipped package sets.

The master reference file contains these eight information sets:

1. Selection catalogue
2. Node-role mappings
3. Functional-layer composition
4. Stack and storage compatibility
5. Package-source defaults
6. Pinned versions
7. Supported hardware
8. Constraints and co-requisites

The reference data records provenance and capture information. Entries in the
selection catalogue include `support_status`. A skill uses only selections
marked `supported` when producing catalog content. It refuses any other
recorded status, reports that status, and presents supported alternatives
without silently substituting one. Product support remains defined by the
published Omnia support matrices; the presence of a catalog or reference-file
entry does not independently establish product support.

### Source and fallback behavior

The skills prefer approved online package repositories, upstream
documentation, and Red Hat compatibility information for package metadata,
dependency, impact, and compatibility checks. If online access is unavailable,
the skills use only the delivered master reference file and disclose the
reduced scope. They do not fabricate packages, versions, repository locations,
dependencies, compatibility results, or changelog entries.

The skill instructions are stored under `src/build_stream/ai_skills/` in the
Omnia source tree. They can be invoked through either of these channels:

- A coding agent with repository file access can read and update catalog files
  within the known source catalog tree.
- A browser-based AI assistant without file access accepts pasted catalog
  content and returns generated or edited catalog text for the operator to
  apply manually.

Both channels use the same source, approval, and no-fabrication contracts.
However, a browser-only channel cannot run schema validation or the
deterministic semantic-comparison command. Run those operations from a channel
with shell access before using the result.

## Prerequisites

- Access to the BuildStreaM catalog Git project and a working branch.
- The catalog samples, catalog validation tooling, master reference file, and
  repository configuration provided with the same Omnia release.
- Python 3 on the system used to validate or compare catalogs. Install Jinja2
  only when an HTML comparison report is required; the JSON diffs and Markdown
  changelog do not require HTML output.
- An approved coding-agent or browser-based AI assistant invocation channel.
- Permission to read the selected catalogs and, when direct editing is used,
  to write under `src/main/samples/catalogs/`.
- For online analysis, access through the site-approved endpoint allowlist to
  the required package repositories, upstream documentation, and Red Hat
  compatibility information.
- The functional group or cluster requirements, including the intended base
  OS, architecture, stack, node roles, GPU, storage, and network selections.

Review the current [Catalog JSON reference](../../Reference/SampleFiles/catalog_json.md)
and the samples under `src/main/samples/` before authoring a catalog.

Do not include passwords, access tokens, keytabs, private keys, customer
identifiers, or other site secrets in prompts, catalogs, skill definitions, or
reference data. Credentials for approved online sources must come from the
invoking platform's secret store.

## Procedure

### Invoke a skill

1. Create or select a working branch in the BuildStreaM catalog project.
2. Choose the invocation channel:
   - In a coding agent, identify the Omnia source tree and the source catalog
     files in scope under
     `src/main/samples/catalogs/<os_version>/`. Direct skill writes are
     restricted to this known source catalog tree. Transfer the reviewed and
     validated result to root `catalog_rhel.json` only during the image-build
     handoff described later on this page.
   - In a browser-based assistant, paste the complete catalog content required
     for generation or editing and request the complete resulting catalog for
     manual validation and application. Use a shell-enabled channel for
     semantic comparison.
3. Select the entry file for the required operation:

   | Operation | Entry file |
   |---|---|
   | Generate a catalog | `src/build_stream/ai_skills/catalog_generation/SKILL.md` |
   | Edit one catalog | `src/build_stream/ai_skills/catalog_editing/edit_catalog.md` |
   | Edit multiple catalogs | `src/build_stream/ai_skills/catalog_editing/bulk_edit_catalog.md` |
   | Analyze impact | `src/build_stream/ai_skills/analysis/impact_analysis.md` |
   | Analyze compatibility | `src/build_stream/ai_skills/analysis/compatibility_analysis.md` |
   | Compare catalog versions | `src/build_stream/ai_skills/diff_changelog/changelog_generator.md` |

   Instruct the approved assistant to follow the selected entry file and read
   the prerequisite files that it identifies. The skills do not add a
   BuildStreaM UI or API operation.
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
6. Use the lowercase field names and structure from the release-matched
   catalog samples. Set `schema_version` to `2` for a new Omnia 2.3 catalog.
7. From the Omnia source root, validate the generated catalog before treating
   it as final:

    ```bash
    python3 src/repo_manager/plugins/module_utils/catalog/catalog_manager.py \
      validate \
      --catalog <path-to-generated-catalog.json> \
      --schema src/repo_manager/schemas/catalog_schema.json
    ```

   An exit code of `0` indicates that the catalog passed schema validation.
   Correct every reported `[ERROR]` before continuing. A browser-only channel
   must return the catalog for this validation rather than claiming that it ran
   the command.
8. Review the output for unresolved packages and outstanding operator-supplied
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
5. For a new revision of the same catalog family, retain `identifier` and
   increment `version`. Use a different `identifier` only for a different
   catalog family. The resulting `identifier-v<version>` value must be unique.
6. After approval, apply the edit only under
   `src/main/samples/catalogs/<os_version>/`. Reject absolute or relative paths
   that resolve outside that boundary.
   Preserve the logical content of unrelated packages, groups, functional
   layers, and catalog metadata. The catalog tool rewrites formatted JSON, so
   raw byte-for-byte formatting is not guaranteed.
7. Validate the result before writing it. A failed validation rejects the edit
   and leaves the catalog unmodified.
8. Generate a new changelog entry or update the applicable changelog with the
   approved change and its disclosed impact.

### Update multiple catalogs

1. State the original value, replacement value, and catalog scope.
2. Identify only catalogs that contain the original value.
3. Run the applicable impact and compatibility checks separately for every
   matching catalog. Present findings per catalog and obtain a separate
   approval decision for a catalog with findings.
4. Apply and validate the edit one catalog at a time.
5. Update the `version` of each changed catalog so that its
   `identifier-v<version>` value is unique.
6. Keep each catalog that fails validation unchanged, and report the specific
   violation. Continue with other matching catalogs that pass validation.
7. Report applied, skipped because of validation, held pending approval,
   declined, and unaffected catalogs. Update the changelog for each applied
   change.

No catalog may be left in a partially edited or schema-invalid state.

### Analyze impact and compatibility

For impact analysis, identify the catalog and whether the proposed target is a
package, group, functional layer, or OS change. The result covers relationships
within that catalog; it does not trace dependencies between separate catalogs.

The analysis attempts the applicable sources in this order: local DNF metadata,
the package's configured live repository, upstream documentation, and the
master reference file. Absence from one master-reference table does not justify
skipping an available repository lookup.

Review the report in this order:

1. Customer-level summary and Critical, High, Medium, or Low severity.
2. Whether the item is actually removed from the built node or remains
   installed because another catalog package requires it.
3. Package, functional-role, cluster-operation, and user or workload impact.
4. Evidence tagged as `repo-metadata`, `upstream-doc`, `catalog`, or
   `inferred`.
5. Pinned and available version information.
6. Recommendations and degraded-mode or architecture-substitution disclosures.

When approved sources cannot answer the request, the report must identify the
failed source and reason, state that the master reference file was used, and
describe the reduced scope. An unresolved relationship must not be presented
as compatible or unaffected.

For compatibility analysis, identify the package or component version, target
OS and architecture, and any other package involved. An online result names
the specific approved source consulted. If Red Hat compatibility information
cannot be reached, the result must include this disclosure:

> Compatibility check is based on master reference file data only. The Red
> Hat Compatibility Matrix was not consulted.

### Compare catalog versions

1. Supply two lowercase-root Schema 2 catalogs: the current catalog and the
   proposed future catalog.
2. From the Omnia source root, run:

    ```bash
    python3 src/repo_manager/plugins/module_utils/catalog/catalog_manager.py diff \
      --current <current-catalog.json> \
      --future <future-catalog.json> \
      --schema src/repo_manager/schemas/catalog_schema.json \
      --output-forward forward_diff.json \
      --output-reverse reverse_diff.json \
      --output-changelog changelog.md \
      --output-html changelog.html
    ```

   Omit `--output-html` when Jinja2 is unavailable or an HTML report is not
   required.
3. If either catalog fails schema validation, correct the reported violation
   and rerun the command. If a catalog uses the legacy uppercase `Catalog`
   root, transform it to Schema 2 before comparing it.
4. A successful command verifies internally that the forward diff reproduces
   the future catalog and the reverse diff restores the current catalog.
5. Review `changelog.md` separately from the machine-readable diffs. The
   implemented offline warning checks cover mismatched Kubernetes component
   pins (`CON-004`) and groups still referenced by another functional layer
   (`CON-007`). Treat a `[BLOCKING] CON-004` warning as a stop condition even
   when diff generation completes successfully.

The changelog is a separate customer-readable artifact and does not replace the
machine-readable diff.

### Prepare the catalog for an image build

1. Review the validated catalog and its changelog on a working branch.
2. For another revision of the same catalog family, retain `identifier` and
   increment `version` so `<identifier>-v<version>` is unique.
3. Place the approved content in the root `catalog_rhel.json` file of the
   managed GitLab project. Files under `catalog/` and source samples under
   `src/main/samples/catalogs/` are references and do not trigger a build.
4. Review `git diff`, then commit the root catalog through the site's normal
   Git and Merge Request controls.
5. Confirm that GitLab selects the BuildStreaM build pipeline for the committed
   `catalog_rhel.json` change.

## Verification

Confirm that:

- every generated or modified catalog is valid JSON and conforms to the
  matching catalog schema;
- a new Omnia 2.3 catalog declares `schema_version: 2`;
- the combination `identifier-v<version>` is unique for a new build;
- each functional layer references existing groups and contains exactly one
  group whose `type` is `base_os`;
- each `base_os` group declares `os` and `os_version`;
- every group component references an existing package, and every package has
  at least one source with the fields required for its package type;
- all catalog-changing operations received explicit operator approval;
- package values, source data, dependencies, and compatibility statements are
  traceable to an identified online source or the master reference file;
- an offline result contains the required reduced-scope disclosure;
- unresolved information is flagged for manual review and is not represented
  as verified content;
- package placement follows the functional-layer composition and constraints
  in the master reference file;
- required operator-supplied repository URLs are identified, and repository
  names are mapped for the selected OS version and architecture in
  `repo_manager_config.yml` before synchronization;
- bulk-edit results identify applied, skipped, held, declined, and unaffected
  catalogs, and no catalog is partially edited or schema-invalid;
- the reverse diff restores the original catalog exactly;
- the human-readable changelog agrees with, but remains separate from, the
  machine-readable change set;
- no `[BLOCKING] CON-004` warning remains unresolved; and
- the approved content is committed as root `catalog_rhel.json` when an image
  build is required.

With file-system access, the skill instructions record degraded analysis events
in `src/build_stream/ai_skills/analysis/degraded_mode_audit.log` and pre-edit
decisions in
`src/build_stream/ai_skills/catalog_editing/pre_edit_gate_audit.log`.
Browser-only channels must include the same event or decision details in their
response because they cannot write these files. Do not place credentials in
either record.

## Next steps

- Review [Update the BuildStreaM Catalog](../../Operations/build_stream/update_catalog.md).
- Run the catalog-validation workflow described in
  [Add or Remove Packages](../repo_manager/adding_additional_packages.md#verification).
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

### Repository metadata is for the wrong architecture

Do not silently use metadata for a different architecture. Configure local
repositories for the target architecture, use an approved online source, or
explicitly approve use of the available architecture as a disclosed stand-in.
If none is acceptable, leave the finding unresolved.

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

For generation or editing, paste the complete catalog content needed for the
operation and request the complete resulting catalog for manual validation and
application. Do not request an exhaustive reversible semantic diff from a
browser-only channel. Run the deterministic comparison command from a channel
with shell access.

### A requested path is outside the catalog repository

Do not apply the write. Use a path under
`src/main/samples/catalogs/<os_version>/` and repeat the request. The skill must
reject traversal or any destination outside that source catalog boundary.

### The reverse diff does not restore the original catalog

Do not apply the change set. Preserve both input catalogs, regenerate the
forward and reverse diffs, and verify both equations before using the result.

### A catalog comparison reports a legacy catalog format

The comparison command accepts the lowercase `catalog` root used by Schema 2.
Use `catalog_manager.py transform` to convert a catalog that uses the legacy
uppercase `Catalog` root, validate the converted file, and repeat the
comparison.

### The HTML changelog is not created

Jinja2 is not installed in the execution environment. Review the Markdown
changelog and JSON diffs, or install the approved Jinja2 package and repeat the
command with `--output-html`. HTML output is optional.

### The changelog contains a blocking Kubernetes-version warning

`CON-004` indicates that Kubernetes component minor-version pins do not agree
after the proposed change. Do not promote the catalog. Align the affected
component pins, validate both catalogs, and regenerate the comparison outputs.
