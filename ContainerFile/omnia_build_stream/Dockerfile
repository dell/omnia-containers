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

# Metadata - OCI Standard Labels
LABEL org.opencontainers.image.title="Omnia Build Stream API Server"
LABEL org.opencontainers.image.description="API server for Omnia Build Stream automation"
LABEL org.opencontainers.image.vendor="Dell Technologies"
LABEL org.opencontainers.image.base.name="fedora:42"

# Omnia-specific labels for internal tooling
LABEL omnia.component="build_stream"
LABEL omnia.type="api_service"

# Update the system and install Python 3.12 with security updates (without pip)
RUN dnf -y install python3 curl ca-certificates \
    gcc gcc-c++ make python3-devel openssh-clients && \
    dnf clean all && \
    rm -rf /var/cache/dnf

# Verify Python version
RUN python3 --version

# Remove rpm pip to avoid "no RECORD file" issue
RUN dnf -y remove python3-pip python3-setuptools python3-wheel || true && \
    dnf clean all && rm -rf /var/cache/dnf


# Install pip 25.3 directly to fix CVE-2025-8869
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3 - "pip==26.0" && \
    python3 -m pip --version && \
    python3 -m pip list | grep pip

# Install uv package manager
RUN python3 -m pip install --no-cache-dir uv==0.9.13

# Copy project configuration files
COPY pyproject.toml uv.lock ./

# Set UV environment to install packages system-wide
ENV UV_PROJECT_ENVIRONMENT="/usr"

# Install dependencies using uv from lock file
RUN uv sync --locked

# Install development dependencies only when BUILD_ENV=development
ARG BUILD_ENV=production
RUN if [ "$BUILD_ENV" = "development" ]; then uv sync --dev; fi

# Create app directory
WORKDIR /opt/omnia/build_stream

# Create SSL directory for volume mount
RUN mkdir -p /etc/ssl/omnia

# -----------------------------
# Runtime defaults
# -----------------------------
ENV HOST=0.0.0.0
ENV PORT=443
ENV APP_DIR=/opt/omnia/build_stream
# Path where Pulp's cert is mounted by Quadlet
ENV PULP_CA_BUNDLE=/etc/pulp/certs/pulp_webserver.crt
ENV REQUESTS_CA_BUNDLE=/etc/pulp/certs/pulp_webserver.crt
ENV CURL_CA_BUNDLE=/etc/pulp/certs/pulp_webserver.crt
ENV SYSTEM_ANCHOR=/etc/pki/ca-trust/source/anchors/pulp_webserver.crt

# SSL certificate paths for uvicorn
ENV SSL_KEYFILE=/etc/ssl/omnia/bs_key.pem
ENV SSL_CERTFILE=/etc/ssl/omnia/bs_cert.pem

# The code (main.py) will be mounted here via Quadlet:
WORKDIR ${APP_DIR}

# Expose HTTPS port
EXPOSE ${PORT:-443}

# Start API server directly
CMD ["sh", "-c", "python3 -m uvicorn main:app --host ${HOST:-0.0.0.0} --port ${PORT:-443} --ssl-keyfile=${SSL_KEYFILE} --ssl-certfile=${SSL_CERTFILE}"]
