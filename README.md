# Omnia 2.0 Image Build Script for all containers

This repository contains a script to build multiple containers images using either `Podman` or `Docker`. The script allows you to build different images like `omnia_core`, `omnia_auth`, `omnia_provision`, `omnia_pcs`, and `omnia_kubespray`.

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
- **omnia_auth**: image for core Omnia container - `auth`.
- **omnia_provision**: image used for provisioning container - `provision`.
- **omnia_pcs**: image for PCS container - `pcs`.
- **omnia_kubespray**: image for Kubespray container - `kubespray`.
- **ubuntu_ldms**: image for LDMS (OVIS) monitoring container - `ubuntu-ldms`.

## Script Usage

### 1. **Building Specific image**

You can specify which container image to build by passing a comma-separated list of container names as an argument.

#### Syntax:
```bash
./build_images.sh <container1,container2,...> [kubespray_version=v<version>] [omnia_branch=<branch_name>] [build_tool=<podman_or_docker>] [image_tag=<tag_version>] [core_tag=<tag>] [auth_tag=<tag>] [provision_tag=<tag>] [pcs_tag=<tag>] [kubespray_tag=<tag>] [ubuntu_ldms_tag=<tag>]
```

#### Example

To build only the core and auth container image:

```bash
./build_images.sh core,auth
```
* For core image, default omnia_branch is `pub/ochami`
* By default, build_tool is considered as podman
* By default, all image tags are `latest`
* `image_tag=<tag>` sets all containers to the same tag
* Individual container tags: `core_tag`, `auth_tag`, `provision_tag`, `pcs_tag`, `kubespray_tag`, `ubuntu_ldms_tag`

```bash
./build_images.sh core,kubespray kubespray_version=v2.28.0 omnia_branch=v2.0.0.0-rc2
```

To build with a specific image tag for all containers (e.g., version 1.0):

```bash
./build_images.sh core,auth image_tag=1.0
```

To build with different tags for different containers:

```bash
./build_images.sh core,auth core_tag=1.0 auth_tag=2.0
```

To build core with version 1.0 and auth with latest:

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
./build_images.sh all core_tag=1.0 auth_tag=1.1 provision_tag=2.0 pcs_tag=1.5 kubespray_tag=3.0 ubuntu_ldms_tag=2.1
```

OR, without passing any argument - this will build all the container and will use `podman` as the default build_tool

```bash
./build_images.sh
```

### 3. **Building Kubespray image**

If we want specific omnia branch and kubespray version both built with docker then we can use like below:

```bash
./build_images.sh all kubespray_version=v2.28.0 omnia_branch=pub/ochami build_tool=docker
```

To build all images with custom tag, specific versions and docker:

```bash
./build_images.sh all kubespray_version=v2.28.0 omnia_branch=pub/ochami build_tool=docker image_tag=1.0
```

To build all images with mixed individual tags and global settings:

```bash
./build_images.sh all kubespray_version=v2.28.0 omnia_branch=pub/ochami build_tool=docker core_tag=1.0 auth_tag=1.2
```

**Note**: 
- `kubespray_version` should be second argument for the script.
- For kubespray image, default kubespray_version is `v2.28.0`
- Kubespray images use a combined tag format: `<kubespray_tag>-<kubespray_version>` (e.g., `1.0-v2.28.0` or `latest-v2.28.0`)
- Follow below k8s to kubespray version map while choosing kubespray version:
- Currently we support v2.26.0, v2.27.0, v2.28.0 versions of kubespray
```yml
k8s_to_kubespray:
  "1.29.5": "v2.27.0"
  "1.31.4": "v2.28.0"
```



## Updating Python Packages

For this project, uv is used for container Python package management. To update Python packages and the uv.lock file the following can be done:
- **1. Install uv**: `pip install uv`.
- **2. Update pyproject.toml**: Navigate to the container folder and update the pyproject.toml. The pyproject.toml file should be updated before running `uv lock` to reflect any changes in dependencies.
- **3. Update the lock file**: From the same directory run `uv lock`.
