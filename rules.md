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

# Omnia Automation Framework — Development Rules

Guidelines for contributing to the omnia-artifactory automation repository.

---

## 1. Automation Design Process

### 1.1 Understand the Omnia Code First

Before writing any automation or test case, **log into the `omnia_core` container and study the actual Omnia codebase**:

```bash
podman exec -it omnia_core bash
ls /omnia/                              # Top-level playbook directories
ls /opt/omnia/input/project_default/    # Deployed input files
cat /omnia/telemetry/telemetry.yml      # Example: read the telemetry playbook
```

Every Omnia playbook starts by importing `utils/include_input_dir.yml`, which sets `input_project_dir` to `/opt/omnia/input/project_default/`. From there, each role loads its config files (e.g., `telemetry_config.yml`, `software_config.json`).

### 1.2 Backtrack from the Feature

When automating a new feature:

1. **Identify the playbook** — Find which playbook under `/omnia/` implements the feature (e.g., `/omnia/telemetry/telemetry.yml`).
2. **Trace the input files** — Check which files from `input_project_dir` the playbook roles load (look for `include_vars` tasks).
3. **Understand the deployment** — Read the roles to understand what containers, services, K8s resources, or files the playbook creates.
4. **Write tests that verify the deployment** — Based on what the playbook actually does, write test cases that check the end state (containers running, services healthy, configs correct, etc.).
5. **Update the dataset** — If the feature needs new input values, add them to the appropriate file in `datasets/project_default/`.

Never write tests based on assumptions. Always verify against the actual Omnia code inside the container.

### 1.3 Input File Flow

```
datasets/project_default/          (automation repo — your input files)
        │
        │  rsync via converge.yml (when sync_dataset_to_core: true)
        ▼
/opt/omnia/input/project_default/  (inside omnia_core container)
        │
        │  include_input_dir.yml → sets input_project_dir
        ▼
Omnia playbook roles               (load config via include_vars)
```

---

## 2. Repository Structure

### 2.1 Module Organization

Every automation module lives under `automation_library/<module_name>/`:

```
automation_library/<module>/
├── __init__.py        # Public API — export only what tests need
├── functions/         # Business logic and verification functions
├── messages/          # Assertion and log message templates
└── vars/              # Module-specific constants
```

### 2.2 Molecule Scenarios

Scenarios live under `molecule/<scenario_name>/` with:
- `molecule.yml` — Scenario configuration
- `create.yml` — Inventory setup
- `converge.yml` — Playbook execution
- `tests/` — Test files organized by suite (`sanity/`, `negative/`, etc.)

Shared Ansible tasks go in `molecule/shared/tasks/`. Do not duplicate tasks across scenarios.

### 2.3 Configuration Files

- **`omnia_test_config.yml`** — Central config for OIM server details. Each user maintains their own copy.
- **`test_run_config.yml`** — Batch scenario runner config. Tracked in git.
- **`pytest.ini`** — Pytest settings and custom marker registration.
- **`requirements.txt`** — Pinned Python dependencies.

---

## 3. Code Standards

### 3.1 Python

- Target Python 3.9+ compatibility.
- Use type hints for all function signatures.
- Follow PEP 8. Use `snake_case` for functions/variables, `UPPER_SNAKE_CASE` for constants.
- Imports must always be at the top of the file, never inline.
- Use `automation_library.core` for shared utilities — do not reimplement host connections, config loading, or formatting.

### 3.2 Ansible

- Use FQCNs for all modules (e.g., `ansible.builtin.shell`, not `shell`).
- Always set `changed_when` and `failed_when` for shell/command tasks.
- Use `no_log: true` when handling passwords or credentials.
- Prefer `ansible.builtin.include_tasks` from `molecule/shared/tasks/` over inline task duplication.

### 3.3 Shell Scripts

- Start every script with `set -euo pipefail`.
- Use functions for reusable logic.
- Support `--help` and `--debug` flags where applicable.

---

## 4. Testing Standards

### 4.1 Test Structure

- Tests go in `molecule/<scenario>/tests/<suite>/` (e.g., `tests/sanity/`, `tests/negative/`).
- Test files must be named `test_*.py`.
- Every test function must use `TestLogger` for structured output and reporting.
- Mark tests with appropriate pytest markers: `@pytest.mark.sanity`, `@pytest.mark.negative`, `@pytest.mark.smoke`, etc.
- Register any new markers in `pytest.ini`.

### 4.2 Test Guidelines

- Each test must be independent — do not rely on execution order unless using `@pytest.mark.order(n)`.
- Use `pytest.skip()` with a clear reason when preconditions are not met — never let tests fail due to missing infrastructure.
- Always assert with descriptive messages. Use message templates from the module's `messages/` directory.
- Use the `host` fixture from `conftest.py` for OIM server connections — do not create your own.

### 4.3 Test Execution

- Use `run_molecule <scenario> verify --suite sanity` for quick validation.
- Use `run_molecule --config` for batch execution via `test_run_config.yml`.
- Run `run_molecule list` to verify scenario discovery before execution.
- The `build_stream` scenario always uses `verify` (no converge step).

---

## 5. Configuration Management

### 5.1 omnia_test_config.yml

- Use placeholder values in documentation (e.g., `<OIM_SERVER_IP>`, `<SSH_PASSWORD>`).
- All config keys must have sensible defaults in the consuming code (use `.get(key, default)`).
- New parameters must be documented in the README parameter reference table.

### 5.2 test_run_config.yml

- Keep all scenarios listed even if disabled (`run: false`).
- Each scenario entry must have exactly three fields: `run`, `command`, `suite`.
- Group scenarios with section comments (e.g., `# --- Install & Setup ---`).
- This file is tracked in git — keep it minimal and clean.

---

## 6. Security

- Never commit IP addresses, passwords, API keys, or internal endpoints.
- Use `<PLACEHOLDER>` format in documentation and examples.
- Use `no_log: true` in Ansible tasks that handle credentials.
- Use `automation_library.core.secrets` for ansible-vault decryption.
- Never hardcode credentials in test files — read from config or vault.

---

## 7. Documentation

- The README must reflect the current repository structure at all times.
- All `omnia_test_config.yml` parameters must be documented with type, default, and description.
- All molecule scenarios must be listed in the scenarios table.
- All dataset files must be documented with which Omnia playbook consumes them.
- Use conventional commit format: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- Reference the scenario or module name when applicable (e.g., `feat(telemetry): add VictoriaMetrics retention test`).

---

## 8. Adding New Scenarios

When adding a new molecule scenario:

1. **Read the Omnia code** — `podman exec -it omnia_core bash` and study the target playbook and its roles.
2. Create `automation_library/<module>/` with `__init__.py`, `functions/`, `messages/`, `vars/`.
3. Create `molecule/<scenario>/` with `molecule.yml`, `create.yml`, `converge.yml`, and `tests/sanity/`.
4. Use `molecule/shared/tasks/setup_inventory.yml` in `create.yml`.
5. Use `molecule/shared/tasks/sync_project_default.yml` in `converge.yml` for dataset sync.
6. Add the scenario to:
   - `test_run_config.yml` (with `run: false` default)
   - `run_molecule.sh` ordered scenario lists
   - `README.md` scenarios table
7. Export public functions from the module's `__init__.py`.

---

## 9. Molecule Lifecycle Rules

- `create.yml` — Inventory setup and SSH readiness only. No deployment logic.
- `converge.yml` — Dataset sync + playbook execution inside `omnia_core`. Must check container existence first.
- `verify` — pytest-testinfra tests. Must handle missing infrastructure gracefully with `pytest.skip()`.

---

## 10. Core Library Usage

- Use `run_on_oim()` for OIM host commands, `run_in_container()` for container commands, `run_on_remote_node()` for cluster node commands.
- Use `load_input_file()` / `get_input_value()` to read config files from the container — do not use raw `podman exec cat`.
- Use `is_software_enabled()` to check software flags before running component-specific tests.
- Prefer `pytest.skip()` over `pytest.fail()` when infrastructure is missing or a feature is disabled.
- Log the skip reason using `TestLogger.skipped()` before calling `pytest.skip()`.
- Use `check_container_running()` before any container operations.

---

## 11. Core Library — Complete Function Catalog

All functions are imported from `automation_library.core`. This is the authoritative list — do not reimplement any of these.

### 11.1 Host & Connection (`host_func.py`)

| Function | Description |
|----------|-------------|
| `get_testinfra_host()` | Returns a testinfra `Host` object. Local mode if `oim_server_ip` is empty/localhost, otherwise SSH. |
| `load_omnia_test_config()` | Loads and returns the `omnia_test_config.yml` dict. |
| `get_dataset_path()` | Returns the local dataset directory path. |
| `is_local_execution()` | Returns `True` if running in local mode. |
| `run_on_oim(host, cmd)` | Runs a shell command on the OIM host. Returns `CompletedProcess`. |
| `run_in_container(host, cmd, container, workdir)` | Runs a command inside a Podman container. Default container: `omnia_core`. |
| `run_on_remote_node(host, target_ip, cmd, user, password, port)` | Runs a command on a remote cluster node via SSH from the OIM. |
| `get_node_info(host, identifier, by)` | Looks up a single node from `pxe_mapping_file.csv` by hostname, IP, service tag, or MAC. |
| `get_nodes_info(host, functional_group)` | Gets all nodes matching a functional group from `pxe_mapping_file.csv`. |
| `get_node_admin_ip(host, identifier)` | Shortcut: get admin IP of a node by identifier. |
| `get_functional_groups_from_pxe_mapping(host)` | Returns `set` of all functional groups in the PXE mapping. |
| `get_group_names_from_pxe_mapping(host)` | Returns `set` of group names (functional group minus arch suffix). |
| `check_container_running(host, container_name)` | Returns dict with `running` bool and container info. |
| `make_verification_result(name, passed, message, details)` | Helper to create a standardized verification result dict. |
| `get_project_root()` | Returns the absolute path to the project root directory. |

### 11.2 Input Loader (`load_inputs_func.py`)

| Function | Description |
|----------|-------------|
| `load_container_file(host, filepath)` | Reads and parses a YAML/JSON file from inside the container. Caches results. |
| `load_input_file(host, filename)` | Loads a file from `/opt/omnia/input/project_default/<filename>`. Caches results. |
| `get_input_value(host, filename, key, default)` | Get a specific value using dot-notation key (e.g., `admin_network.nic_name`). |
| `get_input_bool(host, filename, key, default)` | Same as `get_input_value` but coerces to `bool`. |
| `clear_input_cache()` | Clears the input file cache. Call when files may have changed. |
| `is_software_enabled(host, software_name)` | Checks if a software name exists in `software_config.json` softwares list. |
| `get_config_list_item(host, filename, list_key, match_key, match_value)` | Find an item in a list inside a config file by matching a field value. |
| `get_nfs_client_mount_path(host, nfs_name)` | Get the NFS client mount path from `storage_config.yml`. |

### 11.3 Secrets (`secrets_func.py`)

| Function | Description |
|----------|-------------|
| `view_credentials_file(host, file_path, key_file_path)` | Decrypts an ansible-vault file and returns the parsed dict. |
| `get_credential_value(host, file_path, key_file_path, key)` | Decrypts and extracts a single credential value. |
| `get_multiple_credentials(host, file_path, key_file_path, keys)` | Decrypts and extracts multiple credential values. |

### 11.4 Database (`db_exec_func.py`)

| Function | Description |
|----------|-------------|
| `exec_psql_query(host, query, db, container)` | Executes a SQL query in a Postgres container and returns rows as list of dicts. |
| `query_db_row(host, table, conditions, db, container)` | Query a single row from a Postgres table with conditions dict. |

### 11.5 Node Connectivity (`node_checks_func.py`)

| Function | Description |
|----------|-------------|
| `check_node_connectivity_once(host, admin_ip, hostname)` | Single ping + SSH check on a node. |
| `check_node_connectivity_with_retry(host, admin_ip, hostname, ping_retries, ssh_retries)` | Ping + SSH with configurable retries. |
| `verify_nodes_connectivity(host, nodes, ping_retries, ssh_retries)` | Batch connectivity check for a list of nodes. |
| `check_nodes_reachability(host, nodes)` | Quick reachability check — ping only. |
| `get_reachable_nodes(nodes)` | Filter to reachable nodes from cache. |
| `get_unreachable_nodes(nodes)` | Filter to unreachable nodes from cache. |
| `is_node_reachable(admin_ip)` | Check if a specific node is reachable (from cache). |
| `get_node_error(admin_ip)` | Get the error message for an unreachable node. |
| `clear_connectivity_cache()` | Clear the connectivity result cache. |
| `print_unreachable_nodes(unreachable)` | Log unreachable nodes with details. |
| `get_cloudinit_status(host, target_ip)` | Get cloud-init status on a provisioned node. |
| `wait_for_cloudinit(host, target_ip, timeout, interval)` | Wait for cloud-init to complete on a node. |
| `verify_cloudinit_status(host, nodes)` | Verify cloud-init status on a list of nodes. |

### 11.6 Build Stream (`build_stream_func.py`)

| Function | Description |
|----------|-------------|
| `is_build_stream_enabled(host)` | Check if BuildStream CI/CD is enabled in config. |
| `get_build_stream_job_id(host, stage_name)` | Resolve the BuildStream job ID — from config or latest COMPLETED job in DB. |
| `check_build_stream_stage(host, job_id, stage_name, expected_state)` | Validate a specific pipeline stage matches expected state. |

Stage constants: `STAGE_BUILD_IMAGE_X86_64`, `STAGE_BUILD_IMAGE_AARCH64`, `STAGE_CREATE_LOCAL_REPO`, `STAGE_VALIDATE_IMAGE`, `STAGE_PARSE_CATALOG`, `STAGE_GENERATE_INPUT`

### 11.7 Formatting (`formatting_func.py`)

| Item | Description |
|------|-------------|
| `Colors` | Terminal color codes (RED, GREEN, YELLOW, BLUE, CYAN, etc.) |
| `Symbols` | Unicode symbols (CHECK, CROSS, WARN, INFO, ARROW, BULLET, etc.) |
| `log(message, level)` | Print a formatted log message with color and symbol. |
| `set_debug_mode(enabled)` | Enable or disable debug-level output. |
| `TestLogger` | Structured test logger — `check()`, `passed()`, `failed()`, `skipped()`, `info()`, `debug()`, `section()`, `sub_check()`. |
| `get_test_output()` | Returns collected test output as a string. |

### 11.8 Reports (`report_func.py`)

| Item | Description |
|------|-------------|
| `TestReport` | Report builder — adds server info, test results, generates HTML/JSON. |
| `get_current_report()` | Returns the active `TestReport` instance. |
| `set_current_report(report)` | Sets the active `TestReport` instance. |

### 11.9 Constants (`vars/`)

Key path constants (all strings):

| Constant | Value | Description |
|----------|-------|-------------|
| `OIM_SHARED_PATH` | `/opt/omnia` | OIM shared data directory |
| `INPUT_BASE_PATH` | `/opt/omnia/input/project_default` | Input file base path in container |
| `OMNIA_CORE_CONTAINER` | `omnia_core` | Container name |
| `SOFTWARE_CONFIG_PATH` | `<base>/software_config.json` | Full path to software config |
| `TELEMETRY_CONFIG_PATH` | `<base>/telemetry_config.yml` | Full path to telemetry config |
| `NETWORK_SPEC_PATH` | `<base>/network_spec.yml` | Full path to network spec |
| `PXE_MAPPING_FILE_PATH` | `<base>/pxe_mapping_file.csv` | Full path to PXE mapping |

Functional group constants: `K8S_CONTROL_PLANE_FUNCTIONAL_GROUP`, `K8S_WORKER_NODE_FUNCTIONAL_GROUP`, `SLURM_CONTROL_NODE_FUNCTIONAL_GROUP`, `SLURM_NODE_FUNCTIONAL_GROUP`, `SLURM_NODE_AARCH64_FUNCTIONAL_GROUP`, `LOGIN_NODE_FUNCTIONAL_GROUP`, `MINIMAL_OS_X86_64_FUNCTIONAL_GROUP`, `MINIMAL_OS_AARCH64_FUNCTIONAL_GROUP`, etc.

---

## 12. Dependencies and Git Workflow

- Pin all dependency versions in `requirements.txt`.
- Do not add dependencies without confirming compatibility with the existing stack.
- The `-e .` entry in `requirements.txt` installs the local package in editable mode — do not remove it.
- Keep commits atomic — one logical change per commit.
- Ensure `run_molecule list` works before pushing.
- Run at least one `verify` scenario to confirm no import errors.

---

## 13. test\_run\_config.yml Validation

The `run_molecule.sh --config` command validates `test_run_config.yml` **before** executing any scenarios. Validation checks:

- **Scenario names** must match the supported list (defined in `SUPPORTED_SCENARIOS` at the top of `run_molecule.sh`).
- **`run` values** must be `true` or `false` (YAML booleans).
- **`command` values** must be one of: `test`, `verify`, `converge`, `create`, `prepare`.
- **`suite` values** must be one of: `sanity`, `negative`, `regression`, `smoke`, `stress`, `performance`, `build_auto`, `deploy_auto`, `build_manual`, `deploy_manual`, `cleanup_manual`, or empty string (all tests).

When adding a new scenario or suite, update the `SUPPORTED_*` variables at the top of `run_molecule.sh`.

---

## 14. Cloud-Init Customization

The `additional_cloud_init.yml` dataset file allows injecting custom cloud-init configuration into provisioned nodes:

- **`common`** section applies to ALL nodes.
- **`groups`** section provides per-functional-group overrides.
- Allowed keys: `write_files`, `runcmd` only.
- Prohibited keys: `bootcmd`, `network`, `network-config`, `packages` (platform-managed).
- Platform defaults always take precedence (`merge_how: no_replace`).
- Group names must match functional groups in `pxe_mapping_file.csv`.

---

## 15. Local Mode Execution

When `oim_server_ip` is empty or set to `localhost`/`127.0.0.1`:

- All Ansible plays use `ansible_connection: local` instead of SSH.
- `get_testinfra_host()` returns a `local://` connection.
- `omnia_sh_install` converge runs `omnia.sh --install` on the local machine.
- No SSH credentials are required.
- Dataset sync uses localhost as the rsync target.

This allows running the full automation stack on a single OIM server without a remote control node.
