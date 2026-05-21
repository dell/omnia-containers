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

# Install system dependencies including s3cmd for MinIO access
RUN dnf -y install python3 python3-pip curl ca-certificates s3cmd \
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
#   GHSA-fp55-jw48-c537 (astral-tokio-tar)
#   GHSA-xx64-wwv2-hcqq (astral-tokio-tar)
#   GHSA-vfvv-c25p-m7mm (rkyv)
#   GHSA-82j2-j2ch-gfr8 (rustls-webpki)
#
# WHY pin to 0.11.15?
#   Using "latest" breaks build reproducibility — the same
#   Dockerfile could produce different results on different
#   days. Pinning ensures auditable, deterministic builds.
#   Ref: https://docs.astral.sh/uv/guides/integration/docker/
# -------------------------------------------------------
RUN curl -LsSf https://astral.sh/uv/0.11.15/install.sh | \
    env UV_INSTALL_DIR=/usr/local/bin UV_NO_MODIFY_PATH=1 sh && \
    uv --version

# =======================================================
# PYTHON ENVIRONMENT CONFIGURATION
#
# UV_PYTHON_DOWNLOADS=never
#   Prevents uv from downloading its own managed CPython.
#   Forces uv to use Fedora's system Python 3.13 instead.
#   (Managed CPython bundles vulnerable pip 25.3 internally)
#
# UV_SYSTEM_PYTHON=1
#   Allows uv pip commands (uv pip install, uv pip compile)
#   to target the system Python at /usr/bin/python3.
#   Without this, uv pip refuses to modify non-venv Python.
#
#   NOTE: This does NOT affect project-mode commands
#   (uv sync, uv run, uv add) — those ALWAYS create a
#   .venv regardless of this setting. That is why we use
#   "uv pip install --system" instead of "uv sync" here.
# =======================================================
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_SYSTEM_PYTHON=1

# =======================================================
# DEPENDENCIES: Install production packages from committed
# and audited lock file into system Python.
#
# Copy pyproject.toml + uv.lock BEFORE source code so Docker
# caches the dependency layer. Only a change to these files
# triggers a re-install; source code changes skip this step.
#
# uv export --locked
#   Reads uv.lock, verifies it matches pyproject.toml, and
#   exports exact pinned versions to requirements.txt.
#   FAILS if uv.lock is out of sync — this is the safety gate.
#
# uv pip install --system
#   Installs into system Python (/usr/lib/python3.13/...) so
#   the ENTRYPOINT command (/usr/bin/python3 -m uvicorn) can
#   find all packages including uvicorn.
#
# NOTE: Do NOT use "uv sync --locked" here — it installs into
# a .venv/ which the system Python cannot access at runtime.
# =======================================================
COPY pyproject.toml uv.lock ./
RUN uv export --locked --no-hashes -o requirements.txt && \
    uv pip install --system -r requirements.txt

# Optionally install dev dependencies
ARG BUILD_ENV=production
RUN if [ "$BUILD_ENV" = "development" ]; then \
      uv export --locked --no-hashes --extra dev -o requirements-dev.txt && \
      uv pip install --system -r requirements-dev.txt; \
    fi

# -----------------------------
# S3 Configuration Setup
# -----------------------------
# Copy s3cmd initialization script
COPY init_s3cfg.sh /usr/local/bin/init_s3cfg.sh
RUN chmod +x /usr/local/bin/init_s3cfg.sh

# Create app and SSL directories
WORKDIR /opt/omnia/build_stream
RUN mkdir -p /etc/ssl/omnia

# Runtime environment
ENV APP_DIR=/opt/omnia/build_stream
ENV SSL_KEYFILE=/etc/ssl/omnia/bs_key.pem
ENV SSL_CERTFILE=/etc/ssl/omnia/bs_cert.pem

# MinIO S3 configuration (will be overridden by Quadlet at runtime)
ENV MINIO_ACCESS_KEY=admin
ENV MINIO_SECRET_KEY=
ENV MINIO_HOST=localhost:9000
ENV MINIO_USE_HTTPS=False

WORKDIR ${APP_DIR}

# Entrypoint initializes s3cmd config and starts FastAPI service
ENTRYPOINT ["/bin/bash", "-c", "/usr/local/bin/init_s3cfg.sh || true && exec python3 -Xfrozen_modules=off -m uvicorn main:app --host \"${HOST:?HOST env required}\" --port \"${PORT:?PORT env required}\" --ssl-keyfile \"${SSL_KEYFILE}\" --ssl-certfile \"${SSL_CERTFILE}\""]
