# Omnia Automation — Dataset Guide

> **Version**: 3.1 | **Last updated**: 2026-07-14

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
├── dataset_manifest.yml        ← defines all 6 TCs (source of truth)
├── generate_datasets.py        ← generates TC overlay directories
├── README.md                   ← this file
├── project_default/            ← 17 base config files (always committed)
├── user_registry_example/      ← example registry config
│
│   ── Generated (gitignored) ──────────────────────────
├── tc01_production_standard/   ← 8 overlay files
├── tc02_dell_storage/          ← 9 overlay files
├── tc03_minimal_hpc/           ← 8 overlay files
├── tc04_k8s_multisubnet/       ← 8 overlay files
├── tc05_full_dell_stack/       ← 13 overlay files
└── tc06_buildstream_x86/       ← 9 overlay files
```

**In git**: `dataset_manifest.yml` + `generate_datasets.py` + `project_default/` + `README.md` (21 files)
**Generated locally**: 55 overlay files across 6 TC directories (gitignored)

---

## How It Works

### 1. Manifest defines overrides

`dataset_manifest.yml` contains one block per TC with **only the values that differ** from `project_default/`:

```yaml
tc01_production_standard:
  software_config.json:
    repo_config: "partial"
    softwares:
      - { name: "openldap", arch: ["x86_64"] }
      - { name: "slurm_custom", arch: ["x86_64"] }
      ...
  provision_config.yml:
    dns_enabled: false
  telemetry_config.yml:
    telemetry_sources:
      idrac:
        metrics_enabled: true
      ...
```

### 2. Generator produces overlay directories

`generate_datasets.py` reads the manifest, deep-merges each TC's overrides with the
base files in `project_default/`, and writes only the changed files into `datasets/<tc_name>/`.

```bash
# Generate all 6 TCs
python datasets/generate_datasets.py --clean

# Generate specific TCs (partial name match supported)
python datasets/generate_datasets.py tc01 tc05

# Preview without writing files
python datasets/generate_datasets.py --dry-run
```

The generator also validates that all output files parse correctly (JSON, YAML, CSV).

### 3. Sync playbook applies overlays at runtime

`molecule/shared/tasks/sync_project_default.yml` performs a two-step rsync:

1. **Base** — copies `datasets/project_default/` → `/opt/omnia/input/project_default` on the container
2. **Overlay** — copies `datasets/<tc_name>/` on top, overwriting only the files that exist in the overlay

Files not present in the TC directory (e.g., `security_config.yml`, `high_availability_config.yml`)
inherit their base values automatically. Credentials are encrypted via Ansible Vault after sync.

### 4. Tests auto-adapt

Tests read config from the container and skip/run based on the effective values:

```
dataset: tc01  → ldms.metrics_enabled: true     → LDMS tests RUN
dataset: tc03  → no K8s, no telemetry           → All telemetry + K8s tests SKIP
dataset: tc02  → dns_enabled: true              → DNS tests RUN
```

---

## Quick Start

```bash
# 1. Generate the TC overlay directories (required after git clone/pull)
python datasets/generate_datasets.py --clean

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

- **Overlay files**: `software_config.json`, `network_spec.yml`, `provision_config.yml`, `telemetry_config.yml`, `storage_config.yml`, `omnia_config.yml`, `pxe_mapping_file.csv`, `local_repo_config.yml`
- **Playbook order**: omnia.sh → prepare_oim → local_repo → build_image_x86_64 → provision → telemetry

### TC-02: Dell Storage + Observability

Slurm + K8s + CSI-PowerScale, iDRAC+LDMS+PowerScale telemetry, PowerScale NFS + S3, DNS on, always repo, cloud-init + OME discovery.

- **Overlay files**: above + `additional_cloud_init.yml`, `discovery_config.yml`
- **Playbook order**: omnia.sh → prepare_oim → local_repo → build_image_x86_64 → provision → discovery (OME) → telemetry

### TC-03: Minimal HPC + PowerVault

Slurm-only, no telemetry, PowerVault iSCSI, kernel_version_override, local-disk OIM share.

- **Overlay files**: `software_config.json`, `network_spec.yml`, `provision_config.yml`, `telemetry_config.yml`, `storage_config.yml`, `omnia_config.yml`, `pxe_mapping_file.csv`, `local_repo_config.yml`
- **Playbook order**: omnia.sh → prepare_oim → local_repo → build_image_x86_64 → provision

### TC-04: K8s + Multi-Subnet + RHEL Subscription

K8s-only, iDRAC telemetry, multi-subnet (2 additional), DNS on, RHEL subscription repos, swap on compute.

- **Overlay files**: `software_config.json`, `network_spec.yml`, `provision_config.yml`, `telemetry_config.yml`, `storage_config.yml`, `omnia_config.yml`, `pxe_mapping_file.csv`, `local_repo_config.yml`
- **Playbook order**: omnia.sh → prepare_oim → local_repo → build_image_x86_64 → provision → telemetry

### TC-05: Full Dell Stack (Multi-Arch, Air-Gapped, BuildStream)

Full stack (Slurm + K8s + UCX + OpenMPI + CSI + OpenLDAP), all telemetry (iDRAC + LDMS + PowerScale + VAST), all storage types (PS NFS + VAST NFS + PowerVault iSCSI + PS-S3), multi-arch, air-gapped repos, BuildStream.

- **Overlay files**: 13 files (most extensive TC)
- **Playbook order**: omnia.sh → prepare_oim → local_repo → build_image_x86_64 → build_image_aarch64 → provision → telemetry

### TC-06: BuildStream x86_64

Slurm + K8s + LDMS, iDRAC+LDMS telemetry, BuildStream enabled (x86_64 only — no ARM hardware required). VictoriaMetrics in single mode.

- **Overlay files**: `software_config.json`, `network_spec.yml`, `provision_config.yml`, `telemetry_config.yml`, `storage_config.yml`, `omnia_config.yml`, `pxe_mapping_file.csv`, `build_stream_config.yml`, `gitlab_config.yml`
- **Playbook order**: omnia.sh → prepare_oim → local_repo → build_image_x86_64 → provision → telemetry

---

## Adding a New TC

1. Add a block to `dataset_manifest.yml` — only include values that differ from `project_default/`
2. Run `python datasets/generate_datasets.py my_new_tc`
3. Set `dataset: "my_new_tc"` in `omnia_test_config.yml`
4. Run `molecule converge` → `molecule verify`

---

## Notes

- **After `git clone` or `git pull`**, run `python datasets/generate_datasets.py --clean` to regenerate TC directories
- **Destination is always `/opt/omnia/input/project_default`** — Omnia reads from this fixed path regardless of which dataset was synced
- **Credentials** are auto-encrypted via Ansible Vault during sync; override `omnia_config_credentials.yml` in a TC only if credentials differ from base
- **`pxe_mapping_file.csv`** uses placeholder MACs/IPs; replace with actual hardware values for real deployments
- **Air-gapped (TC-05)** requires a pre-populated repo mirror at the URLs in `local_repo_config.yml`
- **Multi-arch (TC-05)** requires an aarch64 build host (`aarch64_inventory_host_ip` in `build_stream_config.yml`)
