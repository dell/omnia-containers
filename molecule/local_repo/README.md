# Local Repo Molecule Scenario

This Molecule scenario validates the `local_repo` playbook execution and its outcomes.

## Validation Workflow

1. **Pulp Container Validation**
   - Verify Pulp container is running
   - Check container health status
   - Scan logs for errors

2. **Custom Repo Accessibility**
   - Validate Pulp API is accessible from OIM
   - Test API endpoints respond correctly

3. **local_repo Playbook Execution**
   - Execute `local_repo.yml` playbook inside `omnia_core` container
   - Capture execution results

4. **Pulp CLI Command Validation**
   - `pulp rpm repository list`
   - `pulp rpm remote list`
   - `pulp rpm publication list`
   - `pulp rpm distribution list`

5. **Package Download Status Validation**
   - Check top-level `status.csv` file
   - If failures detected, check individual package status files
   - Report failed packages with details

## Directory Structure

```
molecule/local_repo/
├── molecule.yml          # Molecule configuration
├── converge.yml          # Ansible playbook for setup
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── test/
    ├── __init__.py       # Test package init
    ├── conftest.py       # Pytest fixtures
    └── test_local_repo.py # Main test file
```

## Configuration

Configuration is loaded from `automation_library/vars/local_repo_vars.py` which reads from `user_config.yml`.

### Key Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `pulp_container_name` | `pulp` | Name of the Pulp container |
| `local_repo_playbook` | `/omnia/local_repo/local_repo.yml` | Path to playbook in container |
| `top_level_status_file` | `/opt/omnia/offline/status.csv` | Path to main status file |
| `package_status_dir` | `/opt/omnia/offline/packages` | Directory for package status files |
| `custom_repo_base_url` | `http://localhost:8080` | Base URL for Pulp API |

## Running the Tests

### Full Molecule Test Sequence
```bash
cd molecule/local_repo
molecule test
```

### Run Only Converge (Setup)
```bash
molecule converge
```

### Run Only Verification (Tests)
```bash
molecule verify
```

### Run Tests Directly with Pytest
```bash
pytest test/test_local_repo.py -v -s
```

## Environment Variables

The following environment variables can override defaults:

- `CONTAINER_RUNTIME` - Container runtime (podman/docker)
- `PULP_CONTAINER` - Pulp container name
- `LOCAL_REPO_PLAYBOOK` - Path to local_repo playbook
- `TOP_LEVEL_STATUS_FILE` - Path to status.csv
- `PACKAGE_STATUS_DIR` - Path to package status directory
- `CUSTOM_REPO_BASE_URL` - Base URL for Pulp API

## Test Output

The test produces a detailed report showing:
- ✅ **PASSED** - Successful validations
- ⚠️ **WARNINGS** - Non-critical issues
- ⏭️ **SKIPPED** - Skipped validations
- ❌ **FAILED** - Critical failures

Example output:
```
======================================================================
LOCAL_REPO VALIDATION RESULTS
======================================================================

✅ PASSED (8):
   • Container runtime detected: podman
   • Pulp container 'pulp' is running
   • Pulp container health: healthy
   • Custom repo is accessible at http://localhost:8080
   • Pulp command succeeded: pulp rpm repository list
   • All 50 packages downloaded successfully

⚠️  WARNINGS (1):
   • Pulp container has 2 error(s) in recent logs

======================================================================
SUMMARY: 8 passed, 0 failed, 0 skipped, 1 warnings
======================================================================
```
