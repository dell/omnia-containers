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

# Install system dependencies
RUN dnf -y install python3 python3-pip curl ca-certificates \
    gcc gcc-c++ make python3-devel openssh openssh-server passwd && \
    dnf clean all && rm -rf /var/cache/dnf

# Verify Python version (Fedora 42 ships Python 3.13)
RUN python3 --version

# -------------------------------------------------------
# FIX: CVE-2025-8869 (Medium 5.9) & CVE-2026-1703 (Low 2.0)
# Upgrade pip to >=26.0 AND remove the old RPM pip 24.3.1
# metadata so Docker Scout no longer detects it
# -------------------------------------------------------
RUN python3 -m pip install --no-cache-dir --upgrade "pip>=26.0" \
    --break-system-packages && \
    rm -rf /usr/lib/python3.13/site-packages/pip-24.3.1.dist-info && \
    rm -rf /usr/lib/python3.13/site-packages/pip && \
    python3 -m pip --version

# -------------------------------------------------------
# FIX: GHSA-pjjw-68hj-v9mw (Low 2.1) + cargo CVEs
#   CVE-2023-49092  (rsa crate)
#   GHSA-cq8v-f236-94qc (rand crate)
#   GHSA-965h-392x-2mh5 (rustls-webpki)
#   GHSA-xgp8-3hg3-c2mh (rustls-webpki)
#
# Install LATEST uv via official installer to get the
# newest binary with updated Rust dependencies.
# We do NOT install uv via pip (pip-installed uv==0.9.13
# and 0.11.6 still contain older cargo crates).
# -------------------------------------------------------
RUN curl -LsSf https://astral.sh/uv/install.sh | \
    env INSTALLER_NO_MODIFY_PATH=1 sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    mv /root/.local/bin/uvx /usr/local/bin/uvx && \
    uv --version

# -------------------------------------------------------
# Prevent uv from downloading its own managed Python
# (managed cpython bundles vulnerable pip 25.3 internally)
# Force uv to use Fedora's system Python 3.13 instead
# -------------------------------------------------------
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_SYSTEM_PYTHON=1

# Copy project configuration files
# NOTE: Ensure pyproject.toml has:
#   requires-python = ">=3.12"
# and does NOT have "uv>=11.0.7" in [project].dependencies
# (uv is a build tool, not a runtime dependency)
COPY pyproject.toml uv.lock ./

# -------------------------------------------------------
# Regenerate lockfile inside the build to match Python 3.13
# then install production dependencies
# -------------------------------------------------------
RUN uv lock --upgrade && \
    uv sync --frozen --no-install-project

# Optionally install dev dependencies
ARG BUILD_ENV=production
RUN if [ "$BUILD_ENV" = "development" ]; then \
      uv sync --frozen --no-install-project --extra dev; \
    fi

# Create app and SSL directories
WORKDIR /opt/omnia/build_stream
RUN mkdir -p /etc/ssl/omnia

# Runtime environment
ENV APP_DIR=/opt/omnia/build_stream
ENV SSL_KEYFILE=/etc/ssl/omnia/bs_key.pem
ENV SSL_CERTFILE=/etc/ssl/omnia/bs_cert.pem

WORKDIR ${APP_DIR}

# Entrypoint starts FastAPI service using system Python
ENTRYPOINT ["/bin/bash", "-c", "python3 -Xfrozen_modules=off -m uvicorn main:app --host \"${HOST:?HOST env required}\" --port \"${PORT:?PORT env required}\" --ssl-keyfile \"${SSL_KEYFILE}\" --ssl-certfile \"${SSL_CERTFILE}\""]
