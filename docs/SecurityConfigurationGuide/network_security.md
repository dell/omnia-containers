# Network Security

Omnia configures the firewall as required by the third-party tools to enhance security by restricting inbound and outbound traffic to the TCP and UDP ports.

## Network Exposure

Omnia uses port 22 for SSH connections, same as Ansible.

## Firewall Settings

Omnia configures the following ports for use by third-party tools installed by Omnia.

### Host Port Requirements

| Port Number | Protocol | Service | Type of Node |
|-------------|----------|---------|--------------|
| 22 | TCP | SSH | All Nodes |
| 2049 | TCP/UDP | NFS Server | Manager (OIM) |
| 111 | TCP/UDP | RPC Bind | Manager (OIM) |
| 20048 | TCP/UDP | NFS mountd | Manager (OIM) |
| 123 | UDP | NTP | Manager (OIM) |
| 53 | TCP/UDP | DNS – Cluster | Manager (OIM) |
| 9153 | TCP | DNS Metrics | Manager (OIM) |
| 53 | TCP/UDP | DNS – Podman Internal | Manager (OIM) |
| 67 | UDP | DHCP | Manager (OIM) |
| 68 | UDP | DHCP BootPC | Manager (OIM) |
| 69 | UDP | TFTP | Manager (OIM) |
| 3702 | UDP | WS-Discovery (OS) | Manager (OIM) |
| 5353 | UDP | mDNS (OS) | Manager (OIM) |
| 631 | TCP | CUPS printing (OS) | Manager (OIM) |

### Podman Container Port Requirements

| Port | Protocol | Service Name | Type of Node |
|---|---|---|---|
|2225|TCP|Pulp Content Service|Manager (OIM)|
|5000|TCP|OCI Registry|Manager (OIM)|
|9000|TCP|MinIO S3 API|Manager (OIM)|
|9001|TCP|MinIO Console|Manager (OIM)|

### Kubernetes Port Requirements

| Port Number | Protocol | Service | Type of Node |
|---|---|---|---|
|6443|TCP|Kubernetes API server|Manager|
|2379-2380|TCP|etcd server client API|Manager|
|10251|TCP|Kube-scheduler|Manager|
|10252|TCP|Kube-controller manager|Manager|
|10250|TCP|Kubelet API|Compute|
|30000-32767|TCP|NodePort services|Compute|
|5473|TCP|Calico services|Manager/Compute|
|179|TCP|Calico services|Manager/Compute|
|4789|UDP|Calico services|Manager/Compute|
|8285|UDP|Flannel services|Manager/Compute|
|8472|UDP|Flannel services|Manager/Compute|
|10256|TCP|kube-proxy health check|Manager + Compute|
|7472|TCP|MetalLB L2 speaker Prometheus metrics|Manager + Compute|
|7946|TCP|MetalLB gossip/memberlist|Manager + Compute|
|2112|TCP|kube-vip Prometheus metrics + health|Manager|
|10257|TCP|Controller manager secure HTTPS port|Manager|
|10259|TCP|Scheduler secure HTTPS port|Manager|
|10249|TCP|kube-proxy Prometheus metrics|Manager + Compute|
|10248|TCP|kubelet local health check|Manager + Compute|
|9099|TCP|Calico Felix health check|Manager + Compute|
|53|TCP/UDP|Kubernetes CoreDNS|Manager|
|443|TCP|NFS StorageClass dynamic provisioner|Compute|
|45845|TCP|CRI-O runtime service|Manager/Compute|
|18515-18520|TCP|DOCA/OFED RDMA and InfiniBand communication port range|Compute|

### Slurm Port Requirements

| Port | Protocol | Service Name | Type of Node |
|---|---|---|---|
|6817|TCP/UDP|slurmctld|Manager (Slurm)|
|6818|TCP/UDP|slurmd|Compute (Slurm)|
|6819|TCP/UDP|slurmdbd|Manager (Slurm)|
|60001-63000|TCP|Slurm SrunPortRange|Manager + Compute|
|3306|TCP|MariaDB|Manager|

### OpenLDAP Port Requirements

| Port Number | Layer 4 Protocol | Purpose | Node |
|-------------|------------------|---------|------|
| 389 | TCP | LDAP with StartTLS when `ldap_connection_type` is `TLS` | OIM-hosted `omnia_auth`; Slurm and login clients |
| 636 | TCP | LDAPS when `ldap_connection_type` is `SSL` | OIM-hosted `omnia_auth`; Slurm and login clients |

The `omnia_auth` Quadlet publishes both ports. Provisioned clients use the port
selected by `ldap_connection_type`; ports 80 and 443 are not OpenLDAP ports.

### Telemetry Ports

Telemetry ports are service-cluster traffic requirements. The iDRAC MySQL
service is a headless Kubernetes service and is not exposed as a LoadBalancer,
NodePort, or customer-facing database endpoint. Ports 3306 and 33060 must remain
restricted to the trusted service-cluster network.

| Port | Protocol | Service Name | Type of Node |
|---|---|---|---|
|8161|TCP|ActiveMQ Console|Manager (Telemetry K8s)|
|61613|TCP|ActiveMQ STOMP (port 1)|Manager (Telemetry K8s)|
|61616|TCP|ActiveMQ STOMP (port 2)|Manager (Telemetry K8s)|
|8082|TCP|Telemetry Config UI|Manager (Telemetry K8s)|
|3306|TCP|iDRAC MySQL primary (cluster internal)|Service Kubernetes cluster|
|33060|TCP|iDRAC MySQL X Protocol (cluster internal)|Service Kubernetes cluster|
|9092|TCP|Kafka broker plaintext|Manager (Telemetry K8s)|
|9093|TCP|Kafka broker TLS|Manager (Telemetry K8s)|
|9094|TCP|Kafka LoadBalancer|Manager (Telemetry K8s)|
|8443|TCP|VictoriaMetrics service|Manager (Telemetry K8s)|
|8480|TCP|VictoriaMetrics Insert LB|Manager (Telemetry K8s)|
|8481|TCP|VictoriaMetrics Query LB|Manager (Telemetry K8s)|
|2112|TCP|vmagent self-metrics|Manager (Telemetry K8s)|
|8429|TCP|vmagent remote_write receiver|Manager (Telemetry K8s)|
|9427|TCP|vlagent JSON Lines receiver|Manager (Telemetry K8s)|
|9481|TCP|VictoriaLogs vlinsert|Manager (Telemetry K8s)|
|9491|TCP|VictoriaLogs vlstorage health|Manager (Telemetry K8s)|
|9471|TCP|VictoriaLogs vlselect query|Manager (Telemetry K8s)|
|8687|TCP|vector-ldms health|Manager (Telemetry K8s)|
|9599|TCP|vector-ldms metrics|Manager (Telemetry K8s)|
|8688|TCP|vector-ome health|Manager (Telemetry K8s)|
|9600|TCP|vector-ome metrics|Manager (Telemetry K8s)|
|514|TCP/UDP|Syslog plaintext (VLAgent)|Manager (Telemetry K8s)|
|6514|TCP|Syslog TLS (VLAgent)|Manager (Telemetry K8s)|
|6001-6100|TCP|LDMS aggregator|Manager (Telemetry)|
|6001-6100|TCP|LDMS store daemon|Manager (Telemetry)|
|10001-10100|TCP|LDMS sampler|Compute|

### BuildStreaM Ports

BuildStreaM is optional. Open only the paths required for the selected
deployment. The API and GitLab HTTPS ports are configurable in
`build_stream_config.yml`.

| Condition | Source | Destination | Direction | Port and protocol | Purpose | TLS and authentication | Exposure |
|---|---|---|---|---|---|---|---|
| BuildStreaM enabled | GitLab runner or another authorized API client | OIM `build_stream_host_ip` | Inbound to OIM | TCP 8010 by default (`build_stream_port`) | BuildStreaM API | HTTPS. Client registration uses HTTP Basic authentication; token requests use the registered client credentials; protected operations use JWT bearer tokens and, where required, scopes. | The BuildStreaM role opens the configured port in the OIM firewall. Restrict it to intended API clients. |
| Managed GitLab enabled | OIM | GitLab host | Outbound from OIM | TCP 443 by default (`gitlab_https_port`) | Configure GitLab and its managed project, runner, and pipeline variables through the GitLab API | HTTPS with the Omnia-generated GitLab certificate. The deployment tasks authenticate with the GitLab root token and currently disable server-certificate verification. | The GitLab role opens the configured HTTPS port on the GitLab host. Restrict it to administrators, the OIM, and intended GitLab clients. |
| Managed GitLab enabled | OIM | GitLab host | Outbound from OIM | TCP 22 | Initial host administration and passwordless SSH setup | The initial connection uses the stored GitLab SSH password; the role then installs an SSH public key. | The GitLab role opens TCP 22 on the GitLab host. Restrict administrative SSH access. |
| BuildStreaM enabled | BuildStreaM API container | PostgreSQL container on the OIM | Local host communication | TCP 5432 | Store BuildStreaM jobs, stages, image metadata, audit events, and related state | PostgreSQL username and password. Both containers use host networking; the connection is to `localhost` and is not configured for TLS. | The BuildStreaM PostgreSQL role does not add an external firewall rule for 5432. Do not expose it outside the OIM. |

### DOCA/IB Ports

| Port | Protocol | Service Name | Type of Node |
|---|---|---|---|
|18515-18520|TCP/UDP|DOCA/OFED RDMA|Compute (IB nodes)|

### OpenCHAMI Ports

| Port | Protocol | Service Name | Type of Node |
|---|---|---|---|
|5432|TCP|PostgreSQL firewall allowance|Manager (OIM)|
|27778|TCP|OpenCHAMI compatibility firewall allowance|Manager (OIM)|
|27779|TCP|SMD firewall allowance|Manager (OIM)|
|8081|TCP|HAProxy HTTP gateway for PXE boot and metadata requests|Manager (OIM)|
|8443|TCP|HAProxy HTTPS API gateway|Manager (OIM)|
|67/68|UDP|CoreDHCP and PXE clients|Manager (OIM)|
|69|UDP|TFTP|Manager (OIM)|
|53|TCP/UDP|CoreDNS|Manager (OIM)|

The containers for `boot-service` (TCP 8081), `metadata-service` (TCP 8080),
TokenSmith (TCP 8080), SMD (TCP 27779), PostgreSQL (TCP 5432), and step-ca
communicate on internal Podman networks. HAProxy publishes host ports 8081
and 8443 and routes requests to the applicable internal service. The current
deployment also creates host-firewall allowances for TCP 5432, 27778, and
27779; 27778 is retained as an OpenCHAMI compatibility allowance and has no
standalone service in the Fabrica deployment. The deployment does not run
standalone BSS, cloud-init-server, Hydra, or OPAAL services.

## Data Security

Omnia persists configuration, credentials, operational state, artifacts, and
logs. The principal data locations and controls are listed below. Paths use the
configured `OMNIA_DATA_PATH` and `OMNIA_PROJECT_NAME` values unless otherwise
stated.

| Data class | Primary location | Owner and access boundary | Protection implemented by Omnia | Retention and cleanup |
|---|---|---|---|---|
| Domain input, output, and runtime data | `<OMNIA_DATA_PATH>/<domain>/input/<project>/`, `output/<project>/`, and domain-specific runtime paths | OIM administrators and the domain processes that consume the files | Input schemas and domain validation protect the configuration contract; general configuration and output files are not encrypted by Omnia. | Persists until replaced or removed by the applicable domain cleanup. Cleanup behavior differs by domain and option. |
| Playbook and service logs | `/var/log/omnia/<domain>/`, domain log directories, systemd journal, and container logs | OIM administrators; cluster-node administrators for node-local logs | File permissions and host access controls apply. Logs are not generally encrypted by Omnia. | Rotation varies by log producer. Omnia provides an OIM log-backup utility but does not configure a universal retention or backup policy. |
| Domain credentials and Vault material | `<OMNIA_DATA_PATH>/<domain>/input/<project>/*credentials.yml` and the corresponding Vault key | OIM root or trusted administrators and the owning domain | Credential YAML files are encrypted with Ansible Vault. Credential and Vault-key files are assigned restrictive permissions; the key must be protected separately. Runtime service configuration or Kubernetes Secrets can contain derived or copied values and rely on the destination platform's access controls. | Domain cleanup normally removes credentials unless that workflow provides and is run with a preservation option. Back up an encrypted credential file and its matching key together when recovery is required. |
| Pulp repositories and service state | `<REPO_MANAGER_DATA_PATH>/pulp_config/`, or configured dedicated Pulp storage paths | OIM administrators and Pulp services | Pulp is served over HTTPS and uses authenticated administrative access. Omnia does not configure storage encryption for Pulp content or its PostgreSQL data. | Repository Manager cleanup can remove Pulp configuration, database, content, and logs. Back up required repository content before destructive cleanup. |
| Image Build Manager objects and images | `<IMAGE_BUILD_MANAGER_DATA_PATH>/s3/data`, `oci/data`, and build/runtime directories | OIM administrators and the MinIO, registry, and image-build services | MinIO access and secret keys are stored in the Image Build Manager Vault file. The locally managed MinIO and OCI registry data paths are not encrypted by Omnia; the local services are not configured with TLS by this workflow. | Full Image Build Manager cleanup removes locally managed MinIO, registry, artifacts, runtime data, and logs. Selective artifact cleanup can preserve the services. |
| BuildStreaM API state and artifacts | `<OMNIA_DATA_PATH>/build_stream_root/` and `<OMNIA_DATA_PATH>/postgres/data` | OIM administrators and the BuildStreaM and PostgreSQL services | API traffic uses HTTPS and protected operations use JWT authentication. PostgreSQL credentials originate in the BuildStreaM Vault file. Omnia does not configure encryption at rest or TLS for the local PostgreSQL connection. | BuildStreaM cleanup removes API runtime data and credentials. PostgreSQL data is preserved by default and is deleted when cleanup is run with `postgres_backup=false`; that option controls preservation and does not create a backup. |
| Managed GitLab data | `/etc/gitlab`, `/var/opt/gitlab`, `/var/log/gitlab`, and runner configuration on the GitLab host | GitLab-host administrators and GitLab services | GitLab uses HTTPS and its native accounts, tokens, project permissions, and secret-variable controls. Omnia does not configure disk encryption for GitLab data. | Full BuildStreaM cleanup removes the managed GitLab deployment and its data. Back up required repositories and configuration first. |
| Provisioning and OpenCHAMI state | Orchestrator project paths, `<OMNIA_DATA_PATH>/openchami/workdir/`, and OpenCHAMI service volumes | OIM administrators and the provisioning services | Service authentication, file permissions, and host/container access controls apply. Omnia does not configure general encryption at rest for these paths or volumes. | Orchestrator cleanup removes selected generated state and, in RC1, OpenCHAMI persistent service volumes. Review the cleanup selection before execution. |
| Telemetry state | Kafka, VictoriaMetrics, VictoriaLogs, and iDRAC MySQL persistent volumes, plus Telemetry project data | Kubernetes administrators and the applicable source and sink services | Internal telemetry connections use the controls configured for each component, including mTLS where documented. Kubernetes Secret values are encoded, not encrypted at rest unless encryption is enabled separately for the cluster. | Source-owned volumes are removed by Telemetry cleanup. Kafka, VictoriaMetrics, and VictoriaLogs volumes are preserved by default. Component retention settings apply while the services are running. |

Omnia does not establish a universal data-retention, backup, or storage-encryption
policy. The site administrator owns backup selection, protection of backup media,
host and Kubernetes access, and encryption at rest. Review
[OIM cleanup](../Operations/oim_cleanup.md) and
[log management](../Operations/log_management.md) before deleting or exporting
data.

Run the following command routinely on the OIM for the latest RHEL security
updates.

```bash
yum update --security
```

For more information on the passwords used by Omnia, see [Login Security Settings](product_subsystem_security.md#login-security-settings)

## Auditing and Logging

!!! note

    All log paths referenced in this section are on the OIM host filesystem.

Omnia writes domain execution logs and service logs on the OIM. The primary
locations are listed below.

**Omnia Log File Locations**

| Location | Purpose |
|----------|---------|
| `/var/log/omnia/discovery/discovery.log` | Discovery playbook log |
| `/var/log/omnia/repo_manager/repo_manager.log` | Repo Manager playbook log |
| `/var/log/omnia/image_build_manager/image_build_manager.log` | Image Build Manager playbook log |
| `/var/log/omnia/orchestrator/orchestrator.log` | Orchestrator playbook log |
| `/var/log/omnia/telemetry/telemetry.log` | Telemetry playbook log |
| `/var/log/omnia/build_stream/build_stream.log` | BuildStreaM playbook log |
| `/var/log/omnia/utils/utils.log` | Utils playbook log |
| `$OMNIA_DATA_PATH/orchestrator/log/openchami/` | OpenCHAMI logs |
| `<OMNIA_DATA_PATH>/repo_manager/log/` | Repository processing and Pulp logs |

The Orchestrator data root is `<OMNIA_DATA_PATH>/orchestrator`.

Omnia writes the domain-specific logs listed above; the current implementation
does not create an aggregate `/var/log/omnia.log`. Third-party tools installed
by Omnia generate their own separate logs.

!!! note

    Omnia recommends applying masking rules to personally identifiable information (PII) in log files before sending them to external monitoring applications or other third-party destinations.


## Network Vulnerability Scanning

Omnia performs network and application security scans on all modules of the product. Omnia additionally performs Blackduck scans on the open source softwares, which are installed by Omnia at runtime. However, Omnia is not responsible for the third-party software installed using Omnia. Review all third party software before using Omnia to install it.

If you have any feedback about Omnia documentation, please reach out at [omnia.readme@dell.com](mailto:omnia.readme@dell.com).






