# Omnia Container Image Builder

Build Omnia core container images for deployment.

## Quick Start

Build the Omnia core container:

```bash
./build_images.sh core core_tag=2.1 omnia_branch=v2.1.0.0
```

That's it! The image will be available locally as `omnia_core:2.1`.

---

## Prerequisites

**Podman** must be installed.

Install Podman: [podman.io/getting-started/installation](https://podman.io/getting-started/installation)

*Note: Script supports Podman and Docker build tools (default: Podman)*

---

## Common Build Commands

### Build Core Container

```bash
# Build with specific Omnia tag (recommended)
./build_images.sh core omnia_branch=v2.1.0.0

# Build with release candidate (same core tag)
./build_images.sh core omnia_branch=v2.1.0.0-rc2

# Previous RC1 command (for reference)
# ./build_images.sh core core_tag=1.1 omnia_branch=v2.1.0.0-rc1
# Note: RC2 now also uses core_tag=2.1

# Build with specific Omnia branch and default tag
./build_images.sh core omnia_branch=main

# Build with default settings (uses main branch and core tag 2.1)
./build_images.sh core
```

---

## Parameters Reference

**Required for core:**
- `core_tag=<version>` - Container image tag (default: `2.1`)
  - **Rule:** Use first 2 digits of Omnia version (e.g., v2.1.0.0 → core_tag=2.1)
- `omnia_branch=<tag|branch>` - Omnia repo tag or branch name
  - **Tag example:** `v2.1.0.0` (recommended for production)
  - **Branch example:** `main`, `pub/q1_dev`, `staging`
  - **Default:** `main` (if not specified)
  
**Find available versions:**
- Omnia tags: https://github.com/dell/omnia/tags
- Omnia branches: https://github.com/dell/omnia/branches

**Optional:**
- `build_action=<load|push>` - Load locally (default: `load`)
- `build_tool=<podman|docker>` - Build tool (default: `podman`)

---

## Next Steps

After building, verify the image:

```bash
podman images | grep omnia_core
# Output: omnia_core  2.1  ...
```

Then download and run `omnia.sh` to deploy:

```bash
# For tagged releases
wget https://raw.githubusercontent.com/dell/omnia/refs/tags/v2.1.0.0/omnia.sh
chmod +x omnia.sh
./omnia.sh --install

# For branches (e.g., main, pub/q1_dev)
wget https://raw.githubusercontent.com/dell/omnia/refs/heads/main/omnia.sh
chmod +x omnia.sh
./omnia.sh --install
```

---

## Additional Containers

For advanced usage (auth, telemetry, build-stream), see:
- **[ADVANCED_USAGE.md](ADVANCED_USAGE.md)** - Build multiple containers and advanced options
- **[TELEMETRY_CONTAINERS.md](TELEMETRY_CONTAINERS.md)** - iDRAC telemetry containers

---

## Troubleshooting

**Issue:** Warning about default branch
```
⚠️ Warning: omnia_branch not specified, using default branch: main
```
**Solution:** Always specify `omnia_branch` for production builds.

**Issue:** Build fails
**Solution:** Ensure Podman/Docker is running and you have internet access to pull base images.

---

## Building LDMS Producer RPM Package

The `build_rpm.sh` script creates LDMS producer RPM packages for HPC monitoring. It clones the OVIS repository and builds RPM packages in a Rocky Linux 10 container. Supports both x86_64 and aarch64 architectures - run on the respective platform to build for that architecture.

### Prerequisites

Ensure EPEL and AppStream repositories are configured and the following packages are installed:

```bash
sudo dnf install -y python3-devel python3-Cython
```

### Syntax
```bash
./build_rpm.sh -v <LDMS_VERSION> -u <SLURM_REPO_URL> -n <SLURM_REPO_NAME>
# Or positional arguments:
./build_rpm.sh <SLURM_REPO_URL> <SLURM_REPO_NAME>
```

### Parameters
- `-v, --version <version>` - LDMS version to build (default: `4.5.1`)
- `-u, --url <url>` - SLURM repository URL for dependencies
- `-n, --name <name>` - SLURM repository name for RPM packaging
- `-h, --help` - Show help message

### Examples

**Build with default LDMS version (4.5.1):**
```bash
./build_rpm.sh
```

**Build with specific LDMS version:**
```bash
./build_rpm.sh -v 4.5.1
```

**Build with SLURM repository support:**
```bash
./build_rpm.sh -v 4.5.1 -u https://example.com/slurm-repo -n x86_64_slurm_custom
```

**Build with positional arguments:**
```bash
./build_rpm.sh https://example.com/slurm-repo x86_64_slurm_custom
```

### Build Process
1. Clones OVIS repository from GitHub (https://github.com/ovis-hpc/ovis.git)
2. Uses specified LDMS version tag (default: v4.5.1)
3. Sets `LDMS_REPO` environment variable
4. Builds RPM in `/root/ovis-code/ovis` directory
5. Runs `start_build_container.rockylinux10.bash` in container

### Notes
- SLURM repository parameters are optional but recommended for SLURM metrics
- Without SLURM repo, warning is shown but build continues
- Built RPMs are available in `/root/ovis-code/ovis` directory
- Requires Docker/Podman for container-based build
- Supports both x86_64 and aarch64 architectures
- Run this script on the respective platform to build for that architecture

---

## Updating Python Packages

For this project, uv is used for container Python package management. To update Python packages and the uv.lock file:

1. **Install uv**: `pip install uv`
2. **Update pyproject.toml**: Navigate to the container folder and update the pyproject.toml
3. **Update the lock file**: From the same directory run `uv lock`

---

## Support

For issues or questions, refer to the [Omnia documentation](https://omnia.readthedocs.io/en/latest/).

