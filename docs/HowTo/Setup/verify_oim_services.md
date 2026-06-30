
# Verify OIM Services


Perform a comprehensive health check of all Omnia Infrastructure Manager (OIM)
services after running `prepare_oim.yml`. This guide walks through every
service in the `omnia.target` dependency tree.

## Overview


After the OIM is prepared, the following services should be running as
systemd-managed Podman containers:

- **omnia_core** -- Ansible control plane
- **OpenCHAMI stack** -- SMD, BSS, CoreDHCP, TFTP, DNS, and related services
- **Pulp** -- RPM repository management
- **MinIO** -- S3-compatible object storage
- **Registry** -- Local container image registry
- **Omnia Auth** *(optional)* -- Centralized authentication

This guide helps you verify each service is healthy and troubleshoot any that
are not.


## Prerequisites


- The [Prepare Oim](prepare_oim.md) procedure has been completed.
- You have `root` or `sudo` access to the OIM host.


## Procedure


1. **Check the omnia_core service**:

   ```bash title="Run on: OIM host"
   systemctl status omnia_core.service
   ```


   Expected: `Active: active (running)`

2. **List the complete omnia.target dependency tree**:

   ```bash title="Run on: OIM host"
   systemctl list-dependencies omnia.target
   ```


   Expected output:

   ```text title="Expected output on: OIM host"
   omnia.target
   ├─minio.service
   ├─omnia_auth.service
   ├─omnia_core.service
   ├─pulp.service
   ├─registry.service
   └─openchami.target
     ├─bss.service
     ├─coredhcp.service
     ├─cloud-init-server.service
     ├─dnsmasq.service
     ├─hydra.service
     ├─image-server.service
     ├─opaal.service
     ├─smd.service
     └─tftpd.service
   ```


3. **Check each top-level service individually**:

   ```bash title="Run on: OIM host"
   for svc in minio omnia_auth omnia_core pulp registry; do
     echo "=== $svc ==="
     systemctl is-active ${svc}.service
   done
   ```


4. **Check OpenCHAMI sub-services**:

   ```bash title="Run on: OIM host"
   for svc in bss coredhcp cloud-init-server dnsmasq hydra image-server opaal smd tftpd; do
     echo "=== $svc ==="
     systemctl is-active ${svc}.service
   done
   ```


5. **Verify running Podman containers**:

   ```bash title="Run on: OIM host"
   podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
   ```


6. **Test the OpenCHAMI CLI**:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```


   ```bash title="Run on: omnia_core container"
   ochami --help
   ```


   Useful `ochami` commands:

   ```bash title="Run on: omnia_core container"
   # List discovered nodes
   ochami node list

   # Check SMD status
   ochami smd status

   # List boot configurations
   ochami bss list
   ```


7. **Test MinIO / S3 access**:

   ```bash title="Run on: omnia_core container"
   s3cmd ls
   ```


8. **Test Pulp accessibility**:

   ```bash title="Run on: OIM host"
   curl -s http://localhost:8080/pulp/api/v3/status/ | python3 -m json.tool
   ```


   Expected: a JSON response with `"online_workers"` and `"versions"`.


## Verification


All services should report `active (running)`. Use this summary check:

```bash title="Run on: OIM host"
systemctl is-active omnia.target
```


Expected output: `active`

If any service is `inactive` or `failed`, note which one and refer to the
Troubleshooting section below.

**Quick health summary script**:

```bash title="Run on: OIM host"
echo "=== Omnia Service Health ==="
echo "omnia.target:    $(systemctl is-active omnia.target)"
echo "omnia_core:      $(systemctl is-active omnia_core.service)"
echo "openchami.target:$(systemctl is-active openchami.target)"
echo "pulp:            $(systemctl is-active pulp.service)"
echo "minio:           $(systemctl is-active minio.service)"
echo "registry:        $(systemctl is-active registry.service)"
echo "omnia_auth:      $(systemctl is-active omnia_auth.service)"
```



## Next Steps


- [Create Local Repos](create_local_repos.md) -- Sync RPM repositories via Pulp.
- [Build Cluster Images](build_cluster_images.md) -- Build OS boot images.
- [Discover Nodes](discover_nodes.md) -- Discover and provision bare-metal servers.


## Troubleshooting


**A service shows "inactive (dead)"**
   Restart the specific service:

   ```bash title="Run on: OIM host"
   systemctl restart <service-name>.service
   journalctl -u <service-name>.service --no-pager -n 50
   ```


**OpenCHAMI services fail with connection errors**
   Verify the SMD service is running first, as other OpenCHAMI services
   depend on it:

   ```bash title="Run on: OIM host"
   systemctl restart smd.service
   sleep 10
   systemctl restart openchami.target
   ```


**Pulp API returns connection refused**
   Check that the Pulp container is running and listening on port 8080:

   ```bash title="Run on: OIM host"
   podman logs pulp
   ss -tlnp | grep 8080
   ```


**MinIO not accessible**
   Verify MinIO container status and port binding:

   ```bash title="Run on: OIM host"
   podman logs minio
   ss -tlnp | grep 9000
   ```


**omnia.target not found**
   Re-run the `prepare_oim.yml` playbook to regenerate systemd unit files:

   ```bash title="Run on: omnia_core container"
   cd /omnia/prepare_oim
   ansible-playbook prepare_oim.yml --ask-vault-pass
   ```


**Container images missing**
   Rebuild the container images:

   ```bash title="Run on: OIM host"
   cd /opt/omnia
   bash build_images.sh core
   ```
