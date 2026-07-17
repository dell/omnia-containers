# Omnia Automation — Dataset Guide

> **Version**: 3.4 | **Last updated**: 2026-07-17

---

## What Are Datasets?

A **dataset** is a set of Omnia input config files that defines a complete deployment scenario.
The test suite is data-driven — it reads config from the active dataset and automatically
skips or runs tests based on what is enabled. Switching workflows requires **zero test code changes**;
you only change one line in `omnia_test_config.yml`.

---

## Repository Structure

```
datasets/
├── README.md                   ← this file
├── project_default/            ← 17 base config files (reference)
├── templates/                  ← 12 Jinja2 templates (from dell/omnia)
├── user_registry_example/      ← example registry config
│
│   ── Generated TC directories ────────────
├── tc01_production_standard/   ← 17 files (generated from templates)
├── tc02_dell_storage/          ← 17 files (generated from templates)
├── tc03_minimal_hpc/           ← 17 files (generated from templates)
├── tc04_k8s_multisubnet/       ← 17 files (generated from templates)
├── tc05_full_dell_stack/       ← 17 files (generated from templates)
└── tc06_buildstream_x86/       ← 17 files (generated from templates)
```

**In git**: `project_default/` (17 files) + `templates/` (12 `.j2` files) + `utility/generate_datasets.py` + 6 TC directories (17 files each) = 132 files
Each TC directory is **self-contained** with all 17 input files. Files are generated from Jinja2 templates using `utility/generate_datasets.py`.

---

## How It Works

### 1. Template-based TC generation

TC directories are generated from **Jinja2 templates** (sourced from `dell/omnia`)
via `utility/generate_datasets.py`. Each TC's variable overrides are defined in the script; the
templates provide the canonical file structure with comments and formatting. Non-templated
files (`software_config.json`, `security_config.yml`, etc.) are copied from `project_default/`
with TC-specific overrides applied.

> **Important:** TC directories (`tc01_*/` … `tc06_*/`) are **not committed to git**.
> They are generated locally and listed in `.gitignore`. You must run the generation
> command below before your first `molecule converge`.

```bash
# Regenerate all TCs from templates (required after clone or template changes)
python utility/generate_datasets.py --clean

# Regenerate a single TC (partial name matching)
python utility/generate_datasets.py --clean tc05

# Regenerate multiple specific TCs
python utility/generate_datasets.py --clean tc01 tc03 tc05

# Regenerate without deleting existing files (incremental update)
python utility/generate_datasets.py tc05
```

**CLI options:**
- `--clean`: Delete TC directory before regenerating (recommended)
- Positional args: TC name patterns (substring match, e.g., `tc05` matches `tc05_full_dell_stack`)

### 2. Sync to container at runtime

`molecule/shared/tasks/sync_project_default.yml` performs a single rsync of the complete
TC directory to `/opt/omnia/input/project_default` on the container. No two-step merge,
no overlay logic.

### 3. Tests auto-adapt

Tests read config from the container and skip/run based on the effective values:

```
dataset: tc01  → ldms.metrics_enabled: true     → LDMS tests RUN
dataset: tc03  → no K8s, no telemetry           → All telemetry + K8s tests SKIP
dataset: tc02  → dns_enabled: true              → DNS tests RUN
```

---

## Quick Start

```bash
# 0. Activate the virtual environment (if not already active)
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate           # Windows

# 1. Generate TC datasets (required once after clone or template changes)
python utility/generate_datasets.py --clean

# 2. Set the active dataset in omnia_test_config.yml
#    dataset: "tc02_dell_storage"
#    sync_dataset_to_core: true

# 3. Run molecule (syncs dataset to container, then runs tests)
molecule converge -s telemetry
molecule verify -s telemetry
```

---

## Base Config Files (project_default/)

| # | File | Purpose |
|---|------|---------|
| 1 | `software_config.json` | Software stack, architecture, repo_config |
| 2 | `network_spec.yml` | Admin/IB networks, subnets, DNS servers |
| 3 | `provision_config.yml` | PXE, dns_enabled, kernel_override, cloud-init ref |
| 4 | `telemetry_config.yml` | Telemetry sources, sinks, collection targets |
| 5 | `telemetry_storage_config.yml` | Telemetry PVC sizes and resource limits |
| 6 | `storage_config.yml` | NFS/iSCSI mounts, PowerVault, S3 config |
| 7 | `omnia_config.yml` | Slurm clusters, K8s clusters, CSI refs |
| 8 | `omnia_config_credentials.yml` | Credentials (Ansible Vault encrypted at sync) |
| 9 | `local_repo_config.yml` | Repos, registries, RHEL subscription URLs |
| 10 | `build_stream_config.yml` | BuildStream enable/disable |
| 11 | `discovery_config.yml` | BMC/OME discovery |
| 12 | `pxe_mapping_file.csv` | Node inventory (functional groups, IPs, MACs) |
| 13 | `security_config.yml` | Security settings |
| 14 | `high_availability_config.yml` | HA settings |
| 15 | `gitlab_config.yml` | GitLab settings for BuildStream |
| 16 | `additional_cloud_init.yml` | Custom cloud-init write_files/runcmd |
| 17 | `user_registry_credential.yml` | Container registry credentials |

---

## Test Case Coverage

6 TCs cover all **10 axes** (34 options) at least once:

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

## TC Details

### TC-01: Production Standard

Slurm + K8s + LDMS + OpenLDAP, iDRAC+LDMS telemetry, MinIO S3, single-subnet, DNS off, partial repo.

- **Key overrides**: `user_repo_url_x86_64` adds slurm_custom repo; s3 provider set to minio
- **Playbook order**: omnia.sh → prepare_oim → local_repo → build_image_x86_64 → provision → telemetry

### TC-02: Dell Storage + Observability

Slurm + K8s + CSI-PowerScale, iDRAC+LDMS+PowerScale telemetry, PowerScale NFS + S3, DNS on, always repo, cloud-init + OME discovery.

- **Key overrides**: PowerScale mounts, `additional_cloud_init.yml` with custom motd/runcmd, `discovery_config.yml` with OME enabled
- **Playbook order**: omnia.sh → prepare_oim → local_repo → build_image_x86_64 → provision → discovery (OME) → telemetry

### TC-03: Minimal HPC + PowerVault

Slurm-only, no telemetry, PowerVault iSCSI, kernel_version_override, local-disk OIM share.

- **Key overrides**: No K8s cluster, all telemetry disabled, PowerVault config added, only docker-ce + epel repos
- **Playbook order**: omnia.sh → prepare_oim → local_repo → build_image_x86_64 → provision

### TC-04: K8s + Multi-Subnet + RHEL Subscription

K8s-only, iDRAC telemetry, multi-subnet (2 additional), DNS on, RHEL subscription repos, swap on compute.

- **Key overrides**: No Slurm cluster, multi-subnet network, RHEL subscription repos, swap config
- **Playbook order**: omnia.sh → prepare_oim → local_repo → build_image_x86_64 → provision → telemetry

### TC-05: Full Dell Stack (Multi-Arch, Air-Gapped, BuildStream)

Full stack (Slurm + K8s + UCX + OpenMPI + CSI + OpenLDAP), all telemetry (iDRAC + LDMS + PowerScale + VAST), all storage types (PS NFS + VAST NFS + PowerVault iSCSI + PS-S3), multi-arch, air-gapped repos, BuildStream.

- **Key overrides**: All telemetry enabled (incl. UFM + VAST), doubled resource limits, air-gap repo mirrors, user_registry, multi-arch PXE mapping, BuildStream + GitLab enabled
- **Playbook order**: omnia.sh → prepare_oim → local_repo → build_image_x86_64 → build_image_aarch64 → provision → telemetry

**Multi-arch details (TC-05 only):**

- **Mixed-arch cluster provision** — `pxe_mapping_file.csv` contains both `_x86_64` and `_aarch64` functional groups across two subnets (10.50.0.x for x86, 10.50.1.x for ARM)
- **aarch64 Slurm compute with x86_64 control** — `slurm_control_node_x86_64` manages the cluster; `slurm_node_aarch64` nodes serve as compute workers
- **aarch64 LDMS / additional packages** — `software_config.json` sets `ldms` and `additional_packages` with `arch: ["x86_64", "aarch64"]` so images for both architectures include them
- **Cross-arch image build** — `build_stream_config.yml` sets `aarch64_inventory_host_ip` to an ARM build host; the `build_image_aarch64` molecule scenario builds and validates ARM images separately

### TC-06: BuildStream x86_64

Slurm + K8s + LDMS, iDRAC+LDMS telemetry, BuildStream enabled (x86_64 only — no ARM hardware required). VictoriaMetrics in single mode.

- **Key overrides**: BuildStream + GitLab enabled, idrac collection targets (victoria_metrics only, no kafka)
- **Playbook order**: omnia.sh → prepare_oim → local_repo → build_image_x86_64 → provision → telemetry

---

## Dataset Manifest

`dataset_manifest.yml` is **auto-generated** each time `generate_datasets.py` runs. It provides:

- **TC descriptions** and **playbook execution order**
- **Coverage matrix** — which axis option each TC covers
- **File inventory** — all 17 files per TC

```yaml
# Example: machine-readable coverage lookup
coverage_matrix:
  software_stack:
    tc01_production_standard: Slurm+K8s
    tc03_minimal_hpc: Slurm-only
    tc04_k8s_multisubnet: K8s-only
```

> The manifest is gitignored. Run `python utility/generate_datasets.py --clean` to regenerate it.

---

## Adding a New TC

**Option A — Custom overrides file (recommended for user/lab-specific TCs):**

1. Copy the example: `cp datasets/custom_overrides.yml.example datasets/custom_overrides.yml`
2. Define your TC with `metadata`, `overrides`, and optionally `software_config`
3. Run `python utility/generate_datasets.py --clean my_custom_tc`
4. Set `dataset: "my_custom_tc"` in `omnia_test_config.yml`
5. Run `molecule converge` → `molecule verify`

Custom TCs are merged with the built-in 6 TCs and appear in the manifest.
The `custom_overrides.yml` file is gitignored (user-specific).

**Option B — Template-based (for upstream/shared TCs):**

1. Add a new TC entry to `TC_OVERRIDES`, `TC_METADATA`, and `SOFTWARE_CONFIGS` in `utility/generate_datasets.py`
2. Run `python utility/generate_datasets.py --clean my_new_tc`
3. Set `dataset: "my_new_tc"` in `omnia_test_config.yml`
4. Run `molecule converge` → `molecule verify`

**Option C — Manual (quick one-off):**

1. Copy an existing TC directory (e.g., `cp -r tc01_production_standard/ my_new_tc/`)
2. Edit all 17 input files in `my_new_tc/` with your cluster-specific values
3. Set `dataset: "my_new_tc"` in `omnia_test_config.yml`
4. Run `molecule converge` → `molecule verify`

---

## Multi-Dataset Execution — Single Common Framework

The dataset system serves as a **single common framework** for executing across multiple clusters and datasets with minimal additional configuration.

### Architecture

```
datasets/
├── templates/                         ← 12 Jinja2 templates (dell/omnia)
├── project_default/                   ← Base reference dataset (17 files)
├── custom_overrides.yml.example       ← Example for defining custom TCs
├── custom_overrides.yml               ← User-defined custom TCs (gitignored)
├── dataset_manifest.yml               ← Auto-generated coverage manifest (gitignored)
├── tc01_production_standard/          ← TC-01: Generated (17 files, gitignored)
├── tc02_dell_storage/                 ← TC-02: Generated (17 files, gitignored)
├── tc03_minimal_hpc/                  ← TC-03: Generated (17 files, gitignored)
├── tc04_k8s_multisubnet/              ← TC-04: Generated (17 files, gitignored)
├── tc05_full_dell_stack/              ← TC-05: Generated (17 files, gitignored)
├── tc06_buildstream_x86/              ← TC-06: Generated (17 files, gitignored)
└── tc_custom_*/                       ← Custom TCs from custom_overrides.yml (gitignored)
```

Each TC directory contains **all 17 input files** needed for a complete deployment. Files are generated from Jinja2 templates via `utility/generate_datasets.py`. TC directories are **not committed to git** — run the generator after cloning. Every dataset is self-contained and ready to use.

### Input Files (per dataset)

| File | Description |
|------|-------------|
| `software_config.json` | Software packages, arch support, repo policy |
| `network_spec.yml` | Admin/IB networks, subnets, DNS, NTP |
| `provision_config.yml` | PXE mapping path, DNS, kernel override, cloud-init |
| `omnia_config.yml` | Slurm + K8s cluster definitions |
| `storage_config.yml` | NFS/VAST/PowerVault mounts, S3 config |
| `telemetry_config.yml` | Telemetry sources, bridges, sinks |
| `telemetry_storage_config.yml` | VictoriaMetrics, Kafka, Vector resource limits |
| `local_repo_config.yml` | User repos, RHEL subscriptions, air-gap mirrors |
| `discovery_config.yml` | BMC discovery, OME endpoint |
| `build_stream_config.yml` | BuildStream CI/CD pipeline settings |
| `gitlab_config.yml` | GitLab deployment config |
| `high_availability_config.yml` | K8s HA virtual IP |
| `security_config.yml` | LDAP connection type |
| `additional_cloud_init.yml` | Custom cloud-init for node provisioning |
| `omnia_config_credentials.yml` | Credentials (auto-encrypted via Vault) |
| `user_registry_credential.yml` | Container registry credentials |
| `pxe_mapping_file.csv` | Node inventory (MACs, IPs, groups) |

### How It Works

1. **Select a dataset** — Change one line in `omnia_test_config.yml`:
   ```yaml
   dataset: "tc05_full_dell_stack"    # ← switch to any TC
   ```

2. **Sync to OIM** — At converge time, the entire dataset directory is rsync'd to `/opt/omnia/input/project_default` inside the container. Single rsync, no two-step merge.

3. **Data-driven tests** — The test suite reads config from the active dataset and automatically skips or runs tests based on what is enabled. **Zero test code changes** needed when switching between datasets.

### Onboarding a New Cluster / Dataset

```bash
# 1. Copy an existing TC as starting point
cp -r datasets/tc01_production_standard/ datasets/my_new_cluster/

# 2. Edit the files with your cluster-specific values
vi datasets/my_new_cluster/network_spec.yml
vi datasets/my_new_cluster/software_config.json
# ... edit other files as needed

# 3. Point the config and run
# Edit omnia_test_config.yml: dataset: "my_new_cluster"
./run_molecule.sh telemetry test
```

### Scalability

- **Template-driven** — TC files are generated from Jinja2 templates (sourced from `dell/omnia`) ensuring consistency with upstream
- **Self-contained** — Each TC directory has all 17 files; no runtime generation needed
- **Version-controlled** — All TC files are committed to the repo; `git diff` shows exactly what changed per TC
- **One-line switch** — Change `dataset:` in `omnia_test_config.yml` to target any cluster
- **Test reuse** — The same molecule scenarios and test code work across all datasets without modification
- **Easy onboarding** — Add TC overrides to `utility/generate_datasets.py` and run; or copy an existing TC for quick one-off use

---

## Notes

- **Destination is always `/opt/omnia/input/project_default`** — Omnia reads from this fixed path regardless of which dataset was synced
- **Credentials** are auto-encrypted via Ansible Vault during sync; override `omnia_config_credentials.yml` in a TC only if credentials differ from base
- **`pxe_mapping_file.csv`** uses placeholder MACs/IPs; replace with actual hardware values for real deployments
- **Air-gapped (TC-05)** requires a pre-populated repo mirror at the URLs in `local_repo_config.yml`
- **Multi-arch (TC-05)** requires an aarch64 build host (`aarch64_inventory_host_ip` in `build_stream_config.yml`). The automation handles mixed-arch clusters end-to-end: cross-arch image build via `molecule/build_image_aarch64`, heterogeneous provision (x86_64 control + aarch64 compute), and arch-aware package verification. All helper functions (e.g., `get_slurm_compute_nodes()`) automatically query both `_x86_64` and `_aarch64` functional groups
