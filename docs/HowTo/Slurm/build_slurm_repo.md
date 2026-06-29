
# Build Slurm Repository


Build a custom Slurm RPM repository for use with Omnia's local repository
infrastructure. This is useful when you need a specific Slurm version or
custom build options.

## Overview


By default, Omnia installs Slurm from pre-built RPM packages in the local
Pulp repositories. If you need a specific Slurm version, custom compile
options, or patches, you can build Slurm RPMs from source and host them in a
local repository.


## Prerequisites


- The [Create Local Repos](../Setup/create_local_repos.md) procedure is complete (Pulp is
  running and base OS repos are synced).
- A build host with:

  - RHEL 8.x / 9.x or Rocky Linux matching your cluster OS
  - `rpm-build`, `rpmbuild`, and development tools installed
  - At least 10 GB free disk space

- Slurm source tarball (download from
  `<https://www.schedmd.com/downloads.php>`_).


## Procedure


1. **Install build dependencies** on the build host:

   ```bash title="Run on: build host (OIM or dedicated build server)"
   dnf groupinstall -y "Development Tools"
   dnf install -y rpm-build munge-devel munge-libs pam-devel \
     perl-ExtUtils-MakeMaker readline-devel openssl-devel \
     mariadb-devel hwloc-devel lua-devel numactl-devel \
     http-parser-devel json-c-devel libcurl-devel
   ```


2. **Create the RPM build directory structure**:

   ```bash title="Run on: build host"
   mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
   ```


3. **Download the Slurm source tarball**:

   ```bash title="Run on: build host"
   cd ~/rpmbuild/SOURCES
   wget https://download.schedmd.com/slurm/slurm-23.11.4.tar.bz2
   ```


   !!! note

       Replace the version number with your desired Slurm version.

4. **Extract the spec file**:

   ```bash title="Run on: build host"
   tar xjf slurm-23.11.4.tar.bz2 --strip-components=1 -C /tmp slurm-23.11.4/slurm.spec
   cp /tmp/slurm.spec ~/rpmbuild/SPECS/
   ```


5. **Build the RPMs**:

   ```bash title="Run on: build host"
   rpmbuild -ba ~/rpmbuild/SPECS/slurm.spec
   ```


   This process takes **10-30 minutes** depending on hardware. The resulting
   RPMs will be in `~/rpmbuild/RPMS/x86_64/`.

6. **Create a local repository** from the built RPMs:

   ```bash title="Run on: build host"
   dnf install -y createrepo_c
   mkdir -p /opt/omnia/custom_repos/slurm
   cp ~/rpmbuild/RPMS/x86_64/slurm-*.rpm /opt/omnia/custom_repos/slurm/
   createrepo_c /opt/omnia/custom_repos/slurm/
   ```


7. **Upload to Pulp** (from the omnia_core container):

   ```bash title="Run on: omnia_core container"
   # Create a Pulp repository for custom Slurm RPMs
   pulp rpm repository create --name slurm-custom

   # Upload RPMs
   for rpm in /opt/omnia/custom_repos/slurm/*.rpm; do
     pulp rpm content upload --file "$rpm" --repository slurm-custom
   done

   # Create a publication and distribution
   pulp rpm publication create --repository slurm-custom
   pulp rpm distribution create --name slurm-custom \
     --base-path slurm-custom \
     --repository slurm-custom
   ```



## Verification


1. **List the custom repository contents**:

   ```bash title="Run on: build host"
   ls -la /opt/omnia/custom_repos/slurm/
   ```


2. **Verify the repository metadata**:

   ```bash title="Run on: build host"
   ls /opt/omnia/custom_repos/slurm/repodata/
   ```


   You should see `repomd.xml` and related files.

3. **Test package availability via Pulp**:

   ```bash title="Run on: OIM host"
   curl -s http://localhost:8080/pulp/content/slurm-custom/repodata/repomd.xml | head
   ```


4. **Verify RPM versions**:

   ```bash title="Run on: build host"
   rpm -qip ~/rpmbuild/RPMS/x86_64/slurm-23*.rpm | grep -E "^(Name|Version)"
   ```



## Next Steps


- [Setup Slurm](setup_slurm.md) -- Deploy Slurm using the custom RPMs.
- [Create Local Repos](../Setup/create_local_repos.md) -- Integrate the custom repo with
  Omnia's repo management.


## Troubleshooting


**rpmbuild fails with missing dependency**
   Install the missing development package:

   ```bash title="Run on: build host"
   dnf install -y <missing-package>-devel
   ```


**Spec file not found in tarball**
   Download the spec file separately from SchedMD's GitHub:

   ```bash title="Run on: build host"
   wget -O ~/rpmbuild/SPECS/slurm.spec \
     https://raw.githubusercontent.com/SchedMD/slurm/slurm-23-11-4-1/slurm.spec
   ```


**createrepo_c fails**
   Ensure the package is installed:

   ```bash title="Run on: build host"
   dnf install -y createrepo_c
   ```


**Custom RPMs conflict with existing Slurm packages**
   Remove existing Slurm packages before installing custom ones:

   ```bash title="Run on: compute node"
   dnf remove -y slurm slurm-slurmd slurm-slurmctld
   dnf install -y --disablerepo='*' --enablerepo='slurm-custom' slurm slurm-slurmd
   ```
