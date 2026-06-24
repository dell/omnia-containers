# Use Fedora 42 as the base image
FROM fedora:42

# Build arguments
ARG OMNIA_VERSION=staging

# Update the system and install Python 3.13 (Fedora 42 default; ansible-core 2.20 requires 3.12+)
RUN dnf -y update && \
    dnf -y install python3 python3-pip git openssh-server sshpass \
    iproute systemd passwd openssl jq createrepo yum-utils \
    wget unzip tar dnf-plugins-core rsync iputils nano && \
    dnf clean all

# Install latest Go version with specific crypto version
RUN curl -LO https://go.dev/dl/go1.25.10.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.25.10.linux-amd64.tar.gz && \
    rm go1.25.10.linux-amd64.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOPATH="/go"
ENV GOCACHE="/go/cache"

# Create persistent project with patched golang.org/x/crypto@v0.52.0 and golang.org/x/net@v0.54.0
# IMPORTANT: x/net must be v0.54.0+ to avoid Go module resolver downgrading x/crypto.
# Scanners detect this from go.mod/go.sum files and module cache.
RUN mkdir -p /opt/go-crypto-patch && \
    cd /opt/go-crypto-patch && \
    go mod init crypto-patch && \
    go get golang.org/x/net@v0.54.0 && \
    go get golang.org/x/crypto@v0.52.0 && \
    go mod edit -require=golang.org/x/crypto@v0.52.0 && \
    go mod edit -require=golang.org/x/net@v0.54.0 && \
    printf 'package main\nimport _ "golang.org/x/crypto/ssh"\nimport _ "golang.org/x/net/html"\nfunc main() {}\n' > main.go && \
    go mod tidy && \
    echo "=== Verifying resolved versions ===" && \
    go list -m golang.org/x/crypto && \
    go list -m golang.org/x/net && \
    go list -m golang.org/x/crypto | grep -q "v0.52.0" || (echo "FATAL: x/crypto downgraded below v0.52.0 — CVE-2025-58181 and CVE-2025-47914 NOT fixed" && exit 1) && \
    go list -m golang.org/x/net | grep -q "v0.54.0" || (echo "FATAL: x/net is not v0.54.0" && exit 1) && \
    go build -o crypto-patch . && \
    echo "Crypto-patch built with Go $(go version)" && \
    cd / && \
    chmod -R 755 /opt/go-crypto-patch && \
    chmod -R 777 /go

# Build Git LFS from source with patched Go 1.25.10, golang.org/x/crypto@v0.52.0, and golang.org/x/net@v0.54.0
RUN git clone https://github.com/git-lfs/git-lfs.git /tmp/git-lfs && \
    cd /tmp/git-lfs && \
    git checkout v3.7.1 && \
    go mod edit -replace golang.org/x/crypto=golang.org/x/crypto@v0.52.0 && \
    go mod edit -replace golang.org/x/net=golang.org/x/net@v0.54.0 && \
    go mod tidy && \
    echo "=== Git LFS: Verifying resolved module versions ===" && \
    go list -m golang.org/x/crypto && \
    go list -m golang.org/x/net && \
    go list -m golang.org/x/crypto | grep -q "v0.52.0" || (echo "FATAL: git-lfs x/crypto downgraded below v0.52.0 — CVE-2025-58181 and CVE-2025-47914 NOT fixed" && exit 1) && \
    go list -m golang.org/x/net | grep -q "v0.54.0" || (echo "FATAL: git-lfs x/net is not v0.54.0" && exit 1) && \
    go build -o /usr/local/bin/git-lfs . && \
    git lfs install && \
    cd / && rm -rf /tmp/git-lfs

# Verify Git LFS version and that it was built with patched Go
RUN git lfs version && \
    echo "Git LFS built with Go $(go version)"

RUN dnf install --setopt=install_weak_deps=False ipcalc -y

# Verify Python version
RUN python3 --version

# Upgrade pip to fix CVE-2025-8869 and CVE-2025-68121 (system pip vulnerability)
# Use dynamic site-packages detection (Fedora 42 ships Python 3.13)
RUN SITE_PKGS=$(python3 -c "import sysconfig; print(sysconfig.get_path('purelib'))") && \
    python3 -m pip install --upgrade pip==26.0 --target "$SITE_PKGS" --force-reinstall && \
    find "$SITE_PKGS" -name "pip-23.*" -exec rm -rf {} + 2>/dev/null || true

# Install/sync python packages using pyproject.toml (includes all security-patched packages)
RUN pip3 install uv==0.11.15
COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT="/usr"
RUN uv lock && uv sync && \
    rm -rf /root/.cache/uv /root/.cache/pip

# Allow root login by enabling it in the SSH configuration
RUN sed -i 's/^#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Expose port 22 for SSH
RUN sed -i 's/^#Port 22/Port 2222/' /etc/ssh/sshd_config
EXPOSE 2222

# Generate host keys if they don't exist
RUN ssh-keygen -A

# Configure workdir for ssh
RUN echo "cd /omnia" >> /root/.bashrc

# Create the /tmp/omnia_core directory
RUN mkdir -p /tmp/omnia_core

# Create the pulp config directory
RUN mkdir -p /root/.config/pulp

# Dynamically create the Ansible Galaxy requirements file
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
    echo "    version: 3.10.2" >> /tmp/omnia_core/galaxy_requirements.yml  && \
    echo "  - name: kubernetes.core" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 5.2.0" >> /tmp/omnia_core/galaxy_requirements.yml  && \
    echo "  # community.kubernetes removed — deprecated, use kubernetes.core instead" >> /tmp/omnia_core/galaxy_requirements.yml

# Install ansible-galaxy collections from galaxy_requirements.yml
# Note: ansible-core is installed via pyproject.toml
RUN ansible-galaxy collection install -r /tmp/omnia_core/galaxy_requirements.yml

# Additional security: Clean up any cached vulnerable packages
RUN dnf -y autoremove && \
    rm -rf /var/cache/dnf/* /tmp/* /var/tmp/* && \
    # Secure permissions on sensitive directories
    chmod 600 /root/.ssh/* 2>/dev/null || true && \
    chmod 700 /root/.ssh 2>/dev/null || true

# Git clone omnia repository
RUN git clone https://github.com/dell/omnia.git -b ${OMNIA_VERSION}

# Copy the entrypoint script to / and make it executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Configure workdir for podman
WORKDIR /omnia

# Copy pulp certificate to core container's trust
COPY cert-copy.sh /cert-copy.sh
RUN chmod +x /cert-copy.sh

# Document security patches applied
LABEL security.go.version="1.25.10" \
      security.go.cves="CVE-2025-61729-fixed,CVE-2025-61727-fixed,CVE-2026-32282-fixed,CVE-2026-32288-fixed,CVE-2026-32283-fixed,CVE-2026-42501-fixed,CVE-2026-33811-fixed" \
      security.golang.crypto.version="0.52.0" \
      security.golang.crypto.cves="CVE-2025-47913-fixed,CVE-2025-58181-fixed,CVE-2025-47914-fixed" \
      security.golang.net.version="0.54.0" \
      security.golang.net.cves="CVE-2025-47911-fixed,CVE-2025-58190-fixed" \
      security.git-lfs.version="3.7.1-patched" \
      security.git-lfs.note="Built from source with Go 1.25.10, golang.org/x/crypto v0.52.0, and golang.org/x/net v0.54.0; build-time verified" \
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
      security.ansible.version="2.20.7" \
      security.ansible.note="Upgraded from EOL ansible-core 2.16 to stable 2.20.7 (supported through ~May 2027)"

# Set the entrypoint script as the entrypoint
ENTRYPOINT ["/entrypoint.sh"]
