# Omnia 2.0 Image Build Script for all containers

This repository contains a script to build multiple containers images using `Podman`. The script allows you to build different images like `omnia_core`, `omnia_auth`, `omnia_provision`, `omnia_pcs`, and `omnia_kubespray`.

## Prerequisites

Before executing the script, ensure that you have the following installed:

- **Podman**: This script uses `podman` to build the container images. You can install Podman by following the [official installation guide](https://podman.io/getting-started/installation).
- **Bash**: The script is a Bash script, so it requires Bash to run. It should work on most Unix-based systems like Linux and macOS.

## `build_images.sh` Script Overview

The `build_images.sh` script builds the following containers:

- **omnia_core**: image for core Omnia container - `core`.
- **omnia_auth**: image for core Omnia container - `auth`.
- **omnia_provision**: image used for provisioning container - `provision`.
- **omnia_pcs**: image for PCS container - `pcs`.
- **omnia_kubespray**: image for Kubespray container - `kubespray`.

## Script Usage

### 1. **Building Specific image**

You can specify which container image to build by passing a comma-separated list of container names as an argument.

#### Syntax:
```bash
./build_images.sh <container1,container2,...> kubespray_version=v<version> omnia_branch=<branch_name>
```

#### Example

To build only the provision and pcs container image:

```bash
./build_images.sh core,auth,kubespray
```
* For kubespray image, defualt kubespray_version is `v2.28.0`
* For core image, default omnia_branch is `pub/ochami`

```bash
./build_images.sh core,kubespray kubespray_version=v2.26.0 omnia_branch=staging
```

### 2. **Building All images**
To build all available container's images, you can pass all as an argument.

Syntax:

```bash
./build_images.sh all
```
If we want specific kubespray_version image then we can use like below:

```bash
./build_images.sh all kubespray_version=v2.28.0
```

If we want specific omnia branch keeping kubespray as default then we can use like below:

```bash
./build_images.sh all omnia_branch=staging
```

If we want specific omnia branch and kubespray version both then we can use like below:

```bash
./build_images.sh all kubespray_version=v2.28.0 omnia_branch=pub/ochami
```


OR, without passing any argument - this will build all the container but kubespray version will be default - `v2.28.0`

```bash
./build_images.sh
```

**Note**: `kubespray_version` should be second argument for the script.
Follow below k8s to kubespray version map while choosing kubespray version:
Currently we support v2.26.0, v2.27.0, v2.28.0 versions of kubespray
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
