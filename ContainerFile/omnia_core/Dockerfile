# ============================================================
# omnia_core — Wolfi-based image
# Replaces: fedora:42
# Base: chainguard/wolfi-base
# Package manager: apk (NOT dnf/rpm — Wolfi is apk-based)
# ============================================================

FROM docker.io/chainguard/wolfi-base:latest

# Build arguments
ARG OMNIA_VERSION=staging

# ── STEP 1: System packages ──────────────────────────────────────────────────
# Go: Wolfi ships go as a versioned apk package, daily CVE-patched
#   'apk add go' installs latest Go — no manual tarball download needed
#
# git-lfs: Available as 'git-lfs' apk package in Wolfi
#   ✅ Eliminates the ENTIRE multi-step Go source build from your Fedora Dockerfile

RUN apk add --no-cache \
    python3 \
    git \
    git-lfs \
    openssh \
    sshpass \
    iproute2 \
    openssl \
    jq \
    wget \
    unzip \
    rsync \
    iputils \
    nano \
    curl \
    ca-certificates-bundle \
    ca-certificates \
    shadow \
    go \
    build-base

RUN mkdir -p /usr/local/share/ca-certificates

# ── STEP 2: git-lfs init ────────────────────────────────────────────────────
# git-lfs is installed as an apk in step 1. Wolfi rebuilds packages daily.
RUN git lfs install

# ── STEP 3: uv + Python deps from pyproject.toml ────────────────────────────
# uv 0.12.1 via pre-built binary — no pip needed.
# NOTE: No manual Go crypto-patch or pip upgrade steps — Wolfi's daily-rebuilt
# apk packages (go, git-lfs) already carry patched dependencies.
COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT="/usr"
RUN uv sync --locked && \
    rm -rf /root/.cache/uv

RUN ln -sf "$(which pulp)" /usr/local/bin/pulp

# ── STEP 4: SSH configuration ───────────────────────────────────────────────
# Wolfi's openssh package ships sshd. Config path: /etc/ssh/sshd_config
# Key generation: ssh-keygen -A (same as Fedora)
RUN sed -i 's/^#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/^#Port 22/Port 2222/' /etc/ssh/sshd_config

EXPOSE 2222

RUN ssh-keygen -A

# ── STEP 5: Directory setup ─────────────────────────────────────────────────
RUN mkdir -p /tmp/omnia_core /root/.config/pulp /root/.ssh && \
    chmod 700 /root/.ssh

RUN echo "cd /omnia" >> /root/.bashrc

# Verify Python version
RUN python3 --version

# ── STEP 6: Ansible Galaxy requirements ─────────────────────────────────────
# ansible-core is installed via pyproject.toml (uv sync above)
RUN echo "collections:" > /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: ansible.utils" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 5.1.1" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: community.crypto" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 2.23.0" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: community.docker" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 3.12.1" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: community.general" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 10.3.0" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: community.grafana" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 2.1.0" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: community.mysql" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 3.10.3" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: dellemc.os10" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 1.1.1" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: dellemc.openmanage" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 10.0.2" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: ansible.posix" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 2.0.0" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: containers.podman" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 1.16.2" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: community.postgresql" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 3.10.2" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: kubernetes.core" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 5.2.0" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  # community.kubernetes removed — deprecated, use kubernetes.core instead" >> /tmp/omnia_core/galaxy_requirements.yml

ENV ANSIBLE_GALAXY_SERVER_TIMEOUT=300
RUN for i in 1 2 3; do \
      echo "Attempt $i: Installing Ansible Galaxy collections..." && \
      ansible-galaxy collection install -r /tmp/omnia_core/galaxy_requirements.yml --timeout 300 --force-with-deps && break || \
      echo "Attempt $i failed, retrying in 10s..." && sleep 10; \
    done

# ── STEP 7: Cleanup ─────────────────────────────────────────────────────────
# Wolfi: use apk cache cleanup instead of dnf clean all / dnf autoremove
RUN rm -rf /var/cache/apk/* /tmp/* /var/tmp/* && \
    chmod 600 /root/.ssh/* 2>/dev/null || true && \
    chmod 700 /root/.ssh 2>/dev/null || true

# ── STEP 8: Clone Omnia ────────────────────────────────────────────────────
RUN git clone --depth 1 https://github.com/dell/omnia.git -b ${OMNIA_VERSION}

# ── STEP 9: Entrypoint and certs ───────────────────────────────────────────
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /omnia

COPY cert-copy.sh /cert-copy.sh
RUN chmod +x /cert-copy.sh

# ── STEP 10: Security labels ────────────────────────────────────────────────
# NOTE: Wolfi's daily builds automatically patch most CVEs at the OS/package level.
# These labels remain for audit/scanner compliance documentation.
LABEL base.image="cgr.dev/chainguard/wolfi-base" \
      base.distro="wolfi" \
      base.package_manager="apk" \
      base.libc="glibc" \
      security.go.source="wolfi-apk" \
      security.go.note="Installed via wolfi apk; daily CVE patching by Chainguard" \
      security.git-lfs.source="wolfi-apk" \
      security.git-lfs.note="Installed via wolfi apk; daily CVE patching by Chainguard" \
      security.urllib3.version="2.7.0" \
      security.urllib3.cves="CVE-2026-21441-fixed,CVE-2025-66471-fixed,CVE-2025-66418-fixed,GHSA-2xpw-w6gg-jr37-fixed,GHSA-gm62-xv2j-4w53-fixed" \
      security.pyasn1.version="0.6.3" \
      security.pyasn1.cves="CVE-2026-23490-fixed,CVE-2026-30922-fixed,GHSA-63vm-454h-vhhq-fixed,GHSA-jr27-m4p2-rc6r-fixed" \
      security.filelock.version="3.20.3" \
      security.filelock.cves="CVE-2025-68146-fixed,CVE-2026-22701-fixed" \
      security.cryptography.version="48.0.0" \
      security.cryptography.cves="CVE-2026-26007-fixed,GHSA-r6ph-v2qm-q3c2-fixed" \
      security.gitpython.version="3.1.50" \
      security.gitpython.cves="GHSA-x2qx-6953-8485-fixed,GHSA-rpm5-65cw-6hj4-fixed" \
      security.pip.note="Not installed; uv handles all Python package management" \
      security.ansible.version="2.20.7" \
      security.ansible.note="Upgraded from EOL ansible-core 2.16 to stable 2.20.7 (supported through ~May 2027)"

ENTRYPOINT ["/entrypoint.sh"]
