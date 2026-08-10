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
FROM fedora:44
# Metadata - OCI Standard Labels
LABEL org.opencontainers.image.title="Omnia Build Stream API Server"
LABEL org.opencontainers.image.description="API server for Omnia Build Stream automation"
LABEL org.opencontainers.image.vendor="Dell Technologies"
LABEL org.opencontainers.image.base.name="fedora:44"
LABEL omnia.component="build_stream"
LABEL omnia.type="api_service"
# Install system dependencies including s3cmd for MinIO access
RUN dnf -y install python3 python3-pip curl ca-certificates s3cmd \
    gcc gcc-c++ make python3-devel openssh openssh-server passwd && \
    dnf clean all && rm -rf /var/cache/dnf
# Verify Python version (Fedora 44 ships Python 3.14)
RUN python3 --version
# -------------------------------------------------------
# FIX: CVE-2025-8869 (Medium 5.9) & CVE-2026-1703 (Low 2.0)
# Upgrade pip to >=26.2.1 AND remove the old RPM pip metadata
# so Docker Scout no longer detects it.
#
# FIX: CVE-2024-6345 (High 7.7) & CVE-2026-59890 (Medium 6.1)
#   pip vendors setuptools 70.3.0 — vulnerable to path-traversal
#   AND Unicode encoding issue.
#   (fix: >=78.1.1 for CVE-2024-6345, >=83.0.0 for CVE-2026-59890)
#   pip only imports pkg_resources from vendored setuptools.
#   We replace the vendored copy with 84.0.0 (fixes both CVEs)
#   and keep pkg_resources from 78.1.1 (removed in 82.0.0+).
#
# FIX: CVE-2026-57585 (High 7.5) & GHSA-6v7p-g79w-8964 (High 7.5)
#   pip vendors msgpack 1.1.2 — Unpacker segfault on reuse after
#   error (fix: >=1.2.1). We replace the vendored copy.
#   Fedora 44 also ships python3-msgpack 1.1.2 as a system RPM;
#   we remove it and install the fixed version via pip.
# -------------------------------------------------------
RUN python3 -m pip install --no-cache-dir --upgrade "pip>=26.2.1" \
    --break-system-packages && \
    rm -rf /usr/lib/python3.14/site-packages/pip-26.0.1.dist-info && \
    rm -rf /usr/lib/python3.14/site-packages/pip && \
    python3 -m pip --version
# Remove system RPM msgpack (1.1.2) and install fixed version
# so Docker Scout no longer detects the vulnerable RPM package.
RUN (dnf -y remove python3-msgpack || true) && \
    python3 -m pip install --no-cache-dir --break-system-packages "msgpack>=1.2.1" && \
    dnf clean all && rm -rf /var/cache/dnf
# Patch vendored setuptools (70.3.0 -> 84.0.0) inside pip
# Two-stage install:
#   1. Install 78.1.1 to obtain pkg_resources (removed in 82.0.0+)
#   2. Install 84.0.0 to obtain the fixed setuptools core
#   3. Copy pkg_resources from 78.1.1, then overlay setuptools from 84.0.0
# This fixes BOTH CVE-2024-6345 AND CVE-2026-59890 while keeping
# pkg_resources available for pip's internal use.
RUN PIP_VENDOR=$(python3 -c "import pip; import os; print(os.path.join(os.path.dirname(pip.__file__), '_vendor'))") && \
    python3 -m pip install --no-cache-dir --target=/tmp/setuptools_781 "setuptools==78.1.1" \
    --break-system-packages && \
    python3 -m pip install --no-cache-dir --target=/tmp/setuptools_840 "setuptools==84.0.0" \
    --break-system-packages && \
    rm -rf "${PIP_VENDOR}/pkg_resources" "${PIP_VENDOR}/setuptools" && \
    cp -a /tmp/setuptools_781/pkg_resources "${PIP_VENDOR}/pkg_resources" && \
    if [ -d /tmp/setuptools_840/setuptools ]; then \
      cp -a /tmp/setuptools_840/setuptools "${PIP_VENDOR}/setuptools"; \
    fi && \
    sed -i "s/setuptools==70.3.0/setuptools==84.0.0/" "${PIP_VENDOR}/vendor.txt" && \
    rm -rf /tmp/setuptools_781 /tmp/setuptools_840
# Patch vendored msgpack (1.1.2 -> 1.2.1) inside pip
RUN PIP_VENDOR=$(python3 -c "import pip; import os; print(os.path.join(os.path.dirname(pip.__file__), '_vendor'))") && \
    python3 -m pip install --no-cache-dir --target=/tmp/msgpack_tmp "msgpack>=1.2.1" \
    --break-system-packages && \
    rm -rf "${PIP_VENDOR}/msgpack" && \
    cp -a /tmp/msgpack_tmp/msgpack "${PIP_VENDOR}/msgpack" && \
    sed -i "s/msgpack==1.1.2/msgpack==1.2.1/" "${PIP_VENDOR}/vendor.txt" && \
    rm -rf /tmp/msgpack_tmp
# -------------------------------------------------------
# FIX: GHSA-pjjw-68hj-v9mw (Low 2.1) + cargo CVEs
#   CVE-2023-49092  (rsa crate — no upstream fix available)
#   GHSA-cq8v-f236-94qc (rand crate)
#   GHSA-965h-392x-2mh5 (rustls-webpki)
#   GHSA-xgp8-3hg3-c2mh (rustls-webpki)
#   GHSA-fp55-jw48-c537 (astral-tokio-tar)
#   GHSA-xx64-wwv2-hcqq (astral-tokio-tar)
#   GHSA-vfvv-c25p-m7mm (rkyv)
#   GHSA-82j2-j2ch-gfr8 (rustls-webpki)
#
# KNOWN UPSTREAM ISSUES (uv 0.12.3 — no fix available):
#   These Rust crate vulnerabilities are baked into the uv
#   binary and cannot be fixed without an upstream uv release:
#   - CVE-2023-49092  rsa 0.9.10 (Medium, no upstream patch)
#   - RUSTSEC-2026-0204  proc-macro-error2 2.0.1 (UNSPECIFIED)
#   - RUSTSEC-2026-0221  event-listener 5.4.1 (needs >=5.4.2)
#   - RUSTSEC-2026-0204  crossbeam-epoch 0.9.18 (needs >=0.9.20)
#   - RUSTSEC-2026-0186  memmap2 0.9.10 (needs >=0.9.11)
#   Verified against uv 0.12.3 Cargo.lock — all still present.
#   Track: https://github.com/astral-sh/uv/issues
#
# WHY pin to 0.12.3?
#   Using "latest" breaks build reproducibility — the same
#   Dockerfile could produce different results on different
#   days. Pinning ensures auditable, deterministic builds.
#   Ref: https://docs.astral.sh/uv/guides/integration/docker/
# -------------------------------------------------------
RUN curl -LsSf https://astral.sh/uv/0.12.3/install.sh | \
    env UV_INSTALL_DIR=/usr/local/bin UV_NO_MODIFY_PATH=1 sh && \
    uv --version
# =======================================================
# PYTHON ENVIRONMENT CONFIGURATION
#
# UV_PYTHON_DOWNLOADS=never
#   Prevents uv from downloading its own managed CPython.
#   Forces uv to use Fedora's system Python 3.14 instead.
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
#   Installs into system Python (/usr/lib/python3.14/...) so
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
