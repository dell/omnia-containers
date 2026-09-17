# Local Repository and Pulp Issues

Issues related to Repo Manager, Pulp service operations, and repository
synchronization.

## Package Download Failure Due to Slow Storage

???+ note "Symptom"

    The Repository Manager `download` phase reports a failed package, or a
    package reports success but is unavailable from its Pulp distribution.

??? note "Cause"

    Slow or full storage can cause a Pulp task or package download to time out.
    An unreachable source, invalid catalog entry, or registry authentication
    failure can produce the same symptom.

??? note "Resolution"

    1. Check free space and storage latency for the configured Pulp paths.
    2. Review `/var/log/omnia/repo_manager/repo_manager.log` and the current
       runtime status files:

        ```text
        <REPO_MANAGER_DATA_PATH>/log/<os>/<version>/<architecture>/groups_status.csv
        <REPO_MANAGER_DATA_PATH>/log/<os>/<version>/<architecture>/<group>/status.csv
        <REPO_MANAGER_DATA_PATH>/log/<os>/catalog_execution_summary.yml
        ```

    3. Correct the source or storage problem. From `src/main`, rerun:

        ```bash title="Run on: OIM host"
        ./omnia.sh --run repo_manager --tags download
        ./omnia.sh --run repo_manager --tags status
        ```

    Repository Manager uses its runtime status to resume idempotently. Do not
    delete status files or edit an upgrade manifest to retry a download.

## Playbook Fails When Re-Run Multiple Times

???+ note "Symptom"

    A Repository Manager download fails when another synchronization task is
    already active.

??? note "Cause"

    Concurrent runs can contend for the same Pulp resources. An interrupted run
    can also leave an active Pulp task that has not finished cancelling.

??? note "Resolution"

    Do not start concurrent Repository Manager runs. Inspect the active Pulp
    tasks, allow the current task to finish, and rerun the `download` phase.
    Repository Manager detects and recovers an active task left by an
    interrupted earlier run before deciding whether to synchronize again.

## Pulp Reset Password Failed

???+ note "Symptom"

    Pulp credential setup fails during the Repository Manager `prepare` phase.

??? note "Cause"

    - NFS Storage Export Configuration (PowerScale): Missing or incorrect settings for `nfsv4-no-names`, `nfsv4-no-domain`, `nfsv4-no-domain-uids`, and `nfsv4-allow-numeric-ids`.
    - Inconsistent UID and GID mappings between NFS server and client.
    - Missing `no_root_squash` option in NFS export configuration.
    - NFS server connectivity issues or firewall blocking ports 2049, 111, and 20048.

??? note "Resolution"

    Verify the NFS export settings, then rerun
    `./omnia.sh --run repo_manager --tags prepare` from `src/main`.

    For PowerScale-specific configuration details, see the PowerScale configuration on [Deploy PowerScale CSI](../../HowTo/orchestrator/deploy_powerscale_csi.md) page.

## EPEL Repository Unavailable/Unstable/Too Slow

???+ note "Symptom"

    The Repository Manager `download` phase fails while synchronizing EPEL
    metadata or downloading and validating an EPEL package.

    - **Pulp sync stage:** The EPEL URL reachability check fails or the Pulp remote sync to `x86_64_rhel_10.0_epel` (or `aarch64_rhel_10.0_epel`) times out.
    - **RPM download/validation stage:** Individual EPEL-dependent packages (`gedit`, `fping`, `clustershell`, `nss-pam-ldapd`, `apptainer`) fail during `dnf download` or `dnf info` validation.

??? note "Cause"

    The EPEL repository is unavailable, unreachable through the configured proxy or firewall, or contains stale metadata. Additional causes include:

    - Pulp container is not running (verify with `podman ps | grep pulp`).
    - Pulp sync timeout for large EPEL repository (syncs can take 10–20 minutes, especially with `pulp_concurrency: 1` on NFS storage).
    - The EPEL GPG key URL (`https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-10`)
      configured in `repo_manager_config.yml` under
      `repositories.<version>.<arch>.epel.gpgkey` is unreachable.

??? note "Resolution"

    1. Verify connectivity to the EPEL repository and GPG key:

        ```bash title="Run on: OIM host"
        curl -I --connect-timeout 10 https://dl.fedoraproject.org/pub/epel/10/Everything/x86_64/
        curl -I --connect-timeout 10 https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-10
        ```

    2. Verify the Pulp container is running and the EPEL repository sync status:

        ```bash title="Run on: OIM host"
        podman ps | grep pulp
        pulp rpm repository show --name x86_64_rhel_10.0_epel
        pulp rpm remote show --name x86_64_rhel_10.0_epel
        ```

    3. Identify the failed EPEL package in the Omnia logs. The Ansible log
       is at `/var/log/omnia/repo_manager/repo_manager.log`. Runtime status
       files are under
       `<REPO_MANAGER_DATA_PATH>/log/<os>/<version>/<architecture>/`
       (default `/opt/omnia/repo_manager/log/`):

        ```bash title="Run on: OIM host"
        grep -i "epel" /var/log/omnia/repo_manager/repo_manager.log
        grep -iE "epel|failed|timeout|error" /var/log/omnia/repo_manager/repo_manager.log
        cat /opt/omnia/repo_manager/log/rhel/10.0/x86_64/groups_status.csv
        find /opt/omnia/repo_manager/log/rhel/10.0/x86_64 -name status.csv -print
        ```

    4. Apply the appropriate recovery:

        - If EPEL is temporarily unavailable, retry after service recovery by
          rerunning the Repository Manager `download` and `status` phases.
        - To force re-sync of only the EPEL repository without resyncing all repos:

            ```bash title="Run on: OIM host"
            source /opt/omnia/activate-omnia.sh
            cd src/repo_manager/playbooks
            ansible-playbook repo_manager.yml --tags download \
              -e "resync_repos=x86_64_rhel_10.0_epel"
            ```

        - If the EPEL repository is corrupted in Pulp, clean it up and rerun:

            ```bash title="Run on: OIM host"
            source /opt/omnia/activate-omnia.sh
            cd src/repo_manager/playbooks
            ansible-playbook repo_manager.yml --tags cleanup_repos \
              -e "cleanup_repos=x86_64_rhel_10.0_epel,aarch64_rhel_10.0_epel"
            ```

    5. If the default EPEL mirror (`dl.fedoraproject.org`) is slow or unreliable, switch to a faster mirror:

        **a. Find available EPEL mirrors** using the Fedora Mirror Manager:

        For x86_64:

        ```bash title="Run on: OIM host"
        curl -sL "https://mirrors.fedoraproject.org/mirrorlist?repo=epel-z-10.0&arch=x86_64" | grep -v "^#"
        ```

        For aarch64:

        ```bash title="Run on: OIM host"
        curl -sL "https://mirrors.fedoraproject.org/mirrorlist?repo=epel-z-10.0&arch=aarch64" | grep -v "^#"
        ```

        !!! note

            The mirror list URL uses `epel-z-<major>.<minor>` format for point releases (e.g., `epel-z-10.0` for RHEL 10.0, `epel-z-10.1` for RHEL 10.1). Using `epel-10` without the `z` prefix returns mirrors for the latest point release, which may not have packages built for your OS version.

        **b. Test mirror download speed** by downloading a sample package from each candidate mirror. Not all mirrors in the list may be synced or reachable, so test before choosing:

        For x86_64:

        ```bash title="Run on: OIM host"
        wget -O /dev/null https://fedora-archive.ip-connect.info/epel/10.0/Everything/x86_64/Packages/f/fping-5.2-3.el10_0.x86_64.rpm

        wget -O /dev/null http://mirror.math.princeton.edu/pub/fedora-archive/epel/10.0/Everything/x86_64/Packages/f/fping-5.2-3.el10_0.x86_64.rpm

        wget -O /dev/null https://dl.fedoraproject.org/pub/archive/epel/10.0/Everything/x86_64/Packages/f/fping-5.2-3.el10_0.x86_64.rpm
        ```

        For aarch64:

        ```bash title="Run on: OIM host"
        wget -O /dev/null https://fedora-archive.ip-connect.info/epel/10.0/Everything/aarch64/Packages/f/fping-5.2-3.el10_0.aarch64.rpm

        wget -O /dev/null http://mirror.math.princeton.edu/pub/fedora-archive/epel/10.0/Everything/aarch64/Packages/f/fping-5.2-3.el10_0.aarch64.rpm

        wget -O /dev/null https://dl.fedoraproject.org/pub/archive/epel/10.0/Everything/aarch64/Packages/f/fping-5.2-3.el10_0.aarch64.rpm
        ```

        !!! note

            Some mirrors from the mirrorlist may return 404 or time out because they have not fully synced the EPEL 10.0 archive. Skip those and test the next mirror. Choose the mirror with the highest download speed.

        **c. Update the EPEL URL** in
        `$OMNIA_DATA_PATH/repo_manager/input/$OMNIA_PROJECT_NAME/repo_manager_config.yml`.
        Set the `epel.url` value under the applicable OS version and
        architecture:

        For x86_64:

        ```yaml title="File: /opt/omnia/repo_manager/input/project_default/repo_manager_config.yml"
        repositories:
          "10.0":
            x86_64:
              epel:
                url: "https://fedora-archive.ip-connect.info/epel/10.0/Everything/x86_64/"
                gpgkey: "https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-10"
        ```

        For aarch64:

        ```yaml title="File: /opt/omnia/repo_manager/input/project_default/repo_manager_config.yml"
        repositories:
          "10.0":
            aarch64:
              epel:
                url: "https://fedora-archive.ip-connect.info/epel/10.0/Everything/aarch64/"
                gpgkey: "https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-10"
        ```

        !!! note

            If the default `gpgkey` URL is unreachable, replace it with a
            reachable mirror URL or a local copy of the EPEL GPG key. The
            repository mapping key must remain `epel` so it matches the
            selected catalog. EPEL 10.0 packages are in the Fedora **archive**
            mirrors.

    6. Rerun the Repository Manager `download` and `status` phases and verify
       that `repo_status.yml` reports `overall_status: success`.

    !!! note

        For repeatable or air-gapped deployments, host the required EPEL
        packages locally instead of relying on the external EPEL service
        during deployment. In `repo_manager_config.yml`, set `repo_config` to
        `always` and set `caching` to `false` for the EPEL repository so that
        Pulp synchronizes its content for offline use.

## CRI-O repository URL is unreachable from OIM

???+ note "Symptom"

    The Repository Manager `download` phase fails for the `cri-o-v1-35`
    repository.

??? note "Cause"

    The configured CRI-O repository URL is unreachable due to DNS failure,
    geographic mirror redirection, or network restrictions. The default CRI-O
    repository may be inaccessible from the OIM host.

??? note "Resolution"

    1. Remove stale Pulp objects for the affected architecture:

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        pulp rpm distribution destroy --name "x86_64_rhel_10.0_cri-o-v1-35"
        pulp rpm repository destroy --name "x86_64_rhel_10.0_cri-o-v1-35"
        pulp rpm remote destroy --name "x86_64_rhel_10.0_cri-o-v1-35"
        ```

        For aarch64, use `aarch64_rhel_10.0_cri-o-v1-35`.

    2. Verify accessibility of the primary CRI-O repository URL:

        ```bash title="Run on: OIM host"
        CRIO_REPO_URL='https://download.opensuse.org/repositories/isv:/cri-o:/stable:/v1.35/rpm/'
        curl --fail --silent --show-error --head "$CRIO_REPO_URL"
        curl --fail --silent --show-error --head "${CRIO_REPO_URL}repodata/repomd.xml"
        ```

    3. If the primary URL is unreachable, verify the alternative mirror:

        ```bash title="Run on: OIM host"
        CRIO_REPO_URL='https://ftp.gwdg.de/pub/opensuse/repositories/isv:/cri-o:/stable:/v1.35/rpm/'
        curl --fail --silent --show-error --head "$CRIO_REPO_URL"
        curl --fail --silent --show-error --head "${CRIO_REPO_URL}repodata/repomd.xml"
        ```

    4. Update the CRI-O URL in
        `$OMNIA_DATA_PATH/repo_manager/input/$OMNIA_PROJECT_NAME/repo_manager_config.yml`
        under the applicable OS version and architecture:

        ```yaml title="File: /opt/omnia/repo_manager/input/project_default/repo_manager_config.yml"
        repositories:
          "10.0":
            x86_64:
              cri-o-v1-35:
                url: "https://ftp.gwdg.de/pub/opensuse/repositories/isv:/cri-o:/stable:/v1.35/rpm/"
                gpgkey: "https://ftp.gwdg.de/pub/opensuse/repositories/isv:/cri-o:/stable:/v1.35/rpm/repodata/repomd.xml.key"
        ```

    5. Rerun the Repository Manager `download` phase:

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
        ansible-playbook repo_manager.yml --tags download
        ```

    6. Rerun the `status` phase and verify that `repo_status.yml` reports
       `overall_status: success`.

## Intermittent Local Repository Sync Failure Due to Non-Persistent Iptables Rules

???+ note "Symptom"

    Local repository synchronization fails intermittently, particularly after an OIM restart or firewall reload. The OIM may have internet access while the repository container cannot reach external repositories.

??? note "Cause"

    Required outbound traffic from the Podman container network is blocked by the OIM firewall. Temporary firewall rules may also be lost after a restart or firewall reload.

    !!! warning

        Do not set the INPUT, FORWARD, or OUTPUT policies to ACCEPT:

        ```bash title="Do NOT run these commands"
        iptables -P INPUT ACCEPT
        iptables -P FORWARD ACCEPT
        iptables -P OUTPUT ACCEPT
        ```

        These commands effectively bypass the OIM firewall policy and may expose the system to unauthorized traffic.

??? note "Resolution"

    1. Identify the repository container and Podman network:

        ```bash title="Run on: OIM host"
        podman ps -a
        podman network ls
        podman network inspect <network_name>
        ```

    2. Verify connectivity from the affected container:

        ```bash title="Run on: OIM host"
        podman exec <container_name> getent hosts <repository_fqdn>
        podman exec <container_name> curl -Iv --connect-timeout 10 https://<repository_fqdn>/
        ```

    3. Review the active forwarding rules:

        ```bash title="Run on: OIM host"
        iptables -L FORWARD -n -v --line-numbers
        ```

    4. Add narrowly scoped rules. Replace the placeholders with values from your environment:

        ```bash title="Run on: OIM host"
        # Allow established return traffic
        iptables -I FORWARD 1 \
          -d <container_subnet> \
          -m conntrack --ctstate ESTABLISHED,RELATED \
          -j ACCEPT

        # Allow container DNS queries
        iptables -I FORWARD 1 \
          -s <container_subnet> -d <dns_server_ip> \
          -p udp --dport 53 \
          -m conntrack --ctstate NEW,ESTABLISHED \
          -j ACCEPT

        # Allow HTTPS only to the approved repository or proxy
        iptables -I FORWARD 1 \
          -s <container_subnet> -d <repository_or_proxy_cidr> \
          -p tcp --dport 443 \
          -m conntrack --ctstate NEW,ESTABLISHED \
          -j ACCEPT
        ```

        Add TCP port 80 only if the repository explicitly requires HTTP.

        !!! warning

            Do not set the INPUT, FORWARD, or OUTPUT policies to ACCEPT:

            ```bash title="Do NOT run these commands"
            iptables -P INPUT ACCEPT
            iptables -P FORWARD ACCEPT
            iptables -P OUTPUT ACCEPT
            ```

            These commands effectively bypass the OIM firewall policy and may expose the system to unauthorized traffic.

    5. Retest repository access:

        ```bash title="Run on: OIM host"
        podman exec <container_name> curl -Iv --connect-timeout 10 https://<repository_fqdn>/
        ```

    6. Make the scoped rules persistent using the firewall manager configured on the OIM, such as firewalld or nftables.

        !!! note

            For repositories using CDNs or frequently changing IP addresses, route container traffic through an approved outbound proxy and restrict access to the proxy IP and port. Do not create broad internet-access rules.

        **Validation**

        Verify the following to confirm the resolution:

        - Repository synchronization completes successfully without errors
        - The scoped firewall rules persist after an OIM restart or firewall reload
        - Default firewall policies remain unchanged (not set to blanket ACCEPT)
        - No unnecessary inbound or forwarded access has been enabled

## Connectivity Issues

???+ note "Symptom"

    The Repository Manager `precheck` or `download` phase fails with
    connectivity errors. Failures can occur at multiple stages:

    - **Validation stage:** URL reachability checks fail with `<url> is either unreachable, invalid or has incorrect SSL certificates` or `Unreachable registries detected: <host>`.
    - **Pulp sync stage:** Repository sync to the local Pulp server fails or times out.
    - **Download stage:** Package downloads fail with `Download interrupted`, `Max retries exceeded, download failed`, or `Unable to reach Docker Hub (network DNS/timeout/SSL issue)`.
    - **Status phase:** `repo_status.yml` reports `overall_status: failed` or
      omits a catalog-required distribution URL.

??? note "Cause"

    The OIM was unable to reach a required online resource. Specific causes include:

    - External repository URLs are unreachable due to a network outage, DNS
      failure, or firewall rule.
    - User-defined registries or repository URLs in
      `repo_manager_config.yml` are unreachable.
    - SSL/TLS certificate issues — mismatched, expired, or missing certificates for user repositories or registries.
    - Docker Hub rate limiting (HTTP 429), invalid credentials (HTTP 401), or server errors (HTTP 5xx).
    - Pulp container is not running or Pulp endpoint is unresponsive.

??? note "Resolution"

    1. Verify connectivity to the upstream repository URLs configured in the
       project-scoped `repo_manager_config.yml`.

    2. Verify that the Pulp container is running and Pulp endpoint is accessible:

        ```bash title="Run on: OIM host"
        podman ps | grep pulp
        curl -k https://<pulp_server_ip>:<pulp_port>/pulp/api/v3/status/
        ```

    3. If user registries are configured, verify connectivity on the OIM.

    4. Check the logs for specific error messages. The Ansible log is at
       `/var/log/omnia/repo_manager/repo_manager.log`. Runtime status files
       are under `<REPO_MANAGER_DATA_PATH>/log/<os>/<version>/<architecture>/`
       (default `/opt/omnia/repo_manager/log/`):

        ```bash title="Run on: OIM host"
        grep -i "unreachable" /var/log/omnia/repo_manager/repo_manager.log
        grep -iE "unreachable|timeout|connection|failed|SSL" /var/log/omnia/repo_manager/repo_manager.log
        cat /opt/omnia/repo_manager/log/rhel/10.0/x86_64/groups_status.csv
        ```

    5. Apply the appropriate recovery:

        - If the Pulp container is not running, rerun the Repository Manager
          `prepare` phase.
        - If external URLs are unreachable, verify DNS resolution and firewall rules on OIM.
        - If SSL certificate errors occur for user repos, verify that certificate files exist under the expected path and are valid.
        - If Docker Hub rate limiting occurs, wait and retry, or run the
          Repository Manager credential flow and configure the registry entry
          in `repo_manager_config.yml`.

    6. Rerun the Repository Manager `download` and `status` phases after
       resolving the connectivity issue. Previously synchronized content is
       reused unless `resync_repos` requests a resynchronization.

## Software Installation Fails With Checksum Error

???+ note "Symptom"

    Software installation fails with a checksum error.

??? note "Cause"

    Repository Manager did not publish the catalog source that provides the
    software, or the node is using a stale repository configuration.

??? note "Resolution"

    1. Confirm that the selected catalog references the package and that
       `repo_manager_config.yml` defines its source repository.
    2. Run the Repository Manager `download` and `status` phases and verify a
       successful `repo_status.yml`.
    3. Refresh the node repository metadata and rerun the failed installation.

## Pulp Certificate Trust Failure on Compute Nodes

???+ note "Symptom"

    - `dnf install` fails with SSL certificate errors on provisioned compute nodes.
    - Package installation during cloud-init `runcmd` phase fails.
    - Container image pulls from the Pulp mirror fail on nodes.

    Example errors on the compute node:

    ```text title="Expected output"
    SSL certificate problem: unable to get local issuer certificate
    Peer's certificate issuer is not recognized
    Error: Failed to download metadata for repo 'pulp_mirror'
    ```

??? note "Cause"

    The Pulp webserver certificate (`pulp_webserver.crt`) was not copied or trusted on the node. All cloud-init templates include a `runcmd` step that copies the certificate from the NFS-mounted `/cert` directory:

    ```bash
    cp /cert/pulp_webserver.crt /etc/pki/ca-trust/source/anchors && update-ca-trust
    ```

    This step can fail if the NFS mount for `/cert` was not established before the certificate copy step executes.

??? note "Resolution"

    1. Verify the certificate and NFS mount status:

        ```bash title="Run on: compute node"
        # Check if the certificate is present and trusted
        ls -la /etc/pki/ca-trust/source/anchors/pulp_webserver.crt
        ls -la /cert/pulp_webserver.crt

        # Verify the NFS mount for /cert
        mount | grep /cert

        # Test SSL connectivity to Pulp
        openssl s_client -connect <admin_nic_ip>:2225 -showcerts </dev/null 2>&1 | grep -i verify

        # Test package manager connectivity
        dnf repolist
        ```

    2. Mount the certificate NFS share and copy the certificate manually:

        ```bash title="Run on: compute node"
        mount | grep /cert || mount -t nfs <admin_nic_ip>:<share_path>/cert /cert
        cp /cert/pulp_webserver.crt /etc/pki/ca-trust/source/anchors/
        update-ca-trust
        ```

    3. Verify package manager connectivity:

        ```bash title="Run on: compute node"
        dnf repolist
        dnf makecache
        ```

    4. If the issue recurs on re-provisioned nodes, verify the NFS export for the `/cert` directory is accessible from the node network.

## Container Image Pull Fails From Pulp Mirror

???+ note "Symptom"

    - Container images (SIF format) fail to download on Slurm/HPC nodes.
    - `/var/log/apptainer_pull.log` shows pull failures.
    - Expected container images are missing under `/hpc_tools/container_images`.

    Example errors in `/var/log/container_image_download.log` or `/var/log/apptainer_pull.log`:

    ```text title="Expected output"
    [ERROR] Failed to pull container image from Pulp mirror (exit code: 1).
    [INFO] Image may not be available in Pulp or download was interrupted.
    Error: error pulling image: unable to pull <image>: Error initializing source
    TIMEOUT: Container image pull timed out after 1800 seconds
    ```

??? note "Cause"

    - Repository Manager did not synchronize the container image selected by
      the catalog.
    - Pulp mirror endpoint is unreachable from the node (firewall, network issues).
    - Pulp certificate not trusted on the node (see [Pulp certificate trust failure](#pulp-certificate-trust-failure-on-compute-nodes) above).
    - Image tag mismatch between `container_image.list` and what is available in Pulp.

??? note "Resolution"

    1. Check download logs and image status:

        ```bash title="Run on: compute node"
        # Check download log
        tail -50 /var/log/container_image_download.log
        tail -50 /var/log/apptainer_pull.log

        # Check if Pulp mirror is reachable from the node
        curl -sk https://<admin_nic_ip>:2225/v2/_catalog

        # Check what images are expected
        cat /hpc_tools/scripts/container_image.list

        # Check downloaded images
        ls -lh /hpc_tools/container_images/
        ```

    2. Verify the container image exists in Pulp. From the OIM:

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        pulp container repository list
        ```

    3. If the image is missing in Pulp, ensure that it is included in the
       catalog selected by `CATALOG_FILE_PATH`, and rerun Repo Manager.

    4. If the image exists in Pulp but the pull fails, verify certificate trust (see [Pulp certificate trust failure](#pulp-certificate-trust-failure-on-compute-nodes)) and re-run the download script:

        ```bash title="Run on: compute node"
        /hpc_tools/scripts/download_container_image.sh
        ```

## Upstream Repository Sync Failure Due to Stale Metadata (404 on Missing RPM (OR) Checksum Validation Issue)

???+ note "Symptom"

    The Repository Manager `download` phase fails during Pulp synchronization
    with a `404 Not Found` or checksum mismatch for a specific RPM package,
    even though the repository URL is reachable.

    Example errors:

    ```text title="Expected output"
    404, message='Not Found', url='https://<upstream-repo>/<package>-1.<arch>.rpm'
    ```

    ```text title="Expected output"
    Downloading Artifacts: corrupted downloaded file
    Checksum mismatch for <package>-1.<arch>.rpm: expected <expected_checksum>, got <actual_checksum>
    ```

??? note "Cause"

    - The upstream repository metadata (`repodata/*-primary.xml.gz`) references a package file that no longer exists on the server.
    - A newer version of the RPM (e.g., `-2`) has replaced the old version (e.g., `-1`) on the server, but the repository metadata was not regenerated and still lists both versions.
    - The upstream repository replaced a package file (same filename) with updated content, but the repository metadata still contains the old checksum. Pulp downloads the new file, compares it against the stale checksum in the metadata, and fails validation.
    - Pulp with `immediate` download policy (the default when `repo_config: always`) attempts to download **all** packages listed in the metadata. If any package returns HTTP 404 or fails checksum validation, the **entire sync fails** — there is no partial sync.

    !!! note

        This is an upstream repository issue (stale metadata on the vendor server) and cannot be resolved from the OIM side. The fix must come from the upstream repository owner (e.g., NVIDIA) regenerating their metadata with `createrepo_c --update`. However, the workarounds below allow syncing to proceed until the upstream metadata is corrected.

    **Example (CUDA RHEL10 Repository):**

    The NVIDIA CUDA repository for RHEL 10 x86_64 may list `cccl-13-3-13.3.3.3.1-1.x86_64.rpm` in metadata while only `cccl-13-3-13.3.3.3.1-2.x86_64.rpm` exists on the server:

    ```bash title="Verify the stale metadata entry"
    PRIMARY_FILE=$(curl -s "https://developer.download.nvidia.com/compute/cuda/repos/rhel10/x86_64/repodata/repomd.xml" \
      | grep -oP 'href="repodata/\K[^"]*primary\.xml\.gz')
    curl -s "https://developer.download.nvidia.com/compute/cuda/repos/rhel10/x86_64/repodata/$PRIMARY_FILE" \
      | gunzip | grep "cccl-13-3-13.3.3.3.1"
    ```

    ```bash title="Confirm old package returns 404 and new returns 200"
    curl -I "https://developer.download.nvidia.com/compute/cuda/repos/rhel10/x86_64/cccl-13-3-13.3.3.3.1-1.x86_64.rpm"
    curl -I "https://developer.download.nvidia.com/compute/cuda/repos/rhel10/x86_64/cccl-13-3-13.3.3.3.1-2.x86_64.rpm"
    ```

??? note "Resolution"

    If the download fails because upstream metadata is stale, set the affected
    repository to `policy: partial` with `caching: true`. This selects Pulp's
    `on_demand` policy, which synchronizes metadata and defers package
    downloads. Download all required content before disconnecting the
    environment from the internet.

    1. List the available Pulp repository names to identify the correct `repoid` for the affected repository:

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        pulp rpm repository list --field name
        ```

        The output lists repository names such as `x86_64_rhel_10.0_cuda`, `aarch64_rhel_10.0_cuda`, etc. Use the appropriate name as the `--repoid` value and as the value of `cleanup_repos` when running `repo_manager.yml` with the `cleanup_repos` tag in the following steps.

    2. Clean up the affected repositories in Pulp before re-syncing. This removes any corrupted or partially synced content from previous failed attempts. Run this for both x86_64 and aarch64 repositories:

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd src/repo_manager/playbooks
        ansible-playbook repo_manager.yml --tags cleanup_repos \
          -e "cleanup_repos=x86_64_rhel_10.0_cuda,aarch64_rhel_10.0_cuda"
        ```

    3. Update the affected entry in the project-scoped configuration file
       at `<REPO_MANAGER_DATA_PATH>/input/<project>/repo_manager_config.yml`
       (default `/opt/omnia/repo_manager/input/project_default/repo_manager_config.yml`),
       then run the Repository Manager `download` phase:

        ```yaml title="Example: CUDA repository entries with caching: true"
        repositories:
          "10.0":
            x86_64:
              cuda:
                url: "https://developer.download.nvidia.com/compute/cuda/repos/rhel10/x86_64/"
                gpgkey: "https://developer.download.nvidia.com/compute/cuda/repos/rhel10/x86_64/repodata/repomd.xml.key"
                policy: partial
                caching: true
            aarch64:
              cuda:
                url: "https://developer.download.nvidia.com/compute/cuda/repos/rhel10/sbsa/"
                gpgkey: "https://developer.download.nvidia.com/compute/cuda/repos/rhel10/sbsa/repodata/repomd.xml.key"
                policy: partial
                caching: true
        ```

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd src/repo_manager/playbooks
        ansible-playbook repo_manager.yml --tags download
        ```

        Refer to the **Policy and Caching Behavior** table in the
        [Repository Manager configuration](../../Reference/Configuration/repo_manager_config.md)
        reference for the full mapping of policy and caching combinations.

    4. After Repository Manager completes with the partial policy, synchronize
       the entire required repository content from Pulp to a local directory.

        ```bash title="Run on: OIM host"
        dnf reposync --repoid=x86_64_rhel_10.0_cuda \
          --download-path=/path/to/download/directory \
          --download-metadata \
          --norepopath
        ```

    5. To download specific RPMs from the Pulp repository instead of the full sync, run for both x86_64 and aarch64 repositories:

        **Single package:**

        ```bash title="Run on: OIM host"
        dnf download --destdir /path/to/download/directory \
          --repo x86_64_rhel_10.0_cuda \
          package-name
        ```

        **Multiple specific packages:**

        ```bash title="Run on: OIM host"
        dnf download --destdir /path/to/download/directory \
          --repo x86_64_rhel_10.0_cuda \
          package1 package2 package3
        ```

    6. Report the stale metadata issue to the upstream repository owner (e.g., NVIDIA) so that `createrepo_c --update` is run on their server to remove the obsolete entry and update checksums.

!!! info

    - [Create Local Repositories](../../HowTo/repo_manager/configure_repos.md) -- Local repository setup guide.
    - [Log Management](../../Operations/log_management.md) -- Where to find logs for deeper diagnosis.
    - [Pulp Cleanup](../../Operations/pulp_cleanup.md) -- Pulp cleanup procedures.











