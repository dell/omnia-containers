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
# Base: Wolfi (cgr.dev/chainguard/wolfi-base)
# Migrated from: fedora:42
# ============================================================

FROM cgr.dev/chainguard/wolfi-base

# Metadata - OCI Standard Labels
LABEL org.opencontainers.image.title="Omnia Build Stream API Server"
LABEL org.opencontainers.image.description="API server for Omnia Build Stream automation"
LABEL org.opencontainers.image.vendor="Dell Technologies"
LABEL org.opencontainers.image.base.name="cgr.dev/chainguard/wolfi-base"
LABEL omnia.component="build_stream"
LABEL omnia.type="api_service"

# ── System packages ──────────────────────────────────────────
# Package mapping:
#
#   Fedora (dnf)         → Wolfi (apk)           Notes
#   ──────────────────── → ───────────────────── → ─────────────────────
#   python3              → python3
#   python3-pip          → py3-pip
#   curl                 → curl
#   ca-certificates      → ca-certificates-bundle
#   gcc                  → build-base              (includes gcc, g++, make)
#   gcc-c++              → (included in build-base)
#   make                 → (included in build-base)
#   python3-devel        → python3-dev
#   openssh              → openssh
#   openssh-server       → (included in openssh)
#   passwd               → shadow                  (provides useradd/passwd)
#   s3cmd                → ❌ NOT in Wolfi apk     (installed via pip below)
#
RUN apk update && apk add --no-cache \
    python3 \
    py3-pip \
    curl \
    ca-certificates-bundle \
    build-base \
    python3-dev \
    openssh \
    shadow \
    bash

# Verify Python version
RUN python3 --version

# ── pip: No manual CVE fix needed ────────────────────────────
# Fedora Dockerfile had a complex pip upgrade + dist-info deletion:
#   python3 -m pip install --upgrade "pip>=26.0" --break-system-packages
#   rm -rf /usr/lib/python3.13/site-packages/pip-24.3.1.dist-info
#
# Upgraded from 0.11.15 to 0.12.1 to fix:
#   rkyv 0.8.16 -> 0.8.17+  (3 CVEs)
#   crossbeam-epoch 0.9.18 -> 0.9.20+  (1 CVE)
#   memmap2 0.9.10 -> 0.9.11+  (1 CVE)
#   event-listener 5.4.1 -> 5.4.2+  (1 CVE)
#   anyhow 1.0.102 -> 1.0.103+  (1 CVE)
#   + additional Rust dependency CVE fixes
#
# WHY pin to 0.12.1?
#   Using "latest" breaks build reproducibility — the same
#   Dockerfile could produce different results on different
#   days. Pinning ensures auditable, deterministic builds.
#   Ref: https://docs.astral.sh/uv/guides/integration/docker/
# -------------------------------------------------------
RUN curl -LsSf https://astral.sh/uv/0.12.1/install.sh | \
    env UV_INSTALL_DIR=/usr/local/bin UV_NO_MODIFY_PATH=1 sh && \
    uv --version

# ── uv: Install via official Docker image (not curl) ─────────
# Fedora Dockerfile used:
#   curl -LsSf https://astral.sh/uv/0.11.15/install.sh | sh
#
# Best practice is COPY --from= which is:
#   - Faster (no curl download at build time)
#   - More secure (no shell pipe execution)
#   - Reproducible (pinned to exact image tag)
#
# Pinning to 0.11.15 to match the original Dockerfile.
# NOTE: Your team should evaluate upgrading to 0.11.18+ for
# security fixes (GHSA-3cv2-h65g-fgmm, GHSA-4gg8-gxpx-9rph).
COPY --from=ghcr.io/astral-sh/uv:0.11.15 /uv /uvx /usr/local/bin/
RUN uv --version

# ── s3cmd: Install via pip (not available as Wolfi apk) ──────
# s3cmd is a Python package. On Fedora it was installed via dnf,
# but Wolfi does not package it. pip install works identically.
RUN pip3 install --no-cache-dir s3cmd

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

# ── Application directories ─────────────────────────────────
WORKDIR /opt/omnia/build_stream
RUN mkdir -p /etc/ssl/omnia

# ── Runtime environment ─────────────────────────────────────
ENV APP_DIR=/opt/omnia/build_stream
ENV SSL_KEYFILE=/etc/ssl/omnia/bs_key.pem
ENV SSL_CERTFILE=/etc/ssl/omnia/bs_cert.pem

# MinIO S3 configuration (overridden by Quadlet at runtime)
ENV MINIO_ACCESS_KEY=admin
ENV MINIO_SECRET_KEY=
ENV MINIO_HOST=localhost:9000
ENV MINIO_USE_HTTPS=False

WORKDIR ${APP_DIR}

# ── Entrypoint (identical to Fedora version) ─────────────────
ENTRYPOINT ["/bin/bash", "-c", "/usr/local/bin/init_s3cfg.sh || true && exec python3 -Xfrozen_modules=off -m uvicorn main:app --host \"${HOST:?HOST env required}\" --port \"${PORT:?PORT env required}\" --ssl-keyfile \"${SSL_KEYFILE}\" --ssl-certfile \"${SSL_CERTFILE}\""]