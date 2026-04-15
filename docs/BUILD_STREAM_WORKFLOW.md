# Build Stream Workflow Documentation

This document explains the Build Stream feature in the Omnia Automation Framework.

---

## Overview

Build Stream is an automated pipeline that orchestrates the image building process for Omnia deployments. When enabled, it automatically triggers and manages:

1. Image building for x86_64 and aarch64 architectures
2. Local repository creation
3. Image validation
4. Catalog parsing
5. Input generation

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Build Stream Pipeline                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ build_image  │ ─▶ │ build_image  │ ─▶ │ create_local │       │
│  │   x86_64     │    │   aarch64    │    │    _repo     │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                 │                │
│                                                 ▼                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  generate    │ ◀─ │    parse     │ ◀─ │   validate   │       │
│  │   _input     │    │   _catalog   │    │    _image    │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Enable Build Stream

In `datasets/project_default/build_stream_config.yml`:

```yaml
enable_build_stream: true
```

### Build Stream Stages

| Stage | Description |
|-------|-------------|
| `build_image_x86_64` | Build images for x86_64 architecture |
| `build_image_aarch64` | Build images for aarch64 architecture |
| `create_local_repo` | Create local package repository |
| `validate_image` | Validate built images |
| `parse_catalog` | Parse software catalog |
| `generate_input` | Generate deployment inputs |

---

## How It Works

### 1. Stage Detection

The framework checks build stream status using:

```python
from automation_library.core import (
    is_build_stream_enabled,
    check_build_stream_stage,
    get_build_stream_job_id,
)

# Check if build stream is enabled
if is_build_stream_enabled(host):
    # Get current job ID
    job_id = get_build_stream_job_id(host)
    
    # Check specific stage status
    stage_result = check_build_stream_stage(host, "build_image_x86_64")
```

### 2. Stage Constants

```python
from automation_library.core import (
    STAGE_BUILD_IMAGE_X86_64,
    STAGE_BUILD_IMAGE_AARCH64,
    STAGE_CREATE_LOCAL_REPO,
    STAGE_VALIDATE_IMAGE,
    STAGE_PARSE_CATALOG,
    STAGE_GENERATE_INPUT,
)
```

### 3. Converge Protection

When build stream is enabled, manual `molecule converge` is blocked to prevent conflicts:

```yaml
# molecule/shared/tasks/check_build_stream.yml
- name: "[build_stream guard] Abort converge when build_stream is enabled"
  ansible.builtin.fail:
    msg: "BUILD STREAM IS ENABLED — CONVERGE SKIPPED"
  when: build_stream_enabled | bool
```

---

## Test Behavior

### When Build Stream is Disabled

- All tests run normally
- Manual converge operations are allowed
- Verification tests check static state

### When Build Stream is Enabled

- Converge operations are blocked (automated by pipeline)
- Verification tests check pipeline status
- Tests may skip if waiting for pipeline stages

### Skip Pattern

```python
@pytest.mark.sanity
def test_build_stream_health(host):
    """Verify build stream health."""
    if not is_build_stream_enabled(host):
        pytest.skip("build_stream checks skipped (enable_build_stream is false)")
    
    # ... verification logic
```

---

## Database Tables

Build stream uses PostgreSQL to track job status:

| Table | Purpose |
|-------|---------|
| `build_stream_jobs` | Job metadata and status |
| `build_stream_stages` | Stage execution status |
| `build_stream_logs` | Execution logs |

### Query Example

```python
from automation_library.core import exec_psql_query

result = exec_psql_query(
    host,
    "SELECT * FROM build_stream_jobs ORDER BY created_at DESC LIMIT 1"
)
```

---

## Services

### Build Stream Services

| Service | Purpose |
|---------|---------|
| `playbook_watcher.service` | Watches for playbook triggers |
| `omnia_build_stream` | Main build stream container |
| `omnia_postgres` | PostgreSQL for build stream data |

### Service Status Check

```python
def verify_build_stream_services(host):
    """Verify build stream services are running."""
    services = ["playbook_watcher.service"]
    containers = ["omnia_build_stream", "omnia_postgres"]
    
    # Check services
    for svc in services:
        cmd = host.run(f"systemctl is-active {svc}")
        if cmd.rc != 0:
            return {"success": False, "error": f"{svc} not active"}
    
    # Check containers
    for ctr in containers:
        result = check_container_running(host, ctr)
        if not result["success"]:
            return result
    
    return {"success": True}
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Converge blocked | Build stream enabled | Wait for pipeline or disable build stream |
| Stage stuck | Pipeline error | Check `build_stream_logs` table |
| Services not running | Configuration error | Verify `build_stream_config.yml` |

### Debug Commands

```bash
# Check build stream status
podman exec omnia_core cat /opt/omnia/input/project_default/build_stream_config.yml

# Check PostgreSQL
podman exec omnia_postgres psql -U omnia -d omnia -c "SELECT * FROM build_stream_jobs"

# Check service logs
journalctl -u playbook_watcher.service -f
```

---

## Integration with Tests

### Verification Tests

The framework includes tests for build stream verification:

```python
# test_build_stream.py
@pytest.mark.sanity
def test_build_stream_health(host):
    """Verify build stream is healthy when enabled."""
    
@pytest.mark.sanity
def test_postgres_db_tables(host):
    """Verify PostgreSQL tables exist for build stream."""
```

### Conditional Execution

Tests automatically skip when build stream is not enabled:

```python
if not is_build_stream_enabled(host):
    pytest.skip("build_stream not enabled")
```

---

*Last Updated: April 2026*
