# provision Config Reference

The `provision_config.yml` file configures Slurm, Kubernetes, networking, storage, and authentication.

## Location

```
/opt/omnia/orchestrator/input/project_default/provision_config.yml
```

## Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `deploy_slurm` | boolean | No | false | Deploy Slurm job scheduler |
| `deploy_kubernetes` | boolean | No | false | Deploy Kubernetes services |
| `configure_infiniband` | boolean | No | false | Configure InfiniBand networking |
| `configure_ldap` | boolean | No | false | Configure LDAP authentication |
| `slurm_config` | object | No | - | Slurm configuration |
| `kubernetes_config` | object | No | - | Kubernetes configuration |

## Usage Example

```yaml title="File: /opt/omnia/orchestrator/input/project_default/provision_config.yml"
deploy_slurm: true
deploy_kubernetes: true
configure_infiniband: true
configure_ldap: true
slurm_config:
  control_machine: slurm-control-node
kubernetes_config:
  control_plane: service-kube-control-plane
```

## Related Configuration

- [network_spec.md](network_spec.md)
- [storage_config.md](storage_config.md)
- [security_config.md](security_config.md)
- [Domain Contract](../domain_contracts/orchestrator_contract.md)







