# Build Slurm Repository

Build Slurm 25.05 RPMs from source for use with Omnia. This guide covers
building on both x86_64 and aarch64 hosts, with and without GPU support.

## Overview

Omnia requires a user-built Slurm RPM repository. You build the RPMs on
a host running the same OS as your cluster nodes (RHEL 10.0), then host
them on an HTTP server accessible from the OIM.

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
      --with nvml \
      --define "_with_nvml --with-nvml=/usr/local/cuda" \
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

## Hosting the Repository

After building and verifying the RPMs, host them on an HTTP server
accessible from the OIM. See
[Host RPMs on Apache Server](host_slurm_repo.md) for step-by-step
instructions on setting up Apache to serve the repository.

## Next Steps

- [Set Up Slurm](setup_slurm.md) -- Deploy Slurm using the built RPMs
- [Create Local Repos](../Setup/create_local_repos.md) -- Integrate the
  custom repo with Omnia's repo management

## Troubleshooting

For Slurm troubleshooting, see
[Slurm Issues](../../Troubleshooting/slurm.md).
