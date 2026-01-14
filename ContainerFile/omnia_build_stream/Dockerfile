# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Dockerfile for omnia_build_stream FastAPI service
# This container provides the FastAPI service for Omnia Build Stream automation
# Use Fedora 42 as the base image
FROM fedora:42

# Build arguments
ARG OMNIA_VERSION=staging

# Metadata
LABEL maintainer="Omnia Team"
LABEL description="FastAPI service for Omnia Build Stream automation"
LABEL version="1.0"
LABEL omnia.component="build_stream"
LABEL omnia.type="api_service"

# Update the system and install Python 3.12 with security updates
RUN dnf -y update && \
    dnf -y install python3 python3-pip git openssh-clients \
    iproute systemd wget curl jq nano iputils && \
    dnf clean all

# Verify Python version
RUN python3 --version

# Upgrade pip to fix CVE-2025-8869 (pip 24.0 vulnerability)
RUN python3 -m pip install --upgrade pip==25.3

# Install/sync python packages using the uv.lock
RUN pip3 install uv==0.9.13
COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT="/usr"
RUN uv sync --locked

# Install FastAPI, Uvicorn, and required dependencies
RUN python3 -m pip install --no-cache-dir \
    fastapi==0.115.6 \
    uvicorn[standard]==0.34.0 \
    python-multipart==0.0.20

# Create log directory
RUN mkdir -p /var/log/omnia_build_stream

# Create output directories for API operations
RUN mkdir -p /omnia_build_stream/out/generator /omnia_build_stream/out/adapter/config

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:80/health || exit 1

# Document security patches
LABEL security.pip.version="25.3" \
      security.pip.cve="CVE-2025-8869-fixed"

# Start command
CMD ["python3", "-m", "uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "80"]
