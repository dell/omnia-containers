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
- An approved coding agent with access to the checkout.
- The catalogs or catalog requirements needed for the requested operation.

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

### Core catalog generation examples

The following examples demonstrate common catalog generation scenarios for
different cluster configurations:

**1. Minimal Slurm Cluster (x86_64, RHEL 10.2)**

```text
Follow the catalog-generation skill and create a RHEL 10.2 Slurm catalog with
x86_64 controller, compute, login and compiler nodes. Include NVIDIA GPU support
on compute and compiler nodes, InfiniBand, and VAST job storage.
```

**2. Slurm Cluster with Generic NFS (No VAST)**

```text
Follow the catalog-generation skill and create a RHEL 10.2 Slurm catalog with
x86_64 controller, compute, login and compiler nodes. Include NVIDIA GPU support
on compute and compiler nodes, InfiniBand, and Generic NFS job storage.
```

**3. CPU-Only Slurm Cluster (No GPU)**

```text
Follow the catalog-generation skill and create a RHEL 10.2 Slurm catalog with
x86_64 controller, compute, login and compiler nodes. Exclude GPU support
(CPU-only), include InfiniBand, and VAST job storage.
```

**4. ARM64 Slurm Cluster (aarch64)**

```text
Follow the catalog-generation skill and create a RHEL 10.2 Slurm catalog with
aarch64 controller, compute, login and compiler nodes. Include NVIDIA GPU support
on compute and compiler nodes, InfiniBand, and VAST job storage.
```

**5. Mixed Architecture Cluster (x86_64 + aarch64)**

```text
Follow the catalog-generation skill and create a RHEL 10.2 Slurm catalog with
x86_64 controller and aarch64 compute, login and compiler nodes. Include NVIDIA
GPU support on compute and compiler nodes, InfiniBand, and VAST job storage.
```

**6. Kubernetes-Only Cluster**

```text
Follow the catalog-generation skill and create a RHEL 10.2 Kubernetes catalog
with x86_64 control-plane and worker nodes. Include InfiniBand and PowerScale
CSI storage.
```

**7. Mixed Stack Cluster (Slurm + Kubernetes)**

```text
Follow the catalog-generation skill and create a RHEL 10.2 catalog with Slurm
and Kubernetes stacks. For Slurm: x86_64 controller, compute, login and compiler
nodes with NVIDIA GPU support, InfiniBand, and VAST job storage. For Kubernetes:
x86_64 control-plane and worker nodes with PowerScale CSI storage.
```

**8. Hybrid OS Version Cluster (RHEL 10.2 + 10.0)**

```text
Follow the catalog-generation skill and create a hybrid RHEL 10.2 and 10.0
Slurm catalog. Use RHEL 10.2 for x86_64 controller nodes and RHEL 10.0 for
aarch64 compute, login and compiler nodes. Include NVIDIA GPU support on compute
and compiler nodes, InfiniBand, and VAST job storage.
```

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

Additional example invocations:

```text
Follow the bulk-edit-catalog skill and add htop to the admin_debug groups in
slurm_x86_64.json and service_k8s_x86_64.json catalogs.
```

```text
Follow the bulk-edit-catalog skill and remove emacs from every catalog under
<catalog-root> that includes it.
```

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

Additional example invocations:

```text
Follow the impact-analysis skill and explain what would be affected if I
removed iproute from the base-OS group in slurm_x86_64.json catalog.
```

```text
Follow the impact-analysis skill and assess removing NVIDIA GPU support from
slurm_x86_64.json catalog.
```

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

Provide both catalog files.

Additional example invocations:

```text
Follow the catalog-diff skill and compare <current-catalog> with
<updated-catalog>.
```

```text
Follow the catalog-diff skill and show what changed between the RHEL 10.0 and
RHEL 10.2 Slurm x86_64 catalogs.
```

## Verification

Verify that:

- The result reflects the intended catalog and requested scope.
- Any unresolved information is clearly identified, and all proposed catalog
  changes are reviewed and approved before they are applied.

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

Provide the catalog path to a coding agent with repository access.

### The request is ambiguous

Specify the catalog, requested operation, target package or component, and the
affected group, functional layer, operating system, or architecture.
