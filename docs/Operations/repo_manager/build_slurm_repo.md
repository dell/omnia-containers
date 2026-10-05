# Build Slurm Repository

Build Slurm 25.05 RPMs from source for use with Omnia. This guide covers
building on both x86_64 and aarch64 hosts, with and without GPU support.

!!! important
    This page describes a recommended workflow for building Slurm RPMs. Slurm RPMs should be built from source following the official Slurm build and packaging documentation. The steps in this guide are provided for convenience and can be customized as needed for your environment.

## Overview

Omnia requires a user-built Slurm RPM repository. Build the RPMs on a host
running the same RHEL 10 minor release and architecture as the target cluster
nodes, then host them on an HTTP server accessible from the OIM.

!!! important
    Slurm must be compiled **without** UCX support. DOCA-OFED provides
    its own UCX and OpenMPI stack.

## Prerequisites

### x86_64

- A RHEL 10.0 x86_64 build host with internet access.
- If using RHEL subscription, enable the required repositories:

    ```bash title="Run on: x86_64 build host"
    subscription-manager repos --enable rhel-10-for-x86_64-baseos-rpms
    subscription-manager repos --enable rhel-10-for-x86_64-appstream-rpms
    subscription-manager repos --enable codeready-builder-for-rhel-10-x86_64-rpms
    ```

### aarch64

- A RHEL 10.0 aarch64 build host with a free PXE IP address assigned.
- If the aarch64 host does not have internet access, enable network
  masquerading on the OIM to provide connectivity:

    ```bash title="Run on: OIM host"
      #!/bin/bash

      echo "=== Enable MASQUERADE (Internet Sharing) ==="
      echo

      read -p "Enter INTERNET interface name " WAN
      read -p "Enter PXE interface name " LAN

      echo
      echo "WAN interface : $WAN"
      echo "LAN interface : $LAN"
      echo

      # Enable IP forwarding
      echo "[*] Enabling IP forwarding..."
      echo 1 > /proc/sys/net/ipv4/ip_forward

      # Add NAT rule
      echo "[*] Adding MASQUERADE rule..."
      iptables -t nat -A POSTROUTING -o "$WAN" -j MASQUERADE

      # Add forward rules
      echo "[*] Allowing forwarding..."
      iptables -A FORWARD -i "$LAN" -o "$WAN" -j ACCEPT
      iptables -A FORWARD -i "$WAN" -o "$LAN" -m state --state RELATED,ESTABLISHED -j ACCEPT

      echo
      echo "✔ MASQUERADE enabled successfully"
      echo "✔ $LAN can now access internet via $WAN"
    ```

- If using RHEL subscription, enable the required repositories:

    ```bash title="Run on: aarch64 build host"
    subscription-manager repos --enable rhel-10-for-aarch64-baseos-rpms
    subscription-manager repos --enable rhel-10-for-aarch64-appstream-rpms
    subscription-manager repos --enable codeready-builder-for-rhel-10-aarch64-rpms
    ```

## Procedure

### Build Without GPU Support

1. **Install build dependencies**:

    ```bash title="Run on: build host"
    dnf install -y \
      wget git make gcc gcc-c++ rpm-build autoconf automake \
      python3 python3-devel perl perl-devel \
      readline-devel zlib-devel pam-devel dbus-devel \
      hwloc-devel libbpf-devel \
      pmix pmix-devel \
      jansson-devel \
      json-c json-c-devel \
      libyaml libyaml-devel \
      openssl-devel \
      mariadb-devel systemd-devel \
      munge munge-devel
    ```

2. **Download the Slurm source tarball**:

    ```bash title="Run on: build host"
    wget https://download.schedmd.com/slurm/slurm-25.05.2.tar.bz2
    ```

3. **Build the RPMs**:

    ```bash title="Run on: build host"
    rpmbuild -ta slurm-25.05.2.tar.bz2 \
      --with pmix \
      --define "with_pmix --with-pmix=/usr" \
      --with yaml \
      --define "with_yaml --with-yaml" \
      --without hdf5 \
      --define "without_hdf5 --without-hdf5" \
      --without nvml \
      --define "_without_nvml --without-nvml=/usr/local/cuda" \
      --without ucx \
      --define "without_ucx --without-ucx"
    ```

    After the build completes, RPMs are available at
    `/root/rpmbuild/RPMS/x86_64/` or `/root/rpmbuild/RPMS/aarch64/`.

### Build With GPU Support

1. **Install build dependencies** (same as above):

    ```bash title="Run on: build host"
    dnf install -y \
      wget git make gcc gcc-c++ rpm-build autoconf automake \
      python3 python3-devel perl perl-devel \
      readline-devel zlib-devel pam-devel dbus-devel \
      hwloc-devel libbpf-devel \
      pmix pmix-devel \
      jansson-devel \
      json-c json-c-devel \
      libyaml libyaml-devel \
      openssl-devel \
      mariadb-devel systemd-devel \
      munge munge-devel
    ```

2. **Download the Slurm source tarball**:

    ```bash title="Run on: build host"
    wget https://download.schedmd.com/slurm/slurm-25.05.2.tar.bz2
    ```

3. **Download and install the CUDA toolkit**:

    For x86_64:

    ```bash title="Run on: x86_64 build host"
    wget https://developer.download.nvidia.com/compute/cuda/13.0.2/local_installers/cuda_13.0.2_580.95.05_linux.run
    bash cuda_13.0.2_580.95.05_linux.run --silent --toolkit --toolkitpath=/usr/local/cuda --override
    ```

    For aarch64:

    ```bash title="Run on: aarch64 build host"
    wget https://developer.download.nvidia.com/compute/cuda/13.1.0/local_installers/cuda_13.1.0_590.44.01_linux_sbsa.run
    bash cuda_13.1.0_590.44.01_linux_sbsa.run --silent --toolkit --toolkitpath=/usr/local/cuda --override
    ```

4. **Build the RPMs**:

    ```bash title="Run on: build host"
    rpmbuild -ta slurm-25.05.2.tar.bz2 \
      --with pmix \
      --define "with_pmix --with-pmix=/usr" \
      --with yaml \
      --define "with_yaml --with-yaml" \
      --without hdf5 \
      --define "without_hdf5 --without-hdf5" \
      --with nvml \
      --define "_with_nvml --with-nvml=/usr/local/cuda" \
      --without ucx \
      --define "without_ucx --without-ucx"
    ```

    After the build completes, RPMs are available at
    `/root/rpmbuild/RPMS/x86_64/` or `/root/rpmbuild/RPMS/aarch64/`.

## Verification

1. **Verify the build** by installing the base RPMs:

    For x86_64:

    ```bash title="Run on: x86_64 build host"
    sudo rpm -ivh /root/rpmbuild/RPMS/x86_64/slurm-25.05.2-1*.x86_64.rpm \
      /root/rpmbuild/RPMS/x86_64/slurm-slurmd-25.05.2-1*.x86_64.rpm
    ```

    For aarch64:

    ```bash title="Run on: aarch64 build host"
    sudo rpm -ivh /root/rpmbuild/RPMS/aarch64/slurm-25.05.2-1*.aarch64.rpm \
      /root/rpmbuild/RPMS/aarch64/slurm-slurmd-25.05.2-1*.aarch64.rpm
    ```

2. **Verify required shared libraries are present**:

    - For builds without GPU: all required `.so` and `cgroup_v2.so`
      files should be available.
    - For builds with GPU: `gpu_nvml.so` should also be available.

3. **Remove the test packages** after verification:

    ```bash title="Run on: build host"
    sudo dnf remove -y 'slurm'
    ```

### Host the Slurm RPM Repository

After building and verifying the RPMs, publish them as a YUM/DNF repository on
an HTTP server that the OIM can access.

!!! note
    The repository server does not have to be the Slurm build host. If a
    separate server is used, copy the built RPMs to that server before
    generating the repository metadata.

1. **Install Apache and the repository metadata utility**:

    ```bash title="Run on: repository server"
    dnf install -y httpd createrepo
    ```

2. **Start and enable Apache**:

    ```bash title="Run on: repository server"
    systemctl enable --now httpd
    systemctl status httpd
    ```

3. **Allow HTTP traffic when `firewalld` is enabled**:

    ```bash title="Run on: repository server"
    firewall-cmd --permanent --add-service=http
    firewall-cmd --reload
    ```

4. **Create the repository and publish the RPMs**:

    === "x86_64"

        ```bash title="Run on: repository server"
        mkdir -p /var/www/html/slurm_custom
        cp /root/rpmbuild/RPMS/x86_64/slurm-*.rpm /var/www/html/slurm_custom/
        cd /var/www/html/slurm_custom
        createrepo .
        ```

        Repository URL:

        ```text
        http://<REPO_SERVER_IP>/slurm_custom/
        ```

    === "aarch64"

        ```bash title="Run on: repository server"
        mkdir -p /var/www/html/slurm_custom_aarch64
        cp /root/rpmbuild/RPMS/aarch64/slurm-*.rpm /var/www/html/slurm_custom_aarch64/
        cd /var/www/html/slurm_custom_aarch64
        createrepo .
        ```

        Repository URL:

        ```text
        http://<REPO_SERVER_IP>/slurm_custom_aarch64/
        ```

    Keep RPMs built for different RHEL minor releases or architectures in
    separate repositories. Configure the matching URL for each catalog-selected
    RHEL version and architecture.

5. **Verify the repository metadata on the repository server**:

    === "x86_64"

        ```bash title="Run on: repository server"
        ls -l /var/www/html/slurm_custom/repodata
        curl http://localhost/slurm_custom/repodata/repomd.xml
        ```

    === "aarch64"

        ```bash title="Run on: repository server"
        ls -l /var/www/html/slurm_custom_aarch64/repodata
        curl http://localhost/slurm_custom_aarch64/repodata/repomd.xml
        ```

6. **Verify access from the OIM**:

    === "x86_64"

        ```bash title="Run on: OIM host"
        curl http://<REPO_SERVER_IP>/slurm_custom/repodata/repomd.xml
        ```

    === "aarch64"

        ```bash title="Run on: OIM host"
        curl http://<REPO_SERVER_IP>/slurm_custom_aarch64/repodata/repomd.xml
        ```

7. [Add the hosted RPM repository to Repository Manager](../../HowTo/repo_manager/adding_additional_repositories.md)
   for every RHEL version and architecture selected by the catalog. Complete
   Repository Manager synchronization before building cluster images.

#### Optional: Verify from a Client Node

The following example verifies the x86_64 repository from a disposable RHEL
client. Omnia-provisioned cluster nodes should receive their packages through
the Repository Manager and Image Build Manager workflows instead of this
manual configuration.

```bash title="Run on: test client"
cat <<EOF > /etc/yum.repos.d/slurm_custom.repo
[slurm_custom]
name=Slurm Custom Repository
baseurl=http://<REPO_SERVER_IP>/slurm_custom/
enabled=1
gpgcheck=0
EOF

dnf clean all
dnf makecache
dnf repolist
dnf list available | grep slurm
```

!!! warning
    The example disables RPM signature verification and is intended only for
    a trusted, unsigned test repository. Sign production RPMs and configure
    their GPG key according to your organization's security policy.

To test package installation on a disposable client, run:

```bash title="Run on: test client"
dnf install -y slurm slurm-slurmd slurm-slurmctld
```

## Next Steps

- [Set Up Slurm](../../HowTo/orchestrator/deploy_slurm.md) -- Deploy Slurm using the built RPMs
- [Create Local Repositories](../../HowTo/repo_manager/configure_repos.md) -- Integrate the
  custom repo with Omnia's repo management

## Troubleshooting

**Slurm RPM build failures**
   Install missing development packages:

   ```bash title="Run on: build host"
   dnf install -y <missing-package>-devel
   ```

   For aarch64 builds, install kernel headers:

   ```bash title="Run on: aarch64 build host"
   dnf install -y kernel-devel kernel-headers
   ```

   Verify CUDA is installed before running `rpmbuild` with GPU support:

   ```bash title="Run on: build host"
   ls /usr/local/cuda/lib64/stubs/libnvidia-ml.so
   ```

For the complete list, see [Slurm Issues](../../Troubleshooting/orchestrator/slurm.md).
