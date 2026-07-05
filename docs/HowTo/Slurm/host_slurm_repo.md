# Host RPMs on Apache Server

Set up an Apache HTTP server to host the Slurm RPM repository so that
the OIM can download packages during cluster deployment.

## Overview

After building Slurm RPMs (see
[Build Slurm Repository](build_slurm_repo.md)), you need to host them on
an HTTP server accessible from the OIM. This guide uses Apache (`httpd`)
to serve the RPMs as a YUM/DNF repository.

## Prerequisites

- Slurm RPMs are built and verified (see
  [Build Slurm Repository](build_slurm_repo.md)).
- The server on which you want to host the repository is accessible from
  the OIM.

## Procedure

1. **Update system packages**:

    ```bash title="Run on: repo server"
    dnf update -y
    ```

2. **Install Apache**:

    ```bash title="Run on: repo server"
    dnf install -y httpd
    ```

3. **Install createrepo**:

    ```bash title="Run on: repo server"
    dnf install -y createrepo
    ```

4. **Start and enable Apache**:

    ```bash title="Run on: repo server"
    systemctl start httpd
    systemctl enable httpd
    ```

5. **Verify the HTTP service status**:

    ```bash title="Run on: repo server"
    systemctl status httpd
    ```

    The status should be **Active**.

6. **Create a directory, copy the RPMs, and generate repository metadata**:

    ```bash title="Run on: repo server"
    mkdir -p /var/www/html/slurm_custom
    cp /root/rpmbuild/RPMS/x86_64/slurm-*.rpm /var/www/html/slurm_custom/
    cd /var/www/html/slurm_custom
    createrepo .
    ```

    !!! note
        For aarch64 RPMs, create a separate directory:

        ```bash title="Run on: repo server"
        mkdir -p /var/www/html/slurm_custom_aarch64
        cp /root/rpmbuild/RPMS/aarch64/slurm-*.rpm /var/www/html/slurm_custom_aarch64/
        cd /var/www/html/slurm_custom_aarch64
        createrepo .
        ```

### Custom Port (Optional)

If you want to host the repository on a custom port instead of the
default port 80:

1. **Edit the Apache configuration**:

    ```bash title="Run on: repo server"
    vi /etc/httpd/conf/httpd.conf
    ```

    Find the `Listen` parameter and update the port:

    ```text title="File: /etc/httpd/conf/httpd.conf"
    #Listen 12.34.56.78:80
    Listen 8080
    ```

2. **Restart Apache**:

    ```bash title="Run on: repo server"
    systemctl restart httpd
    systemctl status httpd
    ```

## Verification

1. **Verify the repository is accessible** from the OIM:

    ```bash title="Run on: OIM host"
    curl -s http://<repo-server-ip>/slurm_custom/repodata/repomd.xml | head
    ```

    If using a custom port:

    ```bash title="Run on: OIM host"
    curl -s http://<repo-server-ip>:8080/slurm_custom/repodata/repomd.xml | head
    ```

## Configure in Omnia

After hosting the repository, add the URL to `local_repo_config.yml`:

```yaml title="File: /opt/omnia/input/project_default/local_repo_config.yml"
user_repo_url_x86_64:
  - { url: "http://<repo-server-ip>/slurm_custom/", gpgkey: "", name: "slurm_custom" }
```

For aarch64:

```yaml title="File: /opt/omnia/input/project_default/local_repo_config.yml"
user_repo_url_aarch64:
  - { url: "http://<repo-server-ip>/slurm_custom_aarch64/", gpgkey: "", name: "slurm_custom" }
```

!!! important
    The repository `name` must be `slurm_custom` to match the
    `software_config.json` entry.

## Next Steps

- [Set Up Slurm](setup_slurm.md) -- Deploy Slurm using the hosted RPMs
