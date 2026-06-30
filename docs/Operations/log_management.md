
# Log Management


Omnia generates logs at multiple levels: Ansible playbook execution, container
service logs, cluster service logs, and operating system logs. Understanding
where logs are stored and how they are rotated is essential for diagnosing
issues and maintaining a healthy cluster.

## Log locations


### Playbook logs


All Ansible playbook execution logs are written to the OIM host filesystem,
even though playbooks run inside the `omnia_core` Podman container:

| Path | Description |
| --- | --- |
| `/opt/omnia/log/core/playbooks/` | Primary log directory for all Omnia playbook runs. Each playbook generates a timestamped log file (for example, `omnia_2024-01-15.log`). |
| `/opt/omnia/log/core/playbooks/discovery.log` | Node discovery and provisioning log. |
| `/opt/omnia/log/core/playbooks/local_repo.log` | Local repository logs. |
| `/opt/omnia/log/core/playbooks/prepare_oim.log` | Prepare OIM logs. |
| `/opt/omnia/log/core/playbooks/provision.log` | Provision logs. |
| `/opt/omnia/log/core/playbooks/omnia.log` | Main cluster deployment log (Slurm, Kubernetes, authentication). |
| `/opt/omnia/log/core/playbooks/scheduler.log` | Scheduler logs. |
| `/opt/omnia/log/core/playbooks/telemetry.log` | Telemetry stack deployment log. |
| `/opt/omnia/log/core/playbooks/utils.log` | Utility logs. |
| `/opt/omnia/log/core/playbooks/credential_utility.log` | Credential utility logs. |
| `/opt/omnia/log/core/playbooks/validation_omnia_project_default.log` | Omnia input validation report logs. |
| `/opt/omnia/log/core/playbooks/input_validation.log` | Omnia input validation playbook logs. |
| `/opt/omnia/log/openchami/*.log` | OpenCHAMI playbook logs. |
| `/opt/omnia/log/pulp/*.log` | Pulp container logs. |
| `/opt/omnia/log/local_repo/*.log` | Local repo logs. |
| `/opt/omnia/log/core/container/*.log` | Core container logs. |

Additionally, an aggregate of the events taking place during storage,
scheduler, and network role installation called `omnia.log` is created in
`/var/log`.

!!! tip

    To follow a playbook log in real time while a playbook is running, open a
    second terminal on the OIM host:

    ```bash
    tail -f /opt/omnia/log/core/playbooks/omnia.log
    ```


### Container logs


OIM services run as Podman containers. Access their logs with the ``podman
logs`` command:

```bash title="Run on: OIM host"
# List all running containers
podman ps

# View logs for a specific container
podman logs omnia_core
podman logs ochami-smd
podman logs ochami-bss
podman logs coredhcp

# Follow logs in real time
podman logs -f omnia_core

# View only the last 100 lines
podman logs --tail 100 omnia_core
```


| Container | What it logs |
| --- | --- |
| `omnia_core` | Ansible execution output, SSH connections to managed nodes. |
| `ochami-smd` | OpenCHAMI State Manager Daemon: node inventory, hardware discovery. |
| `ochami-bss` | Boot Script Service: PXE boot script generation, boot requests. |
| `coredhcp` | DHCP lease assignments during provisioning. |
| `pulp` | Repository sync status, package downloads. |

### OpenCHAMI logs


OpenCHAMI components write structured JSON logs accessible via Podman:

```bash title="Run on: OIM host"
# SMD logs (node state changes)
podman logs ochami-smd 2>&1 | jq '.'

# BSS logs (boot requests)
podman logs ochami-bss 2>&1 | jq '.'
```


### Slurm logs


On Slurm cluster nodes, logs are stored in standard Slurm log directories:

| Path | Description |
| --- | --- |
| `/var/log/slurm/slurmctld.log` | Slurm controller daemon log (on the control node). |
| `/var/log/slurm/slurmd.log` | Slurm compute daemon log (on each compute node). |
| `/var/log/slurm/slurmdbd.log` | Slurm database daemon log (job accounting). |

```bash title="Run on: Slurm nodes"
# On the Slurm control node
tail -f /var/log/slurm/slurmctld.log

# On a compute node
tail -f /var/log/slurm/slurmd.log
```


### Kubernetes logs


On Kubernetes cluster nodes, use `kubectl` or `journalctl` to access logs:

```bash title="Run on: Kubernetes nodes"
# Pod logs
kubectl logs <pod_name> -n <namespace>

# Kubelet logs on a specific node
ssh <kube_node> journalctl -u kubelet -f
```



## Logrotate configuration


Omnia configures `logrotate` to manage log file sizes on the OIM and prevent
disk exhaustion. The default configuration rotates logs based on size and age.

### Default settings


```text title="File: /etc/logrotate.d/omnia"
# /etc/logrotate.d/omnia
/opt/omnia/log/core/playbooks/*.log {
    weekly
    rotate 12
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root root
}
```


This configuration:

- Rotates log files **weekly**.
- Keeps **12 rotated files** (approximately 3 months of history).
- **Compresses** rotated files with gzip (after a one-rotation delay).
- Skips rotation if the log file is missing or empty.

### Customizing logrotate


To adjust the rotation policy (for example, to rotate daily in high-throughput
environments):

1. Edit the logrotate configuration:

   ```bash
   vi /etc/logrotate.d/omnia
   ```


2. Change `weekly` to `daily` and adjust `rotate` to the desired number
   of files:

   ```text
   /opt/omnia/log/core/playbooks/*.log {
       daily
       rotate 30
       compress
       delaycompress
       missingok
       notifempty
       create 0640 root root
   }
   ```


3. Test the configuration:

   ```bash
   logrotate -d /etc/logrotate.d/omnia
   ```


4. Force an immediate rotation (optional):

   ```bash
   logrotate -f /etc/logrotate.d/omnia
   ```


### Slurm logrotate


Slurm logs are rotated separately. Omnia installs a Slurm-specific logrotate
configuration on the control node:

```text title="File: /etc/logrotate.d/slurm"
# /etc/logrotate.d/slurm
/var/log/slurm/*.log {
    weekly
    rotate 8
    compress
    delaycompress
    missingok
    notifempty
    sharedscripts
    postrotate
        /usr/bin/pkill -HUP slurmctld 2>/dev/null || true
        /usr/bin/pkill -HUP slurmd 2>/dev/null || true
    endscript
}
```



## Sample log output


A sample of the `omnia.log` is provided below:

```text title="Sample omnia.log output"
2021-02-15 15:17:36,877 p=2778 u=omnia n=ansible | [WARNING]: provided hosts
list is empty, only localhost is available. Note that the implicit localhost does not
match 'all'
2021-02-15 15:17:37,396 p=2778 u=omnia n=ansible | PLAY [Executing omnia roles]
************************************************************************************
2021-02-15 15:17:37,454 p=2778 u=omnia n=ansible | TASK [Gathering Facts]
*****************************************************************************************
2021-02-15 15:17:38,856 p=2778 u=omnia n=ansible | ok: [localhost]
2021-02-15 15:17:38,885 p=2778 u=omnia n=ansible | TASK [common : Mount Path]
**************************************************************************************
2021-02-15 15:17:38,969 p=2778 u=omnia n=ansible | ok: [localhost]
```

These logs are intended to enable debugging.

!!! note

    The Omnia product recommends that product users apply masking rules on
    personal identifiable information (PII) in the logs before sending to
    external monitoring applications or sources.


## Logging format


Every log message begins with a timestamp and also carries information on the
invoking play and task. The format is described in the following table:

| Field | Format | Sample Value |
| --- | --- | --- |
| Timestamp | `yyyy-mm-dd h:m:s` | `2021-02-15 15:17` |
| Process ID | `p=xxxx` | `p=2778` |
| User | `u=xxxx` | `u=omnia` |
| Name of the process executing | `n=xxxx` | `n=ansible` |
| The task being executed/invoked | `PLAY/TASK` | `PLAY [Executing omnia roles]` / `TASK [Gathering Facts]` |
| Error | `fatal: [hostname]: Error Message` | `fatal: [localhost]: FAILED! => {"msg": "lookup_plugin.lines}` |
| Warning | `[WARNING]: warning message` | `[WARNING]: provided hosts list is empty` |


## Troubleshooting log issues


| Issue | Resolution |
| --- | --- |
| **Disk full on OIM** | Check log sizes: `du -sh /opt/omnia/log/core/playbooks/`. Force logrotate: `logrotate -f /etc/logrotate.d/omnia`. Remove old compressed logs if needed. |
| **No playbook logs appearing** | Verify the `omnia_core` container is running: `podman ps`. Check that the log volume is mounted: `podman inspect omnia_core \| grep -A5 Mounts`. |
| **Container logs too verbose** | Adjust the log level in the container's configuration file and restart the container: `podman restart <container_name>`. |
| **Slurm logs not rotating** | Verify logrotate configuration exists: `cat /etc/logrotate.d/slurm`. Test with: `logrotate -d /etc/logrotate.d/slurm`. Check if `crond` is running: `systemctl status crond`. |

!!! info

    - [General](../Troubleshooting/general.md) -- General troubleshooting that uses logs
      as a primary diagnostic tool.
    - [Best Practices Checklist](best_practices_checklist.md) -- Storage and maintenance best practices.
