# Dockerfile for Omnia-Kubespray container
FROM fedora:40

# Set environment variables
ENV LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1

# Build arguments
ARG KUBESPRAY_VERSION
ARG SSH_PORT

# Install necessary system packages
RUN dnf makecache -y \
    && dnf install -y \
    bash \
    systemd \
    curl \
    python3-pip \
    git \
    rsync \
    openssh-server \
    iproute \
    && dnf clean all

# Create a virtual environment for Python packages
RUN python3 -m venv /venv

# Ensure pip uses the virtual environment
ENV PATH="/venv/bin:$PATH"

RUN python3 -m ensurepip
RUN mkdir -p /tmp/kubespray
RUN mkdir -p /opt/omnia

# Fetch the pip requirements file dynamically from GitHub based on Kubespray version
RUN curl -L "https://raw.githubusercontent.com/kubernetes-sigs/kubespray/refs/tags/${KUBESPRAY_VERSION}/requirements.txt" -o /tmp/kubespray/pip_requirements.txt

# Add distlib and set cryptography version
RUN echo "distlib" >> /tmp/kubespray/pip_requirements.txt && \
    sed -i '/cryptography/d' /tmp/kubespray/pip_requirements.txt && \
    echo "cryptography==44.0.1" >> /tmp/kubespray/pip_requirements.txt

# Install Python dependencies from the fetched requirements file
RUN pip3 install --no-cache-dir -r /tmp/kubespray/pip_requirements.txt \
    && find /usr -type d -name '*__pycache__' -prune -exec rm -rf {} \;

# Install/sync python packages using the uv.lock
RUN pip3 install uv
COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT="/usr"
RUN uv sync --locked --inexact

# Dynamically create the Ansible Galaxy requirements file
RUN echo "collections:" > /tmp/kubespray/galaxy_requirements.yml && \
    echo "  - name: kubernetes.core" >> /tmp/kubespray/galaxy_requirements.yml && \
    echo "    version: 5.0.0" >> /tmp/kubespray/galaxy_requirements.yml && \
    echo "  - name: https://github.com/kubernetes-sigs/kubespray" >> /tmp/kubespray/galaxy_requirements.yml && \
    echo "    type: git" >>/tmp/kubespray/galaxy_requirements.yml && \
    echo "    version: ${KUBESPRAY_VERSION}" >> /tmp/kubespray/galaxy_requirements.yml

# Install Ansible Galaxy collections
RUN ansible-galaxy install -r /tmp/kubespray/galaxy_requirements.yml

# Configure SSHD
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config

RUN sed -i "s/^#Port 22/Port ${SSH_PORT}/" /etc/ssh/sshd_config

# Copy the entrypoint script to / and make it executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set the entrypoint script as the entrypoint
ENTRYPOINT ["/entrypoint.sh"]
