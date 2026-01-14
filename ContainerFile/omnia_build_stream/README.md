# Omnia Build Stream Container

## Overview
The `omnia_build_stream` container provides a FastAPI service for Omnia Build Stream automation. This container hosts REST API endpoints for catalog parsing, input file generation, and image building operations.

**Deployment Model**: This container is deployed **after** `omnia_core` using `prepare_oim`. It accesses the Omnia repository code through shared volume mounts from `omnia_core`.

## Container Details

- **Container Name**: `omnia_build_stream`
- **Base Image**: Fedora 40
- **Default Tag**: `1.0`
- **Port**: 80 (HTTP)
- **Health Check**: `/health` endpoint
- **Working Directory**: `/omnia/automation-suite/poc/milestone-1` (accessed via volume mount)

## Features

- FastAPI-based REST API service
- Accesses Omnia code via shared volume from `omnia_core` container
- Python 3 with security patches (pip 25.3)
- Built-in health check endpoint
- Support for catalog parsing and input file generation

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OIM Host (RHEL 10)                       │
│                                                             │
│  Shared Path: ${omnia_path}/omnia (e.g., /opt/share/omnia) │
│                          │                                  │
│  ┌───────────────────────┼──────────────────────────────┐  │
│  │  omnia_core           │                              │  │
│  │  - Clones to /omnia inside container                 │  │
│  │  - Volume: ${omnia_path}/omnia → /opt/omnia          │  │
│  │  - WORKDIR: /omnia                                   │  │
│  │  - Port: 2222 (SSH)                                  │  │
│  └───────────────────────┼──────────────────────────────┘  │
│                          │                                  │
│                          │ Shared via host filesystem       │
│                          ↓                                  │
│  ┌───────────────────────┼──────────────────────────────┐  │
│  │  omnia_build_stream   │                              │  │
│  │  - Volume: ${omnia_path}/omnia → /opt/omnia          │  │
│  │  - WORKDIR: /omnia/automation-suite/poc/milestone-1  │  │
│  │  - Runs FastAPI from /omnia (mounted code)           │  │
│  │  - Port: 80 (HTTP)                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          │ Exposed via host network         │
└──────────────────────────┼──────────────────────────────────┘
                           │
                    External Access
               http://<OIM_IP>:80/health
```

## Building the Container

### Using build_images.sh Script

```bash
# Navigate to omnia-artifactory directory
cd omnia-artifactory_priti

# Build with default settings (Podman, tag 1.0)
./build_images.sh build-stream

# Build with specific Omnia branch
./build_images.sh build-stream omnia_branch=staging

# Build with custom tag
./build_images.sh build-stream build_stream_tag=2.0

# Build with Docker and push to registry
./build_images.sh build-stream build_tool=docker build_action=push

# Build with all custom parameters
./build_images.sh build-stream \
  omnia_branch=main \
  build_stream_tag=1.0 \
  build_tool=podman
```

### Manual Build

```bash
cd ContainerFile/omnia_build_stream

# Build with Podman
podman build --build-arg OMNIA_VERSION=staging -t omnia_build_stream:1.0 -f Dockerfile .

# Build with Docker
docker build --build-arg OMNIA_VERSION=staging -t omnia_build_stream:1.0 -f Dockerfile .
```

## Running the Container

**Prerequisites**: 
1. `omnia_core` container must be deployed first via `omnia.sh --install`
2. Omnia repository must be cloned to shared path (handled by omnia_core)
3. Use `prepare_oim` script to deploy this container with proper volume mounts

### Deployment via prepare_oim (Recommended)

This container should be deployed using the `prepare_oim` script which handles:
- Proper volume mounting from omnia_core shared path
- Network configuration
- Service integration with omnia_core

```bash
# After omnia_core is deployed
./prepare_oim --deploy-build-stream
```

### Manual Deployment (for testing)

```bash
# Ensure omnia_core is running first
podman ps | grep omnia_core

# Get the shared path from omnia_core metadata
OMNIA_PATH=$(podman exec omnia_core cat /opt/omnia/.data/oim_metadata.yml | grep oim_shared_path | awk '{print $2}')

# Run with volume mount from omnia_core shared path
# Note: ${OMNIA_PATH}/omnia is mounted to /opt/omnia inside the container
# The container's WORKDIR /omnia will access this via the mount
podman run -d \
  --name omnia_build_stream \
  --hostname omnia_build_stream \
  --network host \
  -v ${OMNIA_PATH}/omnia:/opt/omnia:z \
  -v /var/log/omniaapi:/var/log:z \
  --restart on-failure \
  omnia_build_stream:1.0

# Check status
podman ps | grep omnia_build_stream

# View logs
podman logs -f omnia_build_stream
```

### Systemd Quadlet Deployment (Production)

```bash
# Create Quadlet service file
cat > /etc/containers/systemd/omnia_build_stream.container <<EOF
[Unit]
Description=Omnia Build Stream FastAPI Container
After=omnia_core.service
Requires=omnia_core.service

[Container]
ContainerName=omnia_build_stream
HostName=omnia_build_stream
Image=omnia_build_stream:1.0
Network=host

# Volume mounts (shared from omnia_core)
Volume=${OMNIA_PATH}/omnia:/opt/omnia:z
Volume=/var/log/omniaapi:/var/log:z

[Service]
Restart=always

[Install]
WantedBy=multi-user.target default.target
EOF

# Reload and start
systemctl daemon-reexec
systemctl daemon-reload
systemctl start omnia_build_stream.service
systemctl enable omnia_build_stream.service
```

## API Endpoints

Once the container is running, the following endpoints are available:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check endpoint |
| `/docs` | GET | Swagger UI documentation |
| `/redoc` | GET | ReDoc documentation |
| `/ParseCatalog` | POST | Parse catalog JSON file |
| `/GenerateInputFiles` | POST | Generate Omnia input files |
| `/BuildImage` | POST | Trigger image build |

## Health Check

```bash
# Test health endpoint
curl http://localhost:80/health

# Expected response
{"status":"healthy","service":"omniaapi","version":"1.0","ready":true}
```

## Configuration

### Build Arguments

- `OMNIA_VERSION`: Omnia repository branch/tag to clone (default: `staging`)

### Environment Variables

- `OMNIA_ENV`: Application environment (default: `production`)
- `OMNIA_DEBUG`: Debug mode flag (default: `false`)

### Ports

- **80**: HTTP service port (exposed)

### Volumes

- `/var/log`: Application logs
- `/app/out`: Output directory for generated files

## Integration with OIM

This container is designed to work alongside the `omnia_core` container in an OIM deployment:

```bash
# Ensure omnia_core is running
podman ps | grep omnia_core

# Deploy omnia_build_stream
podman run -d \
  --name omnia_build_stream \
  --network host \
  omnia_build_stream:1.0

# Configure firewall
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --reload

# Verify connectivity
curl http://localhost:80/health
```

## Troubleshooting

### Container won't start

```bash
# Check logs
podman logs omnia_build_stream

# Run interactively for debugging
podman run -it --rm omnia_build_stream:1.0 /bin/bash
```

### Port 80 already in use

```bash
# Check what's using port 80
ss -tlnp | grep :80

# Use a different port
podman run -d --name omnia_build_stream -p 8080:80 omnia_build_stream:1.0
```

### Health check fails

```bash
# Wait for startup (40 seconds)
sleep 40

# Test health endpoint
curl -v http://localhost:80/health

# Check if uvicorn is running
podman exec omnia_build_stream ps aux | grep uvicorn
```

## Security

- Base image: Fedora 40 with latest security updates
- pip upgraded to 25.3 (fixes CVE-2025-8869)
- No root password set
- Health check enabled for monitoring

## Development

### Updating the Container

1. Modify the Dockerfile or application code
2. Rebuild the image:
   ```bash
   ./build_images.sh build-stream build_stream_tag=1.1
   ```
3. Stop and remove old container:
   ```bash
   podman stop omnia_build_stream
   podman rm omnia_build_stream
   ```
4. Deploy new version:
   ```bash
   podman run -d --name omnia_build_stream --network host omnia_build_stream:1.1
   ```

### Testing

```bash
# Test all endpoints
curl http://localhost:80/health
curl http://localhost:80/docs
curl -X POST -F "file=@test_catalog.json" http://localhost:80/ParseCatalog
```

## Related Documentation

- [Container Deployment Guide](../../../omnia_atssa/automation-suite/poc/milestone-1/CONTAINER_DEPLOYMENT_GUIDE.md)
- [Quick Deployment Reference](../../../omnia_atssa/automation-suite/poc/milestone-1/QUICK_DEPLOYMENT_REFERENCE.md)
- [Omnia Documentation](https://github.com/dell/omnia)

## Support

For issues or questions:
- Check the [Omnia GitHub Issues](https://github.com/dell/omnia/issues)
- Review container logs: `podman logs omnia_build_stream`
- Verify health status: `curl http://localhost:80/health`

## Version History

- **1.0** (2025-01-13): Initial release
  - FastAPI service with catalog parsing
  - Health check endpoint
  - Integration with Omnia repository
