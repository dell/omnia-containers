# Omnia 2.0 Image Build Script for all containers

This repository contains a script to build multiple containers images using either `Podman` or `Docker`. The script allows you to build different images like `omnia_core`, `omnia_auth`, `omnia_pcs`, and `ubuntu_ldms`.

## Prerequisites

Before executing the script, ensure that you have the following installed:

### 1. Container Engine

The script supports **Podman** or **Docker**.

#### Option A: Podman

- **Podman**: You can install Podman by following the [official installation guide](https://podman.io/getting-started/installation).

#### Option B: Docker

- **Docker**: You can install Docker using the following commands

```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker
docker --version
docker buildx create --name mybuilder --driver docker-container --use
docker buildx inspect --bootstrap
docker buildx ls
```

### 2. Bash

- **Bash**: The script is a Bash script, so it requires Bash to run. It should work on most Unix-based systems like Linux and macOS.

## `build_images.sh` Script Overview

The `build_images.sh` script builds the following containers:

### Omnia Containers
- **omnia_core**: image for core Omnia container - `core`.
- **omnia_auth**: image for auth Omnia container - `auth`.
- **omnia_pcs**: image for PCS container - `pcs`.
- **ubuntu_ldms**: image for LDMS (OVIS) monitoring container - `ubuntu-ldms`.

### iDRAC Telemetry Containers
- **kafkapump**: Apache Kafka data pump for iDRAC telemetry - `kafkapump`.
- **victoriapump**: VictoriaMetrics data pump for iDRAC telemetry - `victoriapump`.
- **telemetry_receiver**: Complete telemetry collection service - `telemetry-receiver`.

## Quick Reference - Common Commands

```bash
# Build all containers (default: podman, latest tags, staging branch)
./build_images.sh
# ⚠️ Warning will be shown about using default branch: staging

# Build all with specific Omnia branch
./build_images.sh all omnia_branch=v2.0.0.0-rc2

# Build all with Docker and specific tag
./build_images.sh all build_tool=docker image_tag=1.0 omnia_branch=staging

# Build and push all to registry
./build_images.sh all build_tool=docker build_action=push image_tag=1.0 omnia_branch=staging

# Build specific containers (core + auth)
./build_images.sh core,auth image_tag=1.0 omnia_branch=v2.0.0.0-rc2

# Build pipeline (core + auth + ubuntu-ldms)
./build_images.sh pipeline image_tag=1.0 omnia_branch=staging

# Build only core with specific branch
./build_images.sh core omnia_branch=v2.0.0.0-rc2 core_tag=2.0

# Build all telemetry containers
./build_images.sh telemetry

# Build specific telemetry container
./build_images.sh kafkapump image_tag=1.0

# Build telemetry with specific iDRAC repo version
./build_images.sh telemetry idrac_telemetry_version=main image_tag=latest
```

## Script Usage

### Available Parameters

**Container Options:** `all`, `core`, `pcs`, `auth`, `ubuntu-ldms`, `pipeline`, `telemetry`, `kafkapump`, `victoriapump`, `telemetry-receiver`

**Common Parameters (valid for all containers):**
- `build_tool=<podman|docker>` - Build tool to use (default: `podman`)
- `build_action=<load|push>` - Action after build (default: `load`)
- `image_tag=<tag>` - Set same tag for all containers (default: `latest`)

**Omnia Container-Specific Parameters:**
- `omnia_branch=<branch>` - Omnia branch/tag to use for core container (default: `staging`, valid with: `core`, `all`, `pipeline`)
  - ⚠️ **Warning:** If not specified when building core, a warning will be shown with the default branch name
- `core_tag=<tag>` - Individual tag for omnia_core (valid with: `core`, `all`, `pipeline`)
- `auth_tag=<tag>` - Individual tag for omnia_auth (valid with: `auth`, `all`, `pipeline`)
- `pcs_tag=<tag>` - Individual tag for omnia_pcs (valid with: `pcs`, `all`)
- `ubuntu_ldms_tag=<tag>` - Individual tag for ubuntu-ldms (valid with: `ubuntu-ldms`, `all`, `pipeline`)

**iDRAC Telemetry Container-Specific Parameters:**
- `idrac_telemetry_version=<branch|tag>` - iDRAC Telemetry repo version (default: `main`, valid with: `telemetry`, `kafkapump`, `victoriapump`, `telemetry-receiver`)
- `kafkapump_tag=<tag>` - Individual tag for kafkapump (valid with: `kafkapump`, `telemetry`)
- `victoriapump_tag=<tag>` - Individual tag for victoriapump (valid with: `victoriapump`, `telemetry`)
- `telemetry_receiver_tag=<tag>` - Individual tag for telemetry-receiver (valid with: `telemetry-receiver`, `telemetry`)

**Special Options:**
- `all` - Builds: core and auth containers only
- `pipeline` - Builds: core, auth, and ubuntu-ldms containers
- `telemetry` - Builds: kafkapump, victoriapump, and telemetry-receiver containers

**Parameter Validation:**
The script validates parameters in two stages with context-specific error messages:

1. **Invalid parameter names** - Shows only valid parameters for the specific container(s) being built
   ```bash
   # Example: Building core with invalid parameter
   ./build_images.sh core sas=1
   # Error: Invalid parameter(s): sas
   # Valid parameters for 'core': build_tool build_action image_tag core_tag omnia_branch
   ```

2. **Wrong container-specific parameters** - Validates tag parameters match the container type
   ```bash
   # Example: Using auth_tag when building only core
   ./build_images.sh core auth_tag=1.0
   # Error: Parameter 'auth_tag' is not valid for container 'core'
   # Valid parameters for 'core': build_tool build_action image_tag core_tag omnia_branch
   ```

3. **Default branch warning** - When building core without specifying `omnia_branch`
   ```bash
   ./build_images.sh core
   # ⚠️ Warning: omnia_branch not specified, using default branch: staging
   ```

---

### 1. Building ALL Images

Build core and auth containers (the primary Omnia containers).

#### Basic - Default Settings
```bash
# Build all with defaults (podman, latest tags, staging branch) - no parameters needed
./build_images.sh
# ⚠️ Warning: omnia_branch not specified, using default branch: staging

# OR explicitly specify 'all'
./build_images.sh all
# ⚠️ Warning: omnia_branch not specified, using default branch: staging

# Build all with explicit branch (no warning)
./build_images.sh all omnia_branch=staging
```

Both commands build core and auth containers with default settings (podman, latest tags, staging branch).

#### With Docker
```bash
# Build all images with Docker
./build_images.sh all build_tool=docker
```

#### With Omnia Branch/Version
```bash
# Build all with specific Omnia branch (default tool: podman) - no warning
./build_images.sh all omnia_branch=v2.0.0.0-rc2

# Build all with specific branch and Docker - no warning
./build_images.sh all omnia_branch=v2.0.0.0-rc2 build_tool=docker

# Build all with explicit staging branch (same as default but no warning)
./build_images.sh all omnia_branch=staging
```

**Note:** Explicitly specifying `omnia_branch=staging` suppresses the warning even though staging is the default.

#### With Unified Tag for All Images
```bash
# Build all with same tag "1.0"
./build_images.sh all image_tag=1.0

# Build all with tag "1.0" using Docker
./build_images.sh all image_tag=1.0 build_tool=docker

# Build all with tag "2.0" and specific branch
./build_images.sh all omnia_branch=v2.0.0.0-rc2 image_tag=2.0
```

#### With Individual Tags per Container
```bash
# Build all (core and auth) with different tags
./build_images.sh all core_tag=1.0 auth_tag=1.1

# Build all with individual tags using Docker
./build_images.sh all build_tool=docker core_tag=1.0 auth_tag=1.1
```

---

### 2. Building Specific Images

Build individual containers or specific combinations.

#### Single Container Builds
```bash
# Build only core (will show warning about default branch)
./build_images.sh core

# Build only core with specific branch
./build_images.sh core omnia_branch=v2.0.0.0-rc2

# Build only core with specific tag and branch
./build_images.sh core core_tag=1.0 omnia_branch=staging

# Build only core with Docker
./build_images.sh core build_tool=docker core_tag=1.0

# Build only auth (omnia_branch not valid here)
./build_images.sh auth

# Build only auth with specific tag
./build_images.sh auth auth_tag=1.0

# Build only pcs (omnia_branch not valid here)
./build_images.sh pcs

# Build only pcs with specific tag
./build_images.sh pcs pcs_tag=1.0

# Build only ubuntu-ldms (omnia_branch not valid here)
./build_images.sh ubuntu-ldms

# Build only ubuntu-ldms with specific tag
./build_images.sh ubuntu-ldms ubuntu_ldms_tag=1.0
```

**Note:** `omnia_branch` is only valid when building containers that include `core` (i.e., `core`, `all`, `pipeline`, or any combination including `core`).

#### Multiple Specific Containers
```bash
# Build core and auth only (will show warning about default branch)
./build_images.sh core,auth

# Build core and auth with specific branch
./build_images.sh core,auth omnia_branch=v2.0.0.0-rc2

# Build core and auth with same tag
./build_images.sh core,auth image_tag=1.0

# Build core and auth with different tags and branch (only core_tag, auth_tag, omnia_branch are valid)
./build_images.sh core,auth core_tag=1.0 auth_tag=1.1 omnia_branch=staging

# Build core and auth with Docker
./build_images.sh core,auth build_tool=docker core_tag=1.0 auth_tag=1.0

# Build auth and ubuntu-ldms (only auth_tag and ubuntu_ldms_tag are valid)
./build_images.sh auth,ubuntu-ldms auth_tag=1.0 ubuntu_ldms_tag=1.0

# Build core, auth, and ubuntu-ldms (all three tag parameters are valid)
./build_images.sh core,auth,ubuntu-ldms image_tag=1.0
```

**Note:** When building multiple containers, only the tag parameters for those specific containers are valid. For example, using `pcs_tag` when building `core,auth` will result in an error.

#### Pipeline Builds (core + auth + ubuntu-ldms)
```bash
# Build pipeline containers with defaults
./build_images.sh pipeline

# Build pipeline with unified tag
./build_images.sh pipeline image_tag=1.0

# Build pipeline with individual tags
./build_images.sh pipeline core_tag=1.0 auth_tag=1.1 ubuntu_ldms_tag=1.2

# Build pipeline with Docker
./build_images.sh pipeline build_tool=docker image_tag=1.0

# Build pipeline with specific Omnia branch
./build_images.sh pipeline omnia_branch=v2.0.0.0-rc2 image_tag=1.0
```

---

### 3. Pushing Images to Registry

Build and push images to Docker registry (requires `build_tool=docker` and `build_action=push`).

#### Push ALL Images
```bash
# Build and push all images (core and auth) with unified tag and branch
./build_images.sh all build_tool=docker build_action=push image_tag=1.0 omnia_branch=staging

# Build and push all with individual tags and specific branch
./build_images.sh all build_tool=docker build_action=push core_tag=1.0 auth_tag=1.1 omnia_branch=v2.0.0.0-rc2

# Build and push all with specific branch and tag
./build_images.sh all omnia_branch=v2.0.0.0-rc2 build_tool=docker build_action=push image_tag=2.0
```

#### Push Specific Images
```bash
# Build and push only core and auth (includes core, so omnia_branch is valid)
./build_images.sh core,auth build_tool=docker build_action=push core_tag=1.0 auth_tag=1.0 omnia_branch=staging

# Build and push only ubuntu-ldms (no core, so omnia_branch not valid)
./build_images.sh ubuntu-ldms build_tool=docker build_action=push ubuntu_ldms_tag=1.0

# Build and push pipeline containers (includes core, so omnia_branch is valid)
./build_images.sh pipeline build_tool=docker build_action=push image_tag=1.0 omnia_branch=v2.0.0.0-rc2

# Build and push pcs only (no core, so omnia_branch not valid)
./build_images.sh pcs build_tool=docker build_action=push pcs_tag=1.0
```

**Important Notes:**
- ⚠️ `build_action=push` **requires** `build_tool=docker`
- Default registry: `docker.io/dellhpcomniaaisolution`
- Registry can be customized by modifying `OMNIA_DOCKER_REGISTERY` variable in the script
- Pushed images include SBOM and provenance metadata for security


# **Building LDMS PRODUCER RPM Package**

The `build_rpm.sh` script is designed to create LDMS producer RPM packages. It accepts three optional parameters: `LDMS_TAGGED_VERSION`, `SLURM_REPO_URL` and `SLURM_REPO_NAME`.

#### Syntax:
```bash
./build_rpm.sh -v [LDMS_TAGGED_VERSION]-u [SLURM_REPO_URL] -n [SLURM_REPO_NAME]
```

#### Example

- To build the RPM package without any optional parameters:

  ```bash
  ./build_rpm.sh
  ```

- To build the RPM package with both SLURM repository URL and name:

  ```bash
  ./build_rpm.sh -v 4.5.1 -u https://example.com/slurm-repo -n x86_64_slurm_custom
  ```

**Note**: If the `SLURM_REPO_URL` is provided, the script will use it to fetch the necessary dependencies. If `SLURM_REPO_NAME` is provided, it will be used to name the RPM package accordingly.

---

# **Building iDRAC Telemetry Containers**

The build script now supports building containers for iDRAC Telemetry Reference Tools components. These containers are built from the source code in the [iDRAC-Telemetry-Reference-Tools repository](https://github.com/dell/iDRAC-Telemetry-Reference-Tools).

## Components

### 1. **KafkaPump** (`kafkapump`)
Data pump that publishes iDRAC telemetry data to Apache Kafka topics.

### 2. **VictoriaPump** (`victoriapump`)  
Data pump that publishes iDRAC telemetry data to VictoriaMetrics.

### 3. **Telemetry Receiver** (`telemetry-receiver`)
Complete telemetry collection service that includes:
- `idrac-telemetry-receiver` - Main telemetry receiver
- `dbdiscauth` - Database discovery and authentication
- `configui` - Configuration UI  
- `redfishread` - Redfish API reader

## Usage Examples

### Build All Telemetry Containers

```bash
# Build all three telemetry containers with default settings
./build_images.sh telemetry

# Build all with specific tag
./build_images.sh telemetry image_tag=v1.0.0

# Build all with specific iDRAC Telemetry repo version
./build_images.sh telemetry idrac_telemetry_version=v1.2.0 image_tag=1.2.0
```

### Build Individual Telemetry Containers

```bash
# Build only KafkaPump
./build_images.sh kafkapump

# Build only VictoriaPump with specific tag
./build_images.sh victoriapump victoriapump_tag=v1.0.0

# Build only Telemetry Receiver
./build_images.sh telemetry-receiver telemetry_receiver_tag=latest
```

### Build with Different iDRAC Telemetry Versions

```bash
# Build from main branch (default)
./build_images.sh telemetry

# Build from specific tag
./build_images.sh telemetry idrac_telemetry_version=v1.5.0

# Build from specific branch
./build_images.sh telemetry idrac_telemetry_version=develop
```

### Build and Push to Registry

```bash
# Push all telemetry containers to registry
./build_images.sh telemetry \
  build_tool=docker \
  build_action=push \
  image_tag=1.0.0

# Push specific telemetry container
./build_images.sh kafkapump \
  build_tool=docker \
  build_action=push \
  kafkapump_tag=v1.0.0
```

### Build with Individual Tags

```bash
# Build all telemetry containers with different tags
./build_images.sh telemetry \
  kafkapump_tag=kafka-v1.0 \
  victoriapump_tag=victoria-v1.0 \
  telemetry_receiver_tag=receiver-v1.0

# Build multiple with mixed tags
./build_images.sh kafkapump,victoriapump \
  image_tag=1.0.0 \
  idrac_telemetry_version=main
```

## Container Details

### Dockerfile Locations

- **KafkaPump**: `ContainerFile/idrac_telemetry/Dockerfile.kafkapump`
- **VictoriaPump**: `ContainerFile/idrac_telemetry/Dockerfile.victoriapump`
- **Telemetry Receiver**: `ContainerFile/idrac_telemetry/Dockerfile.telemetry_receiver`

### Build Process

1. Clones iDRAC-Telemetry-Reference-Tools repository at specified version
2. Downloads Go dependencies
3. Builds static binaries with version information
4. Creates minimal scratch-based images
5. Includes SBOM and provenance metadata (when pushed)

### Image Characteristics

- **Base Image**: `scratch` (minimal, no OS overhead)
- **User**: Non-root (`telemetry` user)
- **Size**: ~10-20 MB per image
- **Architecture**: `linux/amd64` (default, configurable)
- **Security**: Includes CA certificates, runs as non-root

### Parameters

| Parameter | Description | Default | Valid With |
|-----------|-------------|---------|------------|
| `idrac_telemetry_version` | Git branch/tag of iDRAC-Telemetry-Reference-Tools | `main` | `telemetry`, `kafkapump`, `victoriapump`, `telemetry-receiver` |
| `kafkapump_tag` | Image tag for KafkaPump | `latest` | `kafkapump`, `telemetry` |
| `victoriapump_tag` | Image tag for VictoriaPump | `latest` | `victoriapump`, `telemetry` |
| `telemetry_receiver_tag` | Image tag for Telemetry Receiver | `latest` | `telemetry-receiver`, `telemetry` |

---

## Updating Python Packages

For this project, uv is used for container Python package management. To update Python packages and the uv.lock file the following can be done:
- **1. Install uv**: `pip install uv`.
- **2. Update pyproject.toml**: Navigate to the container folder and update the pyproject.toml. The pyproject.toml file should be updated before running `uv lock` to reflect any changes in dependencies.
- **3. Update the lock file**: From the same directory run `uv lock`.
