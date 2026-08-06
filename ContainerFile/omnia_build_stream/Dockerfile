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

# ============================================================
# Dockerfile for omnia_build_stream FastAPI service
# Base: Wolfi (chainguard/wolfi-base)
# Migrated from: fedora:42
# ============================================================

FROM chainguard/wolfi-base:latest

# Metadata - OCI Standard Labels
LABEL org.opencontainers.image.title="Omnia Build Stream API Server"
LABEL org.opencontainers.image.description="API server for Omnia Build Stream automation"
LABEL org.opencontainers.image.vendor="Dell Technologies"
LABEL org.opencontainers.image.base.name="chainguard/wolfi-base"
LABEL omnia.component="build_stream"
LABEL omnia.type="api_service"

# ── System packages ──────────────────────────────────────────
# Package mapping:
#
#   Fedora (dnf)         → Wolfi (apk)           Notes
#   ──────────────────── → ───────────────────── → ─────────────────────
#   python3              → python3
#   python3-pip          → (not needed — uv handles all package mgmt)
#   curl                 → curl
#   ca-certificates      → ca-certificates-bundle
#   gcc                  → build-base              (includes gcc, g++, make)
#   gcc-c++              → (included in build-base)
#   make                 → (included in build-base)
#   python3-devel        → python3-dev
#   openssh              → openssh
#   openssh-server       → (included in openssh)
#   passwd               → shadow                  (provides useradd/passwd)
#   s3cmd                → ❌ NOT in Wolfi apk     (installed via uv below)
#
RUN apk add --no-cache \
    python3 \
    curl \
    ca-certificates-bundle \
    build-base \
    python3-dev \
    openssh \
    shadow \
    bash

# Verify Python version
RUN python3 --version

# ── uv: Install via official Docker image ─────────────────────
# COPY --from is preferred over curl pipe:
#   - Faster (no download at build time)
#   - More secure (no shell pipe execution)
#   - Reproducible (pinned to exact image tag)
#
# Pinned to 0.12.1 to fix Rust dependency CVEs:
#   rkyv, crossbeam-epoch, memmap2, event-listener, anyhow, etc.
COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /uvx /usr/local/bin/
RUN uv --version

# ── s3cmd: Install via uv (not available as Wolfi apk) ────────
# s3cmd is a Python package. On Fedora it was installed via dnf,
# but Wolfi does not package it.
RUN uv pip install --system --no-cache s3cmd

# =======================================================
# PYTHON ENVIRONMENT CONFIGURATION
# (Identical to Fedora version — no changes needed)
# =======================================================
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_SYSTEM_PYTHON=1

# =======================================================
# DEPENDENCIES: Install from committed lock file
# (Identical logic to Fedora version — no changes needed)
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

# ── S3 Configuration Setup ──────────────────────────────────
COPY init_s3cfg.sh /usr/local/bin/init_s3cfg.sh
RUN chmod +x /usr/local/bin/init_s3cfg.sh

# ── Application directories & runtime environment ───────────
ENV APP_DIR=/opt/omnia/build_stream
ENV SSL_KEYFILE=/etc/ssl/omnia/bs_key.pem
ENV SSL_CERTFILE=/etc/ssl/omnia/bs_cert.pem

# MinIO S3 configuration (overridden by Quadlet at runtime)
ENV MINIO_ACCESS_KEY=admin
ENV MINIO_SECRET_KEY=
ENV MINIO_HOST=localhost:9000
ENV MINIO_USE_HTTPS=False

WORKDIR ${APP_DIR}
RUN mkdir -p /etc/ssl/omnia

EXPOSE 8000

# ── Entrypoint (identical to Fedora version) ─────────────────
ENTRYPOINT ["/bin/bash", "-c", "/usr/local/bin/init_s3cfg.sh || true && exec python3 -Xfrozen_modules=off -m uvicorn main:app --host \"${HOST:?HOST env required}\" --port \"${PORT:?PORT env required}\" --ssl-keyfile \"${SSL_KEYFILE}\" --ssl-certfile \"${SSL_CERTFILE}\""]
