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

## Script Usage

### 1. **Building Specific image**

You can specify which container image to build by passing a comma-separated list of container names as an argument.

#### Syntax:
```bash
./build_images.sh <container1,container2,...> [omnia_branch=<branch_name>] [build_tool=<podman_or_docker>] [build_action=<load_or_push>] [image_tag=<tag_version>] [core_tag=<tag>] [auth_tag=<tag>] [pcs_tag=<tag>] [ubuntu_ldms_tag=<tag>]
```

#### Example

To build only the core and auth container image:

```bash
./build_images.sh core,auth
```
* For core image, default omnia_branch is `staging`
* By default, build_tool is considered as podman
* By default, build_action is considered as load
* By default, all image tags are `latest`
* `image_tag=<tag>` sets all containers to the same tag
* Individual container tags: `core_tag`, `auth_tag`, `pcs_tag`, `ubuntu_ldms_tag`

To build with a specific image tag for all containers (e.g., version 1.0):

```bash
./build_images.sh core,auth image_tag=1.0
```

To build with different tags for different containers:

```bash
./build_images.sh core,auth core_tag=1.0 auth_tag=1.0
```

To build core with specific version and auth with default (latest):

```bash
./build_images.sh core,auth core_tag=1.0
```

To build ubuntu-ldms monitoring container:

```bash
./build_images.sh ubuntu-ldms
```

To build ubuntu-ldms with specific tag:

```bash
./build_images.sh ubuntu-ldms ubuntu_ldms_tag=1.0
```

### 2. **Building All images**

To build all available container's images, you can pass all as an argument.

Syntax:

```bash
./build_images.sh all
```

If we want to build all the images with docker tool then we can use like below:

```bash
./build_images.sh all build_tool=docker
```

If we want specific omnia branch/version keeping build_tool as default then we can use like below:

```bash
./build_images.sh all omnia_branch=v2.0.0.0-rc2
```

If we want specific omnia branch/version with docker tool then we can use like below:

```bash
./build_images.sh all omnia_branch=v2.0.0.0-rc2 build_tool=docker
```

To build all images with a specific tag (e.g., version 1.0):

```bash
./build_images.sh all image_tag=1.0
```

To build all images with custom tag and docker tool:

```bash
./build_images.sh all image_tag=1.0 build_tool=docker
```

To build all images with different individual tags:

```bash
./build_images.sh all core_tag=1.0 auth_tag=1.0 pcs_tag=1.0 ubuntu_ldms_tag=1.0
```

OR, without passing any argument - this will build all the container and will use `podman` as the default build_tool

```bash
./build_images.sh
```

### 3. **Pushing Images to Registry**

To build and push images to Docker registry (requires build_tool=docker):

```bash
./build_images.sh all build_tool=docker build_action=push image_tag=1.0
```
```bash
./build_images.sh core,auth build_tool=docker build_action=push core_tag=1.0 auth_tag=1.0
```

**Note**: 
- `build_action=push` requires `build_tool=docker`
- Default registry is `docker.io/dellhpcomniaaisolution`
- Registry can be customized by modifying `OMNIA_DOCKER_REGISTERY` variable in the script

To push specific containers:

# **Building LDMS PRODUCER RPM Package**

The `build_rpm.sh` script is designed to create LDMS producer RPM packages. It accepts two optional parameters: `SLURM_REPO_URL` and `SLURM_REPO_NAME`.

#### Syntax:
```bash
./build_rpm.sh -u [SLURM_REPO_URL] -n [SLURM_REPO_NAME] 
```

#### Example

- To build the RPM package without any optional parameters:

  ```bash
  ./build_rpm.sh
  ```

- To build the RPM package with both SLURM repository URL and name:

  ```bash
  ./build_rpm.sh -u https://example.com/slurm-repo -n x86_64_slurm_custom
  ```

- To build the RPM package with both SLURM repository URL and name:

  ```bash
  ./build_rpm.sh https://example.com/slurm-repo x86_64_slurm_custom
  ```

**Note**: If the `SLURM_REPO_URL` is provided, the script will use it to fetch the necessary dependencies. If `SLURM_REPO_NAME` is provided, it will be used to name the RPM package accordingly.

## Updating Python Packages

For this project, uv is used for container Python package management. To update Python packages and the uv.lock file the following can be done:
- **1. Install uv**: `pip install uv`.
- **2. Update pyproject.toml**: Navigate to the container folder and update the pyproject.toml. The pyproject.toml file should be updated before running `uv lock` to reflect any changes in dependencies.
- **3. Update the lock file**: From the same directory run `uv lock`.
