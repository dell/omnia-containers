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

- **omnia_core**: image for core Omnia container - `core`.
- **omnia_auth**: image for auth Omnia container - `auth`.
- **omnia_pcs**: image for PCS container - `pcs`.
- **ubuntu_ldms**: image for LDMS (OVIS) monitoring container - `ubuntu-ldms`.

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
```

## Script Usage

### Available Parameters

**Container Options:** `all`, `core`, `pcs`, `auth`, `ubuntu-ldms`, `pipeline`

**Common Parameters (valid for all containers):**
- `build_tool=<podman|docker>` - Build tool to use (default: `podman`)
- `build_action=<load|push>` - Action after build (default: `load`)
- `image_tag=<tag>` - Set same tag for all containers (default: `latest`)

**Container-Specific Parameters:**
- `omnia_branch=<branch>` - Omnia branch/tag to use for core container (default: `staging`, valid with: `core`, `all`, `pipeline`)
  - ⚠️ **Warning:** If not specified when building core, a warning will be shown with the default branch name
- `core_tag=<tag>` - Individual tag for omnia_core (valid with: `core`, `all`, `pipeline`)
- `auth_tag=<tag>` - Individual tag for omnia_auth (valid with: `auth`, `all`, `pipeline`)
- `pcs_tag=<tag>` - Individual tag for omnia_pcs (valid with: `pcs`, `all`)
- `ubuntu_ldms_tag=<tag>` - Individual tag for ubuntu-ldms (valid with: `ubuntu-ldms`, `all`, `pipeline`)

**Special Options:**
- `all` - Builds: core and auth containers only
- `pipeline` - Builds: core, auth, and ubuntu-ldms containers

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

## Updating Python Packages

For this project, uv is used for container Python package management. To update Python packages and the uv.lock file the following can be done:
- **1. Install uv**: `pip install uv`.
- **2. Update pyproject.toml**: Navigate to the container folder and update the pyproject.toml. The pyproject.toml file should be updated before running `uv lock` to reflect any changes in dependencies.
- **3. Update the lock file**: From the same directory run `uv lock`.
