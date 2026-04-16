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
FROM fedora:42

# Metadata - OCI Standard Labels
LABEL org.opencontainers.image.title="Omnia Build Stream API Server"
LABEL org.opencontainers.image.description="API server for Omnia Build Stream automation"
LABEL org.opencontainers.image.vendor="Dell Technologies"
LABEL org.opencontainers.image.base.name="fedora:42"
LABEL omnia.component="build_stream"
LABEL omnia.type="api_service"

# Install system dependencies (without pip)
RUN dnf -y install python3 curl ca-certificates \
    gcc gcc-c++ make python3-devel openssh openssh-server passwd && \
    dnf clean all && rm -rf /var/cache/dnf

RUN python3 --version

# Remove RPM-installed pip/setuptools to avoid "no RECORD file" errors
RUN dnf -y remove python3-pip python3-setuptools python3-wheel || true && \
    dnf clean all && rm -rf /var/cache/dnf

# Install uv package manager (standalone — no pip needed)
RUN curl -LsSf https://astral.sh/uv/0.9.13/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh

# Copy project configuration files
COPY pyproject.toml uv.lock ./

# Install production dependencies from the lockfile
RUN UV_SYSTEM_PYTHON=1 uv sync --frozen --no-install-project

# Optionally install dev dependencies
ARG BUILD_ENV=production
RUN if [ "$BUILD_ENV" = "development" ]; then \
      UV_SYSTEM_PYTHON=1 uv sync --frozen --no-install-project --extra dev; \
    fi

# Create app and SSL directories
WORKDIR /opt/omnia/build_stream
RUN mkdir -p /etc/ssl/omnia

# Runtime environment
ENV APP_DIR=/opt/omnia/build_stream
ENV SSL_KEYFILE=/etc/ssl/omnia/bs_key.pem
ENV SSL_CERTFILE=/etc/ssl/omnia/bs_cert.pem

WORKDIR ${APP_DIR}

ENTRYPOINT ["/bin/bash", "-c", "python3 -Xfrozen_modules=off -m uvicorn main:app --host \"${HOST:?HOST env required}\" --port \"${PORT:?PORT env required}\" --ssl-keyfile \"${SSL_KEYFILE}\" --ssl-certfile \"${SSL_CERTFILE}\""]
