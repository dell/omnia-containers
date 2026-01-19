# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
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
LABEL org.opencontainers.image.title="Omnia Build Stream API Server"
LABEL org.opencontainers.image.description="API server for Omnia Build Stream automation with Pulp CLI integration"
LABEL org.opencontainers.image.vendor="Dell Technologies"
LABEL org.opencontainers.image.version="1.0"
LABEL org.opencontainers.image.base.name="fedora:42"

# Update the system and install Python 3.12 with security updates
RUN dnf -y upgrade --refresh && \
    dnf -y install python3 python3-pip git openssh-clients \
    iproute systemd wget curl jq nano iputils && \
    dnf -y upgrade --security && \
    dnf clean all && \
    rm -rf /var/cache/dnf

# Verify Python version
RUN python3 --version

# Upgrade pip to fix CVE-2025-8869 (pip 24.0 vulnerability)
RUN python3 -m pip install --upgrade pip==25.3 && \
    pip3 --version

# Install uv package manager
RUN pip3 install uv==0.9.13

# Copy project configuration files
COPY pyproject.toml uv.lock ./

# Set UV environment to install packages system-wide
ENV UV_PROJECT_ENVIRONMENT="/usr"

# Install dependencies using uv from lock file
RUN uv sync --locked

# Create output directories for API operations
RUN mkdir -p /omnia_build_stream/out/generator /omnia_build_stream/out/adapter/config

# TODO: Uncomment when api_server.py is available in /opt/omnia/build_stream
# COPY api_server.py /app/api_server.py
# WORKDIR /app

# Copy Pulp configuration script
COPY configure-pulp.sh /configure-pulp.sh
RUN chmod +x /configure-pulp.sh

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port 443
EXPOSE 443

# Document security patches
LABEL security.pip.version="25.3" \
      security.pip.cve="CVE-2025-8869-fixed"

# Set entrypoint to configure Pulp and start the application
ENTRYPOINT ["/entrypoint.sh"]
