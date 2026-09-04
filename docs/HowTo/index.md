# How-to Guides


Task-oriented procedures for deploying, configuring, and managing Omnia
clusters using the domain-based architecture. Each guide follows a consistent structure: **Overview**, **Prerequisites**,
**Procedure**, **Verification**, **Next Steps**, and **Troubleshooting**.

!!! tip

    If you are new to Omnia, start with the [Get Started](../GetStarted/index.md) tutorials
    first. How-to guides assume you understand Omnia's architecture and have a
    working OIM.

## Domain-Based Guides

Omnia organizes functionality into independent domains. Each domain has its own how-to guides:

| Domain | Description | Index Page |
|--------|-------------|------------|
| **main** | Setup, initialization, and cross-domain coordination | [Main](main/index.md) |
| **repo_manager** | Repository mirroring and package synchronization | [Repository Manager](repo_manager/index.md) |
| **discovery** | Node inventory and PXE mapping file generation | [Discovery](discovery/index.md) |
| **image_build_manager** | OS image building and S3 storage | [Image Build Manager](image_build_manager/index.md) |
| **orchestrator** | Slurm, Kubernetes, networking, storage, authentication | [Orchestrator](orchestrator/index.md) |
| **telemetry** | iDRAC, LDMS, storage, and fabric metrics collection | [Telemetry](Telemetry/index.md) |
| **build_stream** | GitLab CI/CD pipeline automation | [BuildStreaM](build_stream/index.md) |
| **utils** | Helper utilities for backup and installation | [Utilities](utils/index.md) |

## Domain-Specific Procedures

Click on a domain above to view its specific how-to guides. Each domain includes:

- Configuration procedures
- Deployment workflows
- Verification steps
- Troubleshooting guidance

!!! note

    Domains are independent and can be executed standalone. However, typical deployments follow the execution order: main → repo_manager → image_build_manager → discovery → orchestrator → telemetry. BuildStreaM orchestrates this sequence automatically via GitLab CI/CD.



















