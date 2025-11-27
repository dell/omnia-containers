ARG fedora_version=38
FROM  fedora:${fedora_version}

LABEL MAINTAINER="Dell Omnia Team"

ARG xcat_version=2.17
ARG xcat_repo_root=https://xcat.org/files/xcat/repos/yum
ARG xcat_baseos=rh9

# Update and install necessary dependencies
RUN dnf makecache -y \
    && dnf install -y \
    hostname \
    openssl \
    systemd \
    patch \
    wget \
    initscripts \
    iputils \
    && dnf clean all

# Install ipcalc
RUN dnf install --setopt=install_weak_deps=False ipcalc -y

# Install dependencies and Python
RUN dnf install -y python3.11 python3.11-pip python3-devel gcc \
    && dnf clean all

# Install/sync python packages using the uv.lock
RUN pip3 install uv==0.9.13
COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT="/usr"
RUN uv sync --locked

# Configure systemd
RUN (cd /lib/systemd/system/sysinit.target.wants/ \
    && for i in *; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done) \
    && rm -f /lib/systemd/system/multi-user.target.wants/* \
    && rm -f /etc/systemd/system/*.wants/* \
    && rm -f /lib/systemd/system/local-fs.target.wants/* \
    && rm -f /lib/systemd/system/sockets.target.wants/*udev* \
    && rm -f /lib/systemd/system/sockets.target.wants/*initctl* \
    && rm -f /lib/systemd/system/basic.target.wants/* \
    && rm -f /lib/systemd/system/anaconda.target.wants/*

# Set up xCAT data directories
RUN mkdir -p /xcatdata/etc/{dhcp,goconserver,xcat} && ln -sf -t /etc /xcatdata/etc/{dhcp,goconserver,xcat} && \
    mkdir -p /install/postscripts/ && mkdir -p /root/.ssh && ln -sf /root/.ssh /install/postscripts/_ssh

RUN dnf install -y -q wget which \
    && wget  https://xcat.org/files/xcat/repos/yum/2.17/xcat-core/xcat-core.repo -O /etc/yum.repos.d/xcat-core.repo \
    && wget https://xcat.org/files/xcat/repos/yum/2.17/xcat-dep/rh9/x86_64/xcat-dep.repo -O /etc/yum.repos.d/xcat-dep.repo \
    && dnf install -y \
    bind-utils \
    xCAT \
    openssh-server \
    rsyslog \
    createrepo \
    chrony \
    man \
    nano \
    pigz \
    bash-completion \
    vim \
    iproute \
    sshpass \
    && dnf clean all

RUN dnf install -y postgresql*.$(uname -m)
RUN dnf install -y perl-DBD-Pg

RUN sed -i -e 's|#PermitRootLogin yes|PermitRootLogin yes|g' \
    -e 's|#Port 22|Port 2223|g' /etc/ssh/sshd_config \
    && echo "StrictHostKeyChecking no" >> /etc/ssh/ssh_config \
    && rm -rf /root/.ssh \
    && mv /xcatdata /xcatdata.NEEDINIT \
    && mv /install /xcatdata.install \
    && mv /tftpboot /xcatdata.tftpboot

# Define environment variables for Genesis tarball and directory
ENV GENESIS_TAR_URL="https://github.com/dell/omnia/raw/refs/heads/main/prepare_oim/roles/install_xcat/redhat/files/xcat-genesis-base-x86_64.tar.gz" \
    GENESIS_DIR="/opt/xcat-genesis"

# Download and extract genesis tarball
RUN wget -O /tmp/genesis.tar.gz "$GENESIS_TAR_URL" && \
    mkdir -p "$GENESIS_DIR" && \
    tar -xzf /tmp/genesis.tar.gz -C "$GENESIS_DIR" && \
    rm -f /tmp/genesis.tar.gz


# Verify, remove, and install xCAT Genesis RPM if needed
RUN genesis_rpm=$(ls "$GENESIS_DIR"/*.rpm | head -n 1 | xargs -n1 basename) && \
    rpm_output=$(rpm -qa | grep xCAT-genesis-base-x86_64) && \
    if echo "$rpm_output" | grep -q "$genesis_rpm"; then \
        echo "xCAT-genesis-base-x86_64 version ${xcat_version} is already installed"; \
    else \
        echo "xCAT-genesis-base-x86_64 version ${xcat_version} is not installed. Replacing with new version."; \
        [ -n "$rpm_output" ] && rpm -e --nodeps "$rpm_output"; \
        dnf install -y "$GENESIS_DIR"/*.rpm --nogpgcheck; \
    fi


COPY pgsqlsetup.patch ddns.patch configeth.patch /patch/
COPY xcat-init.bash /xcat-init.bash
COPY xcat-init.service /etc/systemd/system/xcat-init.service
COPY temp_ks_rhel8.tmpl /opt/xcat/share/xcat/install/rh/compute.rhels8.tmpl
COPY temp_ks_rhel9.tmpl /opt/xcat/share/xcat/install/rh/compute.rhels9.tmpl
COPY temp_pre_rhel8 /opt/xcat/share/xcat/install/scripts/pre.rhels8
COPY temp_post_rhel8 /opt/xcat/share/xcat/install/scripts/post.rhels8
COPY temp_rhel8.pkglist /opt/xcat/share/xcat/install/rh/compute.rhels8.pkglist
COPY 01-receiver.conf /etc/rsyslog.d/01-receiver.conf

RUN chmod 700 /xcat-init.bash
RUN chmod 0644 /opt/xcat/share/xcat/install/rh/compute.rhels8.tmpl
RUN chmod 0644 /opt/xcat/share/xcat/install/rh/compute.rhels9.tmpl
RUN chmod 0644 /opt/xcat/share/xcat/install/scripts/pre.rhels8
RUN chmod 0644 /opt/xcat/share/xcat/install/scripts/post.rhels8
RUN chmod 0644 /opt/xcat/share/xcat/install/rh/compute.rhels8.pkglist

RUN mkdir -p /etc/systemd/system/postgresql.service.d && \
    chmod 0755 /etc/systemd/system/postgresql.service.d
COPY postgresql.conf /etc/systemd/system/postgresql.service.d/postgresql.conf

COPY omnia.service /etc/systemd/system/omnia.service

RUN systemctl enable httpd \
    && systemctl enable sshd \
    && systemctl enable dhcpd \
    && systemctl enable rsyslog \
    && systemctl enable xcatd \
    && systemctl enable xcat-init \
    && systemctl enable omnia

ENV XCATROOT /opt/xcat
ENV PATH="$XCATROOT/bin:$XCATROOT/sbin:$XCATROOT/share/xcat/tools:$PATH" MANPATH="$XCATROOT/share/man:$MANPATH"
VOLUME ["/xcatdata", "/var/log/xcat"]

ENTRYPOINT ["/usr/sbin/init"]
