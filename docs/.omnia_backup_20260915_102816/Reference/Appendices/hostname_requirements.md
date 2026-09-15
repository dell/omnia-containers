
# Hostname Requirements


This page documents the hostname constraints that Omnia enforces on all cluster nodes. Hostnames are assigned via the `HOSTNAME` column in the PXE mapping CSV and must comply with the rules below.

## Rules

| Constraint | Details |
| --- | --- |
| **RFC 952 / RFC 1123 compliant** | - Start with a letter (`a`--`z`).<br>- Contain only letters, digits (`0`--`9`), and hyphens (`-`).<br>- Be 1--63 characters long. |
| **Lowercase only** | Uppercase letters are rejected by `input_validator.yml`. |
| **No domain suffix** | Use `slurm-ctrl-01`, not `slurm-ctrl-01.hpc.example.com`. Domain is appended from `domain_name` in `provision_config.yml`. |
| **No underscores** | Use hyphens instead: `slurm-node-01`, not `slurm_node_01`. |
| **Unique** | Every hostname in the PXE mapping file must be unique. |
| **No reserved names** | Avoid `localhost`, `gateway`, `dns`, or system service names. | 

## Examples

| Hostname | Valid? | Reason |
| --- | --- | --- |
| `slurm-ctrl-01` | ✓ | Lowercase, letter start, hyphens only. |
| `kube-cp-01` | ✓ | Compliant. |
| `Slurm-Ctrl-01` | ✗ | Uppercase letters. |
| `slurm_node_01` | ✗ | Underscores not allowed. |
| `slurm-ctrl-01.hpc.example.com` | ✗ | Domain suffix included. |
| `-slurm-01` | ✗ | Starts with hyphen. |
| `01-slurm` | ✗ | Starts with digit. |
| `a-very-long-hostname-exceeds-sixty-three-characters-total` | ✗ | Exceeds 63 characters. |

## Naming conventions

Use zero-padded numbers (`01`, `02`) to enable Slurm node ranges (e.g., `slurm-gpu-[01-04]`):

| Role | Pattern |
| --- | --- |
| Slurm control | `slurm-ctrl-NN` |
| Slurm compute | `slurm-<type>-NN` |
| Login node | `login-NN` |
| K8s control plane | `kube-cp-NN` |
| K8s worker | `kube-wk-NN` |
| Auth server | `auth-NN` |

!!! info

    - [Pxe Mapping File](../SampleFiles/pxe_mapping_file.md) -- PXE mapping CSV where hostnames are assigned.
    - [Provision Config](../Configuration/provision_config.md) -- `domain_name` parameter that provides the DNS suffix.
