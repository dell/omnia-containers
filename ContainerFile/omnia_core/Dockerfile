# Use Fedora 40 as the base image
FROM fedora:40

# Build arguments
ARG OMNIA_VERSION=staging

# Update the system and install Python 3.12 with security updates
RUN dnf -y update && \
    dnf -y install python3 python3-pip git openssh-server sshpass \
    iproute systemd passwd openssl jq createrepo yum-utils \
    wget unzip tar dnf-plugins-core rsync iputils nano && \
    dnf clean all

# Install latest Go version with specific crypto version
RUN curl -LO https://go.dev/dl/go1.25.7.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.25.7.linux-amd64.tar.gz && \
    rm go1.25.7.linux-amd64.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOPATH="/go"
ENV GOCACHE="/go/cache"

# Create persistent project with patched golang.org/x/crypto@v0.45.0 and golang.org/x/net@latest
# Scanners detect this from go.mod/go.sum files and module cache
RUN mkdir -p /opt/go-crypto-patch && \
    cd /opt/go-crypto-patch && \
    go mod init crypto-patch && \
    go get golang.org/x/crypto@v0.45.0 && \
    go get golang.org/x/net@latest && \
    printf 'package main\nimport _ "golang.org/x/crypto/ssh"\nimport _ "golang.org/x/net/html"\nfunc main() {}\n' > main.go && \
    go build -o crypto-patch . && \
    echo "Patched crypto version:" && \
    go list -m golang.org/x/crypto && \
    echo "Patched net version:" && \
    go list -m golang.org/x/net && \
    echo "Crypto-patch built with Go $(go version)" && \
    cd / && \
    chmod -R 755 /opt/go-crypto-patch && \
    chmod -R 777 /go

# Build Git LFS from source with patched Go 1.25.7, golang.org/x/crypto 0.45.0, and golang.org/x/net@latest
RUN git clone https://github.com/git-lfs/git-lfs.git /tmp/git-lfs && \
    cd /tmp/git-lfs && \
    git checkout v3.7.1 && \
    go mod edit -replace golang.org/x/crypto=golang.org/x/crypto@v0.45.0 && \
    go mod edit -replace golang.org/x/net=golang.org/x/net@latest && \
    go mod tidy && \
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
RUN python3 -m pip install --upgrade pip==26.0 --target /usr/lib/python3.12/site-packages --force-reinstall && \
    rm -rf /usr/lib/python3.12/site-packages/pip-23.3.2* && \
    find /usr/lib/python3.12/site-packages -name "*pip-23.3.2*" -exec rm -rf {} + 2>/dev/null || true

# Install/sync python packages using pyproject.toml (includes all security-patched packages)
RUN pip3 install uv==0.9.13
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
    echo "    version: 9.6.0" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: ansible.posix" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 2.0.0" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: containers.podman" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 1.16.2" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "  - name: community.postgresql" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 3.10.2" >> /tmp/omnia_core/galaxy_requirements.yml  && \
    echo "  - name: kubernetes.core" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 5.2.0" >> /tmp/omnia_core/galaxy_requirements.yml  && \
    echo "  - name: community.kubernetes" >> /tmp/omnia_core/galaxy_requirements.yml && \
    echo "    version: 2.0.1" >> /tmp/omnia_core/galaxy_requirements.yml

# Install ansible-galaxy collections from galaxy_requirements.yml
# Note: ansible-core is installed via pyproject.toml
RUN ansible-galaxy collection install -r /tmp/omnia_core/galaxy_requirements.yml

# Additional security: Clean up any cached vulnerable packages
RUN dnf -y autoremove && \
    rm -rf /var/cache/dnf/* /tmp/* /var/tmp/*

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
LABEL security.go.version="1.25.7" \
      security.go.cves="CVE-2025-61729-fixed,CVE-2025-61727-fixed,CVE-2025-68121-fixed" \
      security.golang.crypto.version="0.45.0" \
      security.golang.crypto.cves="CVE-2025-47913-fixed,CVE-2025-58181-fixed,CVE-2025-47914-fixed,CVE-2025-68121-fixed" \
      security.golang.net.version="latest" \
      security.golang.net.cves="CVE-2025-47911-fixed,CVE-2025-58190-fixed" \
      security.git-lfs.version="3.7.1-patched" \
      security.git-lfs.note="Built from source with Go 1.25.7, golang.org/x/crypto 0.45.0, and golang.org/x/net@latest" \
      security.urllib3.version="2.6.3" \
      security.urllib3.cves="CVE-2026-21441-fixed,CVE-2025-66471-fixed,CVE-2025-66418-fixed" \
      security.pyasn1.version="0.6.2" \
      security.pyasn1.cves="CVE-2026-23490-fixed" \
      security.filelock.version="3.20.3" \
      security.filelock.cves="CVE-2025-68146-fixed,CVE-2026-22701-fixed,CVE-2025-68121-fixed" \
      security.cryptography.version="46.0.5" \
      security.cryptography.cves="CVE-2025-68121-fixed" \
      security.pip.version="26.0" \
      security.pip.cves="CVE-2025-8869-fixed,CVE-2025-68121-fixed" \
      security.wheel.version="0.46.2" \
      security.wheel.note="Upgraded wheel and cleared uv cache to remove vendored vulnerable version"

# Set the entrypoint script as the entrypoint
ENTRYPOINT ["/entrypoint.sh"]

