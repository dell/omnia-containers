# Catalog JSON reference

The catalog JSON defines the functional layers, software packages, and
artifact sources used across the Omnia deployment workflow. Repository Manager uses
the catalog to prepare software repositories, while Image Build Manager and
Orchestrator use it to build images and provision the cluster.

By default, Omnia uses the following catalog:

```text
${OMNIA_DATA_PATH}/catalog/catalog_rhel.json
```

When `OMNIA_DATA_PATH` is not customized, the catalog is available at
`/opt/omnia/catalog/catalog_rhel.json`.

The source copy of the default catalog is available at:

```text
src/main/samples/catalog_rhel.json
```

Additional catalog samples are available under `src/main/samples`.

## Catalog structure

Use the lowercase field names and structure in the samples provided with the
same Omnia release.

| Field | Description |
|---|---|
| `catalog.name` | Customer-readable catalog name. |
| `catalog.version` | Revision of the catalog content. Use a two-part or three-part numeric value, such as `1.0` or `1.0.1`. |
| `catalog.schema_version` | Catalog structure version. New Omnia 2.3 catalogs use `2`. |
| `catalog.identifier` | Stable identifier for a catalog family. Use lowercase letters, numbers, underscores, and hyphens. |
| `catalog.description` | Description of the catalog's intended cluster configuration. |
| `catalog.functionallayer` | Functional layers and the groups included in each layer. |
| `catalog.groups` | Package groups referenced by functional layers. |
| `catalog.packages` | Package definitions and their architecture-specific sources. |

BuildStreaM forms the catalog revision identity as:

```text
<identifier>-v<version>
```

Keep `identifier` unchanged when creating another revision of the same
catalog family and increment `version`. Use a new `identifier` for a
different catalog family. The composite revision identity must be unique for a
new build.

## Functional-layer relationships

Catalog content follows this reference chain:

```text
functional layer -> group -> package -> source
```

Each functional layer lists group keys in `components`. Each group lists
package keys in its own `components`. Every referenced key must exist in the
corresponding `groups` or `packages` object.

Every functional layer must reference exactly one group whose `type` is
`base_os`. A `base_os` group must declare both `os` and `os_version`.

## Package definitions

The catalog supports these package types:

| `packagetype` | Required catalog metadata |
|---|---|
| `rpm` | Architecture and repository name |
| `rpm_repo` | Architecture and repository name |
| `tarball` | Architecture and URL |
| `image` | Package tag, architecture, and registry |
| `git` | Architecture and URL |
| `manifest` | Architecture and URL |
| `pip_module` | Package name and at least one architecture-specific source |

A package can provide separate sources for each architecture. Repository names
must match entries for the selected OS version and architecture in
`repo_manager_config.yml`. In non-subscription mode, each referenced RPM
repository requires an explicit URL. Configure private image registries in
`repo_manager_config.yml`; public registries do not require a private-registry
entry.

## Validation

Validate a generated or edited catalog before selecting it for synchronization
or committing it as the root BuildStreaM `catalog_rhel.json`. Validation
checks:

- required fields and value formats;
- functional-layer-to-group and group-to-package references;
- one `base_os` group per functional layer;
- `os` and `os_version` on base-OS groups;
- duplicate component references;
- package types and their required source fields; and
- unreferenced groups or packages.

See [Add or Remove Packages](../../HowTo/repo_manager/adding_additional_packages.md#verification)
for the catalog validation workflow.

In the managed BuildStreaM GitLab project, only a committed change to the root
`catalog_rhel.json` automatically triggers the build pipeline. Catalogs under
`catalog/` are reference copies and do not automatically trigger a build.
