# Component Specification (SDD)
# Telemetry Config Input Restructuring

| | |
|---|---|
| **Document Type** | Component Specification / Software Design Document (SDD) |
| **Version** | 1.0 |
| **Date** | 04/23/2026 |
| **Author** | Abhishek S A |
| **Related HLD** | Telemetry_Config_Input_Restructuring_Engineering_Spec(HLD).md v0.2 |
| **PR Reference** | dell/omnia #4299 |

---

**Dell Confidential - Internal Use Only**

Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.

---

## Table of Contents

- [1 Overview](#1-overview)
- [2 Component 1 — Input File (telemetry_config.yml)](#2-component-1--input-file-telemetry_configyml)
- [3 Component 2 — JSON Schema (telemetry_config.json)](#3-component-2--json-schema-telemetry_configjson)
- [4 Component 3 — Sink Support Flag Derivation (derive_sink_support_flags.yml)](#4-component-3--sink-support-flag-derivation-derive_sink_support_flagsyml)
- [5 Component 4 — L2 Validation Module (telemetry_validation.py)](#5-component-4--l2-validation-module-telemetry_validationpy)
- [6 Component 5 — Input Validation Registration](#6-component-5--input-validation-registration)
- [7 Component 6 — Ansible Task Orchestration (main.yml)](#7-component-6--ansible-task-orchestration-mainyml)
- [8 Component 7 — Deployment Generation (generate_telemetry_deployments.yml)](#8-component-7--deployment-generation-generate_telemetry_deploymentsyml)
- [9 Component 8 — Jinja2 Template Updates](#9-component-8--jinja2-template-updates)
- [10 Component 9 — Ansible Role Validation (validate_telemetry_config.yml)](#10-component-9--ansible-role-validation-validate_telemetry_configyml)
- [11 Interface Summary](#11-interface-summary)

---

## 1 Overview

This document is the **Component Specification (SDD)** for the Telemetry Config Input Restructuring. It provides code-level design for each component, including the actual implementation code with annotations.

### 1.1 Component Map

```
┌─────────────────────────────────────────────────────────────────┐
│  INPUT LAYER                                                     │
│  telemetry_config.yml (Component 1)                              │
│  telemetry_config.json schema (Component 2)                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ include_vars
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  VALIDATION LAYER (Pre-run)                                      │
│  config.py + logical_validation.py (Component 5)                 │
│  telemetry_validation.py (Component 4)                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │ ansible-playbook run
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  ORCHESTRATION LAYER                                             │
│  main.yml (Component 6)                                          │
│    └─► derive_sink_support_flags.yml (Component 3)               │
│    └─► generate_telemetry_deployments.yml (Component 7)          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ ansible.builtin.template
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  RENDERING LAYER                                                 │
│  Jinja2 Templates (Component 8)                                  │
│  victoria-*.yaml.j2, victorialogs-*.yaml.j2                      │
│  kustomization.yaml.j2, idrac_telemetry_statefulset.yaml.j2      │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Collection target names use `victoria_metrics` / `victoria_logs` | Underscored naming aligns with Ansible variable convention; avoids confusion with the product name vs. the sink identifier |
| No separate `map_telemetry_config_params.yml` | Folded into `derive_sink_support_flags.yml`; scope reduced because all templates and tasks were migrated to direct variable usage |
| `telemetry_sinks` requires all three sinks (victoria_metrics, victoria_logs, kafka) | Simplifies schema (no conditional blocks); unused sinks have zero cost when not targeted |
| `topic_partitions` changed from array to dict | Cleaner YAML; dict keys are inherently unique; eliminates manual duplicate validation |
| Dedicated `telemetry_validation.py` module | Separates telemetry validation from `common_validation.py`; easier unit testing; allows independent evolution |

---

## 2 Component 1 — Input File (telemetry_config.yml)

**File:** `input/telemetry_config.yml`

### 2.1 Complete Structure

```yaml
# telemetry_config.yml — New three-layer Sources → Bridges → Sinks structure

# =============================================================================
# LAYER 1: SOURCES — Data collectors (what collects telemetry data)
# =============================================================================
telemetry_sources:

  idrac:
    metrics_enabled: true                        # boolean | was: idrac_telemetry_support
    collection_targets:                          # array<enum> | was: telemetry_collection_type
      - victoria_metrics                         # IMPORTANT: use victoria_metrics, NOT victoriametrics
      - kafka                                    # Allowed: victoria_metrics | kafka

  ldms:
    metrics_enabled: true                        # boolean | was: implicit from software_config.json
    collection_targets:                          # array<enum> | schema enforces maxItems: 1
      - kafka                                    # LDMS ONLY supports kafka (Vector-LDMS routes to VM)

  dcgm:
    metrics_enabled: true                        # boolean | was: dcgm_support
                                                 # NOTE: dcgm has NO collection_targets (routes via LDMS)

  powerscale:
    metrics_enabled: true                        # boolean | was: powerscale_configurations.powerscale_telemetry_support
    logs_enabled: false                          # boolean | was: powerscale_configurations.powerscale_log_enabled
    collection_targets:                          # array<enum>
      - victoria_metrics                         # Allowed: victoria_metrics | victoria_logs (no kafka)

# =============================================================================
# LAYER 2: BRIDGES — Data routers (Vector pods, Kafka consumers)
# =============================================================================
telemetry_bridges:

  vector_ldms:
    metrics_enabled: true                        # boolean | was: vector_ldms_support (new)

  vector_ome:
    metrics_enabled: true                        # boolean | was: vector_ome_support (new)
    logs_enabled: true                           # boolean | new
    ome_identifier: "ome"                        # string  | new | minLength: 1
                                                 # topic regex: ^ome\..*$

# =============================================================================
# LAYER 3: SINKS — Storage backends (all three required by schema)
# =============================================================================
telemetry_sinks:

  victoria_metrics:                              # KEY: victoria_metrics (not victoriametrics)
    persistence_size: "8Gi"                      # string  | was: victoria_metrics_configurations.persistence_size
    retention_period: 168                        # integer | was: victoria_metrics_configurations.retention_period
                                                 # pattern: ^[0-9]+(Ki|Mi|Gi|Ti|Pi|Ei)$

  victoria_logs:                                 # KEY: victoria_logs (not victorialogs)
    storage_size: "8Gi"                          # string  | was: victoria_logs_configurations.storage_size
    retention_period: 168                        # integer | was: victoria_logs_configurations.retention_period

  kafka:
    persistence_size: "8Gi"                      # string  | was: kafka_configurations.persistence_size
    log_retention_hours: 168                     # integer | was: kafka_configurations.log_retention_hours
    log_retention_bytes: -1                      # integer | -1 = unlimited
    log_segment_bytes: 1073741824                # integer | 1 GB default
    topic_partitions:                            # object  | was: kafka_configurations.topic_partitions (array)
      idrac: 1                                   # was: [{name: idrac, partitions: 1}]
      ldms: 2                                    # was: [{name: ldms, partitions: 2}]

# =============================================================================
# SOURCE-SPECIFIC CONFIGS: LDMS (was top-level flat vars)
# =============================================================================
ldms_configurations:
  agg_port: 6001                                 # integer | was: ldms_agg_port
  store_port: 6001                               # integer | was: ldms_store_port
  sampler_port: 10001                            # integer | was: ldms_sampler_port
  sampler_plugins:                               # array   | was: ldms_sampler_configurations
    - plugin_name: meminfo
      activation_parameters: "interval=30000000 offset=0"
    - plugin_name: procstat2
      activation_parameters: "interval=30000000 offset=0"
    - plugin_name: vmstat
      activation_parameters: "interval=30000000 offset=0"
    - plugin_name: loadavg
      activation_parameters: "interval=30000000 offset=0"
    - plugin_name: procnetdev2
      activation_parameters: "interval=30000000 offset=0"

# =============================================================================
# SOURCE-SPECIFIC CONFIGS: PowerScale
# =============================================================================
powerscale_configurations:
  otel_collector_storage_size: "5Gi"             # string  | unchanged location
  csm_observability_values_file_path: ""         # string  | path to custom Helm values
  additional_remote_write_endpoints: []          # array   | extra Prometheus remote_write targets
```

### 2.2 Parameter Origin Mapping

| New Path | Old Flat Param | Notes |
|----------|---------------|-------|
| `telemetry_sources.idrac.metrics_enabled` | `idrac_telemetry_support` | |
| `telemetry_sources.idrac.collection_targets` | `telemetry_collection_type` | old: comma-string → new: array |
| `telemetry_sources.dcgm.metrics_enabled` | `dcgm_support` | |
| `telemetry_sources.ldms.metrics_enabled` | *(implicit in software_config.json)* | now explicit |
| `telemetry_sources.powerscale.metrics_enabled` | `powerscale_configurations.powerscale_telemetry_support` | moved |
| `telemetry_sources.powerscale.logs_enabled` | `powerscale_configurations.powerscale_log_enabled` | moved |
| `telemetry_sinks.victoria_metrics.*` | `victoria_metrics_configurations.*` | key renamed |
| `telemetry_sinks.victoria_logs.*` | `victoria_logs_configurations.*` | key renamed |
| `telemetry_sinks.kafka.*` | `kafka_configurations.*` | |
| `telemetry_sinks.kafka.topic_partitions` | `kafka_configurations.topic_partitions` (array) | array → dict |
| `ldms_configurations.agg_port` | `ldms_agg_port` | |
| `ldms_configurations.store_port` | `ldms_store_port` | |
| `ldms_configurations.sampler_port` | `ldms_sampler_port` | |
| `ldms_configurations.sampler_plugins` | `ldms_sampler_configurations` | key renamed |

---

## 3 Component 2 — JSON Schema (telemetry_config.json)

**File:** `common/library/module_utils/input_validation/schema/telemetry_config.json`

### 3.1 Top-Level Schema Structure

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Telemetry Configuration",
  "description": "Three-layer telemetry configuration: Sources → Bridges → Sinks.",
  "type": "object",
  "properties": {
    "telemetry_sources": { "$ref": "#/definitions/telemetry_sources" },
    "telemetry_bridges": { "$ref": "#/definitions/telemetry_bridges" },
    "telemetry_sinks":   { "$ref": "#/definitions/telemetry_sinks" },
    "ldms_configurations": { "$ref": "#/definitions/ldms_configurations" },
    "powerscale_configurations": { "$ref": "#/definitions/powerscale_configurations" }
  },
  "required": [
    "telemetry_sources",
    "telemetry_bridges",
    "telemetry_sinks",
    "ldms_configurations",
    "powerscale_configurations"
  ],
  "additionalProperties": true
}
```

### 3.2 telemetry_sources Schema

```json
"telemetry_sources": {
  "type": "object",
  "properties": {
    "idrac": {
      "type": "object",
      "properties": {
        "metrics_enabled": { "type": "boolean", "default": true },
        "collection_targets": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["victoria_metrics", "kafka"]
          },
          "minItems": 1,
          "uniqueItems": true,
          "default": ["victoria_metrics", "kafka"]
        }
      },
      "required": ["metrics_enabled", "collection_targets"]
    },
    "ldms": {
      "type": "object",
      "properties": {
        "metrics_enabled": { "type": "boolean", "default": true },
        "collection_targets": {
          "type": "array",
          "items": { "type": "string", "enum": ["kafka"] },
          "minItems": 1,
          "maxItems": 1,              // LDMS can only target kafka
          "uniqueItems": true,
          "default": ["kafka"]
        }
      },
      "required": ["metrics_enabled", "collection_targets"]
    },
    "dcgm": {
      "type": "object",
      "properties": {
        "metrics_enabled": { "type": "boolean", "default": true }
      },
      "required": ["metrics_enabled"]
      // NOTE: No collection_targets for DCGM — routes through LDMS flow
    },
    "powerscale": {
      "type": "object",
      "properties": {
        "metrics_enabled": { "type": "boolean", "default": true },
        "logs_enabled":    { "type": "boolean", "default": false },
        "collection_targets": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["victoria_metrics", "victoria_logs"]
          },
          "minItems": 1,
          "uniqueItems": true,
          "default": ["victoria_metrics"]
        }
      },
      "required": ["metrics_enabled", "collection_targets"]
    }
  },
  "required": ["idrac", "ldms", "dcgm", "powerscale"]
}
```

### 3.3 telemetry_sinks Schema (victoria_metrics / victoria_logs keys)

```json
"telemetry_sinks": {
  "type": "object",
  "properties": {
    "victoria_metrics": {                        // KEY: victoria_metrics (not victoriametrics)
      "type": "object",
      "properties": {
        "persistence_size": {
          "type": "string",
          "pattern": "^[0-9]+(Ki|Mi|Gi|Ti|Pi|Ei)$",
          "default": "8Gi"
        },
        "retention_period": {
          "type": "integer",
          "minimum": 24,
          "default": 168
        }
      },
      "required": ["persistence_size", "retention_period"]
    },
    "victoria_logs": {                           // KEY: victoria_logs (not victorialogs)
      "type": "object",
      "properties": {
        "storage_size": {
          "type": "string",
          "pattern": "^[0-9]+(Ki|Mi|Gi|Ti|Pi|Ei)$",
          "default": "8Gi"
        },
        "retention_period": {
          "type": "integer",
          "minimum": 24,
          "default": 168
        }
      },
      "required": ["storage_size", "retention_period"]
    },
    "kafka": {
      "type": "object",
      "properties": {
        "persistence_size": { "type": "string", "default": "8Gi" },
        "log_retention_hours": { "type": "integer", "minimum": 1, "default": 168 },
        "log_retention_bytes": { "type": "integer", "default": -1 },
        "log_segment_bytes": { "type": "integer", "minimum": 1, "default": 1073741824 },
        "topic_partitions": {
          "type": "object",
          "properties": {
            "idrac": { "type": "integer", "minimum": 1, "maximum": 100, "default": 1 },
            "ldms":  { "type": "integer", "minimum": 1, "maximum": 100, "default": 2 }
          },
          "additionalProperties": false         // Only idrac and ldms are allowed
        }
      },
      "required": ["persistence_size", "log_retention_hours", "log_retention_bytes",
                   "log_segment_bytes", "topic_partitions"]
    }
  },
  "required": ["victoria_metrics", "victoria_logs", "kafka"]  // All three always required
}
```

### 3.4 Schema Design Changes Summary

| Aspect | Old Schema | New Schema |
|--------|-----------|------------|
| Top-level `required` | 8 flat params (`idrac_telemetry_support`, `dcgm_support`, ...) | 5 structured objects |
| Conditional `allOf` blocks | 3 blocks (based on collection_type string) | None — sources declare targets independently |
| `$defs` / `$ref` | `kafka_configurations`, `victoria_metrics_configurations`, `victoria_logs_configurations` | Inline under `telemetry_sinks` |
| `topic_partitions` type | `array` with `{name, partitions}` items | `object` with integer values, `additionalProperties: false` |
| Victoria sink key | `victoriametrics` | `victoria_metrics` |
| VictoriaLogs sink key | `victorialogs` | `victoria_logs` |

---

## 4 Component 3 — Sink Support Flag Derivation (derive_sink_support_flags.yml)

**File:** `provision/roles/telemetry/tasks/derive_sink_support_flags.yml`

**Purpose:** Single responsibility task that (1) initializes and derives sink support boolean flags from `collection_targets`, and (2) maps minimal legacy variable names for downstream compatibility.

### 4.1 Complete Implementation

```yaml
---
# =============================================================================
# DERIVE SINK SUPPORT FLAGS AND LEGACY VARIABLE MAPPINGS
# =============================================================================
# Analyzes telemetry_sources.*.collection_targets to derive which sinks
# (victoria_metrics, victoria_logs, kafka) are in use.
# Also maps new telemetry_config structure to legacy variable names.
#
# LEGACY VARIABLE MAPPINGS:
#   ldms_support            = telemetry_config.telemetry_sources.ldms.metrics_enabled
#   idrac_telemetry_support = telemetry_config.telemetry_sources.idrac.metrics_enabled
#   dcgm_support            = telemetry_config.telemetry_sources.dcgm.metrics_enabled
#   powerscale_configurations = merged dict of powerscale source flags + detailed config
#
# SINK SUPPORT FLAGS (derived):
#   victoria_metrics_support = true if ANY source has 'victoria_metrics' in collection_targets
#   victoria_logs_support    = true if ANY source has 'victoria_logs' in collection_targets
#   kafka_support            = true if ANY source has 'kafka' in collection_targets
# =============================================================================

- name: Initialize sink support flags
  ansible.builtin.set_fact:
    victoria_metrics_support: false
    victoria_logs_support: false
    kafka_support: false

- name: Set ldms_support based on telemetry_config.yml
  ansible.builtin.set_fact:
    ldms_support: "{{ telemetry_config.telemetry_sources.ldms.metrics_enabled
                      | default(false) | bool }}"

- name: Map telemetry_sources to legacy feature flags
  ansible.builtin.set_fact:
    idrac_telemetry_support: "{{ telemetry_config.telemetry_sources.idrac.metrics_enabled
                                  | default(false) | bool }}"
    dcgm_support: "{{ telemetry_config.telemetry_sources.dcgm.metrics_enabled
                      | default(true) | bool }}"

- name: Map powerscale source + configurations to legacy powerscale_configurations
  ansible.builtin.set_fact:
    powerscale_configurations:
      powerscale_telemetry_support: "{{ telemetry_config.telemetry_sources.powerscale.metrics_enabled
                                         | default(true) | bool }}"
      powerscale_log_enabled: "{{ telemetry_config.telemetry_sources.powerscale.logs_enabled
                                   | default(false) | bool }}"
      otel_collector_storage_size: "{{ telemetry_config.powerscale_configurations.otel_collector_storage_size
                                        | default('5Gi') }}"
      csm_observability_values_file_path: "{{ telemetry_config.powerscale_configurations.csm_observability_values_file_path
                                               | default('') }}"
      additional_remote_write_endpoints: "{{ telemetry_config.powerscale_configurations.additional_remote_write_endpoints
                                              | default([]) }}"
  when: telemetry_config.powerscale_configurations is defined

- name: Check if any source targets victoria_metrics
  ansible.builtin.set_fact:
    victoria_metrics_support: true
  when: >-
    'victoria_metrics' in (telemetry_config.telemetry_sources.idrac.collection_targets | default([])) or
    'victoria_metrics' in (telemetry_config.telemetry_sources.powerscale.collection_targets | default([]))

- name: Check if any source targets victoria_logs
  ansible.builtin.set_fact:
    victoria_logs_support: true
  when: >-
    'victoria_logs' in (telemetry_config.telemetry_sources.powerscale.collection_targets | default([]))

- name: Check if any source targets Kafka
  ansible.builtin.set_fact:
    kafka_support: true
  when: >-
    'kafka' in (telemetry_config.telemetry_sources.idrac.collection_targets | default([])) or
    'kafka' in (telemetry_config.telemetry_sources.ldms.collection_targets | default([]))

- name: Log derived sink support flags
  ansible.builtin.debug:
    msg: >
      Sink support flags derived —
      victoria_metrics_support={{ victoria_metrics_support }},
      victoria_logs_support={{ victoria_logs_support }},
      kafka_support={{ kafka_support }}
    verbosity: 1
```

### 4.2 Derivation Logic Diagram

```
telemetry_config.telemetry_sources.idrac.collection_targets:
  - 'victoria_metrics'  ──────────────────────────────► victoria_metrics_support = true
  - 'kafka'             ─────────────────────────────────────────────────────────► kafka_support = true

telemetry_config.telemetry_sources.ldms.collection_targets:
  - 'kafka'             ─────────────────────────────────────────────────────────► kafka_support = true

telemetry_config.telemetry_sources.powerscale.collection_targets:
  - 'victoria_metrics'  ──────────────────────────────► victoria_metrics_support = true
  - 'victoria_logs'     ──────────────────────────────────────────────────────────────────► victoria_logs_support = true
```

### 4.3 Outputs (Ansible Facts Set)

| Fact | Type | Default | Derivation |
|------|------|---------|------------|
| `victoria_metrics_support` | boolean | `false` | `true` if `victoria_metrics` in any `collection_targets` |
| `victoria_logs_support` | boolean | `false` | `true` if `victoria_logs` in any `collection_targets` |
| `kafka_support` | boolean | `false` | `true` if `kafka` in any `collection_targets` |
| `ldms_support` | boolean | `false` | `telemetry_sources.ldms.metrics_enabled` |
| `idrac_telemetry_support` | boolean | `false` | `telemetry_sources.idrac.metrics_enabled` |
| `dcgm_support` | boolean | `true` | `telemetry_sources.dcgm.metrics_enabled` |
| `powerscale_configurations` | dict | merged | Source flags + `powerscale_configurations` merged |

---

## 5 Component 4 — L2 Validation Module (telemetry_validation.py)

**File:** `common/library/module_utils/input_validation/validation_flows/telemetry_validation.py`

**Purpose:** New dedicated Python module for L2 (cross-field, cross-file) telemetry configuration validation.

### 5.1 Module Structure

```python
# telemetry_validation.py

def check_is_service_cluster_functional_groups_defined(
    errors, input_file_path, omnia_base_dir, project_name, logger, module
):
    """Validates service cluster groups exist in pxe_mapping_file.csv."""
    # 1. Load provision_config.yml to get pxe_mapping_file_path
    # 2. Read pxe_mapping_file.csv with csv.DictReader
    # 3. Check for: service_kube_node_* AND service_kube_control_plane_*
    # Returns True only if BOTH are present

def check_is_slurm_cluster_functional_groups_defined(
    errors, input_file_path, omnia_base_dir, project_name, logger, module
):
    """Validates slurm cluster groups exist in pxe_mapping_file.csv."""
    # 1. Load provision_config.yml → pxe_mapping_file_path
    # 2. Check for: slurm_control_node_* AND slurm_node_*
    # Returns True only if BOTH are present

def get_config_file_paths(input_dir, data, software_config_file_path):
    """Resolves dynamic config file paths (service_k8s.json, csi_driver_powerscale.json)."""
    # Reads cluster_os_type + cluster_os_version from software_config.json
    # Returns dict with service_k8s_json_path, csi_driver_powerscale_json_path

def validate_telemetry_config(
    input_file_path, data, logger, module, omnia_base_dir, module_utils_base, project_name
):
    """Main L2 validation entry point — registered in logical_validation.py."""
```

### 5.2 validate_telemetry_config() Logic Flow

```python
def validate_telemetry_config(input_file_path, data, ...):
    errors = []

    # Step 1: Extract from new three-layer structure
    telemetry_sources   = data.get("telemetry_sources", {})
    telemetry_bridges   = data.get("telemetry_bridges", {})
    telemetry_sinks     = data.get("telemetry_sinks", {})
    ldms_configurations = data.get("ldms_configurations", {})

    idrac_source = telemetry_sources.get("idrac", {})
    ldms_source  = telemetry_sources.get("ldms", {})
    dcgm_source  = telemetry_sources.get("dcgm", {})
    powerscale_source = telemetry_sources.get("powerscale", {})

    idrac_telemetry_support  = idrac_source.get("metrics_enabled", False)
    idrac_collection_targets = idrac_source.get("collection_targets", [])
    vector_ome = telemetry_bridges.get("vector_ome", {})
    kafka_sink = telemetry_sinks.get("kafka", {})
    topic_partitions = kafka_sink.get("topic_partitions", {})

    # Step 2: Per-source collection_targets type validation
    # iDRAC: only {kafka, victoria_metrics}
    invalid_idrac = set(idrac_collection_targets) - {"kafka", "victoria_metrics"}
    if invalid_idrac: errors.append(...)

    # LDMS: only {kafka}
    ldms_targets = set(ldms_source.get("collection_targets", []))
    if ldms_targets and ldms_targets != {"kafka"}: errors.append(...)

    # DCGM: must NOT have collection_targets
    if "collection_targets" in dcgm_source: errors.append(...)

    # PowerScale: only {victoria_metrics, victoria_logs}
    invalid_ps = set(powerscale_source.get("collection_targets", [])) - {
        "victoria_metrics", "victoria_logs"
    }
    if invalid_ps: errors.append(...)

    # Step 3: Service cluster + slurm cluster checks (reads pxe_mapping_file.csv)
    is_service_cluster = check_is_service_cluster_functional_groups_defined(...)
    is_slurm_cluster   = check_is_slurm_cluster_functional_groups_defined(...)

    if idrac_telemetry_support and not is_service_cluster:
        errors.append(...)  # iDRAC requires service cluster

    # Step 4: LDMS bidirectional validation
    ldms_in_telemetry     = ldms_source.get("metrics_enabled", False)
    ldms_in_software_cfg  = check_software_config_for_ldms(software_config_file_path)

    if ldms_in_telemetry and not ldms_in_software_cfg:
        errors.append(...)  # telemetry enables LDMS but software_config missing it
    if ldms_in_software_cfg and not ldms_in_telemetry:
        errors.append(...)  # software_config has LDMS but telemetry disables it
    if ldms_in_software_cfg and not (is_service_cluster and is_slurm_cluster):
        errors.append(...)  # LDMS requires both service cluster + slurm cluster

    # Step 5: Kafka topic_partitions validation (dict format)
    if topic_partitions and isinstance(topic_partitions, dict):
        allowed_topics = {"idrac", "ldms"}
        for name in topic_partitions.keys():
            if name not in allowed_topics: errors.append(...)  # invalid topic name
        # Required topics based on feature flags
        if idrac_telemetry_support and 'kafka' in idrac_collection_targets:
            if 'idrac' not in topic_partitions: errors.append(...)
        if ldms_in_software_cfg and 'ldms' not in topic_partitions:
            errors.append(...)
        # Partition counts must be positive integers
        for name, count in topic_partitions.items():
            if not isinstance(count, int) or count < 1: errors.append(...)

    # Step 6: sampler_plugins validation
    sampler_plugins = ldms_configurations.get("sampler_plugins")
    if sampler_plugins is None: errors.append(...)  # required
    elif isinstance(sampler_plugins, list) and len(sampler_plugins) == 0:
        errors.append(...)  # cannot be empty
    else:
        for i, plugin in enumerate(sampler_plugins or []):
            if not plugin.get("plugin_name", "").strip():
                errors.append(...)  # plugin_name cannot be empty

    # Step 7: Vector-OME bridge validation
    if vector_ome.get("metrics_enabled") or vector_ome.get("logs_enabled"):
        if not vector_ome.get("ome_identifier", "").strip():
            errors.append(...)  # ome_identifier required when bridge enabled

    # Step 8: PowerScale validation (delegates to powerscale_telemetry_validation)
    powerscale_validation_data = dict(data)
    powerscale_validation_data["powerscale_configurations"] = {
        "powerscale_telemetry_support": powerscale_source.get("metrics_enabled", False),
        "powerscale_log_enabled":       powerscale_source.get("logs_enabled", False),
        **data.get("powerscale_configurations", {})
    }
    powerscale_telemetry_validation.validate_powerscale_telemetry_config(
        powerscale_validation_data,
        powerscale_source.get("collection_targets", []),
        software_config_file_path,
        is_service_cluster,
        config_paths,
        logger,
        errors
    )

    return errors
```

### 5.3 Validation Rules Summary

| Rule | Trigger Condition | Error Field |
|------|------------------|-------------|
| Invalid iDRAC target | target not in `{kafka, victoria_metrics}` | `telemetry_sources.idrac.collection_targets` |
| Invalid LDMS target | target not `kafka` | `telemetry_sources.ldms.collection_targets` |
| DCGM has targets | `collection_targets` key present | `telemetry_sources.dcgm.collection_targets` |
| Invalid PowerScale target | target not in `{victoria_metrics, victoria_logs}` | `telemetry_sources.powerscale.collection_targets` |
| iDRAC without service cluster | `metrics_enabled=true` + no service cluster in pxe_mapping | `telemetry_sources.idrac.metrics_enabled` |
| LDMS enabled but not in software_config | `metrics_enabled=true` + no LDMS in software_config.json | `telemetry_sources.ldms.metrics_enabled` |
| LDMS in software_config but disabled | LDMS in software_config + `metrics_enabled=false` | `telemetry_sources.ldms.metrics_enabled` |
| LDMS requires both clusters | LDMS in software_config + missing cluster | `LDMS entry in software_config.json` |
| Missing idrac topic | iDRAC with kafka targets + no `idrac` in topic_partitions | `telemetry_sinks.kafka.topic_partitions` |
| Missing ldms topic | LDMS in software_config + no `ldms` in topic_partitions | `telemetry_sinks.kafka.topic_partitions` |
| Invalid topic name | key not in `{idrac, ldms}` | `telemetry_sinks.kafka.topic_partitions.<name>` |
| Invalid partition count | value < 1 or not integer | `telemetry_sinks.kafka.topic_partitions.<name>` |
| sampler_plugins null | `sampler_plugins` is `None` | `ldms_configurations.sampler_plugins` |
| sampler_plugins empty | empty array `[]` | `ldms_configurations.sampler_plugins` |
| plugin_name empty | `plugin_name: ""` in sampler | `ldms_configurations.sampler_plugins[N].plugin_name` |
| ome_identifier empty | bridge enabled + empty string | `telemetry_bridges.vector_ome.ome_identifier` |

---

## 6 Component 5 — Input Validation Registration

### 6.1 config.py — Tag-to-File Mapping

**File:** `common/library/module_utils/input_validation/common_utils/config.py`

```python
# Tags and the files that will be validated when those tags are invoked
input_file_inventory = {
    ...
    "telemetry": [files["telemetry_config"]],          # Explicit telemetry tag

    "discovery": [                                      # NEW: discovery phase also validates telemetry
        files["provision_config"],
        files["network_spec"],
        files["software_config"],
        files["telemetry_config"]                       # telemetry_config.yml validated during discovery
    ],

    "all": [
        ...
        files["telemetry_config"],                      # Always included in full validation
        ...
    ],
}
```

**Design note:** Adding `discovery` tag ensures `telemetry_config.yml` is validated when running the discovery phase playbook, not just when the `telemetry` tag is explicitly used.

### 6.2 logical_validation.py — Validation Function Registration

**File:** `common/library/module_utils/input_validation/common_utils/logical_validation.py`

```python
from ansible.module_utils.input_validation.validation_flows import telemetry_validation

def validate_input_logic(input_file_path, data, logger, module, ...):
    validation_functions = {
        "provision_config.yml":        provision_validation.validate_provision_config,
        "software_config.json":        common_validation.validate_software_config,
        "network_spec.yml":            provision_validation.validate_network_spec,
        "omnia_config.yml":            common_validation.validate_omnia_config,
        "local_repo_config.yml":       local_repo_validation.validate_local_repo_config,
        "telemetry_config.yml":        telemetry_validation.validate_telemetry_config,  # ← registered here
        "security_config.yml":         common_validation.validate_security_config,
        "storage_config.yml":          common_validation.validate_storage_config,
        "high_availability_config.yml": high_availability_validation.validate_high_availability_config,
        "build_stream_config.yml":     build_stream_validation.validate_build_stream_config,
        "gitlab_config.yml":           gitlab_validation.validate_gitlab_config,
    }

    file_name = input_file_path.split("/")[-1]
    validation_function = validation_functions.get(file_name, None)
    if validation_function:
        return validation_function(
            input_file_path, data, logger, module, omnia_base_dir, module_utils_base, project_name
        )
```

---

## 7 Component 6 — Ansible Task Orchestration (main.yml)

**File:** `provision/roles/telemetry/tasks/main.yml`

### 7.1 Updated main.yml

```yaml
---
- name: Include telemetry configuration file
  ansible.builtin.include_vars:
    file: "{{ telemetry_config_file_path }}"
    name: telemetry_config                        # ← loaded as 'telemetry_config' dict

- name: Read telemetry packages from software config
  ansible.builtin.include_tasks: read_software_config.yml

- name: Derive sink support flags from collection_targets  # ← replaces map_telemetry_config_params
  ansible.builtin.include_tasks: derive_sink_support_flags.yml

- name: Load service images from service_k8s.json
  ansible.builtin.include_tasks: load_service_images.yml

- name: Check kube_vip reachability for validation
  ansible.builtin.include_tasks: check_kube_vip_reachability.yml
  when:
    - victoria_metrics_support | default(false) | bool  # ← new flag name
    - kube_vip is defined
    - kube_vip | length > 0

- name: Configure k8s telemetry service
  when:
    - >-
      (telemetry_config.telemetry_sources.idrac.metrics_enabled | default(false) | bool) or
      (telemetry_config.telemetry_sources.ldms.metrics_enabled | default(false) | bool) or
      (telemetry_config.telemetry_sources.powerscale.metrics_enabled | default(false) | bool) or
      ldms_support | default(false) | bool
  block:
    - name: Service cluster prerequisite
      ansible.builtin.include_tasks: telemetry_prereq.yml

    - name: Deploy PowerScale telemetry metrics
      ansible.builtin.include_tasks: deploy_powerscale_metrics.yml
      when:
        - telemetry_config.telemetry_sources.powerscale.metrics_enabled | default(false) | bool

    - name: Generate telemetry deployments
      ansible.builtin.include_tasks: generate_telemetry_deployments.yml

- name: Configure iDRAC telemetry service
  when:
    - telemetry_config.telemetry_sources.idrac.metrics_enabled | default(false) | bool
  block:
    - name: Validate idrac telemetry config
      ansible.builtin.include_tasks: validate_idrac_inventory.yml
    - name: Generate service cluster metadata
      ansible.builtin.include_tasks: generate_service_cluster_metadata.yml

- name: Include update_ldms_sampler.yml
  ansible.builtin.include_tasks: update_ldms_sampler.yml
  when: ldms_support

- name: Update ldms agg configuration
  ansible.builtin.include_tasks: update_ldms_agg_config.yml
  when: ldms_support

- name: Check if PXE mapping has changed since last run
  ansible.builtin.include_tasks: check_pxe_changes.yml
  when: ldms_support

- name: Restart LDMS configs for node addition and deletion
  ansible.builtin.include_tasks: restart_ldms_configs.yml
  when:
    - ldms_support
    - pxe_changed | default(false) | bool
```

### 7.2 Variable Access Patterns in main.yml

| Pattern | Example |
|---------|---------|
| Direct new-structure access | `telemetry_config.telemetry_sources.idrac.metrics_enabled` |
| Sink support flag (derived) | `victoria_metrics_support \| default(false) \| bool` |
| Legacy fact (set by derive task) | `ldms_support` |

---

## 8 Component 7 — Deployment Generation (generate_telemetry_deployments.yml)

**File:** `provision/roles/telemetry/tasks/generate_telemetry_deployments.yml`

### 8.1 Key Patterns

```yaml
# Victoria deployment — uses victoria_metrics_support flag
- name: Populate Victoria deployment configs
  ansible.builtin.template:
    src: "{{ item.src }}"
    dest: "{{ k8s_client_share_path }}/telemetry/deployments/{{ item.dest }}"
    mode: "{{ file_permissions_644 }}"
  loop: "{{ victoria_templates }}"
  when: victoria_metrics_support | default(false) | bool    # ← new flag name

# VictoriaLogs deployment — uses victoria_logs_support flag
- name: Populate victoria_logs deployment configs
  ansible.builtin.template:
    src: "{{ item.src }}"
    dest: "{{ k8s_client_share_path }}/telemetry/deployments/{{ item.dest }}"
    mode: "{{ file_permissions_644 }}"
  loop: "{{ victorialogs_templates }}"
  when: victoria_logs_support | default(false) | bool       # ← new flag name

# Kafka — reads topic_partitions DIRECTLY as dict (no array conversion)
- name: Kafka configurations
  when: kafka_support
  block:
    - name: Set Kafka configuration variables from telemetry_config
      ansible.builtin.set_fact:
        kafka_log_retention_hours: "{{ telemetry_config.telemetry_sinks.kafka.log_retention_hours | default(168) }}"
        kafka_log_retention_bytes: "{{ telemetry_config.telemetry_sinks.kafka.log_retention_bytes | default(-1) }}"
        kafka_log_segment_bytes:   "{{ telemetry_config.telemetry_sinks.kafka.log_segment_bytes | default(1073741824) }}"

    - name: Create kafka_topic_partitions dictionary from telemetry_config
      ansible.builtin.set_fact:
        kafka_topic_partitions: "{{ telemetry_config.telemetry_sinks.kafka.topic_partitions | default({}) }}"
        # NOTE: already a dict — no conversion needed (unlike old array format)

    - name: Add idrac topic if enabled
      ansible.builtin.set_fact:
        kafka_topics_to_create: "{{ kafka_topics_to_create + [{ 'name': 'idrac', ... }] }}"
      when:
        - telemetry_config.telemetry_sources.idrac.metrics_enabled | default(false) | bool
        - "'kafka' in (telemetry_config.telemetry_sources.idrac.collection_targets | default([]))"
        - "kafka.topics.idrac.name in kafka_topic_partitions"

    - name: Add ldms topic if enabled
      ansible.builtin.set_fact:
        kafka_topics_to_create: "{{ kafka_topics_to_create + [{ 'name': 'ldms', ... }] }}"
      when:
        - ldms_support
        - "kafka.topics.ldms.name in kafka_topic_partitions"

# iDRAC statefulset — direct source check (no legacy variable)
- name: Populate iDRAC telemetry statefulset
  ansible.builtin.template:
    src: 'telemetry/idrac_telemetry/idrac_telemetry_statefulset.yaml.j2'
    dest: "{{ k8s_client_share_path }}/telemetry/deployments/idrac_telemetry_statefulset.yaml"
  when: telemetry_config.telemetry_sources.idrac.metrics_enabled | default(false) | bool
```

---

## 9 Component 8 — Jinja2 Template Updates

**Files:** `provision/roles/telemetry/templates/telemetry/`

### 9.1 victoria-operator-vmcluster.yaml.j2 — New Variable Path

```yaml
# Before (old):
storage: {{ telemetry_config.telemetry_sinks.victoriametrics.persistence_size }}
retentionPeriod: "{{ telemetry_config.telemetry_sinks.victoriametrics.retention_period }}h"

# After (new):
storage: {{ telemetry_config.telemetry_sinks.victoria_metrics.persistence_size }}
retentionPeriod: "{{ telemetry_config.telemetry_sinks.victoria_metrics.retention_period }}h"
```

### 9.2 victorialogs-operator-vlcluster.yaml.j2 — New Variable Path

```yaml
# Before (old):
storage: {{ telemetry_config.telemetry_sinks.victorialogs.storage_size }}
retentionPeriod: "{{ telemetry_config.telemetry_sinks.victorialogs.retention_period }}h"

# After (new):
storage: {{ telemetry_config.telemetry_sinks.victoria_logs.storage_size }}
retentionPeriod: "{{ telemetry_config.telemetry_sinks.victoria_logs.retention_period }}h"
```

### 9.3 kustomization.yaml.j2 — Sink Support Flag Usage

```yaml
# Uses: victoria_metrics_support (not victoriametrics_support)
#        victoria_logs_support    (not victorialogs_support)

{% if victoria_metrics_support | default(false) | bool %}
- path: victoria-operator-vmcluster.yaml
{% endif %}
{% if victoria_logs_support | default(false) | bool %}
- path: victorialogs-operator-vlcluster.yaml
{% endif %}
{% if kafka_support | default(false) | bool %}
- path: kafka.yaml
{% endif %}
```

### 9.4 idrac_telemetry_statefulset.yaml.j2 — collection_targets Check

```yaml
# Before (old):
{% if 'victoriametrics' in telemetry_config.telemetry_sources.idrac.collection_targets %}

# After (new):
{% if 'victoria_metrics' in telemetry_config.telemetry_sources.idrac.collection_targets %}
```

### 9.5 telemetry.sh.j2 — Sink Support Flags

```bash
# Uses new flag names
{% if victoria_metrics_support | bool %}
kubectl apply -f victoria-operator-vmcluster.yaml
{% endif %}
{% if victoria_logs_support | bool %}
kubectl apply -f victorialogs-operator-vlcluster.yaml
{% endif %}
```

### 9.6 Template Variable Reference Guide

| Old Variable | New Variable | Used In |
|-------------|-------------|---------|
| `victoriametrics_support` | `victoria_metrics_support` | `kustomization.yaml.j2`, `telemetry.sh.j2`, `telemetry_prereq.yml` |
| `victorialogs_support` | `victoria_logs_support` | `kustomization.yaml.j2`, `telemetry.sh.j2`, `telemetry_prereq.yml` |
| `telemetry_config.telemetry_sinks.victoriametrics.*` | `telemetry_config.telemetry_sinks.victoria_metrics.*` | `victoria-operator-vmcluster.yaml.j2`, `victoria-statefulset.yaml.j2` |
| `telemetry_config.telemetry_sinks.victorialogs.*` | `telemetry_config.telemetry_sinks.victoria_logs.*` | `victorialogs-operator-vlcluster.yaml.j2` |
| `'victoriametrics' in collection_targets` | `'victoria_metrics' in collection_targets` | `idrac_telemetry_statefulset.yaml.j2` |

---

## 10 Component 9 — Ansible Role Validation (validate_telemetry_config.yml)

**File:** `telemetry/roles/telemetry_validation/tasks/validate_telemetry_config.yml`

**Important:** This task file loads `telemetry_config.yml` **flat** (not under a `telemetry_config` dict), so variables are accessed without the `telemetry_config.` prefix.

```yaml
---
- name: Check that the telemetry_config.yml exists
  ansible.builtin.stat:
    path: "{{ telemetry_config_file }}"
  register: stat_result

- name: Fail if telemetry_config.yml file doesn't exist
  ansible.builtin.fail:
    msg: "{{ fail_msg_telemetry_config_file }}"
  when: not stat_result.stat.exists

- name: Include variable file telemetry_config.yml
  block:
    - name: Include variable file telemetry_config.yml
      ansible.builtin.include_vars: "{{ telemetry_config_file }}"
      register: include_telemetry_config
      no_log: true
  rescue:
    - name: Failed to include telemetry_config.yml
      ansible.builtin.fail:
        msg: "{{ telemetry_config_syntax_fail_msg }}
              Possible Syntax Error Hints: {{ include_telemetry_config.message }}"

- name: Include metadata vars
  ansible.builtin.include_vars: "{{ omnia_metadata_file }}"

- name: Map telemetry_sources to legacy feature flags
  ansible.builtin.set_fact:
    idrac_telemetry_support: "{{ telemetry_sources.idrac.metrics_enabled
                                  | default(false) | bool }}"
    # NOTE: uses 'telemetry_sources' NOT 'telemetry_config.telemetry_sources'
    # because vars are loaded FLAT by include_vars above (no 'name:' parameter)

- name: Warning for iDRAC telemetry is currently disabled
  ansible.builtin.pause:
    seconds: "{{ pause_time_15 }}"
    prompt: "{{ warning_idrac_telemetry_support_false }}"
  when: not (idrac_telemetry_support | bool)

- name: Warning for iDRAC telemetry is currently enabled
  ansible.builtin.pause:
    seconds: "{{ pause_time_15 }}"
    prompt: "{{ warning_idrac_telemetry_support_true }}"
  when: idrac_telemetry_support | bool
```

**Contrast with `main.yml`:** In `main.yml`, vars are loaded as `name: telemetry_config`, so access requires `telemetry_config.telemetry_sources.*`. In `validate_telemetry_config.yml`, vars are loaded flat, so `telemetry_sources.*` is used directly.

---

## 11 Interface Summary

### 11.1 Ansible Facts Interface

Facts produced by `derive_sink_support_flags.yml` and consumed downstream:

```
┌──────────────────────────────────────────────────────────────────────┐
│  FACTS PRODUCED (by derive_sink_support_flags.yml)                   │
│                                                                      │
│  Sink Flags:                                                         │
│    victoria_metrics_support: bool  ─────► telemetry_prereq.yml      │
│    victoria_logs_support:    bool  ─────► kustomization.yaml.j2     │
│    kafka_support:            bool  ─────► generate_telemetry_dep.yml │
│                                                                      │
│  Legacy Compatibility:                                               │
│    idrac_telemetry_support:  bool  ─────► telemetry_validation role  │
│    ldms_support:             bool  ─────► main.yml when: conditions  │
│    dcgm_support:             bool  ─────► generate_telemetry_dep.yml │
│    powerscale_configurations: dict ─────► deploy_powerscale_metrics  │
└──────────────────────────────────────────────────────────────────────┘
```

### 11.2 Variable Path Reference (Quick Lookup)

| Use Case | Variable Path |
|----------|--------------|
| Check if iDRAC enabled (in Ansible tasks) | `telemetry_config.telemetry_sources.idrac.metrics_enabled` |
| Check if iDRAC enabled (in templates) | `telemetry_config.telemetry_sources.idrac.metrics_enabled` |
| Check if victoria_metrics sink is needed | `victoria_metrics_support` (Ansible fact) |
| Check if victoria_logs sink is needed | `victoria_logs_support` (Ansible fact) |
| Check if kafka sink is needed | `kafka_support` (Ansible fact) |
| Get victoria_metrics PVC size | `telemetry_config.telemetry_sinks.victoria_metrics.persistence_size` |
| Get victoria_logs storage size | `telemetry_config.telemetry_sinks.victoria_logs.storage_size` |
| Get kafka retention | `telemetry_config.telemetry_sinks.kafka.log_retention_hours` |
| Get kafka topic partitions | `telemetry_config.telemetry_sinks.kafka.topic_partitions` (dict) |
| Check iDRAC collection targets | `telemetry_config.telemetry_sources.idrac.collection_targets` |
| Get LDMS agg port | `telemetry_config.ldms_configurations.agg_port` |
| Get LDMS sampler plugins | `telemetry_config.ldms_configurations.sampler_plugins` |

### 11.3 Validation Entry Points

| Trigger | Entry Point | File |
|---------|------------|------|
| `ansible-playbook ... --tags telemetry` | `input_file_inventory["telemetry"]` | `config.py` |
| `ansible-playbook ... --tags discovery` | `input_file_inventory["discovery"]` | `config.py` |
| `ansible-playbook ... --tags all` | `input_file_inventory["all"]` | `config.py` |
| L2 validation dispatch | `validate_input_logic()` → `telemetry_validation.validate_telemetry_config` | `logical_validation.py` |
| Ansible role pre-check | `validate_telemetry_config.yml` (flat var load) | `telemetry_validation` role |
