# Build Stream Test Workflow Documentation

## Overview

This document describes how the build stream test reporting has been refined across all test modules to provide clearer and more actionable feedback when build stream job validation fails.

## Key Changes Made

### 1. Shared Fixture Implementation
- Moved `_require_build_stream_job` autouse fixture to `molecule/conftest.py`
- All modules now use shared `build_stream_job_state` dictionary
- Consistent behavior across all build stream dependent modules

### 2. Test Behavior Pattern

#### First Test: `test_build_stream_job_stage`
- **Purpose**: Validates the specific build stream pipeline stage for each module
- **Behavior**: 
  - When job validation fails → **FAILS** explicitly (not skipped)
  - Shows exact job state from database: `NOT FOUND`, `FAILED`, `RUNNING`, etc.
  - Sets shared state for remaining tests

#### Remaining Tests
- **Behavior**: 
  - When build stream job failed → **SKIPS** with clear reason
  - Shows detailed error message with fix instructions
  - Clean output format without truncation

### 3. Module-Specific Stages

Each module validates its own specific build stream pipeline stage:

| Module | Stage Name | Stage Constant |
|--------|------------|----------------|
| **build_image_x86_64** | `build-image-x86_64` | `STAGE_BUILD_IMAGE_X86_64` |
| **build_image_aarch64** | `build-image-aarch64` | `STAGE_BUILD_IMAGE_AARCH64` |
| **local_repo** | `create-local-repository` | `STAGE_CREATE_LOCAL_REPO` |
| **discovery** | `validate-image-on-test` | `STAGE_VALIDATE_IMAGE` |

### 4. Output Format Examples

#### Successful First Test
```
test_build_stream_job_stage
  ✔ PASS: Stage 'build-image-x86_64' completed successfully (job: abc123)
PASSED
```

#### Failed First Test
```
test_build_stream_job_stage
  ✘ FAIL: Stage 'build-image-x86_64' is 'NOT FOUND' — expected COMPLETED (job: 11)
    │ job_id '11' not found — no 'build-image-x86_64' stage entry exists...
FAILED
```

#### Skipped Remaining Tests
```
test_functional_group_content
  ↷ SKIP: Skipped due to build_stream job failure (job_id: 11)
    │ build_stream job is NOT FOUND — skipping test.
    │ Fix: job_id '11' not found — no 'build-image-x86_64' stage entry exists...
SKIPPED
```

## Technical Implementation

### Shared State Management
```python
# In molecule/conftest.py
build_stream_job_state: dict = {
    "checked": False,
    "success": None,
    "job_id": None,
    "job_state": None,
    "error": None,
}
```

### Autouse Fixture Logic
```python
@pytest.fixture(autouse=True)
def _require_build_stream_job(host, request):
    """Skip tests when build_stream job validation failed."""
    # Skip logic only applies to non-build_stream_job_stage tests
    # when build_stream is enabled and job check failed
```

### Test Module Integration
Each test module:
1. Imports shared state: `from molecule.conftest import build_stream_job_state`
2. Sets state in `test_build_stream_job_stage` after validation
3. Remaining tests automatically skip via autouse fixture

## Benefits

1. **Clear Failure Reporting**: First test explicitly fails when job validation fails
2. **Actionable Skip Messages**: Remaining tests show exact reason and fix instructions
3. **Consistent Behavior**: All modules follow same pattern
4. **No Truncation**: Clean output without `...` or truncated messages
5. **Exact State Display**: Shows actual job state from database (`NOT FOUND`, `FAILED`, etc.)

## Affected Modules

- `molecule/build_image_x86_64/tests/test_build_image_x86_64.py`
- `molecule/build_image_aarch64/tests/test_build_image_aarch64.py`
- `molecule/local_repo/tests/test_local_repo.py`
- `molecule/discovery/tests/test_packages.py`
- `molecule/conftest.py` (shared fixture)

## Usage

When running tests with an invalid `build_stream_job_id` in `user_config.yml`:

1. The first test in each module will **FAIL** with clear error message
2. All subsequent tests will **SKIP** with detailed reason
3. Test reports will show proper FAILED/SKIPPED counts
4. No confusing truncated output or unclear skip reasons

This provides much clearer feedback for debugging build stream pipeline issues.
