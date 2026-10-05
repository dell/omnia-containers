# Build LDMS Producer RPM Repository

Build an OVIS Lightweight Distributed Metric Service (LDMS) producer RPM for
HPC monitoring, publish it through an HTTP repository, and make the repository
available to Omnia.

## Overview

The `build_rpm.sh` script in the
[omnia-containers repository](https://github.com/dell/omnia-containers)
clones the OVIS repository and builds an LDMS producer RPM in a Rocky Linux 10
container. The workflow supports `x86_64` and `aarch64`; run it on the same
architecture as the nodes that will use the RPM.

The current script invokes Podman directly. Docker is not an alternative for
this RPM build workflow.

## Prerequisites

- A build host with internet access and the target node architecture.
- EPEL and AppStream repository access.
- `git` and Podman installed and operational.
- An `omnia-containers` checkout. Run the commands from the repository root so
  that `RpmFile/ldms/build/` can be found.
- If LDMS must collect Slurm metrics, a reachable Slurm RPM repository URL and
  repository name.
- Install the required Python development packages:

    ```bash title="Run on: LDMS build host"
    sudo dnf install -y python3-devel python3-Cython
    ```

To obtain the build repository:

```bash title="Run on: LDMS build host"
git clone https://github.com/dell/omnia-containers.git
cd omnia-containers
```

!!! warning
    The build script removes and recreates `$HOME/ovis-code/ovis` before
    checking out the requested OVIS tag. Preserve any unrelated work stored at
    that path before running the script.

## Input Contract

The command syntax is:

```text
./build_rpm.sh -v <LDMS_VERSION> -u <SLURM_REPO_URL> -n <SLURM_REPO_NAME>
```

The Slurm repository URL and name can also be supplied as positional arguments:

```text
./build_rpm.sh <SLURM_REPO_URL> <SLURM_REPO_NAME>
```

| Parameter | Description |
|---|---|
| `-v`, `--version <version>` | LDMS version to build. The default is `4.5.2`. |
| `-u`, `--url <url>` | Slurm repository URL used to resolve dependencies required for Slurm metrics. |
| `-n`, `--name <name>` | Slurm repository name used inside the build container. |
| `-h`, `--help` | Display command usage. |

The Slurm repository parameters are optional. If they are omitted, the build
continues with a warning, but the resulting package might not provide Slurm
metrics.

## Procedure

Run one of the following commands from the `omnia-containers` repository root.

Build LDMS version 4.5.2 using the default:

```bash title="Run on: LDMS build host"
./build_rpm.sh
```

Build a specific LDMS version:

```bash title="Run on: LDMS build host"
./build_rpm.sh -v 4.5.2
```

Build with Slurm repository support:

```bash title="Run on: LDMS build host"
./build_rpm.sh \
  -v 4.5.2 \
  -u http://<REPO_SERVER_IP>/slurm_custom/ \
  -n x86_64_slurm_custom
```

Alternatively, supply the Slurm repository URL and name as positional
arguments:

```bash title="Run on: LDMS build host"
./build_rpm.sh \
  http://<REPO_SERVER_IP>/slurm_custom/ \
  x86_64_slurm_custom
```

The script performs the following operations:

1. Clones `https://github.com/ovis-hpc/ovis.git` at the requested version tag.
2. Sets `LDMS_REPO` to `$HOME/ovis-code/ovis`.
3. Detects the build-host architecture.
4. Starts a Rocky Linux 10 Podman container.
5. Runs `start_build_container.rockylinux10.bash` and builds the RPM in the
   bind-mounted OVIS checkout.

## Verification

The built RPM is available under `$HOME/ovis-code/ovis`. Verify it before
publishing:

```bash title="Run on: LDMS build host"
find "$HOME/ovis-code/ovis" -maxdepth 1 -name 'ovis-ldms-*.rpm' -print
rpm -qpi "$HOME"/ovis-code/ovis/ovis-ldms-*.rpm
```

The RPM filename includes the LDMS version and build-host architecture.

## Host the LDMS Repository

The following example publishes the RPM through Apache. Run it on the LDMS
build host, or copy the RPM to a separate repository server first.

1. Install and start the repository services:

    ```bash title="Run on: repository server"
    dnf install -y httpd createrepo
    systemctl enable --now httpd
    ```

2. If `firewalld` is enabled, allow HTTP traffic:

    ```bash title="Run on: repository server"
    firewall-cmd --permanent --add-service=http
    firewall-cmd --reload
    ```

3. Create the repository and generate its metadata:

    ```bash title="Run on: repository server"
    mkdir -p /var/www/html/ldms
    cp "$HOME"/ovis-code/ovis/ovis-ldms-*.rpm /var/www/html/ldms/
    cd /var/www/html/ldms
    createrepo .
    ```

    Keep packages built for different RHEL minor releases or architectures in
    separate repository directories.

4. Verify the metadata locally and from the OIM:

    ```bash title="Run on: repository server"
    ls -l /var/www/html/ldms/repodata
    curl http://localhost/ldms/repodata/repomd.xml
    ```

    ```bash title="Run on: OIM host"
    curl http://<REPO_SERVER_IP>/ldms/repodata/repomd.xml
    ```

5. Configure the hosted URL as the `ldms` user repository for every required
   RHEL version and architecture. See
   [Add an RPM Repository and Packages](../../HowTo/repo_manager/adding_additional_repositories.md).

6. Run Repository Manager synchronization and verify that the required LDMS
   repository reports success before building cluster images.

## Update Build-Project Python Packages

This task is only for contributors who are changing Python dependencies in the
`omnia-containers` project. It is not required for a normal LDMS RPM build.

1. Install `uv`:

    ```bash title="Run on: development host"
    python3 -m pip install uv
    ```

2. Update `pyproject.toml` in the applicable container directory.

3. From the same directory, update the lock file:

    ```bash title="Run on: development host"
    uv lock
    ```

## Next Steps

- [Configure LDMS Telemetry](../../HowTo/Telemetry/configure_ldms.md)
- [Build Cluster Images](../../HowTo/image_build_manager/build_images.md)
- Refer to the upstream
  [Building LDMS Producer RPM Package](https://github.com/dell/omnia-containers?tab=readme-ov-file#building-ldms-producer-rpm-package)
  section for the corresponding build-project information.
