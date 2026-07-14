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
| 2222 | TCP | SSH — Omnia Core Relay | Manager (OIM) |
| 2049 | TCP/UDP | NFS Server | Manager (OIM) |
| 111 | TCP/UDP | RPC Bind | Manager (OIM) |
| 20048 | TCP/UDP | NFS mountd | Manager (OIM) |
| 123 | UDP | NTP | Manager (OIM) |
| 53 | TCP/UDP | DNS – Cluster | Manager (OIM) |
| 9153 | TCP | DNS Metrics | Manager (OIM) |
| 53 | TCP/UDP | DNS – Podman Internal | Manager (OIM) |
| 67 | UDP | DHCP | Manager (OIM) |
| 68 | UDP | DHCP BootPC | Manager (OIM) |

### Podman Container Port Requirements

| Port | Protocol | Service Name | Type of Node |
|---|---|---|---|
|2222|TCP|Omnia Core|Manager (OIM)|
|2225|TCP|Pulp Content Service|Manager (OIM)|
|5000|TCP|OCI Registry|Manager (OIM)|
|9000|TCP|MinIO S3 API|Manager (OIM)|
|9001|TCP|MinIO Console|Manager (OIM)|
|389|TCP|OpenLDAP|Manager (OIM)|

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

### Slurm Port Requirements

| Port Number | Layer 4 Protocol | Purpose | Node |
|-------------|------------------|---------|------|
| 6817 | TCP/UDP | Slurmctld Port | Manager |
| 6818 | TCP/UDP | Slurmd Port | Compute |
| 6819 | TCP/UDP | Slurmdbd Port | Manager |
| 60001-63000 | TCP | Slurm SrunPortRange | Compute |
| 3306 | TCP | MariaDB | Manager |

### OpenLDAP Port Requirements

| Port Number | Layer 4 Protocol | Purpose | Node |
|-------------|------------------|---------|------|
| 80 | TCP | HTTP | Manager / Login Node |
| 443 | TCP | HTTPS | Manager / Login Node |
| 389 | TCP | LDAP | Manager / Login Node |
| 636 | TCP | LDAPS | Manager / Login Node |

### Telemetry Ports

| Port | Protocol | Service Name | Type of Node |
|---|---|---|---|
|8161|TCP|ActiveMQ Console|Manager (Telemetry K8s)|
|61613|TCP|ActiveMQ STOMP|Manager (Telemetry K8s)|
|61616|TCP|ActiveMQ STOMP|Manager (Telemetry K8s)|
|8082|TCP|Telemetry Config UI|Manager (Telemetry K8s)|
|3306|TCP|MySQL|Manager (Telemetry K8s)|
|33060|TCP|MySQL X Protocol|Manager (Telemetry K8s)|
|9092|TCP|Kafka plaintext|Manager (Telemetry K8s)|
|9093|TCP|Kafka TLS|Manager (Telemetry K8s)|
|9094|TCP|Kafka LoadBalancer|Manager (Telemetry K8s)|
|8443|TCP|VictoriaMetrics Service|Manager (Telemetry K8s)|
|8480|TCP|VictoriaMetrics Insert LB|Manager (Telemetry K8s)|
|8481|TCP|VictoriaMetrics Query LB|Manager (Telemetry K8s)|
|2112|TCP|vmagent metrics|Manager (Telemetry K8s)|
|8429|TCP|vmagent remote_write|Manager (Telemetry K8s)|
|9427|TCP|vlagent JSON receiver|Manager (Telemetry K8s)|
|9481|TCP|VictoriaLogs vlinsert|Manager (Telemetry K8s)|
|9491|TCP|VictoriaLogs health|Manager (Telemetry K8s)|
|9471|TCP|VictoriaLogs query|Manager (Telemetry K8s)|
|8687|TCP|vector-ldms health|Manager (Telemetry K8s)|
|9599|TCP|vector-ldms metrics|Manager (Telemetry K8s)|
|8688|TCP|vector-ome health|Manager (Telemetry K8s)|
|9600|TCP|vector-ome metrics|Manager (Telemetry K8s)|
|514|TCP/UDP|Syslog|Manager (Telemetry K8s)|
|6514|TCP|Syslog TLS|Manager (Telemetry K8s)|
|6001-6100|TCP|LDMS Aggregator / Store Daemon|Manager (Telemetry)|
|10001-10100|TCP|LDMS Sampler|Compute|

### Build Stream Ports

| Port | Protocol | Service Name | Type of Node |
|---|---|---|---|
|8010|TCP|Build Stream API|Manager (OIM)|

### DOCA/IB Ports

| Port | Protocol | Service Name | Type of Node |
|---|---|---|---|
|18515-18520|TCP/UDP|DOCA/OFED RDMA|Compute (IB nodes)|

### OpenCHAMI Ports

| Port | Protocol | Service Name | Type of Node |
|---|---|---|---|
|8081|TCP|HAProxy HTTP|Manager (OIM)|
|8443|TCP|HAProxy HTTPS|Manager (OIM)|
|27779|TCP|SMD|Manager (OIM)|
|27778|TCP|BSS|Manager (OIM)|
|5432|TCP|PostgreSQL|Manager (OIM)|
|9000|TCP|Step CA|Manager (OIM)|
|4444/4445|TCP|Hydra OAuth2|Manager (OIM)|
|67/69|UDP|CoreDHCP|Manager (OIM)|
|53|TCP/UDP|CoreDNS|Manager (OIM)|

## Data Security

Omnia does not store data. The passwords Omnia accepts as input to configure the third party tools are validated and then encrypted using Ansible Vault. Run the following commands routinely on the OIM for the latest RHEL security updates.

```bash
yum update --security
```

For more information on the passwords used by Omnia, see [Login Security Settings](product_subsystem_security.md#login-security-settings)

## Auditing and Logging

Omnia creates and stores log files related to containers at `<nfs_share_path>/omnia/log`.The events during the installation of Omnia are captured as logs. For different roles called by Omnia, separate log files are created as listed below:

**Omnia Log File Locations**

| Location | Purpose |
|----------|---------|
| `/opt/omnia/log/core/playbooks/discovery.log` | Discovery logs |
| `/opt/omnia/log/core/playbooks/local_repo.log` | Local Repository logs |
| `/opt/omnia/log/core/playbooks/prepare_oim.log` | Prepare OIM logs |
| `/opt/omnia/log/core/playbooks/provision.log` | Provision logs |
| `/opt/omnia/log/core/playbooks/scheduler.log` | Scheduler logs |
| `/opt/omnia/log/core/playbooks/telemetry.log` | Telemetry logs |
| `/opt/omnia/log/core/playbooks/utils.log` | Utility logs |
| `/opt/omnia/log/core/playbooks/credential_utility.log` | Credential utility logs |
| `/opt/omnia/log/openchami/*.log` | OpenCHAMI playbook logs |
| `/opt/omnia/log/pulp/*.log` | Pulp container logs |
| `/opt/omnia/log/local_repo/*.log` | Local repository logs |
| `/opt/omnia/log/core/container/*.log` | Core container logs |
| `/opt/omnia/log/core/playbooks/validation_omnia_project_default.log` | Omnia input validation report logs |
| `/opt/omnia/log/core/playbooks/input_validation.log` | Omnia input validation playbook logs |

Additionally, an aggregate of the events taking place during storage, scheduler and network role installation called `omnia.log` is created in `/var/log`.

There are separate logs generated by the third party tools installed by Omnia.

## Logs

A sample of the omnia.log is provided below:

```bash
2021-02-15 15:17:36,877 p=2778 u=omnia n=ansible | [WARNING]: provided hosts
list is empty, only localhost is available. Note that the implicit localhost does not
match 'all'
2021-02-15 15:17:37,396 p=2778 u=omnia n=ansible | PLAY [Executing omnia roles]
************************************************************************************
2021-02-15 15:17:37,454 p=2778 u=omnia n=ansible | TASK [Gathering Facts]
*****************************************************************************************
*
2021-02-15 15:17:38,856 p=2778 u=omnia n=ansible | ok: [localhost]
2021-02-15 15:17:38,885 p=2778 u=omnia n=ansible | TASK [common : Mount Path]
**************************************************************************************
2021-02-15 15:17:38,969 p=2778 u=omnia n=ansible | ok: [localhost]
...
```

These logs are intended to enable debugging.

!!! note

    Omnia recommends applying masking rules to personally identifiable information (PII) in log files before sending them to external monitoring applications or other third-party destinations.

## Logging Format

Every log message begins with a timestamp and also carries information on the invoking play and task.

The format is described in the following table.

**Log Format Reference**

| Field | Format | Sample Value |
|-------|--------|--------------|
| Timestamp | `yyyy-mm-dd h:m:s` | `2021-02-15 15:17:36` |
| Process ID | `p=xxxx` | `p=2778` |
| User | `u=xxxx` | `u=omnia` |
| Name of the Executing Process | `n=xxxx` | `n=ansible` |
| Task Being Executed | `PLAY` / `TASK` | `PLAY [Executing omnia roles]`<br>`TASK [Gathering Facts]` |
| Error | `fatal: [hostname]: Error Message` | `fatal: [localhost]: FAILED! => {"msg": "lookup_plugin.lines"}` |
| Warning | `[WARNING]: warning message` | `[WARNING]: provided hosts list is empty` |


## Network Vulnerability Scanning

Omnia performs network and application security scans on all modules of the product. Omnia additionally performs Blackduck scans on the open source softwares, which are installed by Omnia at runtime. However, Omnia is not responsible for the third-party software installed using Omnia. Review all third party software before using Omnia to install it.

If you have any feedback about Omnia documentation, please reach out at [omnia.readme@dell.com](mailto:omnia.readme@dell.com).
