FROM docker.io/library/almalinux:10.0

RUN dnf clean all && \
    dnf update -y --releasever=10.0 --nogpgcheck && \
    dnf install -y dnf-plugins-core epel-release && \
    dnf config-manager -y --set-enabled crb && \
    dnf clean all

RUN dnf install -y \
        bash \
        buildah \
        python3.12 \
        python3.12-pip \
        fuse-overlayfs \
        tar \
        squashfs-tools \
        fuse-overlayfs

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY src/ /usr/local/bin/
RUN chmod -R 0755 /usr/local/bin/

# Allow non-root to run buildah commands
RUN setcap cap_setuid=ep "$(command -v newuidmap)" && \
    setcap cap_setgid=ep "$(command -v newgidmap)" &&\
    chmod 0755 "$(command -v newuidmap)" && \
    chmod 0755 "$(command -v newgidmap)" && \
    rpm --restore shadow-utils && \
    echo "builder:2000:50000" > /etc/subuid && \
    echo "builder:2000:50000" > /etc/subgid

# Create local user for rootless image builds
RUN useradd --uid 1002 builder && \
    chown -R builder /home/builder

# Make builder the default user when running container
USER builder
WORKDIR /home/builder

ENV BUILDAH_ISOLATION=chroot

ENTRYPOINT ["/usr/bin/buildah", "unshare"]
