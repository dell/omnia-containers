FROM fedora:38

# Configure DNF for security and performance
RUN echo -e 'install_weak_deps=False\n\
assumeyes=True' >> /etc/dnf/dnf.conf

# Disable cisco openh264 repo and update system
RUN sed -i 's/enabled=1/enabled=0/g' /etc/yum.repos.d/fedora-cisco-openh264.repo && \
    dnf update --security && \
    dnf -y upgrade --refresh && \
    dnf -y install \
        passwd \
        pcs \
        which \
        podman \
        openssh-clients && \
    dnf clean all

RUN sed -i '/^\[engine\]$/a remote = true' /usr/share/containers/containers.conf
RUN sed -i 's/ocf_run podman rm --storage $CONTAINER/ocf_run podman rm $CONTAINER/g' /usr/lib/ocf/resource.d/heartbeat/podman
RUN mkdir -p /var/log/cluster
COPY remote-xcatd-check /usr/lib/ocf/resource.d/heartbeat/xcatd-remote-check
RUN chmod +x /usr/lib/ocf/resource.d/heartbeat/xcatd-remote-check

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set the entrypoint script as the entrypoint
ENTRYPOINT ["/entrypoint.sh"]