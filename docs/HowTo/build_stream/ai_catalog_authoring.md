# Use AI-Assisted Catalog Authoring Skills

## Overview

Omnia provides optional AI-assisted skills for generating, editing, analyzing,
and comparing BuildStreaM catalogs. Invoke the skill that matches the catalog
task you want to perform.

| Skill | What it does |
|---|---|
| Catalog generation | Creates a catalog from the cluster roles, operating systems, architectures, software stacks, storage, network, packages, and sources that you provide. |
| Catalog editing | Adds, removes, or updates content in one existing catalog after presenting the proposed change for approval. |
| Bulk catalog editing | Applies the same requested change independently to multiple matching catalogs. |
| Impact analysis | Reports the effect of a proposed package, group, functional-layer, source, version, or operating-system change within one catalog. |
| Compatibility analysis | Investigates package dependencies and checks compatibility with the requested operating system, architecture, package, driver, or kernel. |
| Catalog comparison | Compares two catalogs and produces forward and reverse machine-readable differences and a customer-readable changelog. |

The catalog selection gate, connectivity procedure, working-directory
procedure, and pre-edit gate are companion instructions used by these skills.
Do not invoke the companion instructions directly.

## Prerequisites

- Access to an Omnia source checkout that contains
  `src/build_stream/ai_skills/`.
- An approved coding agent with access to the checkout, or a browser-based AI
  assistant.
- The catalogs or catalog requirements needed for the requested operation.
- For a browser-based assistant, the selected skill file and every companion
  file required by that skill from the same Omnia checkout.

## Procedure

### Invoke a skill from a coding agent

1. Open the Omnia source checkout in the coding agent.
2. Identify the `SKILL.md` file for the required operation.
3. Instruct the coding agent to read the selected skill and its required
   companion files from the same checkout.
4. Provide the request and identify the catalog files involved.
5. Answer any questions needed to resolve missing information.
6. Review and explicitly approve a proposed catalog edit before the agent
   applies it.

### Invoke a skill from a browser-based AI assistant

1. Provide the complete contents of the required `SKILL.md` file to the
   assistant.
2. Provide every companion instruction or reference file identified by the
   skill. Use files from the same Omnia checkout.
3. Provide the complete catalog content required for the operation.
4. State the requested outcome.
5. Review the result before applying it to a catalog file.

A browser-based assistant without shell or file-system access cannot perform
local catalog validation or deterministic catalog comparison. It must identify
the output as unvalidated when those checks cannot be performed.

### Generate a catalog

Use:

```text
src/build_stream/ai_skills/catalog-generation/SKILL.md
```

Example invocation:

```text
Follow the catalog-generation skill and create a catalog for the following
cluster configuration: <cluster-requirements>.
```

Provide the known cluster roles, operating systems, architectures, software
stacks, storage, network, packages, sources, and output requirements. The skill
asks for missing decisions and presents the configuration for confirmation
before creating the catalog.

### Edit one catalog

Use:

```text
src/build_stream/ai_skills/catalog-editing/SKILL.md
```

Example invocation:

```text
Follow the catalog-editing skill and add <package> to <group> in
<catalog-path>.
```

Identify the target catalog and the exact package, group, layer, version,
source, or metadata change. The skill presents the proposed edit for explicit
approval before applying it.

### Edit multiple catalogs

Use:

```text
src/build_stream/ai_skills/bulk-edit-catalog/SKILL.md
```

Example invocation:

```text
Follow the bulk-edit-catalog skill and apply <change> to every catalog under
<catalog-root> that matches <condition>.
```

Provide the catalog root, matching condition, and requested change. The skill
handles and reports each matching catalog independently.

### Analyze the impact of a proposed change

Use:

```text
src/build_stream/ai_skills/impact-analysis/SKILL.md
```

Example invocation:

```text
Follow the impact-analysis skill and report the effect of removing <target>
from <catalog-path>.
```

Identify the catalog, target, proposed operation, and scope. The skill reports
the affected catalog content and its impact.

### Analyze compatibility and dependencies

Use:

```text
src/build_stream/ai_skills/compatibility-analysis/SKILL.md
```

Example invocation:

```text
Follow the compatibility-analysis skill and check whether <package-version>
is compatible with <operating-system-and-architecture>.
```

Provide the package, version, target operating system, architecture, consuming
role, and installation method when known. For a driver check, also provide the
target kernel and driver versions.

### Compare two catalogs

Use:

```text
src/build_stream/ai_skills/catalog-diff/SKILL.md
```

Example invocation:

```text
Follow the catalog-diff skill and compare <current-catalog> with
<future-catalog>.
```

Provide both catalog files. Use a coding agent with shell access when
machine-readable forward and reverse differences are required.

## Verification

Confirm that:

- The assistant used the requested skill file.
- All companion files came from the same Omnia checkout.
- The correct catalogs and requested scope were used.
- The result identifies unresolved information instead of supplying assumed
  values.
- No catalog edit was applied without explicit approval.
- A browser-generated result states when local validation or deterministic
  comparison could not be performed.

## Next steps

- Review the generated output before using or applying it.
- Invoke another catalog skill only when another catalog operation is needed.

## Troubleshooting

### The assistant cannot find a skill

Provide the exact `SKILL.md` path from this guide and confirm that the file
exists in the selected Omnia checkout.

### A companion file is unavailable

Provide the missing file from the same `src/build_stream/ai_skills/` tree. Do
not substitute a similarly named file from another checkout.

### The assistant cannot access a catalog

Provide the catalog path to a coding agent with repository access. For a
browser-based assistant, provide the complete catalog content.

### A browser-based assistant cannot validate or compare catalogs

Use a coding agent with shell access for local validation or deterministic
comparison. Browser-based assistants must identify output that could not be
checked locally as unvalidated.

### The request is ambiguous

Specify the catalog, requested operation, target package or component, and the
affected group, functional layer, operating system, or architecture.
