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

# Build with default settings (uses main branch if not specified)
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

## Building LDMS Producer RPM Package

The `build_rpm.sh` script creates LDMS producer RPM packages for monitoring.

### Syntax
```bash
./build_rpm.sh -v [LDMS_TAGGED_VERSION] -u [SLURM_REPO_URL] -n [SLURM_REPO_NAME]
```

### Examples

**Build RPM with default settings:**
```bash
./build_rpm.sh
```

**Build RPM with custom version and repository:**
```bash
./build_rpm.sh -v 4.5.1 -u https://example.com/slurm-repo -n x86_64_slurm_custom
```

### Notes
- If `SLURM_REPO_URL` is provided, the script uses it to fetch dependencies
- If `SLURM_REPO_NAME` is provided, it names the RPM package accordingly
- All parameters are optional

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

## Updating Python Packages

For this project, uv is used for container Python package management. To update Python packages and the uv.lock file:

1. **Install uv**: `pip install uv`
2. **Update pyproject.toml**: Navigate to the container folder and update the pyproject.toml
3. **Update the lock file**: From the same directory run `uv lock`

---

## Support

For issues or questions, refer to the [Omnia documentation](https://github.com/dell/omnia).

