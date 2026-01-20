# Omnia 2.0 Image Build Script for all containers

This repository contains a script to build multiple containers images using either `Podman` or `Docker`. The script allows you to build different images like `omnia_core`, `omnia_auth`, `omnia_build_stream`and `ubuntu_ldms`.

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
- **omnia_build_stream**: FastAPI service for Omnia Build Stream automation - `build-stream`.
- **ubuntu_ldms**: image for LDMS (OVIS) monitoring container - `ubuntu-ldms`.
- **kafkapump**: Kafka data pump for iDRAC telemetry - `kafkapump`.
- **victoriapump**: VictoriaMetrics data pump for iDRAC telemetry - `victoriapump`.
- **telemetry-receiver**: Complete telemetry collection service - `telemetry-receiver`.
- **image-builder**: OpenCHAMI image builder for creating custom OS images - `image-builder`.

## Quick Reference - Common Commands

```bash
# Build OIM containers (core + auth) - default behavior
./build_images.sh
# ⚠️ Warning will be shown about using default branch: main

# Build OIM with specific Omnia branch
./build_images.sh oim omnia_branch=v2.0.0.0

# Build ALL containers (everything)
./build_images.sh all omnia_branch=v2.0.0.0

# Build OIM with Docker and specific tag
./build_images.sh oim build_tool=docker image_tag=1.0 omnia_branch=staging

# Build specific containers (core + auth)
./build_images.sh core,auth image_tag=1.0 omnia_branch=v2.0.0.

# Build only core with specific branch
./build_images.sh core omnia_branch=v2.0.0.0 core_tag=2.0

# Build all telemetry containers
./build_images.sh telemetry

# Build specific telemetry container
./build_images.sh kafkapump image_tag=1.0

# Build omnia_build_stream container
./build_images.sh build-stream
```

## Script Usage

### Available Parameters

**Container Options:** `oim`, `all`, `core`, `auth`, `build-stream`, `ubuntu-ldms`, `telemetry`, `kafkapump`, `victoriapump`, `telemetry-receiver`, `image-builder`

**Common Parameters (valid for all containers):**
- `build_tool=<podman|docker>` - Build tool to use (default: `podman`)
- `build_action=<load|push>` - Action after build (default: `load` - loads images locally for use)
- `image_tag=<tag>` - Set same tag for all containers (default: `1.0`)

**Note:** By default, `build_action=load` loads all built images into your local container engine (Podman or Docker) making them immediately available for use. This is the recommended action for users.

**Omnia Container-Specific Parameters:**
- `omnia_branch=<branch>` - Omnia branch/tag to use for core container (default: `main`, valid with: `core`, `oim`, `all`)
  - ⚠️ **Warning:** If not specified when building core, a warning will be shown with the default branch name
- `core_tag=<tag>` - Individual tag for omnia_core (valid with: `core`, `oim`, `all`)
- `auth_tag=<tag>` - Individual tag for omnia_auth (valid with: `auth`, `oim`, `all`)
- `build_stream_tag=<tag>` - Individual tag for omnia_build_stream (valid with: `build-stream`, `oim`, `all`)
- `ubuntu_ldms_tag=<tag>` - Individual tag for ubuntu-ldms (valid with: `ubuntu-ldms`, `all`)

**iDRAC Telemetry Container-Specific Parameters:**
- `kafkapump_tag=<tag>` - Individual tag for kafkapump (valid with: `kafkapump`, `telemetry`, `all`)
- `victoriapump_tag=<tag>` - Individual tag for victoriapump (valid with: `victoriapump`, `telemetry`, `all`)
- `telemetry_receiver_tag=<tag>` - Individual tag for telemetry-receiver (valid with: `telemetry-receiver`, `telemetry`, `all`)

**Image Builder Container-Specific Parameters:**
- `image_builder_tag=<tag>` - Individual tag for image-builder (valid with: `image-builder`, `oim`, `all`)

**Note**: 
- Telemetry containers are built from iDRAC-Telemetry-Reference-Tools at commit `e86fecb`. To change the version, modify `IDRAC_TELEMETRY_COMMIT` in `build_images.sh`.

**Special Options:**
- `oim` - Builds: core, auth, build_stream and image-builder containers (required for Omnia deployment) - **This is the default**
- `all` - Builds: all available containers (core, auth, ubuntu-ldms, build_stream, kafkapump, victoriapump, telemetry-receiver, image-builder)
- `telemetry` - Builds: kafkapump, victoriapump, and telemetry-receiver containers


**Parameter Validation:**
The script validates parameters in two stages with context-specific error messages:

1. **Invalid parameter names** - Shows only valid parameters for the specific container(s) being built
   ```bash
   # Example: Building core with invalid parameter
   ./build_images.sh core sas=1
   # Error: Invalid parameter(s): sas
   # Valid parameters for 'core': build_tool image_tag core_tag omnia_branch
   ```

2. **Wrong container-specific parameters** - Validates tag parameters match the container type
   ```bash
   # Example: Using auth_tag when building only core
   ./build_images.sh core auth_tag=1.0
   # Error: Parameter 'auth_tag' is not valid for container 'core'
   # Valid parameters for 'core': build_tool image_tag core_tag omnia_branch
   ```

3. **Default branch warning** - When building core without specifying `omnia_branch`
   ```bash
   ./build_images.sh core
   # ⚠️ Warning: omnia_branch not specified, using default branch: main
   ```

---

### 1. Building OIM Containers (Core + Auth)

Build core, auth and build_stream containers required for Omnia deployment. This is the default and most common option.

#### Basic - Default Settings
```bash
# Build OIM containers with defaults (podman, 1.0 tags, main branch) - no parameters needed
./build_images.sh
# ⚠️ Warning: omnia_branch not specified, using default branch: main

# OR explicitly specify 'oim'
./build_images.sh oim
# ⚠️ Warning: omnia_branch not specified, using default branch: main

# Build OIM with explicit branch (no warning)
./build_images.sh oim omnia_branch=staging
```

These commands build core and auth containers with default settings (podman, 1.0 tags, main branch).

#### With Docker
```bash
# Build OIM containers with Docker
./build_images.sh oim build_tool=docker
```

#### With Omnia Branch/Version
```bash
# Build OIM with specific Omnia branch (default tool: podman) - no warning
./build_images.sh oim omnia_branch=v2.0.0.0

# Build OIM with specific branch and Docker - no warning
./build_images.sh oim omnia_branch=v2.0.0.0 build_tool=docker

# Build OIM with explicit main branch (same as default but no warning)
./build_images.sh oim omnia_branch=main
```

**Note:** Explicitly specifying `omnia_branch=main` suppresses the warning even though main is the default.

#### With Unified Tag
```bash
# Build OIM with same tag "1.0"
./build_images.sh oim image_tag=1.0

# Build OIM with tag "1.0" using Docker
./build_images.sh oim image_tag=1.0 build_tool=docker

# Build OIM with tag "2.0" and specific branch
./build_images.sh oim omnia_branch=v2.0.0.0 image_tag=2.0
```

#### With Individual Tags per Container
```bash
# Build OIM (core and auth) with different tags
./build_images.sh oim core_tag=1.0 auth_tag=1.1

# Build OIM with individual tags using Docker
./build_images.sh oim build_tool=docker core_tag=1.0 auth_tag=1.1
```

---

### 2. Building ALL Containers

Build all available containers including Omnia containers and telemetry components.

```bash
# Build all containers with defaults
./build_images.sh all

# Build all with specific branch
./build_images.sh all omnia_branch=v2.0.0.0

# Build all with unified tag
./build_images.sh all image_tag=1.0

# Build all with Docker
./build_images.sh all build_tool=docker image_tag=1.0

# Build all with individual tags
./build_images.sh all core_tag=1.0 auth_tag=1.1 ubuntu_ldms_tag=1.2
```

---

### 3. Building Specific Images

Build individual containers or specific combinations.

#### Single Container Builds
```bash
# Build only core (will show warning about default branch)
./build_images.sh core

# Build only core with specific branch
./build_images.sh core omnia_branch=v2.0.0.0

# Build only core with specific tag and branch
./build_images.sh core core_tag=1.0 omnia_branch=main

# Build only core with Docker
./build_images.sh core build_tool=docker core_tag=1.0

# Build only auth (omnia_branch not valid here)
./build_images.sh auth

# Build only auth with specific tag
./build_images.sh auth auth_tag=1.0

# Build only ubuntu-ldms (omnia_branch not valid here)
./build_images.sh ubuntu-ldms

# Build only ubuntu-ldms with specific tag
./build_images.sh ubuntu-ldms ubuntu_ldms_tag=1.0

# Build only build-stream
./build_images.sh build-stream

# Build only build-stream with specific tag
./build_images.sh build-stream build_stream_tag=1.0
```

**Note:** `omnia_branch` is only valid when building containers that include `core` (i.e., `core`, `oim`, `all`, or any combination including core).

#### Multiple Specific Containers
```bash
# Build core and auth only (will show warning about default branch)
./build_images.sh core,auth

# Build core and auth with specific branch
./build_images.sh core,auth omnia_branch=v2.0.0.0

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

# Build core and build-stream (only core supports omnia_branch)
./build_images.sh core,build-stream omnia_branch=v2.0.0.0
```

**Note:** When building multiple containers, only the tag parameters for those specific containers are valid. For example, using `ubuntu_ldms_tag` when building `core,auth,build_stream` will result in an error.

---

### 4. Understanding Image Loading (Default Behavior)

By default, the script uses `build_action=load` which builds and loads images into your local container engine.

#### What Happens with Load (Default)
```bash
# These commands automatically load images locally
./build_images.sh oim omnia_branch=v2.0.0.0
./build_images.sh core,auth image_tag=1.0
./build_images.sh all
```

**After building, images are immediately available:**

```bash
# For Podman (default)
podman images | grep omnia
# Output shows: omnia_core:latest, omnia_auth:latest, etc.

# For Docker
docker images | grep omnia
# Output shows: omnia_core:latest, omnia_auth:latest, etc.
```

#### Explicitly Specify Load Action
While `load` is the default, you can explicitly specify it:

```bash
# Explicitly use load action (same as default)
./build_images.sh oim build_action=load image_tag=1.0

# Load with Docker instead of Podman
./build_images.sh oim build_tool=docker build_action=load image_tag=1.0
```

---

# **Building Omnia Build Stream Container**

The build script supports building the `omnia_build_stream` container, which provides a FastAPI service for Omnia Build Stream automation. This container is built using Fedora 42 as the base image and includes Python 3.12 with FastAPI and Uvicorn.

## Component

### **Omnia Build Stream** (`build-stream`)
FastAPI service container for Omnia Build Stream automation. Features:
- Fedora 42 base with Python 3.12
- FastAPI ready (currently disabled, placeholder for future)
- Exposed on port 443 (HTTPS)

## Usage Examples

### Build Omnia Build Stream Container

```bash
# Build build-stream with default settings
./build_images.sh build-stream

# Build with specific tag
./build_images.sh build-stream build_stream_tag=v1.0

# Build with Docker
./build_images.sh build-stream build_tool=docker

```
---

# **Building iDRAC Telemetry Containers**

The build script now supports building containers for iDRAC Telemetry Reference Tools components. The script automatically clones the [iDRAC-Telemetry-Reference-Tools repository](https://github.com/dell/iDRAC-Telemetry-Reference-Tools) at commit `e86fecb` and uses its Dockerfiles to build the images.

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
./build_images.sh telemetry image_tag=v1.0
```

### Build Individual Telemetry Containers

```bash
# Build only KafkaPump
./build_images.sh kafkapump

# Build only VictoriaPump with specific tag
./build_images.sh victoriapump victoriapump_tag=v1.0

# Build only Telemetry Receiver
./build_images.sh telemetry-receiver telemetry_receiver_tag=latest
```

### Build with Individual Tags

```bash
# Build all telemetry containers with different tags
./build_images.sh telemetry \
  kafkapump_tag=kafka-v1.0 \
  victoriapump_tag=victoria-v1.0 \
  telemetry_receiver_tag=receiver-v1.0

# Build multiple with specific tags
./build_images.sh kafkapump,victoriapump image_tag=1.0
```

## Container Details

### Dockerfile Source

Dockerfiles are sourced from the iDRAC-Telemetry-Reference-Tools repository:
- **KafkaPump**: Uses `docker-compose-files/Dockerfile` with `CMD=kafkapump`
- **VictoriaPump**: Uses `docker-compose-files/Dockerfile` with `CMD=victoriapump`
- **Telemetry Receiver**: Uses `docker-compose-files/Dockerfile.telemetry_receiver`

### Build Process

1. Clones iDRAC-Telemetry-Reference-Tools repository at commit `e86fecb` (if not already cloned)
2. Uses Dockerfiles from the cloned repository
3. Builds static binaries from source code
4. Creates minimal scratch-based images

**Note**: To use a different commit/branch/tag, modify the `IDRAC_TELEMETRY_COMMIT` variable in `build_images.sh`.

---

# **Building OpenCHAMI Image Builder Container**

The build script supports building the OpenCHAMI image-builder container for creating custom OS images using a custom Dockerfile optimized for AlmaLinux 10.0.

## Component

### **Image Builder** (`image-builder`)
Container for building custom OS images using buildah in a rootless environment. Features:
- AlmaLinux 10.0 base with Python 3.12
- Buildah for container-based image building
- Rootless operation with proper user namespace configuration

## Usage Examples

### Build Image Builder Container

```bash
# Build image-builder with default settings
./build_images.sh image-builder

# Build with specific tag
./build_images.sh image-builder image_builder_tag=v2.0

# Build with Docker
./build_images.sh image-builder build_tool=docker image_builder_tag=latest

# Build all containers including image-builder
./build_images.sh all

# Build with specific tag for image-builder
./build_images.sh all image_builder_tag=v2.0
```

**Note**: To use a different commit/branch/tag, modify the `IMAGE_BUILDER_COMMIT` variable in `build_images.sh`.

---

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

## Updating Python Packages

For this project, uv is used for container Python package management. To update Python packages and the uv.lock file the following can be done:
- **1. Install uv**: `pip install uv`.
- **2. Update pyproject.toml**: Navigate to the container folder and update the pyproject.toml. The pyproject.toml file should be updated before running `uv lock` to reflect any changes in dependencies.
- **3. Update the lock file**: From the same directory run `uv lock`.
