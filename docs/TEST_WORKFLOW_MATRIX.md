# Test Workflow Matrix: build_stream Enabled vs Disabled

This document describes the behavior of all test modules when `enable_build_stream` is `true` vs `false` in `build_stream_config.yml`.

---

## Quick Reference

| Module | build_stream=true | build_stream=false |
|--------|-------------------|-------------------|
| `build_image_x86_64` | Validates job UUID, uses UUID in S3/regctl paths | Skips job check, uses plain paths |
| `build_image_aarch64` | Validates job UUID, uses UUID in S3/regctl paths | Skips job check, uses plain paths |
| `local_repo` | Validates job UUID for `create-local-repository` stage | Skips job check, runs all Pulp tests |
| `discovery` | Validates job UUID for `validate-image-on-test` stage | Skips job check, runs all node tests |
| `prepare_oim` | Runs build_stream health + DB tests | Skips build_stream tests |
| `telemetry` | No build_stream dependency | No build_stream dependency |
| `omnia_sh_install` | No build_stream dependency | No build_stream dependency |
| `omnia_sh_uninstall` | No build_stream dependency | No build_stream dependency |
| `oim_cleanup` | No build_stream dependency | No build_stream dependency |

---

## Detailed Module Workflows

### 1. `build_image_x86_64` / `build_image_aarch64`

#### build_stream=true (ENABLED)

```
Test Order:
1. test_build_stream_job_stage (order=1)
   ├─ Reads build_stream_job_id from user_config.yml (if set)
   ├─ OR queries latest COMPLETED job from build_stream_db.job_stages
   ├─ Validates job_state == "COMPLETED"
   ├─ IF PASS: Sets _bs_job["success"]=True, continues
   └─ IF FAIL: Sets _bs_job["success"]=False, pytest.skip() with structured message
              → ALL remaining tests SKIPPED via autouse fixture

2. test_functional_group_content (order=2)
   └─ Validates functional_groups_config.yml contains all FGs from pxe_mapping

3. test_regctl_registry_images (order=3)
   └─ Validates regctl registry has base + compute images

4. test_s3_bucket_images (order=4)
   ├─ Gets job_id from get_last_build_image_job_id()
   ├─ Searches S3 with UUID pattern: rhel-<fg>_<UUID>-image-build/
   └─ Validates initramfs, vmlinuz, rootfs for each FG

5. test_all_image_packages (order=5)
   ├─ Gets job_id from get_last_build_image_job_id()
   ├─ Downloads rootfs images using UUID pattern
   ├─ Mounts squashfs, queries rpm -qa
   └─ Validates base + compute packages installed
```

**S3 Path Pattern (build_stream=true):**
```
s3://boot-images/<fg>/rhel-<fg>_<UUID>-image-build/<files>
```

#### build_stream=false (DISABLED)

```
Test Order:
1. test_build_stream_job_stage (order=1)
   └─ pytest.skip("build_stream is disabled") — SKIPPED

2. test_functional_group_content (order=2)
   └─ RUNS NORMALLY (no UUID dependency)

3. test_regctl_registry_images (order=3)
   └─ RUNS NORMALLY (no UUID dependency)

4. test_s3_bucket_images (order=4)
   ├─ job_id = None (build_stream disabled)
   ├─ Searches S3 with plain pattern: grep '<fg>'
   └─ Validates initramfs, vmlinuz, rootfs for each FG

5. test_all_image_packages (order=5)
   ├─ job_id = None (build_stream disabled)
   ├─ Downloads rootfs images using plain pattern
   └─ Validates packages
```

**S3 Path Pattern (build_stream=false):**
```
s3://boot-images/<fg>/<files>
```

---

### 2. `local_repo`

#### build_stream=true (ENABLED)

```
Test Order:
1. test_build_stream_job_stage (order=1)
   ├─ Validates stage: create-local-repository
   ├─ IF PASS: Continues
   └─ IF FAIL: ALL remaining tests SKIPPED

2-12. All Pulp tests (order=2-12)
   └─ Run normally — no UUID dependency in Pulp verification
```

#### build_stream=false (DISABLED)

```
Test Order:
1. test_build_stream_job_stage (order=1)
   └─ SKIPPED ("build_stream is disabled")

2-12. All Pulp tests (order=2-12)
   └─ RUN NORMALLY — Pulp verification has no build_stream dependency
```

**Tests in local_repo:**
| Order | Test | build_stream Dependency |
|-------|------|------------------------|
| 1 | test_build_stream_job_stage | YES - gates others when enabled |
| 2 | test_pulp_container_running | NO |
| 3 | test_pulp_cli_repository_list | NO |
| 4 | test_pulp_api_status | NO |
| 5 | test_software_download_status | NO |
| 6 | test_per_software_package_status | NO |
| 7 | test_pulp_repositories_synced | NO |
| 8 | test_pulp_distributions_published | NO |
| 9 | test_container_repos_synced | NO |
| 10 | test_file_repos_synced | NO |
| 11 | test_pulp_content_accessible | NO |
| 12 | test_software_packages_in_pulp | NO |

---

### 3. `discovery`

#### build_stream=true (ENABLED)

```
Test Order (test_packages.py):
1. test_build_stream_job_stage (order=1)
   ├─ Validates stage: validate-image-on-test
   └─ IF FAIL: test_node_packages_installed SKIPPED

2. test_node_packages_installed (order=2)
   └─ Verifies packages on all nodes from pxe_mapping

Test Order (test_cloudinit.py):
1. test_cloudinit_completed (order=1)
   └─ NO build_stream dependency

Test Order (test_ssh.py):
2-5. SSH tests (order=2-5)
   └─ NO build_stream dependency

Test Order (test_slurm.py):
10-22. Slurm tests (order=10-22)
   └─ NO build_stream dependency

Test Order (test_k8s_telemetry.py):
30-31. K8s tests (order=30-31)
   └─ NO build_stream dependency
```

#### build_stream=false (DISABLED)

```
All discovery tests RUN NORMALLY except:
- test_build_stream_job_stage → SKIPPED
- test_node_packages_installed → RUNS (no gating)
```

---

### 4. `prepare_oim`

#### build_stream=true (ENABLED)

```
Test Order (test_prepare_oim.py):
1-9. Infrastructure tests (order=1-9)
   └─ NO build_stream dependency

Test Order (test_build_stream.py):
10. test_build_stream_health (order=10)
    └─ Validates /health endpoint returns {"status": "healthy"}

11. test_postgres_db_tables (order=11)
    └─ Validates all 6 tables exist in build_stream_db
```

#### build_stream=false (DISABLED)

```
Test Order (test_prepare_oim.py):
1-9. Infrastructure tests (order=1-9)
   └─ RUN NORMALLY

Test Order (test_build_stream.py):
10. test_build_stream_health → SKIPPED
11. test_postgres_db_tables → SKIPPED
```

---

### 5. `telemetry`

**No build_stream dependency** — all tests run the same regardless of build_stream setting.

```
Test Order:
test_idrac_telemetry.py: order 1-4
test_kafka_telemetry.py: order 5-11
test_victoria_telemetry.py: order 12-20
test_delete_node.py: order 21-24
```

---

### 6. `omnia_sh_install` / `omnia_sh_uninstall` / `oim_cleanup`

**No build_stream dependency** — all tests run the same regardless of build_stream setting.

---

## Error Scenarios

### Scenario 1: Invalid job_id in user_config.yml (build_stream=true)

```yaml
# user_config.yml
build_stream_job_id: "invalid-uuid-12345"
```

**Result:**
```
test_build_stream_job_stage → SKIPPED with message:
  "job_id 'invalid-uuid-12345' not found — no '<stage>' stage entry exists 
   for this job in build_stream_db.job_stages"

ALL remaining tests → SKIPPED
  "build_stream job not COMPLETED — skipping test. Fix: <error message>"
```

### Scenario 2: Job exists but not COMPLETED (build_stream=true)

**Result:**
```
test_build_stream_job_stage → SKIPPED with message:
  "Stage '<stage>' for job '<uuid>' is 'RUNNING' (expected 'COMPLETED')"

ALL remaining tests → SKIPPED
```

### Scenario 3: No job_id override, no COMPLETED job in DB (build_stream=true)

**Result:**
```
test_build_stream_job_stage → SKIPPED with message:
  "No '<stage>' stage entry found in build_stream_db.job_stages"

ALL remaining tests → SKIPPED
```

### Scenario 4: build_stream=false, images exist without UUID

**Result:**
```
test_build_stream_job_stage → SKIPPED ("build_stream is disabled")
test_s3_bucket_images → PASS (uses plain grep pattern)
test_all_image_packages → PASS (uses plain grep pattern)
```

### Scenario 5: build_stream=false, no images exist

**Result:**
```
test_build_stream_job_stage → SKIPPED
test_s3_bucket_images → FAIL ("No rootfs image found in S3")
test_all_image_packages → FAIL ("No rootfs image found in S3")
```

---

## Key Differences Summary

| Aspect | build_stream=true | build_stream=false |
|--------|-------------------|-------------------|
| **Job validation** | Required — gates all tests | Skipped |
| **S3 image paths** | `<fg>_<UUID>-image-build/` | `<fg>/` |
| **Regctl image names** | Same (no UUID in registry) | Same |
| **Autouse fixture** | Active — skips on job failure | Inactive |
| **user_config.yml override** | Honored — validates against DB | Ignored |

---

## Running Tests

### With build_stream enabled (default):
```bash
# Ensure build_stream_config.yml has: enable_build_stream: true
molecule verify -s build_image_x86_64
```

### With build_stream disabled:
```bash
# Set in build_stream_config.yml: enable_build_stream: false
molecule verify -s build_image_x86_64
```

### Override job_id for testing:
```yaml
# user_config.yml
build_stream_job_id: "c01cdd28-3c60-4124-bcf0-b53a0ef93c8b"
```
