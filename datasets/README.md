# Omnia Automation — Dataset Guide

## What Is a Dataset?

A **dataset** is a complete set of 17 Omnia input config files that defines a
deployment scenario (network, software, storage, telemetry, etc.). Each test
case (TC) gets its own dataset. To switch scenarios you change **one line** in
`omnia_test_config.yml` — no test code changes required.

---

## Prerequisites

```bash
# Activate the virtual environment
source .venv/bin/activate          # Linux / macOS
# .venv\Scripts\activate           # Windows
```

> **Dependencies:** `jinja2` and `pyyaml` (both included in the standard
> Omnia dev environment / venv).

---

## Generating Datasets

TC directories are **not committed to git**. You must generate them locally
after cloning or whenever templates change.

### Generate all datasets

```bash
python utility/generate_datasets.py --clean
```

### Generate a specific dataset (partial name match)

```bash
python utility/generate_datasets.py --clean tc05
```

### Generate multiple specific datasets

```bash
python utility/generate_datasets.py --clean tc01 tc03 tc05
```

### Incremental update (keep existing files, overwrite only changed)

```bash
python utility/generate_datasets.py tc05
```

### Command reference

| Flag / Argument | Description |
|-----------------|-------------|
| `--clean` | Delete the TC directory before regenerating (recommended) |
| `tc01`, `tc05`, … | TC name patterns — substring match (e.g. `tc05` matches `tc05_full_dell_stack`) |
| *(no args)* | Generate **all** 6 built-in TCs |

---

## Using a Dataset

```bash
# 1. Generate datasets (one-time after clone)
python utility/generate_datasets.py --clean

# 2. Set the active dataset in omnia_test_config.yml
#    dataset: "tc02_dell_storage"
#    sync_dataset_to_core: true

# 3. Run molecule (syncs dataset to OIM container, then runs tests)
molecule converge -s telemetry
molecule verify  -s telemetry
```

When molecule runs, the selected TC directory is rsync'd to
`/opt/omnia/input/project_default` on the container. Tests auto-adapt —
they read config and skip or run based on what is enabled.

---

## Dataset Overview

6 built-in TCs cover **10 configuration axes** (34 options) at least once.

| TC | Name | What It Tests |
|----|------|---------------|
| **TC-01** | Production Standard | Slurm + K8s + LDMS + OpenLDAP, iDRAC telemetry, MinIO S3, single-subnet, DNS off, partial repos |
| **TC-02** | Dell Storage + Observability | Slurm + K8s + CSI-PowerScale, PowerScale NFS + S3 telemetry, DNS on, always repos, cloud-init, OME discovery |
| **TC-03** | Minimal HPC + PowerVault | Slurm-only (no K8s), no telemetry, PowerVault iSCSI, kernel override, local-disk OIM share, minimal repos |
| **TC-04** | K8s + Multi-Subnet | K8s-only (no Slurm), iDRAC telemetry, 2 additional subnets, DNS on, RHEL subscription repos, swap on compute |
| **TC-05** | Full Dell Stack | Everything enabled — Slurm + K8s + all storage + all telemetry, multi-arch (x86 + aarch64), air-gapped repos, BuildStream |
| **TC-06** | BuildStream x86 | Slurm + K8s + LDMS, BuildStream + GitLab enabled (x86-only), VictoriaMetrics single mode |

### Coverage Matrix

| Axis | TC-01 | TC-02 | TC-03 | TC-04 | TC-05 | TC-06 |
|------|-------|-------|-------|-------|-------|-------|
| **A** Software | Slurm+K8s | Slurm+K8s | Slurm-only | K8s-only | Slurm+K8s+MinOS | Slurm+K8s |
| **B** Telemetry | iDRAC+LDMS | +PowerScale | None | iDRAC | +VAST | iDRAC+LDMS |
| **C** Storage | None | PowerScale | PowerVault | None | PS+PV+VAST | None |
| **D** S3 | MinIO | PS-S3 | MinIO | MinIO | PS-S3 | MinIO |
| **E** Network | Single | Single | Single | Multi | Multi | Single |
| **F** DNS | Off | On | Off | On | On | Off |
| **G** Arch | x86 | x86 | x86 | x86 | Multi | x86 |
| **H** OIM Share | NFS-Ext | NFS-Int | Local | NFS-Ext | NFS-Ext | NFS-Ext |
| **I** Repo | partial | always | partial | RHEL-sub | air-gap | partial |
| **J** Options | OpenLDAP | cloud-init, OME | kernel_override | Swap | BuildStream | BuildStream |

---

## Dataset Details

### TC-01: Production Standard

Standard Slurm + K8s cluster with LDMS telemetry and OpenLDAP.

- **Software:** Slurm + K8s
- **Telemetry:** iDRAC + LDMS
- **Storage:** MinIO S3
- **Network:** Single subnet, DNS off, partial repos
- **Playbook order:** omnia.sh → prepare_oim → local_repo →
  build_image_x86_64 → provision → telemetry

### TC-02: Dell Storage + Observability

Adds Dell PowerScale NFS + S3 storage with OME discovery and cloud-init.

- **Software:** Slurm + K8s + CSI-PowerScale
- **Telemetry:** iDRAC + LDMS + PowerScale metrics
- **Storage:** PowerScale NFS mounts + PowerScale S3
- **Network:** Single subnet, DNS on, always repos
- **Extras:** cloud-init (custom motd/runcmd), OME discovery
- **Playbook order:** omnia.sh → prepare_oim → local_repo →
  build_image_x86_64 → provision → discovery (OME) → telemetry

### TC-03: Minimal HPC + PowerVault

Minimal Slurm-only cluster — no K8s, no telemetry, no frills.

- **Software:** Slurm only
- **Telemetry:** None (all disabled)
- **Storage:** PowerVault iSCSI
- **Network:** Single subnet, DNS off, minimal repos (docker-ce + epel)
- **Extras:** kernel version override, local-disk OIM share
- **Playbook order:** omnia.sh → prepare_oim → local_repo →
  build_image_x86_64 → provision

### TC-04: K8s + Multi-Subnet + RHEL Subscription

K8s-only cluster with multiple subnets and RHEL subscription repos.

- **Software:** K8s only (no Slurm)
- **Telemetry:** iDRAC only
- **Storage:** None
- **Network:** Multi-subnet (2 additional subnets), DNS on
- **Extras:** RHEL subscription repos, swap on compute nodes
- **Playbook order:** omnia.sh → prepare_oim → local_repo →
  build_image_x86_64 → provision → telemetry

### TC-05: Full Dell Stack (Multi-Arch, Air-Gapped)

Everything enabled — the "kitchen sink" test case.

- **Software:** Slurm + K8s + UCX + OpenMPI + CSI + OpenLDAP
- **Telemetry:** iDRAC + LDMS + PowerScale + VAST + UFM
- **Storage:** PowerScale NFS + VAST NFS + PowerVault iSCSI + PS-S3
- **Network:** Multi-subnet, DNS on, air-gapped repo mirrors
- **Architecture:** Multi-arch (x86_64 + aarch64)
- **Extras:** BuildStream + GitLab, user_registry, doubled resource limits
- **Playbook order:** omnia.sh → prepare_oim → local_repo →
  build_image_x86_64 → build_image_aarch64 → provision → telemetry

**Multi-arch notes:**
- PXE mapping includes both `_x86_64` and `_aarch64` functional groups
  (10.50.0.x for x86, 10.50.1.x for ARM)
- x86_64 Slurm control plane manages aarch64 compute workers
- `software_config.json` sets `ldms` and `additional_packages` with
  `arch: ["x86_64", "aarch64"]`
- Requires an aarch64 build host (set via
  `aarch64_inventory_host_ip` in `build_stream_config.yml`)

### TC-06: BuildStream x86

BuildStream CI/CD pipeline testing without ARM hardware.

- **Software:** Slurm + K8s + LDMS
- **Telemetry:** iDRAC + LDMS (VictoriaMetrics single mode, no Kafka)
- **Storage:** None
- **Network:** Single subnet, DNS off, partial repos
- **Extras:** BuildStream + GitLab enabled (x86-only)
- **Playbook order:** omnia.sh → prepare_oim → local_repo →
  build_image_x86_64 → provision → telemetry

---

## Files in Each Dataset

Every TC directory contains these 17 input files:

| # | File | What It Configures |
|---|------|--------------------|
| 1 | `software_config.json` | Software packages, architecture, repo policy |
| 2 | `network_spec.yml` | Admin/IB networks, subnets, DNS, NTP |
| 3 | `provision_config.yml` | PXE mapping, DNS toggle, kernel override, cloud-init |
| 4 | `omnia_config.yml` | Slurm + K8s cluster definitions |
| 5 | `omnia_config_credentials.yml` | Credentials (auto-encrypted via Vault) |
| 6 | `storage_config.yml` | NFS/VAST/PowerVault mounts, S3 config |
| 7 | `telemetry_config.yml` | Telemetry sources, sinks, collection targets |
| 8 | `telemetry_storage_config.yml` | VictoriaMetrics, Kafka, Vector resource limits |
| 9 | `local_repo_config.yml` | Repos, registries, RHEL subscriptions, air-gap mirrors |
| 10 | `discovery_config.yml` | BMC / OME discovery settings |
| 11 | `security_config.yml` | LDAP connection type |
| 12 | `high_availability_config.yml` | K8s HA virtual IP |
| 13 | `build_stream_config.yml` | BuildStream CI/CD pipeline settings |
| 14 | `gitlab_config.yml` | GitLab deployment config |
| 15 | `additional_cloud_init.yml` | Custom cloud-init (write_files / runcmd) |
| 16 | `user_registry_credential.yml` | Container registry credentials |
| 17 | `pxe_mapping_file.csv` | Node inventory (MACs, IPs, functional groups) |

---

## Folder Structure

```
datasets/
├── README.md                        ← This file
├── project_default/                 ← 17 base config files (reference/defaults)
├── templates/                       ← 12 Jinja2 templates (from dell/omnia)
├── custom_overrides.yml.example     ← Example for defining custom TCs
├── user_registry_example/           ← Example registry config
│
│   ── Generated (gitignored) ──────
├── tc01_production_standard/        ← 17 generated files
├── tc02_dell_storage/               ← 17 generated files
├── tc03_minimal_hpc/                ← 17 generated files
├── tc04_k8s_multisubnet/            ← 17 generated files
├── tc05_full_dell_stack/            ← 17 generated files
├── tc06_buildstream_x86/            ← 17 generated files
├── custom_overrides.yml             ← User-defined custom TCs (gitignored)
└── dataset_manifest.yml             ← Auto-generated coverage manifest (gitignored)
```

---

## Adding a New Dataset

### Option A — Custom overrides file (recommended)

Best for user-specific or lab-specific TCs.

1. `cp datasets/custom_overrides.yml.example datasets/custom_overrides.yml`
2. Define your TC with `metadata`, `overrides`, and optionally `software_config`
   (see the example file for the full structure)
3. `python utility/generate_datasets.py --clean my_custom_tc`
4. Set `dataset: "my_custom_tc"` in `omnia_test_config.yml`
5. `molecule converge` → `molecule verify`

Custom TCs are merged with the built-in 6 TCs and appear in the manifest.
The `custom_overrides.yml` file is gitignored (user-specific). YAML syntax
is validated automatically — errors are reported with line numbers.

### Option B — Add to the generator script (for shared/upstream TCs)

1. Add entries to `TC_OVERRIDES`, `TC_METADATA`, and `SOFTWARE_CONFIGS`
   in `utility/generate_datasets.py`
2. `python utility/generate_datasets.py --clean my_new_tc`
3. Set `dataset: "my_new_tc"` in `omnia_test_config.yml`
4. `molecule converge` → `molecule verify`

### Option C — Manual copy (quick one-off)

1. `cp -r datasets/tc01_production_standard/ datasets/my_cluster/`
2. Edit the 17 files with your cluster-specific values
3. Set `dataset: "my_cluster"` in `omnia_test_config.yml`
4. `molecule converge` → `molecule verify`

---

## Dataset Manifest

`dataset_manifest.yml` is auto-generated each time the generator runs. It
contains TC descriptions, playbook execution order, coverage metadata, and
a file inventory for every TC.

```yaml
# Example snippet
coverage_matrix:
  software_stack:
    tc01_production_standard: Slurm+K8s
    tc03_minimal_hpc: Slurm-only
    tc04_k8s_multisubnet: K8s-only
```

> The manifest is gitignored. Regenerate it with
> `python utility/generate_datasets.py --clean`.

---

## Important Notes

- TC directories are **generated locally** and listed in `.gitignore` —
  always run the generator after cloning
- Omnia reads config from `/opt/omnia/input/project_default` — the
  selected TC directory is rsync'd there at converge time
- Credentials in `omnia_config_credentials.yml` are auto-encrypted via
  Ansible Vault during sync
- `pxe_mapping_file.csv` uses placeholder MACs/IPs — replace with actual
  hardware values for real deployments
- Air-gapped mode (TC-05) requires a pre-populated repo mirror at the
  URLs defined in `local_repo_config.yml`
- Multi-arch (TC-05) requires an aarch64 build host configured via
  `aarch64_inventory_host_ip` in `build_stream_config.yml`
