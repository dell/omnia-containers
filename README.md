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
# Build all containers (default: podman, latest tags)
./build_images.sh all

# Build all with Docker and specific tag
./build_images.sh all build_tool=docker image_tag=1.0

# Build and push all to registry
./build_images.sh all build_tool=docker build_action=push image_tag=1.0

# Build specific containers
./build_images.sh core,auth image_tag=1.0

# Build pipeline (core + auth + ubuntu-ldms)
./build_images.sh pipeline image_tag=1.0

# Build with specific Omnia branch
./build_images.sh all omnia_branch=v2.0.0.0-rc2 image_tag=2.0
```

## Script Usage

### Available Parameters

**Container Options:** `all`, `core`, `pcs`, `auth`, `ubuntu-ldms`, `pipeline`

**Optional Parameters:**
- `omnia_branch=<branch>` - Omnia branch/tag to use (default: `staging`)
- `build_tool=<podman|docker>` - Build tool to use (default: `podman`)
- `build_action=<load|push>` - Action after build (default: `load`)
- `image_tag=<tag>` - Set same tag for all containers (default: `latest`)
- `core_tag=<tag>` - Individual tag for omnia_core (default: `latest`)
- `auth_tag=<tag>` - Individual tag for omnia_auth (default: `latest`)
- `pcs_tag=<tag>` - Individual tag for omnia_pcs (default: `latest`)
- `ubuntu_ldms_tag=<tag>` - Individual tag for ubuntu-ldms (default: `latest`)

**Special Options:**
- `all` - Builds: core and auth containers only
- `pipeline` - Builds: core, auth, and ubuntu-ldms containers

---

### 1. Building ALL Images

Build core and auth containers (the primary Omnia containers).

#### Basic - Default Settings
```bash
# Build all with defaults (podman, latest tags)
./build_images.sh all
```

**Note:** Running `./build_images.sh` without parameters also defaults to building core and auth containers.

#### With Docker
```bash
# Build all images with Docker
./build_images.sh all build_tool=docker
```

#### With Omnia Branch/Version
```bash
# Build all with specific Omnia branch (default tool: podman)
./build_images.sh all omnia_branch=v2.0.0.0-rc2

# Build all with specific branch and Docker
./build_images.sh all omnia_branch=v2.0.0.0-rc2 build_tool=docker

# Build all with staging branch (default)
./build_images.sh all omnia_branch=staging
```

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
# Build only core
./build_images.sh core

# Build only core with specific tag
./build_images.sh core core_tag=1.0

# Build only core with Docker
./build_images.sh core build_tool=docker core_tag=1.0

# Build only auth
./build_images.sh auth

# Build only auth with specific tag
./build_images.sh auth auth_tag=1.0

# Build only pcs
./build_images.sh pcs

# Build only pcs with specific tag
./build_images.sh pcs pcs_tag=1.0

# Build only ubuntu-ldms
./build_images.sh ubuntu-ldms

# Build only ubuntu-ldms with specific tag
./build_images.sh ubuntu-ldms ubuntu_ldms_tag=1.0
```

#### Multiple Specific Containers
```bash
# Build core and auth only
./build_images.sh core,auth

# Build core and auth with same tag
./build_images.sh core,auth image_tag=1.0

# Build core and auth with different tags
./build_images.sh core,auth core_tag=1.0 auth_tag=1.1

# Build core and auth with Docker
./build_images.sh core,auth build_tool=docker core_tag=1.0 auth_tag=1.0

# Build auth and ubuntu-ldms
./build_images.sh auth,ubuntu-ldms auth_tag=1.0 ubuntu_ldms_tag=1.0

# Build core, auth, and ubuntu-ldms
./build_images.sh core,auth,ubuntu-ldms image_tag=1.0
```

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
# Build and push all images (core and auth) with unified tag
./build_images.sh all build_tool=docker build_action=push image_tag=1.0

# Build and push all with individual tags
./build_images.sh all build_tool=docker build_action=push core_tag=1.0 auth_tag=1.1

# Build and push all with specific branch
./build_images.sh all omnia_branch=v2.0.0.0-rc2 build_tool=docker build_action=push image_tag=2.0
```

#### Push Specific Images
```bash
# Build and push only core and auth
./build_images.sh core,auth build_tool=docker build_action=push core_tag=1.0 auth_tag=1.0

# Build and push only ubuntu-ldms
./build_images.sh ubuntu-ldms build_tool=docker build_action=push ubuntu_ldms_tag=1.0

# Build and push pipeline containers
./build_images.sh pipeline build_tool=docker build_action=push image_tag=1.0

# Build and push pcs only
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
