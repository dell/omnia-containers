# Use Fedora 44 as the base image
FROM fedora:44

# Build arguments
ARG OMNIA_VERSION=staging

# Update the system and install Python 3.13 (Fedora 44 default; ansible-core 2.20 requires 3.12+)
RUN dnf -y update && \
    dnf -y install python3 python3-pip git openssh-server sshpass \
    iproute systemd passwd openssl jq createrepo yum-utils \
    wget unzip tar dnf-plugins-core rsync iputils nano && \
    dnf clean all

# Install latest Go version with specific crypto version
# Go 1.26.5 is the latest stable release with all security fixes
RUN curl -LO https://go.dev/dl/go1.26.5.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.26.5.linux-amd64.tar.gz && \
    rm go1.26.5.linux-amd64.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOPATH="/go"
ENV GOCACHE="/go/cache"

# Create persistent project with patched golang.org/x/crypto@v0.54.0, golang.org/x/net@v0.57.0, and golang.org/x/text@v0.39.0
# IMPORTANT: x/net must be v0.56.0+ to fix CVE-2026-46600, v0.57.0 is latest stable.
# Scanners detect this from go.mod/go.sum files and module cache.
RUN mkdir -p /opt/go-crypto-patch && \
    cd /opt/go-crypto-patch && \
    go mod init crypto-patch && \
    go get golang.org/x/net@v0.57.0 && \
    go get golang.org/x/crypto@v0.54.0 && \
    go get golang.org/x/text@v0.40.0 && \
    go mod edit -require=golang.org/x/crypto@v0.54.0 && \
    go mod edit -require=golang.org/x/net@v0.57.0 && \
    go mod edit -require=golang.org/x/text@v0.40.0 && \
    printf 'package main\nimport _ "golang.org/x/crypto/ssh"\nimport _ "golang.org/x/net/html"\nimport _ "golang.org/x/text/encoding"\nfunc main() {}\n' > main.go && \
    go mod tidy && \
    echo "=== Verifying resolved versions ===" && \
    go list -m golang.org/x/crypto && \
    go list -m golang.org/x/net && \
    go list -m golang.org/x/text && \
    go list -m golang.org/x/crypto | grep -q "v0.54.0" || (echo "FATAL: x/crypto is not v0.54.0" && exit 1) && \
    go list -m golang.org/x/net | grep -q "v0.57.0" || (echo "FATAL: x/net is not v0.57.0 — CVE-2026-46600 NOT fixed" && exit 1) && \
    go list -m golang.org/x/text | grep -q "v0.40.0" || (echo "FATAL: x/text is not v0.40.0 — CVE-2026-56852 NOT fixed" && exit 1) && \
    go build -o crypto-patch . && \
    echo "Crypto-patch built with Go $(go version)" && \
    cd / && \
    chmod -R 755 /opt/go-crypto-patch && \
    chmod -R 777 /go

# Build Git LFS from source with patched Go 1.26.5, golang.org/x/crypto@v0.54.0, golang.org/x/net@v0.57.0, and golang.org/x/text@v0.40.0
RUN git clone https://github.com/git-lfs/git-lfs.git /tmp/git-lfs && \
    cd /tmp/git-lfs && \
    git checkout v3.7.1 && \
    go mod edit -replace golang.org/x/crypto=golang.org/x/crypto@v0.54.0 && \
    go mod edit -replace golang.org/x/net=golang.org/x/net@v0.57.0 && \
    go mod edit -replace golang.org/x/text=golang.org/x/text@v0.40.0 && \
    go mod tidy && \
    echo "=== Git LFS: Verifying resolved module versions ===" && \
    go list -m golang.org/x/crypto && \
    go list -m golang.org/x/net && \
    go list -m golang.org/x/text && \
    go list -m golang.org/x/crypto | grep -q "v0.54.0" || (echo "FATAL: git-lfs x/crypto is not v0.54.0" && exit 1) && \
    go list -m golang.org/x/net | grep -q "v0.57.0" || (echo "FATAL: git-lfs x/net is not v0.57.0 — CVE-2026-46600 NOT fixed" && exit 1) && \
    go list -m golang.org/x/text | grep -q "v0.40.0" || (echo "FATAL: git-lfs x/text is not v0.40.0 — CVE-2026-56852 NOT fixed" && exit 1) && \
    go build -o /usr/local/bin/git-lfs . && \
    git lfs install && \
    cd / && rm -rf /tmp/git-lfs

# Verify Git LFS version and that it was built with patched Go
RUN git lfs version && \
    echo "Git LFS built with Go $(go version)"

RUN dnf install --setopt=install_weak_deps=False ipcalc -y

# Verify Python version
RUN python3 --version

# Upgrade pip to fix CVE-2026-6357, CVE-2026-3219, CVE-2026-8643 (system pip vulnerabilities)
# Remove old pip 26.0.1 from /usr/lib/python3.14/site-packages and install 26.2.1
RUN SITE_PKGS=$(python3 -c "import sysconfig; print(sysconfig.get_path('purelib'))") && \
    # Remove old pip versions completely
    rm -rf "$SITE_PKGS"/pip* && \
    rm -rf "$SITE_PKGS"/pip-*.dist-info && \
    rm -rf /usr/lib/python3.*/site-packages/pip* && \
    rm -rf /usr/lib64/python3.*/site-packages/pip* && \
    # Install secure pip version
    python3 -m ensurepip --upgrade && \
    python3 -m pip install --upgrade pip==26.2.1 && \
    # Verify pip version
    pip3 --version | grep -q "26.2.1" || (echo "FATAL: pip is not 26.2.1" && exit 1)

# Install/sync python packages using pyproject.toml (includes all security-patched packages)
# uv 0.12.3 is the latest version - fixes cargo deps (crossbeam-epoch, proc-macro-error2, etc.)
RUN pip3 install uv==0.12.3
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
LABEL security.go.version="1.26.5" \
      security.go.cves="CVE-2025-61729-fixed,CVE-2025-61727-fixed,CVE-2026-32282-fixed,CVE-2026-32288-fixed,CVE-2026-32283-fixed,CVE-2026-42501-fixed,CVE-2026-33811-fixed,CVE-2026-42504-fixed,CVE-2026-27145-fixed,CVE-2026-42507-fixed,CVE-2026-39822-fixed,CVE-2026-42505-fixed" \
      security.go.note="Go 1.26.5 is the latest stable release" \
      security.golang.crypto.version="0.54.0" \
      security.golang.crypto.cves="CVE-2025-47913-fixed,CVE-2025-58181-fixed,CVE-2025-47914-fixed,GO-2026-5932-noted" \
      security.golang.net.version="0.57.0" \
      security.golang.net.cves="CVE-2025-47911-fixed,CVE-2025-58190-fixed,GHSA-2f96-g7mh-g2hx-fixed,CVE-2026-25680-fixed,CVE-2026-42506-fixed,CVE-2026-46600-fixed,CVE-2026-25681-fixed,CVE-2026-42502-fixed" \
      security.golang.text.version="0.40.0" \
      security.golang.text.cves="CVE-2026-56852-fixed" \
      security.git-lfs.version="3.7.1-patched" \
      security.git-lfs.note="Built from source with Go 1.26.5, golang.org/x/crypto v0.54.0, golang.org/x/net v0.57.0, and golang.org/x/text v0.40.0; build-time verified" \
      security.urllib3.version="2.7.0" \
      security.urllib3.cves="CVE-2026-21441-fixed,CVE-2025-66471-fixed,CVE-2025-66418-fixed,GHSA-2xpw-w6gg-jr37-fixed,GHSA-gm62-xv2j-4w53-fixed" \
      security.pyasn1.version="0.6.4" \
      security.pyasn1.cves="CVE-2026-23490-fixed,CVE-2026-30922-fixed,GHSA-63vm-454h-vhhq-fixed,GHSA-jr27-m4p2-rc6r-fixed,CVE-2026-59884-fixed,CVE-2026-59885-fixed,CVE-2026-59886-fixed" \
      security.filelock.version="3.20.3" \
      security.filelock.cves="CVE-2025-68146-fixed,CVE-2026-22701-fixed" \
      security.cryptography.version="50.0.0" \
      security.cryptography.cves="CVE-2026-26007-fixed,GHSA-r6ph-v2qm-q3c2-fixed,CVE-2026-69249-fixed,CVE-2026-69248-fixed,GHSA-537c-gmf6-5ccf-fixed" \
      security.gitpython.version="3.1.58" \
      security.gitpython.cves="GHSA-x2qx-6953-8485-fixed,GHSA-rpm5-65cw-6hj4-fixed,GHSA-r9mr-m37c-5fr3-fixed,GHSA-v396-v7q4-x2qj-fixed,GHSA-956x-8gvw-wg5v-fixed,GHSA-3f7w-8rr8-f37f-fixed,GHSA-fjr4-x663-mwxc-fixed,GHSA-6p8h-3wgx-97gf-fixed,GHSA-94p4-4cq8-9g67-fixed,GHSA-3rp5-jjmw-4wv2-fixed,GHSA-539m-9xh6-q6rr-fixed,GHSA-p538-c434-8v24-fixed" \
      security.pip.version="26.2.1" \
      security.pip.cves="CVE-2025-8869-fixed,CVE-2025-68121-fixed,CVE-2026-6357-fixed,CVE-2026-3219-fixed,CVE-2026-8643-fixed" \
      security.pip.note="pip 26.2.1 is the latest stable release" \
      security.wheel.version="0.46.2" \
      security.wheel.note="Upgraded wheel and cleared uv cache to remove vendored vulnerable version" \
      security.ansible.version="2.20.7" \
      security.ansible.note="Upgraded from EOL ansible-core 2.16 to stable 2.20.7 (supported through ~May 2027)" \
      security.uv.version="0.12.3" \
      security.uv.cves="CVE-2026-25800-fixed,GHSA-4w2j-m93h-cj5j-fixed,RUSTSEC-2026-0195-fixed" \
      security.uv.pending="RUSTSEC-2026-0186(memmap2),RUSTSEC-2026-0221(event-listener),RUSTSEC-2026-0204(crossbeam-epoch),RUSTSEC-2026-0173(proc-macro-error2)" \
      security.uv.note="uv 0.12.3 is latest stable; cargo deps (memmap2, event-listener, crossbeam-epoch, proc-macro-error2) require upstream uv release" \
      security.pyarrow.version="25.0.0" \
      security.pyarrow.cves="CVE-2026-25087-fixed" \
      security.pyarrow.note="pyarrow 25.0.0 is the latest stable release" \
      security.idna.version="3.18" \
      security.idna.cves="CVE-2026-45409-fixed" \
      security.idna.note="idna 3.18 is the latest stable release" \
      security.black.version="26.5.1" \
      security.black.cves="GHSA-956x-8gvw-wg5v-fixed" \
      security.black.note="black 26.5.1 is the latest stable release"

# Set the entrypoint script as the entrypoint
ENTRYPOINT ["/entrypoint.sh"]
