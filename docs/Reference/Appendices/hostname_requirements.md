
# Hostname Requirements


This page documents the hostname constraints that Omnia enforces on all cluster nodes. Hostnames are assigned via the `HOSTNAME` column in the PXE mapping CSV and must comply with the rules below.

## Rules

| Constraint | Details |
| --- | --- |
| **RFC 952 / RFC 1123 compliant** | - Start with a letter (`a`--`z`).<br>- Contain only letters, digits (`0`--`9`), and hyphens (`-`).<br>- Be 1--63 characters long. |
| **Lowercase only** | Uppercase letters are rejected by the Orchestrator PXE mapping validator. |
| **No domain suffix** | Use `slurm-ctrl-01`, not `slurm-ctrl-01.hpc.example.com`. The OIM domain is configured through `SYSTEM_DOMAIN_NAME` in `omnia.env`. |
| **No underscores** | Use hyphens instead: `slurm-node-01`, not `slurm_node_01`. |
| **Unique** | Every hostname in the PXE mapping file must be unique. |
| **Cluster DNS format** | By default, use exactly `nid001` through `nid999`. Descriptive custom names are supported only when Cluster DNS is disabled by setting `dns_enabled: false`. |
| **No reserved names** | Avoid `localhost`, `gateway`, `dns`, or system service names. | 

## Examples

| Hostname | Valid? | Reason |
| --- | --- | --- |
| `nid001` | ✓ | Default three-digit format for Cluster DNS. |
| `slurm-ctrl-01` | ✓ | Compliant when Cluster DNS is disabled. |
| `kube-cp-01` | ✓ | Compliant when Cluster DNS is disabled. |
| `Slurm-Ctrl-01` | ✗ | Uppercase letters. |
| `slurm_node_01` | ✗ | Underscores not allowed. |
| `slurm-ctrl-01.hpc.example.com` | ✗ | Domain suffix included. |
| `-slurm-01` | ✗ | Starts with hyphen. |
| `01-slurm` | ✗ | Starts with digit. |
| `a-very-long-hostname-that-exceeds-the-sixty-three-character-limit-for-hosts` | ✗ | Exceeds 63 characters. |

## Naming conventions

When Cluster DNS is disabled by setting `dns_enabled: false`, use zero-padded
numbers (`01`, `02`) to enable Slurm node ranges (for example,
`slurm-gpu-[01-04]`):

| Role | Pattern |
| --- | --- |
| Slurm control | `slurm-ctrl-NN` |
| Slurm compute | `slurm-<type>-NN` |
| Login node | `login-NN` |
| K8s control plane | `kube-cp-NN` |
| K8s worker | `kube-wk-NN` |
| Auth server | `auth-NN` |

By default, use the `nidNNN` convention for every role and maintain the role
assignment in `FUNCTIONAL_GROUP_NAME`.

!!! info

    - [Pxe Mapping File](../SampleFiles/pxe_mapping_file.md) -- PXE mapping CSV where hostnames are assigned.
    - [Main Environment](../Configuration/omnia_env.md) -- `SYSTEM_DOMAIN_NAME` provides the OIM domain name.















