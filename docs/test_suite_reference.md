<!-- Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. -->

# Test Suite Reference

This document serves as the central reference for all test suites and test cases in the Omnia Automation Framework. Each scenario contributor should document their test cases here.

---

## Test Suite Types

| Suite | Purpose | Run Command |
|-------|---------|-------------|
| `sanity` | Basic functionality validation — quick checks that confirm deployment succeeded | `--suite sanity` |
| `negative` | Error handling and edge cases — verify graceful failures | `--suite negative` |
| `regression` | Full test coverage — comprehensive validation of all features | `--suite regression` |
| `smoke` | Critical path only — fastest subset of sanity tests | `--marker smoke` |
| `stress` | Load and endurance tests | `--suite stress` |
| `performance` | Performance benchmarks | `--suite performance` |

### Build Stream Suites

| Suite | Purpose |
|-------|---------|
| `build_auto` | Build pipeline auto-trigger tests |
| `deploy_auto` | Deploy pipeline auto-trigger tests |
| `build_manual` | Build pipeline manual trigger tests |
| `deploy_manual` | Deploy pipeline manual trigger tests |
| `cleanup_manual` | Cleanup pipeline tests (manual trigger only) |

---

## Pytest Markers

All markers are registered in `pytest.ini`. Use `--marker <name>` to filter by decorator.

| Marker | Description |
|--------|-------------|
| `sanity` | Sanity test cases |
| `negative` | Negative test cases (e.g., reboot scenarios) |
| `stress` | Stress test cases |
| `build_auto` | Build pipeline auto-trigger tests |
| `deploy_auto` | Deploy pipeline auto-trigger tests |
| `build_manual` | Build pipeline manual trigger tests |
| `deploy_manual` | Deploy pipeline manual trigger tests |
| `cleanup_manual` | Cleanup pipeline tests |
| `ldap` | LDAP user authentication and PAM tests |
| `sanityib` | InfiniBand sanity tests |
| `vast_telemetry` | VAST storage telemetry tests |

---

## Test Case Documentation

> **Contributors:** Add your test case descriptions below, organized by scenario.
> Follow the template for each scenario section.

### Template

```
### <scenario_name>

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| `test_example` | `test_example.py` | Brief description |

#### Negative Tests

| Test | File | Description |
|------|------|-------------|
| `test_error_handling` | `test_negative.py` | Brief description |
```

---

### omnia\_sh\_install

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### prepare\_oim

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### gitlab\_install

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### local\_repo

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### build\_image\_x86\_64

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### build\_image\_aarch64

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### discovery

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### provision

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### telemetry

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

#### Negative Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### apptainer

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

#### Negative Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### kubernetes

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

#### Negative Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### slurm

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

#### Negative Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### dcgm

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

#### Negative Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### hpc\_benchmarks

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### vast\_storage

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

#### Negative Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

#### Performance Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### build\_stream

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

#### Stress Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### one\_shot\_log\_extraction

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### gitlab\_cleanup

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### oim\_cleanup

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |

---

### omnia\_sh\_uninstall

#### Sanity Tests

| Test | File | Description |
|------|------|-------------|
| _Add your test cases here_ | | |
