# Advanced Container Build Usage

This document covers building multiple Omnia containers and advanced configuration options.

## Build Multiple Containers

### OIM Deployment (Core + Auth + Build Stream + Image Builder)

```bash
# Build all OIM containers (recommended for production)
./build_images.sh oim omnia_branch=v2.2.0.0

# Build with Docker
./build_images.sh oim omnia_branch=v2.2.0.0 build_tool=docker

# Build with custom tags
./build_images.sh oim omnia_branch=v2.2.0.0 core_tag=2.2 auth_tag=1.0
```

### Build ALL Containers

```bash
# Build everything (core, auth, ubuntu-ldms, build-stream, telemetry, image-builder)
./build_images.sh all omnia_branch=v2.2.0.0

# Build all with custom tags
./build_images.sh all omnia_branch=v2.2.0.0 core_tag=2.2 auth_tag=1.1 ubuntu_ldms_tag=1.0
```

### Build Specific Combinations

```bash
# Build core and auth
./build_images.sh core,auth omnia_branch=v2.2.0.0 core_tag=2.2 auth_tag=1.0

# Build core and build-stream
./build_images.sh core,build-stream omnia_branch=v2.2.0.0 core_tag=2.2
```

---

## Individual Container Builds

### Auth Container

```bash
# Build auth with default tag
./build_images.sh auth

# Build auth with custom tag
./build_images.sh auth auth_tag=1.0
```

### Build Stream Container

```bash
# Build build-stream with default tag
./build_images.sh build-stream

# Build with custom tag
./build_images.sh build-stream build_stream_tag=1.0
```

### Ubuntu LDMS Container

```bash
# Build ubuntu-ldms
./build_images.sh ubuntu-ldms

# Build with custom tag
./build_images.sh ubuntu-ldms ubuntu_ldms_tag=1.0
```

### Image Builder Container

```bash
# Build image-builder
./build_images.sh image-builder

# Build with custom tag
./build_images.sh image-builder image_builder_tag=1.0
```

---

## Advanced Parameters

### All Available Parameters

**Common (valid for all containers):**
- `build_tool=<podman|docker>` - Build tool (default: `podman`)
- `build_action=<load|push>` - Load locally or push to registry (default: `load`)

**Container-specific tags:**
- `core_tag=<tag>` - omnia_core tag (default: `2.2`)
- `auth_tag=<tag>` - omnia_auth tag (default: `1.0`)
- `build_stream_tag=<tag>` - omnia_build_stream tag (default: `1.0`)
- `ubuntu_ldms_tag=<tag>` - ubuntu-ldms tag (default: `1.0`)
- `image_builder_tag=<tag>` - image-builder tag (default: `1.0`)
- `omnia_branch=<branch>` - Only valid with core container

### Push to Registry

```bash
# Build and push core to registry (requires Docker)
./build_images.sh core core_tag=2.2 omnia_branch=v2.2.0.0 build_tool=docker build_action=push

# Note: Requires OMNIA_DOCKER_REGISTERY variable in script
```

---

## Parameter Validation

The script validates parameters and shows context-specific errors:

```bash
# Invalid parameter
./build_images.sh core invalid_param=value
# Error: Invalid parameter(s): invalid_param
# Valid parameters for 'core': build_tool build_action core_tag omnia_branch

# Wrong container-specific parameter
./build_images.sh core auth_tag=1.0
# Error: Parameter 'auth_tag' is not valid for container 'core'
```

---

## Container Details

### Available Containers

| Container | Short Name | Default Tag | Description |
|-----------|------------|-------------|-------------|
| omnia_core | core | 2.2 | Core Omnia container |
| omnia_auth | auth | 1.0 | Auth service container |
| omnia_build_stream | build-stream | 1.0 | FastAPI build automation |
| ubuntu-ldms | ubuntu-ldms | 1.0 | LDMS (OVIS) monitoring |
| image-builder | image-builder | 1.0 | OpenCHAMI image builder |

### Special Build Groups

- **oim** - Builds: core, auth, build-stream, image-builder (required for Omnia deployment)
- **all** - Builds: all available containers
- **telemetry** - Builds: kafkapump, victoriapump, telemetry-receiver (see TELEMETRY_CONTAINERS.md)

---

## Docker vs Podman

**Podman (default):**
- No daemon required
- Rootless by default
- Compatible with most Docker commands

**Docker:**
- Requires daemon running
- Needed for `build_action=push`
- Requires buildx for multi-platform builds

### Docker Setup

```bash
sudo systemctl start docker
sudo systemctl enable docker
docker buildx create --name mybuilder --driver docker-container --use
docker buildx inspect --bootstrap
```

---

## Troubleshooting

**Multiple containers fail:**
Check internet connectivity and ensure base images can be pulled.

**Permission errors with Podman:**
Run as non-root user or configure subuid/subgid mappings.

**Docker push fails:**
Verify registry credentials and `OMNIA_DOCKER_REGISTERY` variable in script.

---

## Back to Main Documentation

- [Main README](README.md) - Quick start for core container
- [TELEMETRY_CONTAINERS.md](TELEMETRY_CONTAINERS.md) - iDRAC telemetry containers
