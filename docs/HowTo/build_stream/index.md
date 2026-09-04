# Build Stream

The build_stream domain (collection: `omnia.build_stream`) provides a RESTful API service that orchestrates GitOps-based CI/CD pipelines for automated image building and deployment using GitLab.

## Overview

Build Stream is a RESTful API service that orchestrates the creation and management of build jobs for the Omnia infrastructure platform. It provides a centralized interface for managing software catalog parsing, local repository creation, image building, and validation workflows. The FastAPI service runs inside a Podman container, while Ansible playbooks run directly on the host from the shared Omnia venv.

**Customer-facing interface**: GitLab CE Omnibus with TLS, CI/CD pipelines, runner, and project configuration
**Backend orchestration**: FastAPI REST API that triggers domain execution (repo_manager, image_build_manager, discovery, orchestrator, telemetry)

## Prerequisites

Before using the build_stream domain, ensure the following prerequisites are met:

- **Main domain setup completed**: The omnia.sh CLI must be installed and configured (`./omnia.sh -s`)
- **GitLab requirements**: Sufficient system resources for GitLab CE (4GB+ RAM, 20GB+ disk space)
- **Network connectivity**: OIM must have network access to GitLab repositories and external services
- **Container runtime**: Podman must be installed and operational on the OIM host
- **Input files configured**: `build_stream_config.yml` must be properly configured
- **Domain dependencies**: Other domains (repo_manager, image_build_manager, etc.) must be available for pipeline execution

## System Context

```
  GitLab Pipeline (customer-facing)
         ↓
  Build Stream REST API
         ↓
  Domain execution:
  - repo_manager
  - image_build_manager
  - discovery
  - orchestrator
  - telemetry
```

## When to Use This Domain

- Use when implementing GitOps-based deployment
- Use when automating image building and deployment via REST API
- Use when managing image catalogs and pipelines
- Optional service - not part of the core domain execution flow

## Domain Workflow

The domain supports the following execution tags:

| Tag | Description | Prerequisites |
|-----|-------------|---------------|
| `validate` | Validate catalog and pipeline configuration | No |
| `prepare` | Deploy GitLab and CI/CD infrastructure | Yes |
| `execute` | Execute build and deploy pipelines | Yes |
| `cleanup` | Remove pipeline artifacts | No |

## Execution Flow

Build Stream follows a clean architecture pattern with clear separation of concerns:

1. **API Layer** - FastAPI routes and HTTP handling
2. **Core Layer** - Business logic, entities, and domain services
3. **Orchestrator Layer** - Use cases that coordinate workflows
4. **Infrastructure Layer** - External integrations and data persistence
5. **Common Layer** - Shared utilities and configuration

## Key Inputs

| Input | Location | Purpose |
|-------|----------|---------|
| `build_stream_config.yml` | `/opt/omnia/build_stream/input/<project>/build_stream_config.yml` | BSM + GitLab configuration |
| `omnia.env` | `/etc/omnia/omnia.env` | Common environment variables |

**Input Sources:**
- **Administrator** - Provides build_stream configuration
- **Domain initialization** - Stages input files from source tree

## Key Outputs

| Output | Location | Purpose |
|--------|----------|---------|
| Build status | `/opt/omnia/build_stream/output/<project>/` | Build job status and results |
| Playbook logs | `/opt/omnia/build_stream/log/playbooks/` | Ansible playbook execution logs |
| Job queue | `/opt/omnia/build_stream/playbook_queue/` | Watcher job queue directory |

## Output Contract

This contract is consumed by:
- **GitLab pipelines** - For automated CI/CD workflows
- **Administrators** - For monitoring build status and results

## Build Stream Components

| Category | Component | Description |
|----------|-----------|-------------|
| **API Service** | FastAPI | REST API for build job management |
| **Database** | PostgreSQL | Persistent job and artifact metadata |
| **CI/CD** | GitLab | CI/CD pipeline for catalog-driven builds |
| **Orchestration** | Playbook watcher | Monitors queue and triggers Ansible playbooks |
| **Execution** | Ansible playbooks | Infrastructure provisioning and deployment |

## Related Guides

## Core Deployment
- [Deploy GitLab](deploy_gitlab.md) -- Deploy GitLab CE Omnibus with CI/CD pipelines

## Pipeline Operations
- [Execute Build Pipeline](execute_build_pipeline.md) -- Execute build pipeline via GitLab
- [Execute Deploy Pipeline](execute_deploy_pipeline.md) -- Execute deploy pipeline via GitLab
- [Add Nodes to Cluster](add_nodes.md) -- Add nodes to cluster via pipeline
- [Initialize Telemetry](initialize_telemetry.md) -- Initialize telemetry via pipeline
- [Update Catalog](update_catalog.md) -- Update software catalog
- [Cleanup Operations](cleanup_operations.md) -- Cleanup pipeline artifacts
- [Retry Pipelines](retry_pipelines.md) -- Retry failed pipelines

## Additional
- [Getting Started: Build Stream](../../GetStarted/buildstream_deployment.md) -- Quick start guide
- [Domain Contract](../../Reference/domain_contracts/build_stream_contract.md) -- Build Stream domain contract




