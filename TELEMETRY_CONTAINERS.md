# iDRAC Telemetry Containers

Build containers for iDRAC telemetry data collection and streaming.

## Overview

The telemetry containers integrate with Dell iDRAC to collect hardware metrics and stream them to Kafka or VictoriaMetrics.

**Source:** iDRAC-Telemetry-Reference-Tools repository (commit `e86fecb`)

---

## Quick Start

### Build All Telemetry Containers

```bash
./build_images.sh telemetry
```

This builds:
- **kafkapump** - Streams to Kafka
- **victoriapump** - Streams to VictoriaMetrics  
- **telemetry-receiver** - Collects from iDRAC

---

## Individual Container Builds

### KafkaPump

Publishes iDRAC telemetry data to Apache Kafka topics.

```bash
# Build with default tag
./build_images.sh kafkapump

# Build with custom tag
./build_images.sh kafkapump kafkapump_tag=1.0
```

### VictoriaPump

Publishes iDRAC telemetry data to VictoriaMetrics.

```bash
# Build with default tag
./build_images.sh victoriapump

# Build with custom tag
./build_images.sh victoriapump victoriapump_tag=1.0
```

### Telemetry Receiver

Complete telemetry collection service with:
- `idrac-telemetry-receiver` - Main receiver
- `dbdiscauth` - Database discovery/auth
- `configui` - Configuration UI
- `redfishread` - Redfish API reader

```bash
# Build with default tag
./build_images.sh telemetry-receiver

# Build with custom tag
./build_images.sh telemetry-receiver telemetry_receiver_tag=1.0
```

---

## Build with Custom Tags

```bash
# Build all with individual tags
./build_images.sh telemetry \
  kafkapump_tag=kafka-v1.0 \
  victoriapump_tag=victoria-v1.0 \
  telemetry_receiver_tag=receiver-v1.0

# Build multiple containers with specific tags
./build_images.sh kafkapump,victoriapump kafkapump_tag=1.0 victoriapump_tag=1.0
```

---

## Build with Docker

```bash
# Build all telemetry containers with Docker
./build_images.sh telemetry build_tool=docker

# Build specific container with Docker
./build_images.sh kafkapump build_tool=docker kafkapump_tag=1.0
```

---

## Container Details

### Build Process

1. Clones iDRAC-Telemetry-Reference-Tools repository at commit `e86fecb`
2. Uses Dockerfiles from the cloned repository
3. Builds static binaries from source code
4. Creates minimal scratch-based images

### Dockerfile Sources

- **KafkaPump**: `docker-compose-files/Dockerfile` with `CMD=kafkapump`
- **VictoriaPump**: `docker-compose-files/Dockerfile` with `CMD=victoriapump`
- **Telemetry Receiver**: `docker-compose-files/Dockerfile.telemetry_receiver`

### Change Telemetry Version

To use a different commit/branch/tag:

1. Edit `build_images.sh`
2. Modify `IDRAC_TELEMETRY_COMMIT` variable
3. Delete `.idrac-telemetry-tools` directory
4. Run build again

---

## Verify Built Images

```bash
# List telemetry images
podman images | grep -E "kafkapump|victoriapump|telemetry"

# Expected output:
# kafkapump           1.0  ...
# victoriapump        1.0  ...
# idrac_telemetry_receiver  1.0  ...
```

---

## Available Parameters

**Telemetry-specific tags:**
- `kafkapump_tag=<tag>` - KafkaPump container tag (default: `1.0`)
- `victoriapump_tag=<tag>` - VictoriaPump container tag (default: `1.0`)
- `telemetry_receiver_tag=<tag>` - Telemetry Receiver container tag (default: `1.0`)

**Common parameters:**
- `build_tool=<podman|docker>` - Build tool (default: `podman`)
- `build_action=<load|push>` - Load locally or push to registry (default: `load`)

---

## Troubleshooting

**Issue:** Clone fails
```
Failed to clone iDRAC-Telemetry-Reference-Tools
```
**Solution:** Check internet connectivity and GitHub access.

**Issue:** Build fails at specific commit
**Solution:** Verify commit `e86fecb` exists in the repository or update `IDRAC_TELEMETRY_COMMIT`.

**Issue:** Static binary compilation errors
**Solution:** Ensure sufficient disk space and memory for Go compilation.

---

## Integration

These containers are typically deployed on nodes where iDRAC telemetry needs to be collected. See Omnia documentation for:
- Telemetry configuration
- Kafka/VictoriaMetrics setup
- iDRAC integration steps

---

## Back to Main Documentation

- [Main README](README.md) - Quick start for core container
- [ADVANCED_USAGE.md](ADVANCED_USAGE.md) - Build multiple containers and advanced options
