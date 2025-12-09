# Molecule Tests: prepare_oim

This Molecule scenario validates the OIM (Omnia Infrastructure Manager) deployment by:

1. **SSH into OIM server** - Connect to the target OIM server
2. **Execute prepare_oim playbook** - Run the playbook inside `omnia_core` container
3. **Exit container and validate**:
   - OpenCHAMI containers and service status
   - Auth container/service (only when LDAP is configured in `software_config.json`)
   - omnia.target and all its dependencies

## Architecture

```
automation_2.0/
├── automation_library/
│   ├── functions/
│   │   └── prepare_oim_func.py    # Python validation logic
│   ├── vars/
│   │   └── prepare_oim_vars.py    # Configuration variables
│   └── messages/
│       └── prepare_oim_msgs.py    # User-facing messages
│
└── molecule/
    └── prepare_oim/
        ├── molecule.yml           # Molecule configuration
        ├── converge.yml           # Ansible playbook (SSH + run playbook)
        ├── requirements.txt       # Python dependencies
        ├── README.md              # This file
        └── test/
            ├── __init__.py
            ├── conftest.py                   # Pytest fixtures (uses automation_library)
            ├── test_openchami_containers.py  # OpenCHAMI container tests
            ├── test_auth_service.py          # Auth service tests (LDAP-conditional)
            └── test_omnia_target.py          # omnia.target validation tests
```

## Prerequisites

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OIM_SERVER_IP` | Target OIM server IP | `localhost` |
| `OIM_SSH_USER` | SSH username | `root` |
| `OIM_SSH_PASSWORD` | SSH password | (empty) |
| `OIM_SSH_PORT` | SSH port | `22` |
| `SOFTWARE_CONFIG_PATH` | Path to software_config.json | `/opt/omnia/software_config.json` |
| `CONTAINER_RUNTIME` | Container runtime (podman/docker) | `podman` |
| `OMNIA_CORE_CONTAINER` | Name of omnia_core container | `omnia_core` |
| `PREPARE_OIM_PLAYBOOK` | Path to prepare_oim playbook | `/opt/omnia/playbooks/prepare_oim.yml` |
| `PREPARE_OIM_INVENTORY` | Path to Ansible inventory | `/opt/omnia/inventory` |
| `PLAYBOOK_TIMEOUT` | Playbook execution timeout (seconds) | `600` |

## Running Tests

### Full Molecule Test Sequence

```bash
cd /root/automation_2.0
molecule test -s prepare_oim
```

### Run Only Verification (pytest)

```bash
cd /root/automation_2.0
molecule verify -s prepare_oim
```

### Run Converge + Verify

```bash
cd /root/automation_2.0
molecule converge -s prepare_oim
molecule verify -s prepare_oim
```

### Run pytest Directly

```bash
cd /root/automation_2.0/molecule/prepare_oim
export OIM_SERVER_IP=10.134.123.11
export OIM_SSH_USER=root
export OIM_SSH_PASSWORD=yourpassword
pytest test/ -v
```

## Test Details

### OpenCHAMI Container Tests (`test_openchami_containers.py`)

- `test_container_runtime_available` - Verifies podman/docker is installed
- `test_openchami_containers_exist` - Checks all required containers exist
- `test_openchami_containers_running` - Verifies containers are in "Up" state
- `test_openchami_containers_healthy` - Checks container health status
- `test_openchami_service_*` - Validates openchami.service systemd unit

### Auth Service Tests (`test_auth_service.py`)

> **Note:** These tests are **skipped** if LDAP is not configured in `software_config.json`

- `test_auth_containers_exist_when_ldap_enabled` - Checks auth containers exist
- `test_auth_containers_running_when_ldap_enabled` - Verifies auth containers running
- `test_auth_service_running_when_ldap_enabled` - Validates auth systemd service
- `test_ldap_connectivity_when_enabled` - Tests LDAP port accessibility

### omnia.target Tests (`test_omnia_target.py`)

- `test_omnia_target_exists` - Verifies omnia.target unit exists
- `test_omnia_target_enabled` - Checks target is enabled on boot
- `test_omnia_target_active` - Verifies target is active
- `test_all_dependencies_active` - Validates all dependencies are running
- `test_critical_dependencies_running` - Checks critical services
- `test_no_failed_dependencies` - Ensures no dependencies in failed state

## LDAP Configuration

The auth service tests check for LDAP configuration in `software_config.json`:

```json
{
  "ldap": true,
  ...
}
```

If `ldap` is `false` or not present, auth-related tests are automatically skipped.

## Customizing Configuration

All configuration is centralized in `automation_library/vars/prepare_oim_vars.py`:

```python
PREPARE_OIM_VARS = {
    # OpenCHAMI containers to validate
    "openchami_containers": [
        "openchami-smd",
        "openchami-bss",
        # Add or remove containers as needed
    ],
    
    # Auth containers (LDAP-dependent)
    "auth_containers": [
        "openchami-opaal",
        "openchami-ldap",
    ],
    
    # omnia.target critical dependencies
    "omnia_critical_dependencies": [
        "openchami.service",
        "network.target",
        "multi-user.target",
    ],
}
```

All assertion messages are in `automation_library/messages/prepare_oim_msgs.py`.

## Troubleshooting

### Tests fail to connect to remote host

1. Verify SSH credentials in environment variables
2. Check network connectivity: `ping $OIM_SERVER_IP`
3. Test SSH manually: `ssh $OIM_SSH_USER@$OIM_SERVER_IP`

### Container tests fail

1. Check container runtime: `podman ps` or `docker ps`
2. View container logs: `podman logs <container-name>`
3. Restart containers: `systemctl restart openchami`

### omnia.target tests fail

1. Check target status: `systemctl status omnia.target`
2. List dependencies: `systemctl list-dependencies omnia.target`
3. View logs: `journalctl -u omnia.target`
