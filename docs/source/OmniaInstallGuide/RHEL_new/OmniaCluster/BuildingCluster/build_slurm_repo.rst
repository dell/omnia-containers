Enable repository for x86_64   
===============================

The build steps must be performed on RHEL 10.0 OS node.

**Prerequisites**

If you are using RHEL subscription, enable CodeReady Builder (CRB) ::
    
     subscription-manager repos --enable rhel-10-for-x86_64-baseos-rpms
     subscription-manager repos --enable rhel-10-for-x86_64-appstream-rpms
     subscription-manager repos --enable codeready-builder-for-rhel-10-x86_64-rpms

Enable repository for aarch64   
===============================

**Prerequisites**

1. Identify the aarch64 node, install the operating system, and assign a free PXE IP address.
2. If internet connection is not available, do the following:

        1. Enable the network masquerading to provide internet access.
        2. Run the following script: ::

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

3. If you are using RHEL subscription, enable CodeReady Builder (CRB) ::

        subscription-manager repos --enable rhel-10-for-aarch64-baseos-rpms
        subscription-manager repos --enable rhel-10-for-aarch64-appstream-rpms
        subscription-manager repos --enable codeready-builder-for-rhel-10-aarch64-rpms





Build Slurm repository without GPU support
=======================================================

1. Install dependencies. The following command is provided as an example: ::
      
        dnf install -y   wget git make gcc gcc-c++ rpm-build autoconf automake   python3 python3-devel perl perl-devel   readline-devel zlib-devel pam-devel dbus-devel   hwloc-devel libbpf-devel   pmix pmix-devel   jansson-devel   json-c json-c-devel   libyaml libyaml-devel   openssl-devel   mariadb-devel systemd-devel   munge munge-devel 



2. Download slurm tar file: wget, `Download <https://download.schedmd.com/slurm/slurm-25.05.2.tar.bz2>`_    

3. Run the RPM Build command. Run the following command from the directory containing the downloaded tar file. The following command is provided as an example:  ::

        rpmbuild -ta slurm-25.05.2.tar.bz2  --with pmix   --define "with_pmix --with-pmix=/usr"    --with yaml   --define "with_yaml --with-yaml"  --without hdf5   --define "without_hdf5 --without-hdf5"

After the build is completed, the RPMs are available at ``/root/rpmbuild/RPMS/x86_64/`` or ``/root/rpmbuild/RPMS/aarch64/``.

    .. image:: ../../../../images/slurm_rpm_build.png

4. To verify the build before hosting, navigate to ``/root/rpmbuild/RPMS/x86_64/`` or ``/root/rpmbuild/RPMS/aarch64/`` and run the following command: ::
       
        sudo rpm -ivh slurm-25.05.2-1*.x86_64.rpm 
        slurm-slurmd-25.05.2-1*.x86_64.rpm

 Or, ::

        sudo rpm -ivh slurm-25.05.2-1*.aarch64.rpm 
        slurm-slurmd-25.05.2-1*.aarch64.rpm

All the required .so, cgroup_v2.so files should be available.

    .. image:: ../../../../images/slurm_rpm_build_1.png

After you verify the build, remove the rpm packages. ::
        
        sudo dnf remove -y 'slurm'

Build Slurm repository with GPU support
==============================================

1. Install dependencies. The following command is provided as an example: ::
      
        dnf install -y   wget git make gcc gcc-c++ rpm-build autoconf automake   python3 python3-devel perl perl-devel   readline-devel zlib-devel pam-devel dbus-devel   hwloc-devel libbpf-devel   pmix pmix-devel   jansson-devel   json-c json-c-devel   libyaml libyaml-devel   openssl-devel   mariadb-devel systemd-devel   munge munge-devel


2. Download slurm tar file: wget, `Download <https://download.schedmd.com/slurm/slurm-25.05.2.tar.bz2>`_ 

3. Download the cuda tool kit for x86_64: wget `Download <https://developer.download.nvidia.com/compute/cuda/13.0.2/local_installers/cuda_13.0.2_580.95.05_linux.run>`_
   
   Download the cuda tool kit for aarch64: wget `Download <https://developer.download.nvidia.com/compute/cuda/13.1.0/local_installers/cuda_13.1.0_590.44.01_linux_sbsa.run>`_

The cuda_13.0.2_580.95.05_linux.run file is downloaded.

4. After the file is downloaded, run the following command from the directory where the file is downloaded: ::
    
        bash cuda_13.0.2_580.95.05_linux.run --silent --toolkit --toolkitpath=/usr/local/cuda -–override

5. Run the RPM Build command. Run the following command from the directory containing the downloaded tar file. The following command is provided as an example: ::

        rpmbuild -ta slurm-25.05.2.tar.bz2  --with pmix   --define "with_pmix --with-pmix=/usr"     --with yaml   --define "with_yaml --with-yaml"  --without hdf5   --define "without_hdf5 --without-hdf5" --with nvml   --define "_with_nvml --with-nvml=/usr/local/cuda"

After the build is completed, the RPMs are available at ``/root/rpmbuild/RPMS/x86_64/`` or ``/root/rpmbuild/RPMS/aarch64/``.

    .. image:: ../../../../images/slurm_rpm_build_2.png

6. To verify the build before hosting, navigate to ``/root/rpmbuild/RPMS/x86_64/`` or ``/root/rpmbuild/RPMS/aarch64/`` and run the following command: ::

        sudo rpm -ivh slurm-25.05.2-1*.x86_64.rpm 
        slurm-slurmd-25.05.2-1*.x86_64.rpm
     
 Or, ::

        sudo rpm -ivh slurm-25.05.2-1*.aarch64.rpm 
        slurm-slurmd-25.05.2-1*.aarch64.rpm

All required .so along with the gpu_nvml.so should be available.

    .. image:: ../../../../images/slurm_rpm_build_3.png


After you verify the build, remove the rpm packages. ::
        
        sudo dnf remove -y 'slurm'

