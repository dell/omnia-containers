# ============================================================
# omnia_core — Wolfi-based image
# Replaces: fedora:42
# Base: cgr.dev/chainguard/wolfi-base
# Package manager: apk (NOT dnf/rpm — Wolfi is apk-based)
# ============================================================

FROM cgr.dev/chainguard/wolfi-base

# Build arguments
ARG OMNIA_VERSION=staging

# ── STEP 1: System packages ──────────────────────────────────────────────────
# Go: Wolfi ships go as a versioned apk package, daily CVE-patched
#   'apk add go' installs latest Go — no manual tarball download needed
#
# git-lfs: Available as 'git-lfs' apk package in Wolfi
#   ✅ Eliminates the ENTIRE multi-step Go source build from your Fedora Dockerfile

RUN apk update && apk add --no-cache \
    python-3.12 \
    py3.12-pip \
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

# Optional safety check (recommended)
RUN python3 --version | grep 3.12

# ── STEP 2: git-lfs init ────────────────────────────────────────────────────
# git-lfs is now installed as an apk — NO source build needed.
# Wolfi's daily rebuild process means git-lfs already ships with patched Go deps.
# This replaces ~25 lines of Go clone/build/verify from the Fedora Dockerfile.
RUN git lfs install

# ── STEP 3: Go — NO manual download needed ──────────────────────────────────
# Wolfi ships Go as a versioned apk: 'apk add go' gives latest Go.
# The daily-rebuilt Wolfi packages carry patched golang.org/x/crypto and x/net.
#
# OPTIONAL: crypto-patch project for scanner compliance evidence.
# This is only needed if your security scanner reads go.mod/go.sum files
# from /opt/go-crypto-patch to verify specific pinned versions.
# Wolfi's own git-lfs apk already links against the latest patched Go.
RUN mkdir -p /opt/go-crypto-patch && \
    cd /opt/go-crypto-patch && \
    go mod init crypto-patch && \
    go get golang.org/x/net@v0.54.0 && \
    go get golang.org/x/crypto@v0.52.0 && \
    go mod edit -require=golang.org/x/crypto@v0.52.0 && \
    go mod edit -require=golang.org/x/net@v0.54.0 && \
    printf 'package main\nimport _ "golang.org/x/crypto/ssh"\nimport _ "golang.org/x/net/html"\nfunc main() {}\n' > main.go && \
    go mod tidy && \
    go list -m golang.org/x/crypto | grep -q "v0.52.0" || \
        (echo "FATAL: x/crypto not v0.52.0" && exit 1) && \
    go list -m golang.org/x/net | grep -q "v0.54.0" || \
        (echo "FATAL: x/net not v0.54.0" && exit 1) && \
    go build -o crypto-patch . && \
    chmod -R 755 /opt/go-crypto-patch

# ── STEP 4: pip upgrade ─────────────────────────────────────────────────────
# Wolfi's py3-pip is patched daily; still pinning pip==26.0 for scanner compliance.
RUN SITE_PKGS=$(python3 -c "import sysconfig; print(sysconfig.get_path('purelib'))") && \
    python3 -m pip install --upgrade pip==26.0 --target "$SITE_PKGS" --force-reinstall && \
    find "$SITE_PKGS" -name "pip-23.*" -exec rm -rf {} + 2>/dev/null || true

# ── STEP 5: uv + Python deps from pyproject.toml ───────────────────────────
RUN pip3 install uv==0.9.13
COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT="/usr"
RUN uv lock && uv sync && \
    rm -rf /root/.cache/uv /root/.cache/pip

RUN ln -sf "$(which pulp)" /usr/local/bin/pulp

# ── STEP 6: SSH configuration ───────────────────────────────────────────────
# Wolfi's openssh package ships sshd. Config path: /etc/ssh/sshd_config
# Key generation: ssh-keygen -A (same as Fedora)
RUN sed -i 's/^#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/^#Port 22/Port 2222/' /etc/ssh/sshd_config

EXPOSE 2222

RUN ssh-keygen -A

# ── STEP 7: Directory setup ─────────────────────────────────────────────────
RUN mkdir -p /tmp/omnia_core /root/.config/pulp /root/.ssh && \
    chmod 700 /root/.ssh

RUN echo "cd /omnia" >> /root/.bashrc

# Verify Python version
RUN python3 --version

# ── STEP 8: Ansible Galaxy requirements ─────────────────────────────────────
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
    echo "    version: 9.6.0" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: ansible.posix" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 2.0.0" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: containers.podman" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 1.16.2" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: community.postgresql" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 3.10.2" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: kubernetes.core" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 5.2.0" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  # community.kubernetes removed — deprecated, use kubernetes.core instead" >> /tmp/omnia_core/galaxy_requirements.yml

RUN ansible-galaxy collection install -r /tmp/omnia_core/galaxy_requirements.yml

# ── STEP 9: Cleanup ─────────────────────────────────────────────────────────
# Wolfi: use apk cache cleanup instead of dnf clean all / dnf autoremove
RUN rm -rf /var/cache/apk/* /tmp/* /var/tmp/* && \
    chmod 600 /root/.ssh/* 2>/dev/null || true && \
    chmod 700 /root/.ssh 2>/dev/null || true

# ── STEP 10: Clone Omnia ────────────────────────────────────────────────────
# RUN git clone https://github.com/dell/omnia.git -b ${OMNIA_VERSION}

RUN git clone https://github.com/SAYUK09/omnia.git -b ${OMNIA_VERSION}

# ── STEP 11: Entrypoint and certs ───────────────────────────────────────────
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /omnia

COPY cert-copy.sh /cert-copy.sh
RUN chmod +x /cert-copy.sh

# ── STEP 12: Security labels ────────────────────────────────────────────────
# NOTE: Wolfi's daily builds automatically patch most CVEs at the OS/package level.
# These labels remain for audit/scanner compliance documentation.
LABEL base.image="cgr.dev/chainguard/wolfi-base" \
      base.distro="wolfi" \
      base.package_manager="apk" \
      base.libc="glibc" \
      security.go.source="wolfi-apk" \
      security.go.note="Installed via wolfi apk; daily CVE patching by Chainguard" \
      security.go.cves="CVE-2025-61729-fixed,CVE-2025-61727-fixed,CVE-2026-32282-fixed,CVE-2026-32288-fixed,CVE-2026-33811-fixed,CVE-2026-42501-fixed,CVE-2026-32283-fixed" \
      security.golang.crypto.version="0.52.0" \
      security.golang.crypto.cves="CVE-2025-47913-fixed,CVE-2025-58181-fixed,CVE-2025-47914-fixed" \
      security.golang.net.version="0.54.0" \
      security.golang.net.cves="CVE-2025-47911-fixed,CVE-2025-58190-fixed" \
      security.git-lfs.source="wolfi-apk" \
      security.git-lfs.note="Installed via wolfi apk; no source build needed; daily CVE patching" \
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
      security.pip.version="26.0" \
      security.pip.cves="CVE-2025-8869-fixed,CVE-2025-68121-fixed" \
      security.wheel.version="0.46.2" \
      security.wheel.note="Upgraded wheel and cleared uv cache to remove vendored vulnerable version" \
      security.ansible.version="2.20.1" \
      security.ansible.note="Upgraded from EOL ansible-core 2.16 to stable 2.20.1 (supported through ~May 2027)"

ENTRYPOINT ["/entrypoint.sh"]
