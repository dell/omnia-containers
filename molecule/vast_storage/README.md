# VAST Storage Integration Test Suite

## Overview
This test suite validates VAST storage integration with Omnia infrastructure, covering RDMA mounts, PowerScale/PowerVault backends, storage isolation, and performance targets.

**Test Specification**: TSPEC-STOR-2026-001 v1.0.0  
**Parent Documents**: 
- BSPEC-STOR-001 (vast_storage_bspec.pdf)
- FSPEC-STOR-001 (vast_functional_spec.md)
- ESPEC-STOR-001 (vast_engineering.md)

## Test Categories

### 1. Functional Tests (`tests/sanity/`)
- **Configuration**: Storage config parsing, backend assignment, mount options
- **Network**: InfiniBand configuration, RDMA connectivity, DNS resolution
- **VAST Specific**: Client installation, kernel module, RDMA mounts
- **Storage Isolation**: Per-node scratch, /tmp bind mounts, hostname directories
- **Integration**: Slurm state persistence, job storage paths, MPI checkpoints
- **Coverage**: 50+ test cases (TC-001 through TC-087)

### 2. Negative Tests (`tests/negative/`)
- **Error Handling**: Invalid YAML, missing configs, mount failures
- **Recovery**: STALE handle recovery, mount retry logic
- **Misconfigurations**: IB_MAC without IP, client boot failures
- **Coverage**: TC-010, TC-024, TC-033, TC-066, TC-069-073

### 3. Performance Tests (`tests/performance/`)
- **RDMA Latency**: Target <200 µs avg, <500 µs p99
- **Throughput**: Target ≥20 GB/s aggregate
- **IOPS**: Target >1M for 4KB random reads
- **Coverage**: TC-027, TC-076-077

## Prerequisites

### Environment Requirements
- OIM Node with Ansible 2.14+
- Compute nodes with InfiniBand HCA
- Controller nodes for Slurm
- VAST storage cluster (for full testing)
- PowerScale NFS server (optional)
- PowerVault iSCSI storage (optional)

### Configuration Files
- `/omnia/input/storage_config.yaml` - Storage backend configuration
- `/omnia/input/pxe_mapping.csv` - Network and IB mappings
- `/omnia/inventory/ansible_inventory.yml` - Node inventory

## Running Tests

### Full Test Suite
```bash
cd /root/rohith/automation/dcgm/working_hpc_auto/omnia-artifactory
molecule test -s vast_storage
```

### Specific Test Categories
```bash
# Functional tests only
molecule verify -s vast_storage -- -m sanity

# Negative tests only  
molecule verify -s vast_storage -- -m negative

# Performance tests only
molecule verify -s vast_storage -- -m performance

# Specific test case
molecule verify -s vast_storage -- -k test_vast_rdma_mount
```

### Test with Existing Environment
```bash
# Skip create/destroy, only run tests
molecule converge -s vast_storage
molecule verify -s vast_storage
```

## Test Coverage Matrix

| Category | Test Cases | Coverage |
|----------|------------|----------|
| BSpec ACs (6.1.5) | 7 | 100% |
| BSpec Requirements (6.1.x) | 14 | 100% |
| FSpec System Behaviors | 13 | 85% |
| FSpec Business Logic | 8 | 100% |
| FSpec Validations | 12 | 92% |
| FSpec NFRs | 6 | 83% |
| Error Scenarios | 10 | 80% |

## Key Test Scenarios

### Critical Path (P0)
- TC-001: Single backend active
- TC-003: Per-node scratch isolation
- TC-013: IB network configuration
- TC-016: VAST RDMA mount
- TC-021: VAST on compute only
- TC-048: IB link validation
- TC-052: Controller no VAST

### Performance Validation
- TC-027: RDMA latency (<200 µs)
- TC-076: Aggregate throughput (≥20 GB/s)
- TC-077: IOPS (>1M)

### Error Recovery
- TC-066: STALE handle recovery
- TC-024: Invalid YAML handling
- TC-033: Mount failure logging

## Known Limitations

### Test Environment
- Full RDMA performance requires physical IB hardware
- VAST cluster required for complete mount verification
- Scale testing limited by available node count
- Some tests marked `@manual` for physical lab validation

### Coverage Gaps
- SB-007: TCP fallback (not supported)
- SB-010: Mount health monitoring (not supported)
- VC-009: Max 10 mounts constraint (not covered)
- NFR-PERF-005: CPU overhead measurement (not covered)

## Troubleshooting

### Common Issues

1. **No nodes accessible**
   - Verify SSH connectivity to nodes
   - Check ansible inventory configuration
   - Ensure passwordless SSH is configured

2. **IB interface not found**
   - Expected in environments without InfiniBand
   - Tests will skip or warn appropriately

3. **VAST client not installed**
   - Expected in test environments
   - Full testing requires vastnfs RPM

4. **Performance targets not met**
   - Test environment may have limitations
   - Production validation required for full performance

### Debug Options
```bash
# Verbose output
molecule verify -s vast_storage -- -v

# Debug specific test
molecule verify -s vast_storage -- -k test_name -vv

# Show all test output
molecule verify -s vast_storage -- --tb=short --capture=no
```

## Integration with CI/CD

### GitLab CI Example
```yaml
vast-storage-tests:
  stage: test
  script:
    - molecule test -s vast_storage
  artifacts:
    reports:
      junit: molecule/vast_storage/reports/*.xml
  only:
    changes:
      - automation_library/vast_storage/**
      - molecule/vast_storage/**
```

### Jenkins Pipeline Example
```groovy
stage('VAST Storage Tests') {
    steps {
        sh 'molecule test -s vast_storage'
    }
    post {
        always {
            junit 'molecule/vast_storage/reports/*.xml'
        }
    }
}
```

## Contributing

### Adding New Tests
1. Add test case to appropriate category file
2. Update TEST_NAMES in messages module
3. Implement verification function if needed
4. Document in test specification

### Test Naming Convention
- Functional: `test_<feature>_<aspect>`
- Negative: `test_<error>_handling`
- Performance: `test_<metric>_performance`

## Support

For issues or questions:
- Review test specification: `vast_storage_test_spec.md`
- Check parent documents: BSpec, FSpec, ESpec
- Contact: Omnia Test Automation Team
