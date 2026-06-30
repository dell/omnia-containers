
# Hostname Requirements


This page documents the hostname constraints that Omnia enforces on all
cluster nodes. Hostnames are assigned via the `HOSTNAME` column in the
PXE mapping CSV and must comply with the rules below.

## Rules


| # | Rule | Details |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | **Lowercase only** | Hostnames must consist entirely of lowercase characters. Uppercase letters are rejected by `input_validator.yml`. |  |  |  |  |
| 2 | **No domain suffix** | Do not include a domain name in the hostname field. Use `slurm-ctrl-01`, not `slurm-ctrl-01.hpc.example.com`. The domain suffix is appended automatically from `domain_name` in `provision_config.yml`. |  |  |  |  |
| 3 | **RFC 952 / RFC 1123 compliant** | Hostnames must: | Start with a letter (`a`--`z`). | Contain only letters (`a`--`z`), digits (`0`--`9`), and hyphens (`-`). | Not start or end with a hyphen. | Be between 1 and 63 characters long. |
| 4 | **No underscores** | Underscores (`_`) are not permitted in hostnames per RFC 952. Use hyphens (`-`) instead: `slurm-node-01`, not `slurm_node_01`. |  |  |  |  |
| 5 | **No consecutive hyphens** | Avoid double hyphens (`--`) as some DNS implementations handle them inconsistently. |  |  |  |  |
| 6 | **Unique across the cluster** | Every hostname in the PXE mapping file must be unique. Duplicate hostnames cause provisioning failures. |  |  |  |  |
| 7 | **No reserved names** | Do not use `localhost`, `gateway`, `dns`, or any hostname that conflicts with system services. |  |  |  |  |

## Valid and invalid examples


| Hostname | Valid? | Reason |
| --- | --- | --- |
| `slurm-ctrl-01` | Yes | Lowercase, starts with letter, uses hyphens. |
| `kube-cp-01` | Yes | Short and descriptive. |
| `gpu-node-r760xa-03` | Yes | Includes model info for identification. |
| `Slurm-Ctrl-01` | **No** | Contains uppercase letters. |
| `slurm_node_01` | **No** | Contains underscores. |
| `slurm-ctrl-01.hpc.example.com` | **No** | Includes domain suffix (appended automatically). |
| `-slurm-01` | **No** | Starts with a hyphen. |
| `01-slurm` | **No** | Starts with a digit. |
| `a` | Yes | Minimum 1 character (though descriptive names are recommended). |
| `a-very-long-hostname-that-exceeds-sixty-three-characters-in-total-length` | **No** | Exceeds 63-character maximum. |

## Recommended naming conventions


| Role | Pattern | Example |
| --- | --- | --- |
| Slurm control | `slurm-ctrl-NN` | `slurm-ctrl-01` |
| Slurm compute | `slurm-<type>-NN` | `slurm-gpu-01`, `slurm-cpu-01` |
| Login node | `login-NN` | `login-01` |
| K8s control plane | `kube-cp-NN` | `kube-cp-01`, `kube-cp-02` |
| K8s worker | `kube-wk-NN` | `kube-wk-01` |
| Auth server | `auth-NN` | `auth-01` |

!!! tip

    Using a consistent naming scheme with zero-padded numbers (`01`, `02`)
    allows Slurm node ranges (`slurm-gpu-[01-04]`) and simplifies inventory
    management.

!!! info

    - [Pxe Mapping File](../SampleFiles/pxe_mapping_file.md) -- PXE mapping CSV where
      hostnames are assigned.
    - [Provision Config](../Configuration/provision_config.md) -- `domain_name`
      parameter that provides the DNS suffix.
