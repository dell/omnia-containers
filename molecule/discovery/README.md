# Discovery Module - Including Minimal OS Validation

This module runs the discovery.yml playbook inside the omnia_core container and validates the deployment, including Minimal OS functional groups.

## Features

### Discovery Validation
- ✅ Discovery playbook execution
- ✅ SSH connectivity tests
- ✅ Cloud-init verification
- ✅ Slurm configuration
- ✅ K8s telemetry checks
- ✅ Admin debug packages

### Minimal OS Validation (Integrated)
- ✅ Functional group schema (os_x86_64, os_aarch64)
- ✅ Architecture validation
- ✅ Base OS packages
- ✅ LDMS packages and service state
- ✅ Additional packages support
- ✅ Excluded packages verification
- ✅ Network identity and isolation
- ✅ SSH access and security
- ✅ Package manager functionality

## Test Files

```
molecule/discovery/tests/
├── test_ssh.py                    # SSH connectivity
├── test_cloudinit.py              # Cloud-init verification
├── test_slurm.py                  # Slurm configuration
├── test_k8s_telemetry.py          # K8s telemetry
├── test_admin_debug_packages.py   # Debug packages
└── test_minimal_os.py             # Minimal OS validation (19 tests)
```

## Prerequisites

- omnia_core container running (`omnia.sh --install` completed)
- prepare_oim.yml completed
- pxe_mapping_file.csv configured with nodes
- (Optional) Minimal OS functional groups configured

## Usage

```bash
# Run all checks + playbook + verify
./run_molecule.sh discovery test

# Run playbook only
./run_molecule.sh discovery converge

# Run verification tests only
./run_molecule.sh discovery verify
```

## Minimal OS Tests (19 tests)

### Functional Tests (13)
1. `test_functional_group_schema` - Validates functional groups
2. `test_architecture_x86_64` - x86_64 architecture
3. `test_architecture_aarch64` - aarch64 architecture
4. `test_base_packages` - Base OS packages
5. `test_ldms_packages` - LDMS packages
6. `test_excluded_packages` - No Slurm/K8s/CUDA
7. `test_additional_packages` - Custom packages
8. `test_additional_packages_fallback` - Graceful fallback
9. `test_network_identity` - Hostname/IP
10. `test_handoff_services` - Required services
11. `test_ssh_access` - SSH authentication
12. `test_package_manager` - dnf functionality
13. `test_ldms_service_state` - LDMS not running

### Negative Tests (3)
14. `test_architecture_mismatch_detection` - Validation enforced
15. `test_missing_image_detection` - Image detection
16. `test_invalid_packages_handling` - Package validation

### Security Tests (3)
17. `test_network_isolation` - Management network
18. `test_ssh_key_access` - SSH key-based access
19. `test_no_embedded_credentials` - No credentials

## Configuration

### user_config.yml
```yaml
oim_server_ip: "100.10.0.103"
oim_server_user: "root"
oim_server_password: "dell"
```

### PXE Mapping
Configure minimal OS nodes in `/opt/omnia/input/project_default/pxe_mapping_file.csv`:
```csv
hostname,functional_group,admin_ip,bmc_ip,service_tag
osnode,os_x86_64,10.40.7.205,100.10.1.188,G8L3Q03
```

### Additional Packages (Optional)
Create `/etc/omnia/additional_packages.json`:
```json
{
  "packages": ["vim", "htop", "custom-rpm"]
}
```

## Expected Results

```
======================== 30 passed, 9 skipped ========================
```

- Discovery tests: ~11 tests
- Minimal OS tests: 19 tests
- Total: ~42 tests (some may skip based on configuration)

## Minimal OS Features

### Supported
- ✅ Base OS packages (kernel, systemd, NetworkManager, etc.)
- ✅ LDMS packages for monitoring
- ✅ Additional custom packages via additional_packages.json
- ✅ SSH key authentication
- ✅ Network isolation
- ✅ Package manager (dnf)

### Excluded
- ❌ Slurm packages
- ❌ Kubernetes packages
- ❌ Docker/Podman
- ❌ CUDA/NVIDIA drivers
- ❌ MPI libraries

## Troubleshooting

### No Minimal OS nodes found
```bash
# Check PXE mapping
cat /opt/omnia/input/project_default/pxe_mapping_file.csv | grep "os_x86_64\|os_aarch64"

# Minimal OS tests will skip gracefully if no nodes configured
```

### Functional groups not found
```bash
# Check functional groups
podman exec omnia_core ls /etc/omnia/functional_groups/os_*.yml

# Minimal OS tests will skip if groups not configured
```

### SSH connectivity issues
```bash
# Test SSH to node
ssh root@<node_admin_ip> 'echo OK'

# Check authorized keys
ssh root@<node_admin_ip> 'cat /root/.ssh/authorized_keys'
```

## Integration Benefits

By integrating Minimal OS validation into the discovery module:

1. **Single Test Suite**: No separate molecule scenario needed
2. **Unified Reporting**: All results in one report
3. **Shared Infrastructure**: Uses same OIM server connection
4. **Simplified Workflow**: One command runs all validations
5. **Better Maintenance**: Fewer files to maintain

## Reports

After running tests, view reports:
```bash
# JSON report
cat reports/test_report.json | jq

# HTML report
firefox reports/test_report.html
```

## Notes

- Minimal OS tests are optional - they skip gracefully if nodes not configured
- Tests validate both x86_64 and aarch64 architectures
- LDMS service should NOT be running at handoff (started by RKE2)
- Additional packages are optional - tests skip if not configured
